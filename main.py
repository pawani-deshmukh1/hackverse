from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Ensure we use the actual integrated orchestrator from earlier!
from orchestrator import analyze as run_orchestrator
from schemas import AnalyzeRequest

# Set up logging for the hackathon presentation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audioauth.gateway")

app = FastAPI(title="AudioAuth Core API")

# Allow the frontend to talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API ENDPOINT ---
@app.post("/api/v1/analyze")
async def process_audio(request: AnalyzeRequest):
    try:
        logger.info(f"Incoming audio stream. Language: {request.language}")
        
        # --- THE SAFETY NET ---
        # Dynamically grab the audio whether your schema named it 'audio_data' or 'audio_base64'
        raw_b64 = request.audio_data if hasattr(request, 'audio_data') else getattr(request, 'audio_base64', '')
        
        # ADD THIS LINE: Strip the HTML header if it slipped through!
        if "," in raw_b64: raw_b64 = raw_b64.split(",")[1]
        
        # 1. Acoustic Math (Librosa + FFmpeg)
        from services.audio_processor import analyze_and_plot_audio
        acoustic_data = analyze_and_plot_audio(raw_b64)
        
        # 2. PyTorch (Local Edge Inference)
        from services.pytorch_engine import get_pytorch_threat_score
        pytorch_results = get_pytorch_threat_score(raw_b64) 
        
        # 3. Hybrid AI Detective (Gemini Cloud w/ Ollama Offline Fallback)
        from orchestrator import analyze
        final_report = await analyze(
            audio_base64=raw_b64, 
            language=request.language
        )
        
        return {
            "status": "success",
            "spectrogram": acoustic_data.get("spectrogram_image_base64", ""),
            "metrics": acoustic_data.get("metrics", {"duration_seconds": 0, "snr_db": 0}),
            "neural_score": pytorch_results,
            "forensic_report": final_report
        }

    except Exception as e:
        logger.error(f"Pipeline Failure: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- MOUNT FRONTEND ---
# This line makes your FastAPI server also host your HTML/CSS/JS!
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    logger.info("🚀 AudioAuth Hybrid Engine Online. Port: 8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
