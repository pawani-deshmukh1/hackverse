import json
import logging
from google import genai
from google.genai import types
from schemas import AnalyzeResponse, AcousticScores, AcousticSignal
from config import get_settings

logger = logging.getLogger("audioauth.gemini")
settings = get_settings()

async def call_gemini(prompt: str) -> tuple[dict, str]:
    """Call Gemini API and force strict JSON output."""
    if not settings.gemini_api_key: # Add this to your config.py!
        raise ValueError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=settings.gemini_api_key)
    model_name = "gemini-2.5-flash" # Blazing fast for hackathons
    
    logger.info(f"Calling Gemini ({model_name})...")
    
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )
    
    logger.debug(f"Gemini raw response: {response.text[:300]}")
    return json.loads(response.text), model_name

def build_analyze_response(result: dict, engine: str, model: str, processing_ms: int, spectrogram_image: str) -> AnalyzeResponse:
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
        engine_used=         "gemini",
        model_used=          model,
        processing_ms=       processing_ms,
        spectrogram_image=   spectrogram_image
    )
