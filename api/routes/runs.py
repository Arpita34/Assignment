"""api/routes/runs.py — GET/DELETE /api/runs"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, delete
from api.database import AsyncSessionLocal, GenerationRun, Response, PersonaRecord

router = APIRouter()


@router.get("/")
async def list_runs():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(GenerationRun).order_by(GenerationRun.created_at.desc()))
        runs = result.scalars().all()
    return [{
        "run_id": r.run_id, "n_requested": r.n_requested,
        "n_generated": r.n_generated, "n_rejected": r.n_rejected,
        "model_used": r.model_used, "cost_usd": r.cost_usd,
        "duration_seconds": r.duration_seconds, "survey_title": r.survey_title,
        "status": r.status, "created_at": str(r.created_at),
    } for r in runs]


@router.get("/{run_id}")
async def get_run(run_id: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(GenerationRun).where(GenerationRun.run_id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run.run_id, "n_generated": run.n_generated, "status": run.status}


@router.delete("/{run_id}")
async def delete_run(run_id: str):
    """Delete a run and all its associated responses and personas."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(GenerationRun).where(GenerationRun.run_id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        await db.execute(delete(Response).where(Response.run_id == run_id))
        await db.execute(delete(PersonaRecord).where(PersonaRecord.run_id == run_id))
        await db.execute(delete(GenerationRun).where(GenerationRun.run_id == run_id))
        await db.commit()
    return {"deleted": run_id}
