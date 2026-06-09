"""
src/generator/pipeline.py
Main generation pipeline. Orchestrates persona → profile → numeric → Q5 → validate.
Runs async with configurable concurrency via semaphore.
"""

from __future__ import annotations
import asyncio
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator, Callable

import numpy as np
from loguru import logger

from src.parser.models import SurveySchema
from src.personas.generator import Persona, generate_personas
from src.profiler.correlation import get_behavior_profile, sample_delivery, BehaviorProfile
from src.generator.numeric import sample_numeric_answers
from src.generator.opentext import generate_q5


class RPMThrottler:
    """Enforces a strict Requests Per Minute (RPM) limit to prevent HTTP 429 errors."""
    def __init__(self, rpm: int):
        self.interval = 60.0 / float(rpm)
        self.last_req = 0.0
        self.lock = asyncio.Lock()

    async def wait(self):
        async with self.lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_req
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
            self.last_req = asyncio.get_event_loop().time()


@dataclass
class SurveyResponse:
    response_id: str
    persona_id: str
    persona_archetype: str
    q1_satisfaction: int
    q2_nps: int
    q3_category: str
    q4_delivery_on_time: bool
    q5_open_text: str
    coherence_score: float = 1.0
    sentiment_compound: float = 0.0
    generation_attempts: int = 1
    violations: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PipelineStats:
    run_id: str
    n_requested: int
    n_generated: int = 0
    n_rejected: int = 0
    model_used: str = ""
    estimated_cost_usd: float = 0.0
    duration_seconds: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Approx cost: Groq free tier, negligible; set to 0.0
GROQ_COST_PER_1K_TOKENS = 0.0


async def generate_single_response(
    persona: Persona,
    schema: SurveySchema,
    model: str,
    semaphore: asyncio.Semaphore,
    rng: np.random.Generator,
    throttler: RPMThrottler | None = None,
    max_retries: int = 3,
    coherence_threshold: float = 0.6,
    validate_fn: Callable | None = None,
) -> SurveyResponse:
    """Generate a single survey response with coherence validation + retry."""
    from src.validator.coherence import validate_coherence

    attempt = 0
    best_response: SurveyResponse | None = None

    while attempt < max_retries:
        attempt += 1

        # 1. Sample delivery status
        late = sample_delivery(persona.archetype, rng)

        # 2. Get behavior profile
        profile: BehaviorProfile = get_behavior_profile(persona.archetype, late, rng)

        # 3. Sample numeric answers (zero LLM)
        numeric = sample_numeric_answers(persona, profile, rng)

        # 4. Generate Q5 (one LLM call)
        if throttler:
            await throttler.wait()
            
        q5 = await generate_q5(
            persona=persona,
            profile=profile,
            q1=numeric["q1_satisfaction"],
            q2=numeric["q2_nps"],
            q4=numeric["q4_delivery_on_time"],
            model=model,
            semaphore=semaphore,
        )

        # 5. Build response object
        response = SurveyResponse(
            response_id=str(uuid.uuid4()),
            persona_id=persona.id,
            persona_archetype=persona.archetype,
            q1_satisfaction=numeric["q1_satisfaction"],
            q2_nps=numeric["q2_nps"],
            q3_category=numeric["q3_category"],
            q4_delivery_on_time=numeric["q4_delivery_on_time"],
            q5_open_text=q5,
            generation_attempts=attempt,
        )

        # 6. Validate coherence
        result = validate_coherence(response)
        response.coherence_score = result.score
        response.sentiment_compound = result.sentiment_compound
        response.violations = result.violations

        if result.is_coherent:
            return response

        logger.debug(
            f"Attempt {attempt}/{max_retries} failed coherence "
            f"(score={result.score:.2f}, violations={result.violations})"
        )
        best_response = response  # Keep best attempt even if not coherent

    # Return best attempt after exhausting retries
    logger.warning(f"Returning low-coherence response after {max_retries} retries")
    return best_response  # type: ignore[return-value]


async def run_pipeline(
    schema: SurveySchema,
    model: str | None = None,
    seed: int = 42,
    max_concurrent: int = 10,
    coherence_threshold: float = 0.6,
    max_retries: int = 3,
    progress_callback: Callable[[int, int], None] | None = None,
) -> tuple[list[SurveyResponse], PipelineStats]:
    """Run the full 7-stage pipeline and return all responses + stats.

    Args:
        schema: Validated survey schema.
        model: Groq model name (defaults to env MODEL_NAME).
        seed: Random seed.
        max_concurrent: Max parallel LLM calls.
        coherence_threshold: Min score to accept without retry.
        max_retries: Max retries per response.
        progress_callback: Optional fn(completed, total) for progress reporting.

    Returns:
        Tuple of (responses list, pipeline stats).
    """
    import time

    start_time = time.time()
    run_id = str(uuid.uuid4())
    model = model or os.getenv("MODEL_NAME", "llama3-8b-8192")
    n = schema.n

    logger.info(f"Pipeline starting: run_id={run_id}, N={n}, model={model}")

    # Stage 1: Generate personas
    personas: list[Persona] = generate_personas(n, seed=seed)

    # Stage 2: Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)
    rng = np.random.default_rng(seed)
    
    # 30 RPM limit for Groq Free Tier
    throttler = RPMThrottler(30)

    # Stage 3: Generate all responses concurrently
    tasks = [
        generate_single_response(
            persona=p,
            schema=schema,
            model=model,
            semaphore=semaphore,
            rng=np.random.default_rng(seed + i),   # Per-response seed
            throttler=throttler,
            max_retries=max_retries,
            coherence_threshold=coherence_threshold,
        )
        for i, p in enumerate(personas)
    ]

    responses: list[SurveyResponse] = []
    completed = 0

    for coro in asyncio.as_completed(tasks):
        resp = await coro
        responses.append(resp)
        completed += 1
        if progress_callback:
            progress_callback(completed, n)
        if completed % 20 == 0:
            logger.info(f"Progress: {completed}/{n} responses generated")

    duration = time.time() - start_time
    n_rejected = sum(1 for r in responses if r.coherence_score < coherence_threshold)

    stats = PipelineStats(
        run_id=run_id,
        n_requested=n,
        n_generated=len(responses),
        n_rejected=n_rejected,
        model_used=model,
        estimated_cost_usd=0.0,   # Groq free tier
        duration_seconds=round(duration, 2),
    )

    logger.success(
        f"Pipeline complete: {len(responses)} responses in {duration:.1f}s, "
        f"{n_rejected} below coherence threshold"
    )
    return responses, stats
