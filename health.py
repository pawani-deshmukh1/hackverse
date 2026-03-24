from fastapi import APIRouter
from schemas import HealthResponse, EngineStatus, ModelsResponse
from services.ollama_engine import check_ollama_health
from config import get_settings
import httpx
import logging

router = APIRouter()
logger = logging.getLogger("audioauth.routes.health")
settings = get_settings()


async def _check_claude() -> bool:
    if not settings.anthropic_api_key:
        return False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": settings.anthropic_api_key, "anthropic-version": "2023-06-01"},
            )
            return resp.status_code == 200
    except Exception:
        return False


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check engine availability",
)
async def health_check() -> HealthResponse:
    """Returns the status of Claude and Ollama engines."""
    claude_ok = await _check_claude()
    ollama_ok, ollama_models = await check_ollama_health()

    if claude_ok and ollama_ok:
        status = "healthy"
    elif claude_ok or ollama_ok:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        claude=EngineStatus(
            available=claude_ok,
            model=settings.claude_model,
            note=None if claude_ok else "API key missing or unreachable",
        ),
        ollama=EngineStatus(
            available=ollama_ok,
            model=settings.ollama_model,
            note=None if ollama_ok else "Ollama not running — start with `ollama serve`",
        ),
        primary="claude",
        fallback="ollama",
    )


@router.get(
    "/models",
    response_model=ModelsResponse,
    summary="List configured models",
)
async def list_models() -> ModelsResponse:
    """Returns configured model names and all locally available Ollama models."""
    _, ollama_models = await check_ollama_health()
    return ModelsResponse(
        claude_model=settings.claude_model,
        ollama_model=settings.ollama_model,
        ollama_models_available=ollama_models,
    )
