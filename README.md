# AudioAuth | AI Voice Forensic Engine

**Real-time synthetic voice detection using Hybrid Neural Inference.**

---

## 📌 Project Description

AudioAuth is an AI-powered system designed to detect whether an audio sample is human or AI-generated.
It combines deep learning models with signal processing and explainable AI to provide real-time, reliable, and interpretable results.

---

## ⚠️ Problem Statement

AI can generate highly realistic cloned voices, making it difficult to distinguish between real and fake audio.
This leads to:

* Voice-based financial scams
* Spread of misinformation
* Identity fraud

There is no reliable real-time system to verify voice authenticity.

---

## 🚀 Features and Functionality

* **Local Neural Scorer:** Uses a Wav2Vec2 transformer (mo-thecreator/Deepfake-audio-detection) for zero-shot classification.
* **Acoustic Artifact Sniper:** Librosa-powered Mel-Spectrogram generation for visual frequency analysis.
* **Explainable AI (XAI):** Gemini 2.5 Flash integrates neural scores into human-readable forensic reports.
* **Military-Grade Failover:** 100% offline detection capability via local Ollama (Llama 3.1) integration.
* **Real-time Analysis:** Upload or record audio and get instant results.
* **Confidence Scoring:** Displays risk level with detailed reasoning.
* **Visual Proof:** Spectrogram visualization for explainability.

---

## 🛠️ Tech Stack Used

* **Backend:** FastAPI, PyTorch, Librosa, Pydantic v2, mo-thecreator/Deepfake-audio-detection.
* **Frontend:** Vanilla JS, HTML5, Tailwind CSS (optimized for zero-latency capture).
* **Deployment:** Git LFS (Architecture) + Google Drive (Model Weights Mirror).

---

## ⚙️ Setup / Installation Instructions

1. **Clone the repository:**

   ```bash
   git clone <your-repo-link>
   cd audioauth
   ```

2. **Environment Setup:**
   Create a `.env` file in the root directory and add your API key for the Forensic Report Generation:

   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Local Neural Weights:**
   Download the 369MB `model.safetensors` file from the Drive link below and place it inside the:

   ```
   models/voice_detector/
   ```

5. **Run the Hybrid Engine:**

   ```bash
   python main.py
   ```

   *The FastAPI server will automatically serve the frontend. Open your browser and go to:*
   👉 `http://localhost:8000` (or `8080`)

---

## 📂 Model Weights

Due to the model size (369MB), weights are mirrored here for judge verification:
https://drive.google.com/file/d/1eC1B_WbUS1x3aZ83vDKkDgq0Is2LTzpW/view?usp=drive_link

---

## 👥 Team Details

* Ashutosh M (Backend & ML Integration)
* Pawani Deshmukh (Frontend Architecture)
* Khushalika Aglawe (Database & Backend Integration)
* Kashish Bhiwapurkar (Presentation Design)

---

## 🔮 Future Scope

* Integration with banking and fraud detection systems
* WhatsApp/Call-based scam detection tools
* Browser extension for media verification
* Real-time call monitoring systems

---

## 🎯 Conclusion

AudioAuth provides a real-time, explainable, and scalable solution to detect AI-generated voices and prevent misuse.
