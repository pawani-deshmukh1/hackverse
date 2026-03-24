import httpx
import json
import logging
from config import get_settings

logger = logging.getLogger("audioauth.ollama")
settings = get_settings()


async def call_ollama(prompt: str) -> tuple[dict, str]:
    """
    Call local Ollama instance with the analysis prompt.
    Returns (parsed_dict, model_name).
    Raises httpx.HTTPError or ValueError on failure.
    """
    url = f"{settings.ollama_base_url}/api/generate"

    payload = {
        "model":  settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,      # Low temp for consistent JSON
            "top_p": 0.9,
            "num_predict": 1200,
        },
        "format": "json",            # Ollama native JSON mode
    }

    logger.info(f"Calling Ollama ({settings.ollama_model}) at {settings.ollama_base_url}...")

    async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

    data = response.json()
    raw_text = data.get("response", "").strip()

    logger.debug(f"Ollama raw response: {raw_text[:300]}")

    parsed = _parse_json_response(raw_text)
    return parsed, settings.ollama_model


async def check_ollama_health() -> tuple[bool, list[str]]:
    """Returns (is_available, list_of_local_models)."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            return True, models
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        return False, []


def _parse_json_response(raw: str) -> dict:
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.lower().startswith("json"):
            clean = clean[4:]
    clean = clean.strip().rstrip("```").strip()

    # Ollama sometimes wraps with extra text before/after JSON
    # Find first { and last }
    start = clean.find("{")
    end   = clean.rfind("}") + 1
    if start != -1 and end > start:
        clean = clean[start:end]

    return json.loads(clean)
