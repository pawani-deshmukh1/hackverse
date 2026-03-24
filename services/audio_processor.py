import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import soundfile as sf
import tempfile
import os

def analyze_and_plot_audio(base64_audio: str):
    """
    Takes Base64 audio, calculates forensic math, and generates a Spectrogram image.
    """
    # 1. Decode Base64 to a temporary file (safest way for librosa to read it)
    audio_bytes = base64.b64decode(base64_audio)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_path = temp_audio.name

    try:
        # 2. Load the audio file into Librosa
        y, sr = librosa.load(temp_path, sr=16000)
        
        # --- THE MATH (For the LLM) ---
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Calculate a basic Signal-to-Noise Ratio (SNR) proxy
        signal_power = np.mean(y**2)
        noise_power = np.var(y) # simplified approximation
        snr = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 0
        
        # --- THE VISUAL (For the UI) ---
        # Generate the Mel-Spectrogram (This is what exposes AI artifacts)
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
        S_dB = librosa.power_to_db(S, ref=np.max)
        
        # Create a matplotlib figure (without opening a window)
        plt.figure(figsize=(10, 4))
        librosa.display.specshow(S_dB, x_axis='time', y_axis='mel', sr=sr, fmax=8000, cmap='magma')
        plt.colorbar(format='%+2.0f dB')
        plt.title('Forensic Mel-Spectrogram Analysis')
        plt.tight_layout()
        
        # Save the plot to a BytesIO object instead of a file
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
        buf.seek(0)
        
        # Convert the image to Base64 so the frontend can render it as <img src="data:image/png;base64,...">
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close() # Free up memory!

        # 3. Return the package
        return {
            "metrics": {
                "duration_seconds": round(duration, 2),
                "snr_db": round(snr, 2),
                "is_too_clean": bool(snr > 30) # AI audio is often suspiciously clean
            },
            "spectrogram_image_base64": image_base64
        }

    finally:
        # Clean up the temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
