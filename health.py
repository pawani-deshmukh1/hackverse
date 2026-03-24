from fastapi import APIRouter
from schemas import HealthResponse, EngineStatus, ModelsResponse
from services.ollama_engine import check_ollama_health
from config import get_settings
import httpx
import logging

router = APIRouter()
logger = logging.getLogger("audioauth.routes.health")
settings = get_settings()


async def _check_gemini() -> bool:
    if not settings.gemini_api_key:
        return False
    return True


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check engine availability",
)
async def health_check() -> HealthResponse:
    """Returns the status of Gemini and Ollama engines."""
    gemini_ok = await _check_gemini()
    ollama_ok, ollama_models = await check_ollama_health()

    if gemini_ok and ollama_ok:
        status = "healthy"
    elif gemini_ok or ollama_ok:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        gemini=EngineStatus(
            available=gemini_ok,
            model="gemini-2.5-flash",
            note=None if gemini_ok else "API key missing",
        ),
        ollama=EngineStatus(
            available=ollama_ok,
            model=settings.ollama_model,
            note=None if ollama_ok else "Ollama not running — start with `ollama serve`",
        ),
        primary="gemini",
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
        gemini_model="gemini-2.5-flash",
        ollama_model=settings.ollama_model,
        ollama_models_available=ollama_models,
    )
