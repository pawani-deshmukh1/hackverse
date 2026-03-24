from schemas import Language

SUPPORTED_LANGUAGES = {
    Language.tamil:     "Tamil (தமிழ்)",
    Language.english:   "English",
    Language.hindi:     "Hindi (हिन्दी)",
    Language.malayalam: "Malayalam (മലയാളം)",
    Language.telugu:    "Telugu (తెలుగు)",
    Language.auto:      "auto-detected",
}


def build_analysis_prompt(language: str, audio_metrics: dict, pytorch_results: dict) -> str:
    """
    Constructs a high-precision forensic prompt using local ML scores and acoustic math.
    """
    
    # Extract data for the prompt
    duration = audio_metrics.get("duration_seconds", "Unknown")
    snr = audio_metrics.get("snr_db", 0)
    pt_label = pytorch_results.get("label", "Unknown")
    pt_score = pytorch_results.get("score", 0)

    return f"""
    SYSTEM ROLE: 
    You are 'AudioAuth-Forensics', a specialized AI Auditor for the Indian Judiciary and Cyber-Crime cells. 
    Your mission is to provide an EXPLAINABLE verdict on whether a voice sample is HUMAN or AI_GENERATED.

    --- DATA INPUTS ---
    Target Language: {language}
    Sample Duration: {duration} seconds
    Acoustic SNR: {snr} dB
    Local Neural Engine Score (Wav2Vec2): {pt_score}% probability of being {pt_label}

    --- FORENSIC CONTEXT ---
    1. AI voices (ElevenLabs, RVC, VITS) often have an SNR > 25dB because they lack natural background 'room air'.
    2. Deepfakes often show 'Spectral Aliasing' (ghosting in high frequencies) which our local model detects.
    3. Humans have micro-tremors (jitter/shimmer) and irregular breathing pauses that AI models struggle to replicate.

    --- TASK ---
    Based on the {pt_score}% Neural Engine score, generate a structured forensic report. 
    If the Neural Engine says AI_GENERATED and the SNR is high, be highly suspicious.
    
    OUTPUT FORMAT (Strict JSON only):
    {{
      "verdict": "HUMAN" | "AI_GENERATED",
      "confidence": <integer 0-100>,
      "language_detected": "{language}",
      "language_confidence": 95,
      "reasoning": "<2-3 professional sentences explaining the verdict based on the SNR and Neural Score>",
      "signals": [
        {{"type": "negative", "text": "Unnatural spectral smoothness detected by Wav2Vec2"}},
        {{"type": "negative", "text": "Suspiciously high SNR ({snr}dB) suggests studio-clean synthesis"}},
        {{"type": "positive", "text": "Natural prosody variance found in phoneme transitions"}}
      ],
      "scores": {{
        "prosody_naturalness": <0-100>,
        "spectral_authenticity": <0-100>,
        "breath_patterns": <0-100>,
        "vocal_micro_variations": <0-100>,
        "phoneme_naturalness": <0-100>
      }},
      "risk_level": "LOW" | "MEDIUM" | "HIGH",
      "recommendation": "<Actionable advice for a bank or court>"
    }}
    """
