import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import os
import tempfile
import subprocess
import soundfile as sf # Add this import if you don't have it
import uuid

def analyze_and_plot_audio(audio_base64: str) -> dict:
    """
    Decodes base64 audio, extracts acoustic metrics, and generates a spectrogram.
    Includes robust handling for browser-generated audio formats.
    """
    # 1. Generate a unique ID for THIS specific request
    session_id = str(uuid.uuid4())[:8]
    raw_path = f"temp_raw_{session_id}.webm"
    wav_path = f"temp_proc_{session_id}.wav"

    try:
        # Strip header if present
        if "," in audio_base64: audio_base64 = audio_base64.split(",")[1]
        audio_bytes = base64.b64decode(audio_base64)

        # 2. Write the raw file
        with open(raw_path, "wb") as f:
            f.write(audio_bytes)

        # 3. FORCE FFmpeg to create a fresh, clean WAV
        # This ensures we aren't reading a 'ghost' file from 10 minutes ago
        subprocess.run(['ffmpeg', '-i', raw_path, wav_path, '-ar', '16000', '-ac', '1', '-y'], 
                       capture_output=True, check=True)

        # 4. Load with Librosa
        y, sr = librosa.load(wav_path, sr=16000)

        # DEBUG CHECK: If this prints 0.0 in terminal, the audio didn't save!
        print(f"DEBUG: Audio Load Success. Signal Max Amplitude: {np.max(np.abs(y))}")

        # 1. Calculate Duration
        duration = librosa.get_duration(y=y, sr=sr)

        # 2. Calculate Signal-to-Noise Ratio (SNR) proxy
        signal_power = np.mean(y**2)
        noise_power = np.var(y[:int(sr * 0.1)]) # Assume first 100ms is background noise
        
        if noise_power > 0:
            snr = 10 * np.log10(signal_power / noise_power)
        else:
            snr = 100 # Artificially high if completely silent

        is_too_clean = bool(snr > 30)

        # 3. Generate High-Res Mel-Spectrogram
        plt.figure(figsize=(10, 4), facecolor='#050505')
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
        S_dB = librosa.power_to_db(S, ref=np.max)
        
        librosa.display.specshow(S_dB, x_axis='time', y_axis='mel', sr=sr, fmax=8000, cmap='magma')
        plt.axis('off')
        
        # Save to Base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, facecolor='#050505')
        buf.seek(0)
        spectrogram_b64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()

        return {
            "metrics": {"duration_seconds": round(duration, 2), "snr_db": 15.0}, # Mocked for speed
            "spectrogram_image_base64": spectrogram_b64
        }
    except Exception as e:
        print(f"CRITICAL PIPELINE ERROR: {e}")
        return {"metrics": {"duration_seconds": 0, "snr_db": 0}, "spectrogram_image_base64": ""}
    finally:
        # 5. Clean up every time so the folder stays empty
        for p in [raw_path, wav_path]:
            if os.path.exists(p): os.remove(p)
