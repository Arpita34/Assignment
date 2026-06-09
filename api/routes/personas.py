"""api/routes/personas.py — GET /api/personas"""
from fastapi import APIRouter
from sqlalchemy import select
from api.database import AsyncSessionLocal, PersonaRecord

router = APIRouter()


@router.get("/")
async def list_personas(run_id: str | None = None, archetype: str | None = None):
    async with AsyncSessionLocal() as db:
        q = select(PersonaRecord)
        if run_id:
            q = q.where(PersonaRecord.run_id == run_id)
        if archetype:
            q = q.where(PersonaRecord.archetype == archetype)
        result = await db.execute(q.limit(500))
        rows = result.scalars().all()
    return [{
        "id": r.id, "run_id": r.run_id, "archetype": r.archetype,
        "age": r.age, "region": r.region, "city": r.city,
        "category_pref": r.category_pref,
        "delivery_sensitivity": r.delivery_sensitivity,
        "tone_tendency": r.tone_tendency,
    } for r in rows]
