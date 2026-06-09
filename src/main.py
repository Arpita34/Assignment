"""
src/main.py
CLI entrypoint for the Synthetic Survey Response Generator.

Usage:
    python -m src.main --survey surveys/ecommerce.json --n 200
    python -m src.main --survey surveys/ecommerce.json --n 50 --model llama3-70b-8192
"""

from __future__ import annotations
import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load .env before any module imports that read env vars
load_dotenv()

from src.parser.loader import load_survey
from src.generator.pipeline import run_pipeline
from src.output.writer import write_outputs
from src.output.charts import generate_qa_charts


def setup_logging(level: str = "INFO") -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
        level=level,
        colorize=True,
    )
    logger.add(
        "outputs/run.log",
        rotation="10 MB",
        level="DEBUG",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synthetic Survey Response Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --survey surveys/ecommerce.json --n 200
  python -m src.main --survey surveys/ecommerce.json --n 50 --model llama3-70b-8192 --seed 123
        """,
    )
    parser.add_argument(
        "--survey", required=True,
        help="Path to survey JSON file (e.g. surveys/ecommerce.json)",
    )
    parser.add_argument(
        "--n", type=int, default=None,
        help="Number of responses to generate (overrides survey file setting)",
    )
    parser.add_argument(
        "--model", default=None,
        help="Groq model name (default: $MODEL_NAME env var or llama3-8b-8192)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--output-dir", default="outputs",
        help="Output directory (default: outputs/)",
    )
    parser.add_argument(
        "--format", choices=["csv", "json", "both"], default="both",
        help="Export format (default: both)",
    )
    parser.add_argument(
        "--concurrency", type=int, default=10,
        help="Max concurrent LLM calls (default: 10)",
    )
    parser.add_argument(
        "--coherence-threshold", type=float, default=0.6,
        help="Minimum coherence score to accept a response (default: 0.6)",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log verbosity (default: INFO)",
    )
    parser.add_argument(
        "--no-charts", action="store_true",
        help="Skip QA chart generation",
    )
    return parser.parse_args()


def progress_callback(completed: int, total: int) -> None:
    pct = completed / total * 100
    bar_len = 30
    filled = int(bar_len * completed / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\r  [{bar}] {completed}/{total} ({pct:.0f}%)", end="", flush=True)
    if completed == total:
        print()


async def main_async() -> None:
    args = parse_args()
    setup_logging(args.log_level)

    # ── Banner ────────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("  Synthetic Survey Response Generator")
    logger.info("  Powered by Groq (free tier)")
    logger.info("=" * 60)

    # ── Check API key ─────────────────────────────────────────────────────────
    if not os.getenv("GROQ_API_KEY"):
        logger.error(
            "GROQ_API_KEY not found!\n"
            "  1. Get a free key at: https://console.groq.com/keys\n"
            "  2. Add it to .env:  GROQ_API_KEY=gsk_..."
        )
        sys.exit(1)

    # ── Load survey ───────────────────────────────────────────────────────────
    schema = load_survey(args.survey)

    # Override N if provided via CLI
    if args.n is not None:
        schema.n = args.n

    logger.info(f"Survey: '{schema.title}' | N={schema.n} responses")

    # ── Run pipeline ──────────────────────────────────────────────────────────
    logger.info("Starting generation pipeline...")
    responses, stats = await run_pipeline(
        schema=schema,
        model=args.model,
        seed=args.seed,
        max_concurrent=args.concurrency,
        coherence_threshold=args.coherence_threshold,
        progress_callback=progress_callback,
    )

    # ── Write outputs ─────────────────────────────────────────────────────────
    df = write_outputs(
        responses=responses,
        stats=stats,
        output_dir=args.output_dir,
        export_format=args.format,
    )

    # ── Generate charts ───────────────────────────────────────────────────────
    if not args.no_charts:
        generate_qa_charts(df, Path(args.output_dir) / "qa_report.png")

    # ── Summary ───────────────────────────────────────────────────────────────
    coherent_count = (df["coherence_score"] >= args.coherence_threshold).sum()
    logger.info("─" * 60)
    logger.info(f"  ✅ Responses generated : {stats.n_generated}")
    logger.info(f"  ✅ Above threshold     : {coherent_count}/{stats.n_generated}")
    logger.info(f"  ⚠️  Below threshold    : {stats.n_rejected}")
    logger.info(f"  ⏱️  Duration           : {stats.duration_seconds:.1f}s")
    logger.info(f"  💰 API cost (Groq)    : FREE TIER")
    logger.info(f"  📁 Output dir         : {args.output_dir}/")
    logger.info("─" * 60)
    logger.success("All done! Check the outputs/ folder.")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
