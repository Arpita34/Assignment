"""
tests/eval/test_llm_judge.py
LLM Eval Layer 2: LLM-as-judge coherence test (optional, costs ~$0.01).
Run separately: pytest tests/eval/test_llm_judge.py -m llm -v

Requires GROQ_API_KEY to be set.
"""

import pytest
import os
from pathlib import Path


@pytest.mark.llm
def test_llm_judge_coherence(responses_df):
    """Sample 20 responses and ask Groq to rate their coherence 1–5.

    Pass condition: mean coherence > 3.5/5.
    """
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        pytest.skip("GROQ_API_KEY not set — skipping LLM eval test")

    client = Groq(api_key=api_key)
    model = os.getenv("MODEL_NAME", "llama3-8b-8192")

    sample = responses_df.sample(min(20, len(responses_df)), random_state=42)
    scores = []

    for _, row in sample.iterrows():
        prompt = f"""Rate this survey response on a coherence scale of 1–5.

Coherence means: does the open-text feedback logically match the numeric ratings?

Survey Response:
- Overall satisfaction: {row['q1_satisfaction']}/5
- Likelihood to recommend: {row['q2_nps']}/10
- Delivery on time: {row['q4_delivery_on_time']}
- Feedback: "{row['q5_open_text']}"

Rate ONLY with a single digit 1–5 where:
1 = Completely incoherent (positive text with low scores or vice versa)
3 = Moderately coherent
5 = Perfectly coherent (text matches ratings exactly)

Reply with ONLY the number."""

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.0,
            )
            text = response.choices[0].message.content.strip()
            score = int(text[0])   # Take first character as score
            if 1 <= score <= 5:
                scores.append(score)
        except Exception as e:
            print(f"  Warning: LLM judge call failed: {e}")
            continue

    if len(scores) < 5:
        pytest.skip(f"Too few successful judge scores ({len(scores)})")

    mean_score = sum(scores) / len(scores)
    print(f"\n  LLM-as-judge mean coherence: {mean_score:.2f}/5 (n={len(scores)})")
    print(f"  Score distribution: {scores}")

    assert mean_score > 3.5, (
        f"LLM judge mean coherence too low: {mean_score:.2f}/5 (min 3.5)"
    )
