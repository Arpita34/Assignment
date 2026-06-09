"""
src/output/writer.py
Exports generated responses to CSV and JSON files.
"""

from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from loguru import logger

from src.generator.pipeline import SurveyResponse, PipelineStats


def responses_to_dataframe(responses: list[SurveyResponse]) -> pd.DataFrame:
    """Convert list of SurveyResponse to a Pandas DataFrame."""
    records = []
    for r in responses:
        records.append({
            "response_id": r.response_id,
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
            "violations": "|".join(r.violations) if r.violations else "",
            "created_at": r.created_at,
        })
    return pd.DataFrame(records)


def write_csv(df: pd.DataFrame, path: str | Path) -> None:
    """Write the DataFrame to a CSV file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    logger.success(f"CSV written: {path}  ({len(df)} rows)")


def write_json(df: pd.DataFrame, path: str | Path) -> None:
    """Write the DataFrame to a JSON file (records orientation)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    records = df.to_dict(orient="records")
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False, default=str)
    logger.success(f"JSON written: {path}  ({len(records)} records)")


def write_stats(stats: PipelineStats, path: str | Path) -> None:
    """Write pipeline stats summary to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(vars(stats), f, indent=2, default=str)
    logger.success(f"Stats written: {path}")


def write_outputs(
    responses: list[SurveyResponse],
    stats: PipelineStats,
    output_dir: str | Path = "outputs",
    export_format: str = "both",
) -> pd.DataFrame:
    """Write all outputs to the specified directory.

    Args:
        responses: Generated survey responses.
        stats: Pipeline run statistics.
        output_dir: Directory for output files.
        export_format: 'csv' | 'json' | 'both'

    Returns:
        The responses DataFrame.
    """
    output_dir = Path(output_dir)
    df = responses_to_dataframe(responses)

    if export_format in ("csv", "both"):
        write_csv(df, output_dir / "responses.csv")
    if export_format in ("json", "both"):
        write_json(df, output_dir / "responses.json")

    write_stats(stats, output_dir / "run_stats.json")
    return df
