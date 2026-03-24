import sounddevice as sd
import numpy as np
import wave
import base64
import json
import time
import requests

def record_audio(filename="temp_live.wav", duration=5, fs=16000):
    print(f"\n🎤 RECORDING FOR {duration} SECONDS... SPEAK NOW!")
    # Record mono audio at 16kHz (standard for speech models)
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait() # Wait until recording is finished
    print("✅ Recording complete.")

    # Save to WAV file
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2) # 2 bytes = 16-bit
        wf.setframerate(fs)
        wf.writeframes(recording.tobytes())
    return filename

def generate_payload_and_send(filename, language="Hindi"):
    # Read the audio and encode to Base64
    with open(filename, "rb") as audio_file:
        encoded_string = base64.b64encode(audio_file.read()).decode('utf-8')

    # Construct the JSON payload (Matches your friend's structure)
    payload = {
        "session_id": f"live_demo_{int(time.time())}",
        "language": language,
        "audio_data": encoded_string,
        "sampling_rate": 16000,
        "label": "Human" # Change to 'AI' if testing a clone
    }

    print("\n📦 JSON Payload generated. Sending to local FastAPI backend...")

    # Instantly test your backend
    try:
        response = requests.post("http://127.0.0.1:8000/api/v1/analyze", json=payload)
        print(f"\n🧠 Backend Response: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Failed to connect to backend: {e}")

if __name__ == "__main__":
    # The Demo Flow
    input("Press Enter to start recording the 'Human' sample...")
    audio_file = record_audio(duration=6) # 6 seconds of speaking
    generate_payload_and_send(audio_file, language="English")
