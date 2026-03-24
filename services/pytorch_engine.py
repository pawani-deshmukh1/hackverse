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

def get_pytorch_threat_score(audio_input: str):
    """
    Analyzes audio locally using the Wav2Vec2 model.
    Accepts either a file path OR a base64 string.
    """
    import base64
    import tempfile
    
    if not voice_classifier:
        return {"label": "ERROR", "score": 0.0}
        
    is_temp = False
    temp_path = ""
    
    try:
        # Check if it's base64 (usually very long) or a file path
        if len(audio_input) > 255 or audio_input.startswith("data:"):
            raw_b64 = audio_input
            if raw_b64.startswith("data:"):
                raw_b64 = raw_b64.split(";base64,", 1)[-1]
            
            # Decode and save to temp file
            audio_bytes = base64.b64decode(raw_b64 + "==")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                temp_audio.write(audio_bytes)
                temp_path = temp_audio.name
                is_temp = True
            
            target_path = temp_path
        else:
            target_path = audio_input
            
        # Run inference
        results = voice_classifier(target_path)
        
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
    finally:
        if is_temp and os.path.exists(temp_path):
            os.remove(temp_path)
