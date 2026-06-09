"""
src/generator/prompts.py
Prompt templates for Q5 open-text generation.
Prompts are persona-aware and tone-directed to ensure coherence.
"""

from __future__ import annotations
from src.personas.generator import Persona
from src.profiler.correlation import BehaviorProfile

# ─── Tone to instruction mapping ─────────────────────────────────────────────
TONE_INSTRUCTIONS: dict[str, str] = {
    "positive": (
        "Your feedback should be genuinely positive and appreciative. "
        "You may mention one small, specific area for improvement."
    ),
    "neutral": (
        "Your feedback should be balanced — acknowledge what worked and suggest "
        "one or two concrete improvements in a mild, constructive way."
    ),
    "negative": (
        "Your feedback should clearly express dissatisfaction. Mention a specific "
        "product or service issue. Be direct but not rude."
    ),
    "mixed_delay": (
        "You are mostly satisfied but frustrated about the late delivery. "
        "Acknowledge the product quality but specifically call out the shipping delay."
    ),
    "mildly_negative": (
        "You are slightly disappointed. Express mild frustration and suggest "
        "one concrete improvement, keeping the tone moderate."
    ),
    "very_negative": (
        "You are very unhappy. Express strong dissatisfaction about a specific problem "
        "— product quality, customer service, or a broken/wrong item. Be specific and direct."
    ),
    "delivery_positive": (
        "Focus primarily on the excellent delivery experience. "
        "Mention speed, packaging, or tracking. Keep overall tone very positive."
    ),
    "delivery_negative": (
        "Focus your frustration specifically on the late or failed delivery. "
        "Mention the impact it had on you. Keep the tone firm and specific."
    ),
    "price_quality": (
        "Focus on the price-to-quality ratio. Express that you expected more "
        "value for the price or compare favorably. Keep the tone analytical."
    ),
    "price_quality_negative": (
        "Express that the late delivery made the poor value-for-money feel worse. "
        "Suggest better shipping options or price adjustments."
    ),
}


def build_q5_prompt(
    persona: Persona,
    profile: BehaviorProfile,
    q1: int,
    q2: int,
    q4: bool,
) -> str:
    """Build a persona-aware prompt for Q5 open-text generation.

    Args:
        persona: The persona context.
        profile: The behavior profile with tone and topic hints.
        q1: The satisfaction score (1–5).
        q2: The NPS score (0–10).
        q4: True if delivery was on time.

    Returns:
        Prompt string to send to the LLM.
    """
    delivery_str = "on time" if q4 else "late"
    topics_str = ", ".join(profile.q5_topics[:4])
    tone_instruction = TONE_INSTRUCTIONS.get(profile.q5_tone, TONE_INSTRUCTIONS["neutral"])

    prompt = f"""You are writing a real customer survey response. You are a {persona.age}-year-old customer from {persona.city}, {persona.region}.

You recently purchased a {persona.category_pref} product from an e-commerce store.
Your experience summary:
- Overall satisfaction: {q1}/5
- Likelihood to recommend: {q2}/10
- Delivery was: {delivery_str}

Survey question: "What could we improve?"

Instructions:
- Write exactly 1–2 sentences as your answer.
- {tone_instruction}
- Naturally reference topics like: {topics_str}.
- Sound like a real human — not polished or AI-generated.
- Do NOT start your response with "I" or "As a customer".
- Do NOT use lists, bullet points, or quotation marks.
- Respond with ONLY your survey answer, nothing else."""

    return prompt
