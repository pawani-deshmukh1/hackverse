import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import os
import tempfile
import soundfile as sf # Add this import if you don't have it

def analyze_and_plot_audio(audio_base64: str) -> dict:
    """
    Decodes base64 audio, extracts acoustic metrics, and generates a spectrogram.
    Includes robust handling for browser-generated audio formats.
    """
    try:
        audio_bytes = base64.b64decode(audio_base64)
        
        # Write to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name

        try:
            # Attempt to load using SoundFile first (more robust for raw browser data)
            y, sr = sf.read(temp_path)
            # If it's stereo, convert to mono for Librosa
            if len(y.shape) > 1:
                y = np.mean(y, axis=1)
            # Resample to 16000Hz if needed
            if sr != 16000:
                y = librosa.resample(y, orig_sr=sr, target_sr=16000)
                sr = 16000
        except Exception as e:
            # Fallback to librosa if soundfile fails
            print(f"Soundfile failed, falling back to librosa: {e}")
            y, sr = librosa.load(temp_path, sr=16000)

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

        # Cleanup
        os.remove(temp_path)

        return {
            "metrics": {
                "duration_seconds": round(duration, 2),
                "snr_db": round(float(snr), 2),
                "is_too_clean": is_too_clean
            },
            "spectrogram_image_base64": spectrogram_b64
        }
    except Exception as e:
        print(f"Acoustic processing error: {e}")
        # Return a safe fallback so the pipeline doesn't completely crash
        return {
            "metrics": {"duration_seconds": 0, "snr_db": 0, "is_too_clean": False},
            "spectrogram_image_base64": ""
        }
