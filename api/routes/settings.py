"""api/routes/settings.py — GET/POST /api/settings"""
import os
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SettingsBody(BaseModel):
    model_name: str | None = None
    n: int | None = None
    max_concurrent: int | None = None
    coherence_threshold: float | None = None


@router.get("/")
async def get_settings():
    return {
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
        "model_name": os.getenv("MODEL_NAME", "llama3-8b-8192"),
        "n": int(os.getenv("N", "200")),
        "max_concurrent": int(os.getenv("MAX_CONCURRENT_CALLS", "10")),
        "coherence_threshold": float(os.getenv("COHERENCE_THRESHOLD", "0.6")),
    }


@router.post("/test-connection")
async def test_connection():
    """Test the Groq API connection with a minimal prompt."""
    import time
    from groq import AsyncGroq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"success": False, "message": "GROQ_API_KEY not set"}
    try:
        client = AsyncGroq(api_key=api_key)
        start = time.time()
        resp = await client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "llama3-8b-8192"),
            messages=[{"role": "user", "content": "Say 'ok'"}],
            max_tokens=5,
        )
        latency_ms = int((time.time() - start) * 1000)
        return {"success": True, "latency_ms": latency_ms, "model": resp.model}
    except Exception as e:
        return {"success": False, "message": str(e)}
