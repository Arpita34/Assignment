"""
tests/unit/test_parser.py
Unit tests for survey schema parser. No LLM calls.
"""

import pytest
from pydantic import ValidationError
from src.parser.models import SurveySchema, SurveyQuestion, QuestionType
from src.parser.loader import load_survey


class TestSurveyParserValid:
    """Test that valid survey schemas parse without error."""

    def test_valid_ecommerce_survey_parses(self, sample_survey_path):
        """The bundled ecommerce.json must parse with 5 questions."""
        schema = load_survey(sample_survey_path)
        assert isinstance(schema, SurveySchema)
        assert len(schema.questions) == 5
        assert schema.title == "E-Commerce Customer Satisfaction Survey"

    def test_question_types_correct(self, sample_survey_path):
        """Each question has the expected type."""
        schema = load_survey(sample_survey_path)
        types = [q.type for q in schema.questions]
        assert types == [
            QuestionType.RATING,
            QuestionType.NPS,
            QuestionType.SINGLE_CHOICE,
            QuestionType.SINGLE_CHOICE,
            QuestionType.OPEN_TEXT,
        ]

    def test_q1_scale_correct(self, sample_survey_path):
        schema = load_survey(sample_survey_path)
        q1 = schema.questions[0]
        assert q1.scale == [1, 5]

    def test_q2_scale_correct(self, sample_survey_path):
        schema = load_survey(sample_survey_path)
        q2 = schema.questions[1]
        assert q2.scale == [0, 10]

    def test_q3_options_correct(self, sample_survey_path):
        schema = load_survey(sample_survey_path)
        q3 = schema.questions[2]
        assert set(q3.options) == {"Electronics", "Clothing", "Home", "Other"}

    def test_n_default_value(self, minimal_survey_dict):
        schema = SurveySchema.model_validate(minimal_survey_dict)
        assert schema.n == 10

    def test_question_ids_unique(self, minimal_survey_dict):
        schema = SurveySchema.model_validate(minimal_survey_dict)
        ids = [q.id for q in schema.questions]
        assert len(ids) == len(set(ids))


class TestSurveyParserInvalid:
    """Test that invalid schemas raise ValidationError."""

    def test_invalid_question_type_raises(self):
        with pytest.raises(ValidationError):
            SurveyQuestion(
                id="q1",
                type="invalid_type",   # type: ignore
                label="Test?",
            )

    def test_rating_without_scale_raises(self):
        with pytest.raises(ValidationError):
            SurveyQuestion(
                id="q1",
                type=QuestionType.RATING,
                label="Rating?",
                # scale missing
            )

    def test_single_choice_with_one_option_raises(self):
        with pytest.raises(ValidationError):
            SurveyQuestion(
                id="q1",
                type=QuestionType.SINGLE_CHOICE,
                label="Choice?",
                options=["OnlyOne"],
            )

    def test_duplicate_question_ids_raise(self, minimal_survey_dict):
        minimal_survey_dict["questions"][1]["id"] = "q1"  # Duplicate
        with pytest.raises(ValidationError):
            SurveySchema.model_validate(minimal_survey_dict)

    def test_missing_title_raises(self, minimal_survey_dict):
        del minimal_survey_dict["title"]
        with pytest.raises(ValidationError):
            SurveySchema.model_validate(minimal_survey_dict)

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            load_survey("nonexistent/path.json")
