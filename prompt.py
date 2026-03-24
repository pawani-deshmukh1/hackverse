from schemas import Language

SUPPORTED_LANGUAGES = {
    Language.tamil:     "Tamil (தமிழ்)",
    Language.english:   "English",
    Language.hindi:     "Hindi (हिन्दी)",
    Language.malayalam: "Malayalam (മലയാളം)",
    Language.telugu:    "Telugu (తెలుగు)",
    Language.auto:      "auto-detected",
}


def build_analysis_prompt(
    b64_preview: str,
    language: Language,
    sample_label: str | None,
    audio_size_kb: float,
) -> str:
    lang_instruction = (
        f"The audio is expected to be in {SUPPORTED_LANGUAGES[language]}. Analyse accordingly."
        if language != Language.auto
        else "Auto-detect the spoken language from acoustic and phonetic cues."
    )

    label_line = f"Sample label : {sample_label}" if sample_label else "Sample label : (not provided)"

    return f"""You are AudioAuth, a forensic audio analysis engine specialised in detecting AI-generated and synthetic voices.

Your job: analyse the provided audio metadata and classify the voice as HUMAN or AI_GENERATED.

--- SAMPLE INFO ---
{label_line}
Audio size   : {audio_size_kb:.1f} KB (encoded)
Language     : {lang_instruction}
Base64 prefix: {b64_preview}

--- DETECTION CRITERIA ---
Analyse for the following acoustic indicators:
1. Spectral envelope smoothness — AI voices are unnaturally consistent
2. Prosody & intonation — AI often has flat or robotic rhythm
3. Breath patterns — humans breathe; TTS models typically do not
4. Vocal micro-variations — jitter, shimmer, formant wobble present in humans
5. Phoneme boundary transitions — AI can produce over-smooth coarticulation
6. Background and room noise consistency
7. Emotional naturalness — pitch shifts during emphasis
8. Clipping, artefacts, or codec anomalies typical of AI pipelines

--- OUTPUT FORMAT ---
Respond with ONLY a valid JSON object, no markdown fences, no preamble, no trailing text.

{{
  "verdict": "HUMAN" | "AI_GENERATED",
  "confidence": <integer 0-100>,
  "language_detected": "<full language name>",
  "language_confidence": <integer 0-100>,
  "reasoning": "<2-3 sentences explaining the verdict>",
  "signals": [
    {{"type": "positive", "text": "<human-like signal>"}},
    {{"type": "negative", "text": "<AI/synthetic signal>"}},
    {{"type": "neutral",  "text": "<ambiguous signal>"}}
  ],
  "scores": {{
    "prosody_naturalness":    <0-100>,
    "spectral_authenticity":  <0-100>,
    "breath_patterns":        <0-100>,
    "vocal_micro_variations": <0-100>,
    "phoneme_naturalness":    <0-100>
  }},
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "recommendation": "<one concise action recommendation>"
}}

Rules:
- Include 3–5 signals covering both positive and negative findings
- Be decisive — avoid hedging unless confidence is genuinely below 55
- risk_level should be HIGH if verdict is AI_GENERATED and confidence > 70
- Return ONLY the JSON object
"""
