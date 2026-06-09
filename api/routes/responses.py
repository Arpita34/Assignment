"""
api/routes/responses.py
GET  /api/responses           — Paginated, filterable response list.
GET  /api/responses/export    — Stream CSV/JSON download.
PATCH /api/responses/{id}     — Manual override (approve low-coherence response).
"""

from __future__ import annotations
import csv
import io
import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, and_
from api.database import AsyncSessionLocal, Response

router = APIRouter()


@router.get("/")
async def list_responses(
    run_id: str | None = None,
    q1_min: int | None = Query(default=None, ge=1, le=5),
    q1_max: int | None = Query(default=None, ge=1, le=5),
    q3: str | None = None,
    q4: bool | None = None,
    search: str | None = None,
    flagged: bool | None = None,
    coherence_min: float | None = Query(default=None, ge=0.0, le=1.0),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Paginated, filterable list of responses."""
    async with AsyncSessionLocal() as db:
        q = select(Response)

        filters = []
        if run_id:
            filters.append(Response.run_id == run_id)
        if q1_min is not None:
            filters.append(Response.q1_satisfaction >= q1_min)
        if q1_max is not None:
            filters.append(Response.q1_satisfaction <= q1_max)
        if q3:
            filters.append(Response.q3_category == q3)
        if q4 is not None:
            filters.append(Response.q4_delivery_on_time == q4)
        if search:
            filters.append(Response.q5_open_text.ilike(f"%{search}%"))
        if flagged:
            filters.append(Response.coherence_score < 0.7)
        if coherence_min is not None:
            filters.append(Response.coherence_score >= coherence_min)

        if filters:
            q = q.where(and_(*filters))

        # Count total
        from sqlalchemy import func, select as sa_select
        count_q = sa_select(func.count()).select_from(Response)
        if filters:
            count_q = count_q.where(and_(*filters))
        total_result = await db.execute(count_q)
        total = total_result.scalar()

        # Fetch page
        result = await db.execute(q.offset(offset).limit(limit))
        rows = result.scalars().all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": [_response_to_dict(r) for r in rows],
        }


@router.get("/export")
async def export_responses(
    run_id: str | None = None,
    format: str = Query(default="csv", pattern="^(csv|json)$"),
):
    """Stream all responses as CSV or JSON download."""
    async with AsyncSessionLocal() as db:
        q = select(Response)
        if run_id:
            q = q.where(Response.run_id == run_id)
        result = await db.execute(q)
        rows = result.scalars().all()
        data = [_response_to_dict(r) for r in rows]

    if format == "csv":
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=responses.csv"},
        )
    else:
        return StreamingResponse(
            iter([json.dumps(data, indent=2, default=str)]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=responses.json"},
        )


class PatchResponseBody(BaseModel):
    manually_approved: bool | None = None


@router.patch("/{response_id}")
async def patch_response(response_id: str, body: PatchResponseBody):
    """Manually approve or reject a flagged response."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Response).where(Response.response_id == response_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Response not found")

        if body.manually_approved is not None:
            row.manually_approved = body.manually_approved

        await db.commit()
        return _response_to_dict(row)


def _response_to_dict(r: Response) -> dict:
    return {
        "response_id": r.response_id,
        "run_id": r.run_id,
        "persona_id": r.persona_id,
        "persona_archetype": r.persona_archetype,
        "q1_satisfaction": r.q1_satisfaction,
        "q2_nps": r.q2_nps,
        "q3_category": r.q3_category,
        "q4_delivery_on_time": r.q4_delivery_on_time,
        "q5_open_text": r.q5_open_text,
        "coherence_score": r.coherence_score,
        "sentiment_compound": r.sentiment_compound,
        "generation_attempts": r.generation_attempts,
        "violations": r.violations.split("|") if r.violations else [],
        "manually_approved": r.manually_approved,
        "created_at": str(r.created_at),
    }
