"""
api/routes/surveys.py
POST /api/surveys — Save a survey definition and return a survey_id.
GET  /api/surveys  — List saved surveys.
"""

from __future__ import annotations
import json
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.parser.models import SurveySchema
from src.parser.loader import load_survey

router = APIRouter()
SURVEYS_DIR = Path("surveys")
SURVEYS_DIR.mkdir(exist_ok=True)


class SurveyCreateRequest(BaseModel):
    survey: dict


@router.post("/")
async def create_survey(req: SurveyCreateRequest):
    """Validate and save a survey definition. Returns survey_id."""
    try:
        schema = SurveySchema.model_validate(req.survey)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    survey_id = str(uuid.uuid4())[:8]
    path = SURVEYS_DIR / f"{survey_id}.json"
    with path.open("w") as f:
        json.dump(req.survey, f, indent=2)

    return {"survey_id": survey_id, "title": schema.title, "n": schema.n}


@router.get("/")
async def list_surveys():
    """List all saved survey files."""
    surveys = []
    for path in sorted(SURVEYS_DIR.glob("*.json")):
        try:
            schema = load_survey(path)
            surveys.append({
                "survey_id": path.stem,
                "title": schema.title,
                "n": schema.n,
                "question_count": len(schema.questions),
            })
        except Exception:
            pass
    return surveys


@router.get("/{survey_id}")
async def get_survey(survey_id: str):
    path = SURVEYS_DIR / f"{survey_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Survey not found")
    with path.open() as f:
        return json.load(f)
