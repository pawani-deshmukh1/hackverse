import sys
import os

# Add the current directory to the Python path so it can find the 'services' folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from audio_recorder_streamlit import audio_recorder
import base64
import tempfile
import asyncio
from services.audio_processor import analyze_and_plot_audio
from services.pytorch_engine import get_pytorch_threat_score
from orchestrator import analyze
from schemas import AnalyzeRequest

# --- UI CONFIG ---
st.set_page_config(page_title="AudioAuth | Internal Debugger", layout="wide")
st.title("🛡️ AudioAuth Forensic Laboratory")
st.markdown("---")

# --- SIDEBAR: CONFIG ---
st.sidebar.header("System Configuration")
language = st.sidebar.selectbox("Target Language", ["English", "Hindi", "Tamil", "Telugu", "Malayalam"])
test_mode = st.sidebar.radio("Test Engine", ["Hybrid (Full Pipeline)", "Local Only (No Internet)"])

# --- LIVE RECORDING SECTION ---
st.subheader("🎤 00 // Live Signal Capture")
st.write("Click the mic icon and speak for 5 seconds...")
audio_bytes = audio_recorder(
    text="Click to Record",
    recording_color="#e74c3c",
    neutral_color="#10b981",
    icon_size="3x",
)

# --- IF AUDIO IS CAPTURED ---
if audio_bytes:
    # Save the live recording to a temp WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    st.audio(audio_bytes, format="audio/wav")
    st.success("✅ Signal captured. Analyzing live vector...")

    # --- EXECUTION (Same as before) ---
    col1, col2 = st.columns([1, 1])
    
    with st.spinner("🔬 Running Forensic Multi-Engine Analysis..."):
        # Convert bytes to Base64 for your pipeline
        b64_audio = base64.b64encode(audio_bytes).decode('utf-8')

        # 1. Run Librosa
        librosa_results = analyze_and_plot_audio(b64_audio)
        
        # 2. Run PyTorch (Local Neural Brain)
        pytorch_results = get_pytorch_threat_score(tmp_path)

    # --- DISPLAY RESULTS ---
    with col1:
        st.subheader("📊 01 // Acoustic Spectrogram")
        st.image(f"data:image/png;base64,{librosa_results['spectrogram_image_base64']}")
        
        st.subheader("🧮 02 // Signal Metrics")
        m = librosa_results['metrics']
        st.json({
            "SNR (dB)": m['snr_db'],
            "Duration (s)": m['duration_seconds'],
            "Suspiciously Clean?": m['is_too_clean']
        })

    with col2:
        st.subheader("🧠 03 // Neural Engine Score")
        score = pytorch_results['score']
        label = pytorch_results['label']
        
        # Color coding the metric
        color = "red" if label == "AI_GENERATED" else "green"
        st.markdown(f"### Verdict: :{color}[{label}]")
        st.progress(score / 100)
        st.write(f"Confidence: **{score}%**")

        st.subheader("🕵️ 04 // AI Detective Report (Gemini)")
        if test_mode == "Hybrid (Full Pipeline)":
            # Simulate the orchestrator call
            req = AnalyzeRequest(audio_base64=b64_audio, language=language.lower())
            try:
                # Running the async orchestrator in a sync Streamlit environment
                final_report = asyncio.run(analyze(req))
                st.success(final_report.reasoning)
                st.write("**Signals Detected:**")
                for s in final_report.signals:
                    icon = "🚩" if s.type == "negative" else "✅"
                    st.write(f"{icon} {s.text}")
            except Exception as e:
                st.error(f"Gemini/Ollama Error: {str(e)}")
        else:
            st.warning("Offline Mode: Cloud reporting skipped. Using local heuristics only.")

    # Cleanup
    os.remove(tmp_path)

st.markdown("---")
st.caption("AudioAuth v1.0 | Ashutosh M | Hackverse 2026")