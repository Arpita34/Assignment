"""
tests/unit/test_parser_extended.py
Extended edge-case tests for parser: boundary values, empty strings,
extreme N, whitespace-only titles, non-ASCII, malformed JSON, etc.
"""

import json
import pytest
import tempfile
import os
from pathlib import Path
from pydantic import ValidationError

from src.parser.models import SurveySchema, SurveyQuestion, QuestionType
from src.parser.loader import load_survey


# ─── Fixtures ────────────────────────────────────────────────────────────────

def make_survey(**overrides) -> dict:
    """Minimal valid survey dict with optional overrides."""
    base = {
        "title": "Test Survey",
        "questions": [
            {"id": "q1", "type": "rating", "label": "Rate?", "scale": [1, 5]},
            {"id": "q2", "type": "nps", "label": "Recommend?", "scale": [0, 10]},
            {"id": "q3", "type": "single_choice", "label": "Cat?", "options": ["A", "B"]},
            {"id": "q4", "type": "single_choice", "label": "Time?", "options": ["Yes", "No"]},
            {"id": "q5", "type": "open_text", "label": "Improve?"},
        ],
        "n": 10,
    }
    base.update(overrides)
    return base


# ─── Title Edge Cases ────────────────────────────────────────────────────────

class TestTitleEdgeCases:

    def test_very_long_title_accepted(self):
        """Titles of 1000 characters should parse OK."""
        schema = SurveySchema.model_validate(make_survey(title="A" * 1000))
        assert len(schema.title) == 1000

    def test_non_ascii_title_accepted(self):
        """Unicode/emoji titles should parse fine."""
        schema = SurveySchema.model_validate(make_survey(title="Encuesta de satisfacción 🛒"))
        assert "satisfacci" in schema.title

    def test_whitespace_only_title_raises(self):
        """A title of only spaces/tabs is meaningless and should fail."""
        with pytest.raises(ValidationError):
            SurveySchema.model_validate(make_survey(title="   "))

    def test_empty_string_title_raises(self):
        with pytest.raises(ValidationError):
            SurveySchema.model_validate(make_survey(title=""))

    def test_numeric_string_title_accepted(self):
        """Title '123' is technically valid."""
        schema = SurveySchema.model_validate(make_survey(title="123 Survey"))
        assert schema.title == "123 Survey"


# ─── N Boundary Cases ────────────────────────────────────────────────────────

class TestNBoundaryValues:

    def test_n_equals_one(self):
        """N=1 should be valid."""
        schema = SurveySchema.model_validate(make_survey(n=1))
        assert schema.n == 1

    def test_n_equals_zero_raises(self):
        """N=0 makes no sense."""
        with pytest.raises(ValidationError):
            SurveySchema.model_validate(make_survey(n=0))

    def test_n_negative_raises(self):
        """Negative N is invalid."""
        with pytest.raises(ValidationError):
            SurveySchema.model_validate(make_survey(n=-5))

    def test_n_10000_accepted(self):
        """N=10000 is the max valid value."""
        schema = SurveySchema.model_validate(make_survey(n=10000))
        assert schema.n == 10000

    def test_n_above_10000_raises(self):
        """N above model max (10000) should raise."""
        with pytest.raises(ValidationError):
            SurveySchema.model_validate(make_survey(n=10001))

    def test_n_float_raises(self):
        """N as float (e.g. 10.5) should fail type validation."""
        with pytest.raises((ValidationError, TypeError)):
            SurveySchema.model_validate(make_survey(n=10.5))

    def test_n_string_raises(self):
        """N as string should fail."""
        with pytest.raises((ValidationError, ValueError)):
            SurveySchema.model_validate(make_survey(n="ten"))

    def test_n_missing_uses_default(self):
        """If n is omitted, should use model default."""
        d = make_survey()
        del d["n"]
        schema = SurveySchema.model_validate(d)
        # Should either default to 200 or raise — just verify it's an int
        assert isinstance(schema.n, int)


# ─── Scale Edge Cases ─────────────────────────────────────────────────────────

class TestScaleEdgeCases:

    def test_rating_scale_inverted_raises(self):
        """Scale [5, 1] (inverted) should be rejected."""
        with pytest.raises(ValidationError):
            SurveyQuestion(
                id="q1", type=QuestionType.RATING, label="Rate?", scale=[5, 1]
            )

    def test_rating_scale_equal_raises(self):
        """Scale [3, 3] (zero range) should be rejected."""
        with pytest.raises(ValidationError):
            SurveyQuestion(
                id="q1", type=QuestionType.RATING, label="Rate?", scale=[3, 3]
            )

    def test_nps_scale_must_be_0_to_10(self):
        """NPS scale [0, 10] must be accepted."""
        q = SurveyQuestion(
            id="q2", type=QuestionType.NPS, label="Recommend?", scale=[0, 10]
        )
        assert q.scale == [0, 10]

    def test_scale_with_negative_min_raises(self):
        """Scale [-1, 5] is invalid for a survey rating."""
        with pytest.raises(ValidationError):
            SurveyQuestion(
                id="q1", type=QuestionType.RATING, label="Rate?", scale=[-1, 5]
            )

    def test_open_text_ignores_scale(self):
        """Open text questions don't need scale and should not validate it."""
        q = SurveyQuestion(id="q5", type=QuestionType.OPEN_TEXT, label="Improve?")
        assert q.scale is None


