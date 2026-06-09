"""
src/parser/models.py
Pydantic v2 models for survey schema validation.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class QuestionType(str, Enum):
    RATING = "rating"
    NPS = "nps"
    SINGLE_CHOICE = "single_choice"
    OPEN_TEXT = "open_text"


class SurveyQuestion(BaseModel):
    id: str = Field(..., description="Unique question identifier, e.g. 'q1'")
    type: QuestionType = Field(..., description="Question type")
    label: str = Field(..., description="Question text shown to respondent")
    scale: Optional[list[int]] = Field(
        default=None,
        description="[min, max] for rating/NPS questions",
    )
    options: Optional[list[str]] = Field(
        default=None,
        description="Choices for single_choice questions",
    )

    @field_validator("options")
    @classmethod
    def validate_options_not_empty_strings(cls, v):
        if v is not None:
            for opt in v:
                if not opt or not opt.strip():
                    raise ValueError("Option strings must not be empty or whitespace-only.")
        return v

    @model_validator(mode="after")
    def validate_type_constraints(self) -> "SurveyQuestion":
        if self.type in (QuestionType.RATING, QuestionType.NPS):
            if self.scale is None or len(self.scale) != 2:
                raise ValueError(
                    f"Question '{self.id}' of type '{self.type}' requires a "
                    f"'scale' field with exactly [min, max]."
                )
            lo, hi = self.scale
            if lo < 0:
                raise ValueError(
                    f"Question '{self.id}': scale min must be >= 0, got {lo}."
                )
            if lo >= hi:
                raise ValueError(
                    f"Question '{self.id}': scale min must be strictly less than max, got [{lo}, {hi}]."
                )
        if self.type == QuestionType.SINGLE_CHOICE:
            if not self.options or len(self.options) < 2:
                raise ValueError(
                    f"Question '{self.id}' of type 'single_choice' requires "
                    f"at least 2 options."
                )
        return self


class SurveySchema(BaseModel):
    title: str = Field(..., description="Survey title", min_length=1)
    description: Optional[str] = Field(default=None)
    version: Optional[str] = Field(default="1.0")
    questions: list[SurveyQuestion] = Field(
        ..., description="Ordered list of survey questions", min_length=1
    )
    n: int = Field(default=200, ge=1, le=10000, description="Number of responses to generate")

    @field_validator("title")
    @classmethod
    def title_must_not_be_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Survey title must not be empty or whitespace-only.")
        return v

    @model_validator(mode="after")
    def validate_question_ids_unique(self) -> "SurveySchema":
        ids = [q.id for q in self.questions]
        if len(ids) != len(set(ids)):
            raise ValueError("All question IDs must be unique.")
        return self
