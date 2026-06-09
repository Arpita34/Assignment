"""
api/routes/analytics.py
GET /api/analytics/{run_id} — Pre-aggregated distribution stats for charts.
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func
from api.database import AsyncSessionLocal, Response

router = APIRouter()


@router.get("/{run_id}")
async def get_analytics(run_id: str):
    """Return pre-aggregated analytics for a run (used by the Analytics page)."""
    async with AsyncSessionLocal() as db:
        q = select(Response).where(Response.run_id == run_id)
        result = await db.execute(q)
        rows = result.scalars().all()

    if not rows:
        raise HTTPException(status_code=404, detail="No responses found for this run")

    import pandas as pd
    df = pd.DataFrame([{
        "q1": r.q1_satisfaction,
        "q2": r.q2_nps,
        "q3": r.q3_category,
        "q4": r.q4_delivery_on_time,
        "coherence": r.coherence_score,
        "sentiment": r.sentiment_compound,
        "archetype": r.persona_archetype,
    } for r in rows])

    q1_dist = df["q1"].value_counts().sort_index().to_dict()
    q2_nps = {
        "detractors": int((df["q2"] <= 6).sum()),
        "passives": int(((df["q2"] >= 7) & (df["q2"] <= 8)).sum()),
        "promoters": int((df["q2"] >= 9).sum()),
    }
    q3_dist = df["q3"].value_counts().to_dict()
    q4_dist = {
        "on_time": int((df["q4"] == True).sum()),
        "late": int((df["q4"] == False).sum()),
    }
    coherence_stats = df["coherence"].describe().to_dict()
    archetype_dist = df["archetype"].value_counts().to_dict()

    corr = float(df[["q1", "q2"]].corr().iloc[0, 1]) if len(df) > 1 else 0.0

    # Scatter data (sample 100 points max)
    sample = df.sample(min(100, len(df)), random_state=42)
    scatter = [{"x": int(r["q1"]), "y": int(r["q2"])} for _, r in sample.iterrows()]

    return {
        "q1_dist": {str(k): int(v) for k, v in q1_dist.items()},
        "q2_nps": q2_nps,
        "q3_dist": {str(k): int(v) for k, v in q3_dist.items()},
        "q4_dist": q4_dist,
        "coherence_stats": {k: round(float(v), 4) for k, v in coherence_stats.items()},
        "archetype_dist": {str(k): int(v) for k, v in archetype_dist.items()},
        "corr_sat_nps": round(corr, 4),
        "scatter_sat_nps": scatter,
        "total": len(df),
        "mean_satisfaction": round(float(df["q1"].mean()), 2),
        "mean_nps": round(float(df["q2"].mean()), 2),
    }
