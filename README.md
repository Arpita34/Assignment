# ⚡ Synthetic Survey Response Generator

Generate **200 realistic, coherent, and diverse** synthetic survey responses using a 7-stage pipeline with Groq LLM — all within the **free tier** ($0.00 cost).

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Your Groq API Key

```bash
# Copy the example env file
copy .env.example .env
```

Then edit `.env` and add your key:
```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

> Get a **free** key at: https://console.groq.com/keys

### 3. Generate 200 Responses

```bash
python -m src.main --survey surveys/ecommerce.json --n 200
```

### 4. Check Outputs

```
outputs/
├── responses.csv      ← 200 synthetic responses
├── responses.json     ← Same data in JSON format
├── qa_report.png      ← 9-panel quality assurance chart
└── run_stats.json     ← Pipeline run statistics
```

---

## 🧪 Run Tests

```bash
# Unit tests only (no API key needed, ~5 seconds)
pytest tests/unit/ -v

# Statistical tests (requires generated outputs/responses.csv)
pytest tests/statistical/ --responses-csv=outputs/responses.csv -v

# LLM eval tests (optional, costs $0.00 on Groq free tier)
pytest tests/eval/ -m llm -v --responses-csv=outputs/responses.csv

# Full suite with coverage
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## 🌐 Web Dashboard (Optional)

### Start the FastAPI Backend

```bash
uvicorn api.main:app --reload --port 8000
```

### Start the React Frontend

```bash
cd frontend
npm install
npm run dev
```

Then open: **http://localhost:5173**

The dashboard has 8 pages:
| Route | Page |
|---|---|
| `/` | Survey Config — build your survey schema |
| `/generate` | Generation Dashboard — live progress via SSE |
| `/responses` | Response Explorer — filter, sort, export |
| `/analytics` | Analytics Overview — Recharts visualizations |
| `/personas` | Persona Inspector — browse all 200 personas |
| `/review` | Coherence Review — flag and approve low-coherence responses |
| `/history` | Run History — track all past generation runs |
| `/settings` | Settings — API key status, model selection |

---

## 🏗️ Architecture (7-Stage Pipeline)

```
Survey JSON
    │
    ▼
[1] Parser         → Pydantic v2 schema validation
    │
    ▼
[2] Personas       → 5 archetypes × Faker demographics (N personas)
    │
    ▼
[3] Profiler       → Correlation matrix → behavior profiles (pure Python, 0 LLM)
    │
    ▼
[4] Generator      → NumPy sampling for Q1–Q4 + Groq LLM for Q5 only
    │
    ▼
[5] Validator      → VADER sentiment + rule engine → coherence score
    │
    ▼
[6] Filter         → TF-IDF cosine similarity diversity check
    │
    ▼
[7] Output         → CSV + JSON + 9-panel QA chart
```

---

## 📊 Persona Archetypes

| Archetype | Weight | Q1 Sat | Q2 NPS | Delivery Sensitivity |
|---|---|---|---|---|
| Happy Customer | 30% | 4–5 | 8–10 | Low |
| Neutral Passive | 25% | 3 | 6–7 | Medium |
| Frustrated Detractor | 20% | 1–2 | 0–3 | High |
| Delivery Focused | 15% | Driven by Q4 | Driven by Q4 | Very High |
| Value Seeker | 10% | 3–4 | 5–7 | Low |

---

## 💰 Cost Breakdown

| Item | Cost |
|---|---|
| Q1, Q2, Q3, Q4 generation | $0.00 (NumPy) |
| Q5 open-text — 200 × Groq | $0.00 (free tier) |
| Coherence validation | $0.00 (VADER) |
| **Total for 200 responses** | **$0.00** |

Budget limit: $2.00 → **100% within budget**

---

## 📁 Project Structure

```
f:\AssignSS\
├── src/
│   ├── main.py                  # CLI entrypoint
│   ├── parser/                  # Pydantic schema validation
│   ├── personas/                # Faker + archetype generation
│   ├── profiler/                # Correlation rule engine
│   ├── generator/               # NumPy sampler + Groq LLM
│   ├── validator/               # VADER + coherence rules
│   └── output/                  # CSV/JSON writer + charts
├── api/                         # FastAPI backend (web UI)
│   └── routes/                  # 7 API route modules
├── frontend/                    # React + Vite (8 pages)
│   └── src/pages/
├── tests/
│   ├── unit/                    # 23 tests, no LLM required
│   ├── statistical/             # 8 distribution tests
│   └── eval/                    # 3 LLM eval tests
├── surveys/
│   └── ecommerce.json           # Test survey definition
├── outputs/                     # Generated data (created on run)
├── .env.example                 # Environment config template
├── requirements.txt
└── README.md
```

---

## 🛠️ CLI Options

```bash
python -m src.main \
  --survey surveys/ecommerce.json \
  --n 200 \
  --model llama3-8b-8192 \
  --seed 42 \
  --output-dir outputs \
  --format both \
  --concurrency 10 \
  --coherence-threshold 0.6 \
  --log-level INFO
```

| Flag | Default | Description |
|---|---|---|
| `--survey` | required | Path to survey JSON |
| `--n` | from file | Number of responses |
| `--model` | `llama3-8b-8192` | Groq model name |
| `--seed` | `42` | Reproducibility seed |
| `--output-dir` | `outputs/` | Where to save files |
| `--format` | `both` | `csv`, `json`, or `both` |
| `--concurrency` | `10` | Max parallel Groq calls |
| `--coherence-threshold` | `0.6` | Min score to accept response |
| `--no-charts` | off | Skip chart generation |

---

## 📋 Quality Criteria

| Criterion | Metric | Target |
|---|---|---|
| Realism | VADER tone alignment | ≥ 80% high-sat → positive |
| Diversity | TF-IDF mean cosine similarity | < 0.4 |
| Coherence | Pearson r(Q1, Q2) | > 0.6 |
| Distribution | Chi-square on Q3 | p > 0.05 |
| Spread | Q1 standard deviation | > 1.0 |
| Delivery impact | On-time vs late mean sat | Δ > 0.3 |
