# AudioAuth | AI Voice Forensic Engine

**Real-time synthetic voice detection using Hybrid Neural Inference.**

## 🚀 Key Features
* **Local Neural Scorer:** Uses a Wav2Vec2 transformer (mo-thecreator/Deepfake-audio-detection) for zero-shot classification.
* **Acoustic Artifact Sniper:** Librosa-powered Mel-Spectrogram generation for visual frequency analysis.
* **Explainable AI (XAI):** Gemini 2.5 Flash integrates neural scores into human-readable forensic reports.
* **Military-Grade Failover:** 100% offline detection capability via local Ollama (Llama 3.1) integration.

## 🛠️ Technical Stack
* **Backend:** FastAPI, PyTorch, Librosa, Pydantic v2.
* **Frontend:** Vanilla JS, HTML5, Tailwind CSS (optimized for zero-latency capture).
* **Deployment:** Git LFS (Architecture) + Google Drive (Model Weights Mirror).

## 📂 Model Weights
Due to the model size (369MB), weights are mirrored here for judge verification: [IN
