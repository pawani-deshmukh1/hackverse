import base64
import logging
import time
from schemas import AnalyzeRequest, AnalyzeResponse
from prompt import build_analysis_prompt
from services.claude_engine import call_claude, build_analyze_response
from services.ollama_engine import call_ollama
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


async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    start = time.monotonic()

    # ── Validate & decode ──────────────────────────────────────────────────────
    if len(request.audio_base64.encode()) > settings.max_audio_b64_bytes:
        raise ValueError(
            f"audio_base64 exceeds maximum allowed size "
            f"({settings.max_audio_b64_bytes // 1_000_000} MB encoded)"
        )

    raw_b64, size_kb = _extract_raw_b64(request.audio_base64)

    # Send only first 300 chars of b64 to the model (the model can't actually
    # hear the audio — it analyses the request metadata + our forensic prompt)
    b64_preview = raw_b64[:300]

    prompt = build_analysis_prompt(
        b64_preview=b64_preview,
        language=request.language,
        sample_label=request.sample_label,
        audio_size_kb=size_kb,
    )

    result_dict = None
    engine_used = None
    model_used  = None
    last_error  = None

    # ── Primary: Claude ────────────────────────────────────────────────────────
    if settings.anthropic_api_key:
        try:
            result_dict, model_used = await call_claude(prompt)
            engine_used = "claude"
            logger.info("Analysis completed via Claude")
        except Exception as e:
            last_error = e
            logger.warning(f"Claude failed ({type(e).__name__}: {e}), falling back to Ollama...")
    else:
        logger.info("No ANTHROPIC_API_KEY set — skipping Claude, using Ollama directly")

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
        raise RuntimeError(
            f"Both engines failed. Last error: {last_error}. "
            "Check ANTHROPIC_API_KEY and ensure Ollama is running (`ollama serve`)."
        )

    processing_ms = int((time.monotonic() - start) * 1000)

    return build_analyze_response(result_dict, engine_used, model_used, processing_ms)
