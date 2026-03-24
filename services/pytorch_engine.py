from transformers import pipeline
import os
import logging

logger = logging.getLogger("audioauth.pytorch")

# Get the absolute path to your local model folder
# This ensures it works regardless of where you run main.py from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "voice_detector")

logger.info(f"🚀 Loading Local Neural Engine from: {MODEL_PATH}")

try:
    # This points the pipeline to your local folder. No internet needed!
    voice_classifier = pipeline(
        "audio-classification", 
        model=MODEL_PATH, 
        framework="pt"
    )
    logger.info("✅ Local Neural Engine Online.")
except Exception as e:
    logger.error(f"❌ Failed to load local model: {e}")
    voice_classifier = None

def get_pytorch_threat_score(audio_file_path: str):
    """
    Analyzes audio locally using the Wav2Vec2 model.
    """
    if not voice_classifier:
        return {"label": "ERROR", "score": 0.0}
    
    try:
        # Run inference
        results = voice_classifier(audio_file_path)
        
        # The model usually returns labels like 'LABEL_0' (Human) and 'LABEL_1' (AI)
        # OR 'real' and 'fake'. Let's find the 'fake' or 'AI' one.
        # We'll look for the highest score result.
        top_result = results[0]
        
        # Map the labels for the UI
        label = top_result['label'].upper()
        if "FAKE" in label or "LABEL_1" in label or "SPOOF" in label:
            final_label = "AI_GENERATED"
        else:
            final_label = "HUMAN"

        return {
            "label": final_label,
            "score": round(top_result['score'] * 100, 2)
        }
    except Exception as e:
        logger.error(f"Inference error: {e}")
        return {"label": "ERROR", "score": 0.0}
