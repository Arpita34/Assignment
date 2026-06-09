"""
src/parser/loader.py
Load and validate survey definitions from JSON/YAML files.
"""

from __future__ import annotations
import json
from pathlib import Path
from loguru import logger
from .models import SurveySchema


def load_survey(path: str | Path) -> SurveySchema:
    """Load a survey definition from a JSON file and validate it.

    Args:
        path: Path to the survey JSON file.

    Returns:
        Validated SurveySchema instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the JSON is invalid or fails schema validation.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Survey file not found: {path}")

    logger.info(f"Loading survey from: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    schema = SurveySchema.model_validate(raw)
    logger.success(
        f"Survey loaded: '{schema.title}' — "
        f"{len(schema.questions)} questions, N={schema.n}"
    )
    return schema
