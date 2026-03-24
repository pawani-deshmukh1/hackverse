import os
import torch
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
import librosa
import base64
import uuid
import subprocess
import logging

logger = logging.getLogger("audioauth.pytorch")

# 1. Define the ABSOLUTE path to your model folder
# This ensures Windows never gets confused about where 'models' is located
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "voice_detector")

print(f"DEBUG: Attempting to load model from: {MODEL_PATH}")

try:
    # 2. Check if the config file actually exists before trying to load
    if not os.path.exists(os.path.join(MODEL_PATH, "config.json")):
        raise FileNotFoundError(f"Missing config.json in {MODEL_PATH}")

    # 3. Load the local processor and model
    processor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_PATH)
    model = Wav2Vec2ForSequenceClassification.from_pretrained(MODEL_PATH)
    
    # 4. Move to GPU if available (for speed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval() # Set to evaluation mode

    print("✅ SUCCESS: Wav2Vec2 Local Model Loaded into RAM!")

except Exception as e:
    print(f"❌ CRITICAL ERROR: Could not load local model. Details: {e}")
    # Fallback to online model if the local one is corrupted (optional)
    # model_id = "facebook/wav2vec2-base-960h"
    # processor = Wav2Vec2FeatureExtractor.from_pretrained(model_id)
    # model = Wav2Vec2ForSequenceClassification.from_pretrained(model_id)
    processor = None
    model = None

def get_pytorch_threat_score(audio_b64):
    if not processor or not model:
        return {"label": "ERROR", "score": 0.0}

    try:
        # 1. We already proved this logic works in the processor!
        if "," in audio_b64: audio_b64 = audio_b64.split(",")[1]
        audio_bytes = base64.b64decode(audio_b64)
        
        # 2. Use a unique temp file just for the neural engine
        temp_path = f"neural_temp_{uuid.uuid4().hex[:6]}.wav"
        raw_path = f"raw_neural_{uuid.uuid4().hex[:6]}.webm"
        
        # Use FFmpeg to ensure the neural engine gets a clean WAV
        with open(raw_path, "wb") as f:
            f.write(audio_bytes)
        
        subprocess.run(['ffmpeg', '-i', raw_path, temp_path, '-ar', '16000', '-ac', '1', '-y'], 
                       capture_output=True)

        # 3. Load specifically for Wav2Vec2
        input_audio, _ = librosa.load(temp_path, sr=16000)
        
        # 4. Run Inference
        inputs = processor(input_audio, sampling_rate=16000, return_tensors="pt", padding=True)
        if 'device' in globals():
            inputs = inputs.to(device)

        with torch.no_grad():
            logits = model(**inputs).logits
        
        # 5. Calculate Score
        # Make sure index [1] is 'AI' and [0] is 'Human' based on your model training!
        probs = torch.nn.functional.softmax(logits, dim=-1)
        ai_prob = probs[0][1].item() 

        # --- THE CALIBRATION ---
        # If it's still hitting 100% on human files, your model might be inverted.
        # Check if index 0 is actually the AI label!
        label = "AI_GENERATED" if ai_prob > 0.85 else "HUMAN"

        # Cleanup
        if os.path.exists(temp_path): os.remove(temp_path)
        if os.path.exists(raw_path): os.remove(raw_path)

        return {"score": round(ai_prob * 100, 1), "label": label}

    except Exception as e:
        print(f"Neural Engine Error: {e}")
        return {"score": 0.0, "label": "ERROR"}
