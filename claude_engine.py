import httpx
import json
import logging
from schemas import AnalyzeResponse, AcousticScores, AcousticSignal
from config import get_settings

logger = logging.getLogger("audioauth.claude")
settings = get_settings()

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"


async def call_claude(prompt: str) -> dict:
    """
    Call Anthropic Claude API with the analysis prompt.
    Returns the parsed JSON dict from Claude's response.
    Raises httpx.HTTPError or ValueError on failure.
    """
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set in environment")

    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": settings.claude_model,
        "max_tokens": settings.claude_max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient(timeout=settings.claude_timeout) as client:
        logger.info(f"Calling Claude ({settings.claude_model})...")
        resp = client.post(CLAUDE_API_URL, headers=headers, json=payload)
        # Use await-compatible send
        response = await client.post(CLAUDE_API_URL, headers=headers, json=payload)
        response.raise_for_status()

    data = response.json()
    raw_text = "".join(
        block.get("text", "")
        for block in data.get("content", [])
        if block.get("type") == "text"
    ).strip()

    logger.debug(f"Claude raw response: {raw_text[:300]}")
    return _parse_json_response(raw_text), settings.claude_model


def _parse_json_response(raw: str) -> dict:
    # Strip any accidental markdown fences
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.lower().startswith("json"):
            clean = clean[4:]
    clean = clean.strip().rstrip("```").strip()
    return json.loads(clean)


def build_analyze_response(result: dict, engine: str, model: str, processing_ms: int) -> AnalyzeResponse:
    """Convert raw dict from LLM into a validated AnalyzeResponse."""
    signals = [
        AcousticSignal(type=s["type"], text=s["text"])
        for s in result.get("signals", [])
    ]
    scores_raw = result.get("scores", {})
    scores = AcousticScores(
        prosody_naturalness=    int(scores_raw.get("prosody_naturalness", 50)),
        spectral_authenticity=  int(scores_raw.get("spectral_authenticity", 50)),
        breath_patterns=        int(scores_raw.get("breath_patterns", 50)),
        vocal_micro_variations= int(scores_raw.get("vocal_micro_variations", 50)),
        phoneme_naturalness=    int(scores_raw.get("phoneme_naturalness", 50)),
    )
    return AnalyzeResponse(
        verdict=             result.get("verdict", "HUMAN"),
        confidence=          int(result.get("confidence", 50)),
        language_detected=   result.get("language_detected", "Unknown"),
        language_confidence= int(result.get("language_confidence", 50)),
        reasoning=           result.get("reasoning", ""),
        signals=             signals,
        scores=              scores,
        risk_level=          result.get("risk_level", "MEDIUM"),
        recommendation=      result.get("recommendation", ""),
        engine_used=         engine,
        model_used=          model,
        processing_ms=       processing_ms,
    )
