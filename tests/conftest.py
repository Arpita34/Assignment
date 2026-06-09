"""
tests/conftest.py
Shared pytest fixtures for all test layers.
"""

from __future__ import annotations
import pytest
import pandas as pd
from pathlib import Path


def pytest_addoption(parser):
    """Add --responses-csv CLI option for statistical tests."""
    parser.addoption(
        "--responses-csv",
        action="store",
        default="outputs/responses.csv",
        help="Path to generated responses CSV (default: outputs/responses.csv)",
    )


@pytest.fixture(scope="session")
def responses_csv(request) -> str:
    return request.config.getoption("--responses-csv")


@pytest.fixture(scope="session")
def responses_df(responses_csv) -> pd.DataFrame:
    path = Path(responses_csv)
    if not path.exists():
        pytest.skip(f"responses.csv not found at {path} — run the pipeline first")
    return pd.read_csv(path)


@pytest.fixture
def sample_survey_path() -> Path:
    return Path("surveys/ecommerce.json")


@pytest.fixture
def minimal_survey_dict() -> dict:
    return {
        "title": "Test Survey",
        "questions": [
            {"id": "q1", "type": "rating", "label": "Satisfaction?", "scale": [1, 5]},
            {"id": "q2", "type": "nps", "label": "Recommend?", "scale": [0, 10]},
            {"id": "q3", "type": "single_choice", "label": "Category?",
             "options": ["A", "B"]},
            {"id": "q4", "type": "single_choice", "label": "On time?",
             "options": ["Yes", "No"]},
            {"id": "q5", "type": "open_text", "label": "Improve?"},
        ],
        "n": 10,
    }
