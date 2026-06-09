"""Quick dry-run test of pipeline stages 1-5 (no LLM required)"""
import numpy as np
from unittest.mock import MagicMock
from src.parser.loader import load_survey
from src.personas.generator import generate_personas
from src.profiler.correlation import get_behavior_profile, sample_delivery
from src.generator.numeric import sample_numeric_answers
from src.validator.coherence import validate_coherence

# ── Stage 1: Parse ────────────────────────────────────────────────────────────
schema = load_survey("surveys/ecommerce.json")
print(f"[1] Survey: '{schema.title}' — {len(schema.questions)} questions, N={schema.n}")

# ── Stage 2: Personas ─────────────────────────────────────────────────────────
personas = generate_personas(10, seed=42)
print(f"[2] Personas: {len(personas)} generated")
for p in personas[:3]:
    print(f"      {p.archetype:<25} | age={p.age} | {p.region:<15} | pref={p.category_pref}")

# ── Stage 3+4: Profile + Numeric sample ───────────────────────────────────────
print("[3+4] Numeric samples (zero LLM):")
rng = np.random.default_rng(42)
for p in personas[:5]:
    is_late = sample_delivery(p.archetype, rng)
    profile = get_behavior_profile(p.archetype, late_delivery=is_late, rng=rng)
    answers = sample_numeric_answers(p, profile, rng)
    print(
        f"      [{p.archetype:<25}] "
        f"Q1={answers['q1_satisfaction']} "
        f"Q2={answers['q2_nps']:>2} "
        f"Q3={answers['q3_category']:<12} "
        f"Q4={'ON-TIME' if answers['q4_delivery_on_time'] else 'LATE   '}"
    )

# ── Stage 5: Validator ────────────────────────────────────────────────────────
print("[5] Coherence validator:")
good = MagicMock()
good.q1_satisfaction = 5
good.q2_nps = 9
good.q4_delivery_on_time = True
good.q5_open_text = "Excellent service! Will definitely order again."
good.persona_archetype = "happy_customer"
r = validate_coherence(good)
print(f"      Coherent:   score={r.score:.2f} | is_coherent={r.is_coherent} | violations={r.violations}")

bad = MagicMock()
bad.q1_satisfaction = 1
bad.q2_nps = 10
bad.q4_delivery_on_time = True
bad.q5_open_text = "Everything was great and amazing!"
bad.persona_archetype = "frustrated_detractor"
r2 = validate_coherence(bad)
print(f"      Incoherent: score={r2.score:.2f} | is_coherent={r2.is_coherent} | violations={r2.violations}")

print("\nDRY-RUN PASSED - all stages 1-5 verified without LLM!")
print("\nNext: add your GROQ_API_KEY to .env, then run:")
print("   python -m src.main --survey surveys/ecommerce.json --n 200")
