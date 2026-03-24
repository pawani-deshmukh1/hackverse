from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
from enum import Enum


class Language(str, Enum):
    auto     = "auto"
    tamil    = "tamil"
    english  = "english"
    hindi    = "hindi"
    malayalam = "malayalam"
    telugu   = "telugu"


class AnalyzeRequest(BaseModel):
    session_id: str = Field("demo_123", description="Session tracking ID")
    audio_data: str = Field(..., alias="audio_base64", description="Base64-encoded audio data")
    language: Language = Field(Language.auto)
    sampling_rate: int = Field(16000)
    sample_label: Optional[str] = Field(None)

    @field_validator("audio_data")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("audio_data must not be empty")
        # Strip data URI prefix if present
        if v.startswith("data:"):
            if ";base64," not in v:
                raise ValueError("Invalid data URI format. Expected data:<mime>;base64,<data>")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "demo_123",
                "audio_base64": "data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAP...",
                "language": "english",
                "sampling_rate": 16000,
                "sample_label": "suspect_call_01.mp3"
            }
        }
    }


# ── Signal item ────────────────────────────────────────────────────────────────

class SignalType(str, Enum):
    positive = "positive"   # human-like trait
    negative = "negative"   # synthetic/AI trait
    neutral  = "neutral"    # ambiguous


class AcousticSignal(BaseModel):
    type: SignalType
    text: str


# ── Acoustic feature scores ────────────────────────────────────────────────────

class AcousticScores(BaseModel):
    prosody_naturalness:     int = Field(..., ge=0, le=100)
    spectral_authenticity:   int = Field(..., ge=0, le=100)
    breath_patterns:         int = Field(..., ge=0, le=100)
    vocal_micro_variations:  int = Field(..., ge=0, le=100)
    phoneme_naturalness:     int = Field(..., ge=0, le=100)


# ── Main response ──────────────────────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    verdict:             Literal["HUMAN", "AI_GENERATED"]
    confidence:          int = Field(..., ge=0, le=100, description="0–100 confidence in verdict")
    language_detected:   str
    language_confidence: int = Field(..., ge=0, le=100)
    reasoning:           str
    signals:             List[AcousticSignal]
    scores:              AcousticScores
    risk_level:          Literal["LOW", "MEDIUM", "HIGH"]
    recommendation:      str
    engine_used:         Literal["gemini", "ollama", "pytorch"] = Field(
        ..., description="Which inference engine produced this result"
    )
    model_used:          str = Field(..., description="Exact model identifier used")
    processing_ms:       Optional[int] = Field(None, description="Server-side processing time in milliseconds")
    spectrogram_image:   str = Field(..., description="Base64 PNG image of the audio spectrum for the UI UI")

    model_config = {
        "json_schema_extra": {
            "example": {
                "verdict": "AI_GENERATED",
                "confidence": 91,
                "language_detected": "English",
                "language_confidence": 97,
                "reasoning": "The audio exhibits unnaturally consistent pitch variance and lacks micro-tremors typical of human speech. Breath pattern transitions are absent between sentences, strongly indicating TTS synthesis.",
                "signals": [
                    {"type": "negative", "text": "No breath intake detected between long utterances"},
                    {"type": "negative", "text": "Spectral envelope too smooth — lacks natural jitter"},
                    {"type": "positive", "text": "Realistic background room tone present"},
                    {"type": "neutral",  "text": "Intonation patterns borderline natural"}
                ],
                "scores": {
                    "prosody_naturalness": 28,
                    "spectral_authenticity": 19,
                    "breath_patterns": 8,
                    "vocal_micro_variations": 22,
                    "phoneme_naturalness": 35
                },
                "risk_level": "HIGH",
                "recommendation": "Do not authenticate — high probability of synthetic voice. Escalate for human review.",
                "engine_used": "claude",
                "model_used": "claude-sonnet-4-20250514",
                "processing_ms": 2340
            }
        }
    }


# ── Health response ────────────────────────────────────────────────────────────

class EngineStatus(BaseModel):
    available: bool
    model:     str
    note:      Optional[str] = None


class HealthResponse(BaseModel):
    status:  Literal["healthy", "degraded", "unhealthy"]
    gemini:  EngineStatus
    ollama:  EngineStatus
    primary: Literal["gemini", "ollama"]
    fallback: Literal["gemini", "ollama"]


class ModelsResponse(BaseModel):
    gemini_model:  str
    ollama_model:  str
    ollama_models_available: List[str]
