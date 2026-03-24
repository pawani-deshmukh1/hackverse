import base64
import logging
import time
import tempfile
import os
from schemas import AnalyzeRequest, AnalyzeResponse
from prompt import build_analysis_prompt
from services.gemini_engine import call_gemini, build_analyze_response
from ollama_engine import call_ollama
from services.audio_processor import analyze_and_plot_audio
from services.pytorch_engine import get_pytorch_threat_score
from config import get_settings

logger = logging.getLogger("audioauth.orchestrator")
settings = get_settings()


def _extract_raw_b64(audio_b64: str) -> tuple[str, float]:
    """
    Strip data URI prefix and return (raw_b64_string, size_kb).
    """
    raw = audio_b64.strip()
    if raw.startswith("data:"):
        raw = raw.split(";base64,", 1)[-1]

    # Validate it's plausible base64
    try:
        decoded = base64.b64decode(raw + "==")  # pad safely
        size_kb = len(decoded) / 1024
    except Exception:
        raise ValueError("Provided audio_base64 is not valid base64 data")

    return raw, size_kb


async def analyze(audio_base64: str = None, language: str = "english", request: AnalyzeRequest = None) -> dict:
    start = time.monotonic()

    # Support both schema and raw unpacking
    if request:
        raw_b64 = request.audio_data
        lang = request.language
    else:
        raw_b64 = audio_base64
        lang = language

    # ── Validate & decode ──────────────────────────────────────────────────────
    if len(raw_b64.encode()) > settings.max_audio_b64_bytes:
        raise ValueError(f"audio_data exceeds maximum allowed size")

    raw_b64, size_kb = _extract_raw_b64(raw_b64)

    # Send only first 300 chars of b64 to the model
    b64_preview = raw_b64[:300]
    
    # Process audio locally to get metrics and spectrogram image
    audio_results = analyze_and_plot_audio(raw_b64)
    spectrogram_image = audio_results["spectrogram_image_base64"]
    audio_metrics = audio_results["metrics"]

    # 2.5 💥 THE HEAVY HITTER: PyTorch Local Inference
    logger.info("🧠 Running local PyTorch Wav2Vec2 inference...")
    
    # We now call it natively with Base64 since the PyTorch wrapper handles temp files perfectly!
    try:
        pytorch_results = get_pytorch_threat_score(raw_b64)
        logger.info(f"PyTorch Score: {pytorch_results['score']}% {pytorch_results['label']}")
    except Exception as e:
        logger.error(f"Failed calling PyTorch: {e}")
        pytorch_results = {"label": "ERROR", "score": 0.0}

    prompt = build_analysis_prompt(
        language=lang,
        audio_metrics=audio_metrics,
        pytorch_results=pytorch_results
    )

    result_dict = None
    engine_used = None
    model_used  = None
    last_error  = None

    # ── Primary: Gemini ────────────────────────────────────────────────────────
    if settings.gemini_api_key:
        try:
            result_dict, model_used = await call_gemini(prompt)
            engine_used = "gemini"
            logger.info("Analysis completed via Gemini")
        except Exception as e:
            last_error = e
            logger.warning(f"Gemini failed ({type(e).__name__}: {e}), falling back to Ollama...")
    else:
        logger.info("No GEMINI_API_KEY set — skipping Gemini, using Ollama directly")

    # ── Fallback: Ollama ───────────────────────────────────────────────────────
    if result_dict is None:
        try:
            result_dict, model_used = await call_ollama(prompt)
            engine_used = "ollama"
            logger.info("Analysis completed via Ollama")
        except Exception as e:
            last_error = e
            logger.error(f"Ollama also failed: {e}")

    if result_dict is None:
        logger.warning(f"Both engines failed. Last error: {last_error}. Falling back to OFFLINE PyTorch.")
        result_dict = {
            "verdict": pytorch_results["label"],
            "confidence": int(pytorch_results["score"]),
            "language_detected": "Unknown",
            "language_confidence": 0,
            "reasoning": "OFFLINE MODE: Analysis performed by local Wav2Vec2 Neural Network. Cloud reporting unavailable.",
            "signals": [],
            "scores": {},
            "risk_level": "HIGH" if pytorch_results["score"] > 70 else "LOW",
            "recommendation": "Cloud unreachable. Relying on local acoustic heuristic.",
        }
        engine_used = "pytorch"
        model_used = "mo-thecreator/Deepfake-audio-detection"

    processing_ms = int((time.monotonic() - start) * 1000)

    # Dump the Pydantic schema to dictionary so main.py can unpack it easily
    resp = build_analyze_response(result_dict, engine_used, model_used, processing_ms, spectrogram_image)
    return resp.model_dump()
