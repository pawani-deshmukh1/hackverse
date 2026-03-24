# 🎙️ AudioAuth — Backend API

AI vs Human voice classification engine built with **FastAPI**.  
Primary engine: **Anthropic Claude** | Fallback: **Ollama (llama3.1)**

---

## ⚡ Quick Start

### 1. Install dependencies
```bash
cd audioauth
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Start Ollama (fallback)
```bash
ollama serve          # in a separate terminal
ollama pull llama3.1  # only needed once (~4.7 GB)
```

### 4. Run the API
```bash
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs → http://localhost:8000/docs

---

## 📡 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analyze` | Classify a voice sample |
| GET  | `/api/v1/health`  | Check engine availability |
| GET  | `/api/v1/models`  | List configured models |
| GET  | `/docs`           | Swagger UI |

---

## 🔬 Analyze Request

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "audio_base64": "data:audio/mp3;base64,SUQzBAAAAAAAI1RTUVV...",
    "language": "english",
    "sample_label": "suspect_call_01.mp3"
  }'
```

### Supported languages
`auto` · `tamil` · `english` · `hindi` · `malayalam` · `telugu`

### Convert a local file to base64 (Python)
```python
import base64

with open("audio.mp3", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
    payload = f"data:audio/mp3;base64,{b64}"
```

---

## 📦 Response Schema

```json
{
  "verdict": "AI_GENERATED",
  "confidence": 91,
  "language_detected": "English",
  "language_confidence": 97,
  "reasoning": "The audio exhibits unnaturally consistent pitch...",
  "signals": [
    {"type": "negative", "text": "No breath intake detected between utterances"},
    {"type": "positive", "text": "Realistic room tone present"}
  ],
  "scores": {
    "prosody_naturalness": 28,
    "spectral_authenticity": 19,
    "breath_patterns": 8,
    "vocal_micro_variations": 22,
    "phoneme_naturalness": 35
  },
  "risk_level": "HIGH",
  "recommendation": "Do not authenticate — escalate for human review.",
  "engine_used": "claude",
  "model_used": "claude-sonnet-4-20250514",
  "processing_ms": 2340
}
```

---

## 🔁 Failover Logic

```
Request → Claude API
            ✅ success → return result (engine_used: "claude")
            ❌ fail    → Ollama llama3.1
                           ✅ success → return result (engine_used: "ollama")
                           ❌ fail    → 503 error
```

---

## 🩺 Health Check

```bash
curl http://localhost:8000/api/v1/health
```

```json
{
  "status": "healthy",
  "claude":  {"available": true,  "model": "claude-sonnet-4-20250514"},
  "ollama":  {"available": true,  "model": "llama3.1"},
  "primary": "claude",
  "fallback": "ollama"
}
```

---

## 🗂️ Project Structure

```
audioauth/
├── main.py              # FastAPI app entry point
├── config.py            # Settings (env vars)
├── schemas.py           # Pydantic request/response models
├── prompt.py            # Shared LLM prompt builder
├── requirements.txt
├── .env.example
├── routes/
│   ├── analyze.py       # POST /api/v1/analyze
│   └── health.py        # GET  /api/v1/health, /models
└── services/
    ├── orchestrator.py  # Failover logic
    ├── claude_engine.py # Anthropic API client
    └── ollama_engine.py # Ollama local client
```
# hackverse
AudioAuth is an AI-powered API that detects whether a voice sample is human or AI-generated, helping prevent fraud and ensure media authenticity across multiple languages.
