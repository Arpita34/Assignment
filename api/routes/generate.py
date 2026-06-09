"""
api/routes/generate.py
POST /api/generate      — Start a generation run (SSE streaming).
DELETE /api/runs/{id}   — Cancel a run.
"""

from __future__ import annotations
import asyncio
import json
import os
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger

from src.parser.loader import load_survey
from src.generator.pipeline import run_pipeline, SurveyResponse, PipelineStats
from src.output.writer import write_outputs, responses_to_dataframe
from src.output.charts import generate_qa_charts
from api.database import AsyncSessionLocal, GenerationRun, PersonaRecord, Response
from sqlalchemy import insert

router = APIRouter()

# Global cancellation flags: run_id → bool
_cancel_flags: dict[str, bool] = {}


class GenerateRequest(BaseModel):
    survey_id: str
    n: int = 200
    model: str | None = None
    seed: int = 42
    concurrency: int = 10
    coherence_threshold: float = 0.6


def _sse(event_type: str, data: dict) -> str:
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

# ...

@router.get("/")
async def start_generation(
    survey_id: str,
    n: int = Query(default=200),
    model: str | None = Query(default=None),
    seed: int = Query(default=42),
    concurrency: int = Query(default=10),
    coherence_threshold: float = Query(default=0.6)
):
    """Start a generation run and stream SSE progress events."""
    req = GenerateRequest(
        survey_id=survey_id,
        n=n,
        model=model,
        seed=seed,
        concurrency=concurrency,
        coherence_threshold=coherence_threshold
    )
    survey_path = Path("surveys") / f"{req.survey_id}.json"
    if not survey_path.exists():
        # Try the default ecommerce survey
        survey_path = Path("surveys/ecommerce.json")
        if not survey_path.exists():
            raise HTTPException(status_code=404, detail="Survey not found")

    schema = load_survey(survey_path)
    schema.n = req.n
    model = req.model or os.getenv("MODEL_NAME", "llama3-8b-8192")

    async def event_stream():
        run_id = None
        try:
            # Create DB run record
            async with AsyncSessionLocal() as db:
                run = GenerationRun(
                    n_requested=req.n,
                    model_used=model,
                    survey_title=schema.title,
                    status="running",
                )
                db.add(run)
                await db.commit()
                await db.refresh(run)
                run_id = run.run_id

            _cancel_flags[run_id] = False

            yield _sse("started", {"run_id": run_id, "n": req.n, "model": model})

            completed = [0]
            start_time = time.time()

            def on_progress(done: int, total: int):
                completed[0] = done
                # Check cancellation
                if _cancel_flags.get(run_id):
                    raise asyncio.CancelledError("Run cancelled by user")

            # Run pipeline as a task so we can yield progress periodically
            pipeline_task = asyncio.create_task(
                run_pipeline(
                    schema=schema,
                    model=model,
                    seed=req.seed,
                    max_concurrent=req.concurrency,
                    coherence_threshold=req.coherence_threshold,
                    progress_callback=on_progress,
                )
            )

            last_yielded = 0
            while not pipeline_task.done():
                await asyncio.sleep(0.5)
                current = completed[0]
                if current > last_yielded:
                    yield _sse("progress", {"completed": current})
                    last_yielded = current

            # Await the task to catch any exceptions and get results
            responses, stats = await pipeline_task
            
            # Yield final progress
            if completed[0] > last_yielded:
                yield _sse("progress", {"completed": completed[0]})

            stats.run_id = run_id

            # Write outputs
            df = write_outputs(responses, stats, output_dir="outputs", export_format="both")
            generate_qa_charts(df, "outputs/qa_report.png")

            # Save to DB
            await _save_to_db(run_id, responses, stats)

            yield _sse("completed", {
                "run_id": run_id,
                "n_generated": stats.n_generated,
                "n_rejected": stats.n_rejected,
                "duration_seconds": stats.duration_seconds,
            })

        except asyncio.CancelledError:
            yield _sse("cancelled", {"run_id": run_id})
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            yield _sse("error", {"message": str(e)})
        finally:
            if run_id:
                _cancel_flags.pop(run_id, None)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


async def _save_to_db(run_id: str, responses: list[SurveyResponse], stats: PipelineStats):
    """Persist responses and update run record in SQLite."""
    async with AsyncSessionLocal() as db:
        # Update run stats
        from sqlalchemy import update
        await db.execute(
            update(GenerationRun)
            .where(GenerationRun.run_id == run_id)
            .values(
                n_generated=stats.n_generated,
                n_rejected=stats.n_rejected,
                duration_seconds=stats.duration_seconds,
                cost_usd=stats.estimated_cost_usd,
                status="done",
            )
        )

        # Insert responses
        for r in responses:
            db.add(Response(
                response_id=r.response_id,
                run_id=run_id,
                persona_id=r.persona_id,
                persona_archetype=r.persona_archetype,
                q1_satisfaction=r.q1_satisfaction,
                q2_nps=r.q2_nps,
                q3_category=r.q3_category,
                q4_delivery_on_time=r.q4_delivery_on_time,
                q5_open_text=r.q5_open_text,
                coherence_score=r.coherence_score,
                sentiment_compound=r.sentiment_compound,
                generation_attempts=r.generation_attempts,
                violations="|".join(r.violations),
            ))

        await db.commit()


@router.delete("/{run_id}")
async def cancel_run(run_id: str):
    """Signal a running pipeline to cancel."""
    if run_id not in _cancel_flags:
        raise HTTPException(status_code=404, detail="Run not found or already completed")
    _cancel_flags[run_id] = True
    return {"status": "cancelling", "run_id": run_id}
