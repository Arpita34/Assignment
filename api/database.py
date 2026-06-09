"""
api/database.py
SQLite + SQLAlchemy async setup for the web dashboard.
"""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey,
    create_engine, event
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./outputs/survey.db"
SYNC_DATABASE_URL = "sqlite:///./outputs/survey.db"


class Base(DeclarativeBase):
    pass


class GenerationRun(Base):
    __tablename__ = "generation_runs"

    run_id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    n_requested    = Column(Integer, nullable=False)
    n_generated    = Column(Integer, default=0)
    n_rejected     = Column(Integer, default=0)
    model_used     = Column(String, default="llama3-8b-8192")
    cost_usd       = Column(Float, default=0.0)
    duration_seconds = Column(Float, default=0.0)
    survey_title   = Column(String, default="")
    status         = Column(String, default="pending")   # pending|running|done|cancelled
    created_at     = Column(DateTime, default=datetime.utcnow)

    responses = relationship("Response", back_populates="run", cascade="all, delete-orphan")
    personas  = relationship("PersonaRecord", back_populates="run", cascade="all, delete-orphan")


class PersonaRecord(Base):
    __tablename__ = "personas"

    id                   = Column(String, primary_key=True)
    run_id               = Column(String, ForeignKey("generation_runs.run_id"), nullable=False)
    archetype            = Column(String, nullable=False)
    age                  = Column(Integer)
    region               = Column(String)
    city                 = Column(String)
    category_pref        = Column(String)
    delivery_sensitivity = Column(Float)
    tone_tendency        = Column(String)
    created_at           = Column(DateTime, default=datetime.utcnow)

    run = relationship("GenerationRun", back_populates="personas")
    response = relationship("Response", back_populates="persona", uselist=False)


class Response(Base):
    __tablename__ = "responses"

    response_id           = Column(String, primary_key=True)
    run_id                = Column(String, ForeignKey("generation_runs.run_id"), nullable=False)
    persona_id            = Column(String, ForeignKey("personas.id"), nullable=False)
    persona_archetype     = Column(String)
    q1_satisfaction       = Column(Integer)
    q2_nps                = Column(Integer)
    q3_category           = Column(String)
    q4_delivery_on_time   = Column(Boolean)
    q5_open_text          = Column(Text)
    coherence_score       = Column(Float, default=1.0)
    sentiment_compound    = Column(Float, default=0.0)
    generation_attempts   = Column(Integer, default=1)
    violations            = Column(Text, default="")
    manually_approved     = Column(Boolean, default=False)
    created_at            = Column(DateTime, default=datetime.utcnow)

    run     = relationship("GenerationRun", back_populates="responses")
    persona = relationship("PersonaRecord", back_populates="response")


# ─── Async engine ─────────────────────────────────────────────────────────────
async_engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables if they don't exist."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """FastAPI dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        yield session