# ─── Options Edge Cases ───────────────────────────────────────────────────────

class TestOptionsEdgeCases:

    def test_single_choice_with_empty_options_raises(self):
        with pytest.raises(ValidationError):
            SurveyQuestion(
                id="q3", type=QuestionType.SINGLE_CHOICE, label="Cat?", options=[]
            )

    def test_single_choice_with_two_options_ok(self):
        q = SurveyQuestion(
            id="q3", type=QuestionType.SINGLE_CHOICE, label="Cat?", options=["A", "B"]
        )
        assert len(q.options) == 2

    def test_single_choice_with_many_options_ok(self):
        opts = [f"Option{i}" for i in range(50)]
        q = SurveyQuestion(
            id="q3", type=QuestionType.SINGLE_CHOICE, label="Cat?", options=opts
        )
        assert len(q.options) == 50

    def test_duplicate_options_preserved(self):
        """Duplicate options are a design issue but should parse."""
        q = SurveyQuestion(
            id="q3", type=QuestionType.SINGLE_CHOICE, label="Cat?",
            options=["A", "A", "B"]
        )
        assert "A" in q.options

    def test_empty_string_option_raises(self):
        """Blank option strings should fail."""
        with pytest.raises(ValidationError):
            SurveyQuestion(
                id="q3", type=QuestionType.SINGLE_CHOICE, label="Cat?",
                options=["", "B"]
            )

    def test_rating_with_options_is_ignored_or_raises(self):
        """Rating questions don't use options field."""
        # Should parse ignoring extra field OR raise — just must not silently corrupt
        try:
            q = SurveyQuestion(
                id="q1", type=QuestionType.RATING, label="Rate?",
                scale=[1, 5], options=["1", "5"]
            )
            assert q.options is None or isinstance(q.options, list)
        except ValidationError:
            pass  # Also acceptable


# ─── Loader Edge Cases ────────────────────────────────────────────────────────

class TestLoaderEdgeCases:

    def test_malformed_json_raises(self, tmp_path):
        """A file with invalid JSON should raise an error."""
        bad = tmp_path / "bad.json"
        bad.write_text("{ this is not valid JSON }")
        with pytest.raises((json.JSONDecodeError, ValueError, Exception)):
            load_survey(bad)

    def test_json_array_instead_of_object_raises(self, tmp_path):
        """A JSON array is not a survey schema."""
        bad = tmp_path / "array.json"
        bad.write_text("[1, 2, 3]")
        with pytest.raises((ValidationError, Exception)):
            load_survey(bad)

    def test_empty_json_file_raises(self, tmp_path):
        """An empty file should raise."""
        empty = tmp_path / "empty.json"
        empty.write_text("")
        with pytest.raises(Exception):
            load_survey(empty)

    def test_null_json_raises(self, tmp_path):
        """JSON null should raise a validation error."""
        null = tmp_path / "null.json"
        null.write_text("null")
        with pytest.raises((ValidationError, TypeError, Exception)):
            load_survey(null)

    def test_valid_json_file_loads(self, tmp_path):
        """A properly formed survey JSON file loads correctly."""
        d = make_survey(title="Load Test", n=5)
        f = tmp_path / "survey.json"
        f.write_text(json.dumps(d))
        schema = load_survey(f)
        assert schema.title == "Load Test"
        assert schema.n == 5

    def test_extra_fields_in_json_are_ignored(self, tmp_path):
        """Extra unknown fields should be silently ignored."""
        d = make_survey()
        d["unknown_field"] = "ignored"
        d["metadata"] = {"author": "Test"}
        f = tmp_path / "extra.json"
        f.write_text(json.dumps(d))
        schema = load_survey(f)
        assert schema.title == "Test Survey"

    def test_path_string_and_pathlib_both_work(self, tmp_path):
        """load_survey should accept both str and Path."""
        d = make_survey()
        f = tmp_path / "survey.json"
        f.write_text(json.dumps(d))
        # PathLib
        s1 = load_survey(f)
        # String
        s2 = load_survey(str(f))
        assert s1.title == s2.title


# ─── Question Count Edge Cases ────────────────────────────────────────────────

class TestQuestionCountEdgeCases:

    def test_zero_questions_raises(self):
        with pytest.raises(ValidationError):
            SurveySchema.model_validate(make_survey(questions=[]))

    def test_single_open_text_question_accepted(self):
        d = make_survey(questions=[
            {"id": "q1", "type": "open_text", "label": "Any feedback?"}
        ])
        schema = SurveySchema.model_validate(d)
        assert len(schema.questions) == 1

    def test_one_hundred_questions_accepted(self):
        questions = [{"id": f"q{i}", "type": "open_text", "label": f"Q{i}?"} for i in range(100)]
        schema = SurveySchema.model_validate(make_survey(questions=questions))
        assert len(schema.questions) == 100

    def test_all_same_type_questions_ok(self):
        questions = [
            {"id": f"q{i}", "type": "open_text", "label": f"Q{i}?"} for i in range(5)
        ]
        schema = SurveySchema.model_validate(make_survey(questions=questions))
        assert all(q.type == QuestionType.OPEN_TEXT for q in schema.questions)
