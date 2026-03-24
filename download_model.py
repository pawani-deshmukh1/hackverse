from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
import os

model_id = "mo-thecreator/Deepfake-audio-detection"
save_path = "./models/voice_detector/"

os.makedirs(save_path, exist_ok=True)

print("Downloading model to local storage...")
model = AutoModelForAudioClassification.from_pretrained(model_id)
extractor = AutoFeatureExtractor.from_pretrained(model_id)

model.save_pretrained(save_path)
extractor.save_pretrained(save_path)
print(f"Model saved to {save_path}. You can now run offline!")
