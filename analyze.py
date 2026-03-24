from fastapi import APIRouter, HTTPException
from schemas import AnalyzeRequest, AnalyzeResponse
from services.orchestrator import analyze
import logging

router = APIRouter()
logger = logging.getLogger("audioauth.routes.analyze")


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Classify a voice sample as Human or AI-Generated",
    response_description="Structured classification result with confidence score, signals, and feature scores",
)
async def analyze_audio(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    ## AudioAuth Voice Analysis

    Accepts a **Base64-encoded audio file** and returns a forensic classification:

    - **verdict**: `HUMAN` or `AI_GENERATED`
    - **confidence**: 0–100 score
    - **language_detected**: auto-detected or confirmed language
    - **signals**: list of acoustic indicators supporting the verdict
    - **scores**: per-feature acoustic authenticity scores
    - **risk_level**: `LOW` / `MEDIUM` / `HIGH`
    - **engine_used**: which engine produced the result (`claude` or `ollama`)

    ### Supported Languages
    Tamil · English · Hindi · Malayalam · Telugu (+ auto-detect)

    ### Audio Format
    Pass either:
    - A **data URI**: `data:audio/mp3;base64,<data>`
    - A **raw base64** string

    Supported formats: MP3, WAV, OGG, M4A, FLAC
    """
    try:
        result = await analyze(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error during analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
