"""
api/main.py
FastAPI application for the Synthetic Survey Generator web dashboard.
"""

from __future__ import annotations
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

from api.database import init_db
from api.routes import surveys, generate, responses, analytics, personas, runs, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    os.makedirs("outputs", exist_ok=True)
    await init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Synthetic Survey Generator API",
    description="Generate realistic synthetic survey responses using Groq LLM.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS for React dev server ─────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(surveys.router,   prefix="/api/surveys",   tags=["surveys"])
app.include_router(generate.router,  prefix="/api/generate",  tags=["generate"])
app.include_router(responses.router, prefix="/api/responses", tags=["responses"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(personas.router,  prefix="/api/personas",  tags=["personas"])
app.include_router(runs.router,      prefix="/api/runs",      tags=["runs"])
app.include_router(settings.router,  prefix="/api/settings",  tags=["settings"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "groq_configured": bool(os.getenv("GROQ_API_KEY"))}
