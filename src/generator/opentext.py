"""
src/generator/opentext.py
Async Groq LLM client for Q5 open-text generation.
Uses semaphore to rate-limit concurrent calls.
"""

from __future__ import annotations
import asyncio
import os
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from groq import AsyncGroq, RateLimitError, APIError

from src.personas.generator import Persona
from src.profiler.correlation import BehaviorProfile
from .prompts import build_q5_prompt

# ─── Groq Client ─────────────────────────────────────────────────────────────
_client: AsyncGroq | None = None


def get_client() -> AsyncGroq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY not set. "
                "Add it to your .env file: GROQ_API_KEY=gsk_..."
            )
        _client = AsyncGroq(api_key=api_key)
    return _client


# ─── Retry-decorated LLM call ────────────────────────────────────────────────
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((RateLimitError, APIError)),
    reraise=True,
)
async def _call_llm(prompt: str, model: str) -> str:
    """Single LLM call with retry logic."""
    client = get_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120,
        temperature=0.85,       # High temperature for diversity
        top_p=0.95,
    )
    text = response.choices[0].message.content or ""
    return text.strip()


async def generate_q5(
    persona: Persona,
    profile: BehaviorProfile,
    q1: int,
    q2: int,
    q4: bool,
    model: str,
    semaphore: asyncio.Semaphore,
) -> str:
    """Generate Q5 open-text for a single response.

    Args:
        persona: The persona context.
        profile: Behavior profile (tone, topics).
        q1, q2, q4: Numeric answers for context.
        model: Groq model name.
        semaphore: Controls concurrency.

    Returns:
        Generated open-text string.
    """
    prompt = build_q5_prompt(persona, profile, q1, q2, q4)

    async with semaphore:
        try:
            text = await _call_llm(prompt, model)
            # Basic cleanup
            text = text.strip().strip('"').strip("'")
            if not text:
                text = "The overall experience was okay but there's room for improvement."
            return text
        except Exception as e:
            logger.warning(f"LLM call failed for persona {persona.id}: {e}")
            return _fallback_response(profile.q5_tone)


def _fallback_response(tone: str) -> str:
    """Deterministic fallback when LLM call fails."""
    fallbacks = {
        "positive":          "Everything was great — maybe consider offering loyalty rewards.",
        "neutral":           "The experience was decent; improving delivery tracking would help.",
        "negative":          "The product quality did not meet expectations and customer support was hard to reach.",
        "mixed_delay":       "Product was good but the late delivery was frustrating.",
        "mildly_negative":   "The checkout process could be smoother and delivery updates more frequent.",
        "very_negative":     "The item arrived damaged and customer service took days to respond.",
        "delivery_positive": "Delivery was impressively fast and packaging was excellent.",
        "delivery_negative": "The shipment arrived a week late with no proactive updates.",
        "price_quality":     "Good value overall but competitor pricing is becoming hard to ignore.",
        "price_quality_negative": "For this price range, late delivery is simply not acceptable.",
    }
    return fallbacks.get(tone, "There is room for improvement in the overall experience.")
