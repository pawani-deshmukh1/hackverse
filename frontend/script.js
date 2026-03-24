'use strict';

// ─── DOM Refs ────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const recordBtn = $('recordBtn');
const recordLabel = $('recordLabel');
const recordTimer = $('recordTimer');
const recordWaveform = $('recordWaveform');
const waveformBars = $('waveformBars');
const audioUpload = $('audioUpload');
const uploadLabel = $('uploadLabel');
const fileInfo = $('fileInfo');
const fileName = $('fileName');
const analyzeBtn = $('analyzeBtn');
const analyzeBtnText = $('analyzeBtnText');
const loadingSpinner = $('loadingSpinner');
const languageSelect = $('languageSelect');

const resultsSection = $('resultsSection');
const spectroIdle = $('spectroIdle');
const spectrogramImg = $('spectrogramImg');
const spectrogramRender = $('spectrogram-render');

const scoreNumber = $('scoreNumber');
const scoreCircle = $('scoreCircle');
const confBar = $('confBar');
const confLabel = $('confLabel');
const riskBadge = $('riskBadge');
const attackType = $('attackType');

const transcriptBox = $('transcriptBox');
const wordCount = $('wordCount');

const actionAlert = $('actionAlert');
const actionTitle = $('actionTitle');
const actionMessage = $('actionMessage');

const metadataStrip = $('metadata');
const metaDuration = $('meta-duration');
const metaSnr = $('meta-snr');
const metaEngine = $('meta-engine');

let audioFile = null;

// --- Live Audio Capture Global Variables ---
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

// Initialize microphone access
async function setupAudio() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            console.log("Recording stopped, processing audio...");
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            audioFile = new File([audioBlob], "live_capture.wav", { type: 'audio/wav' });
            
            fileName.textContent = "Live Signal Captured";
            fileInfo.classList.remove('hidden');
            analyzeBtn.disabled = false;
            
            // Immediately trigger the analysis seamlessly
            audioChunks = [];
            analyzeBtn.click();
        };
    } catch (err) {
        console.error("Microphone access denied or failed.", err);
        alert("Please allow microphone access to use live capture.");
    }
}
setupAudio();

recordBtn.addEventListener('click', () => {
    if (!mediaRecorder) {
        setupAudio().then(() => toggleRecording());
    } else {
        toggleRecording();
    }
});

function toggleRecording() {
    if (!isRecording) {
        mediaRecorder.start();
        isRecording = true;
        recordLabel.innerText = "RECORDING... (Click to Stop)";
        recordBtn.style.borderColor = "#ff2222";
        recordBtn.style.color = "#ff2222";
    } else {
        mediaRecorder.stop();
        isRecording = false;
        recordLabel.innerText = "RECORD AUDIO";
        recordBtn.style.borderColor = "";
        recordBtn.style.color = "";
    }
}

// ─── Upload ──────────────────────────────────────────────────────────────────
audioUpload.addEventListener('change', e => {
  const f = e.target.files[0];
  if (f) {
    audioFile = f;
    fileName.textContent = f.name;
    fileInfo.classList.remove('hidden');
    analyzeBtn.disabled = false;

    // 🔥 Reset previous results
    resultsSection.classList.add('hidden');
    spectrogramRender.classList.add('hidden');
    spectrogramImg.classList.add('hidden');
    spectroIdle.classList.remove('hidden');
  }
});

// ─── Analyze ─────────────────────────────────────────────────────────────────
analyzeBtn.addEventListener('click', async () => {
  if (!audioFile) return;

  setLoading(true);

  console.log("Transmitting payload to Hybrid Engine...");

  // Convert file to Base64 to align with the backend's AnalyzeRequest schema
  const reader = new FileReader();
  reader.readAsDataURL(audioFile);
  reader.onload = async () => {
      try {
          // This removes the "data:audio/wav;base64," part
          const base64Clean = reader.result.split(',')[1]; 

          const response = await fetch("http://localhost:8080/api/v1/analyze", {
              method: "POST",
              headers: {
                  "Content-Type": "application/json"
              },
              body: JSON.stringify({
                  audio_base64: base64Clean, // Send the clean string
                  language: languageSelect.value.toLowerCase() // Sends "english" instead of "en"
              })
          });

          if (!response.ok) {
              throw new Error(`Server Error: ${response.status}`);
          }

          const data = await response.json();
          console.log("Analysis Complete:", data);

          // Render Results beautifully through the existing UI map
          renderResults({
              confidence: data.neural_score.score,
              risk: data.forensic_report.risk_level,
              reason: data.forensic_report.signals,
              transcript: data.forensic_report.reasoning,
              highlighted_words: ["AI", "synthetic", "human", "machine", "algorithm"],
              spectrogram: data.spectrogram,
              duration: data.metrics.duration_seconds || "N/A",
              snr: data.metrics.snr_db || 0,
              engine: data.forensic_report.engine_used || "Wav2Vec2 + Gemini"
          });

      } catch (error) {
          console.error("Integration Error:", error);
          alert("Pipeline failed. Check server console.");
      }
      setLoading(false);
  };
});

// ─── Loading ─────────────────────────────────────────────────────────────────
function setLoading(val) {
  analyzeBtn.disabled = val;
  analyzeBtnText.classList.toggle('hidden', val);
  loadingSpinner.classList.toggle('hidden', !val);
}

// ─── Render ──────────────────────────────────────────────────────────────────
function renderResults(data) {
  const { confidence, risk, reason, transcript, highlighted_words, spectrogram, duration, snr, engine } = data;

  resultsSection.classList.remove('hidden');

  // --- 1. SPECTROGRAM ---
  if (spectrogram && spectrogram.length > 10) {
    spectrogramImg.src = `data:image/png;base64,${spectrogram}`;
    spectrogramImg.classList.remove('hidden');
    spectrogramRender.src = `data:image/png;base64,${spectrogram}`;
    spectrogramRender.classList.remove('hidden');
    spectroIdle.classList.add('hidden');
  } else {
    console.warn("Spectrogram missing or empty.");
  }

  // --- 2. COLORS & SCORES ---
  let color = "#00ff41"; // Green (Safe)
  let riskText = "LOW RISK";
  
  if (risk === "HIGH" || confidence > 70) {
      color = "#ff2222"; // Red
      riskText = "HIGH RISK";
  } else if (risk === "MEDIUM" || confidence > 40) {
      color = "#ffcc00"; // Yellow
      riskText = "MEDIUM RISK";
  }

  // Main Confidence Matrix (Section 04)
  confBar.style.width = confidence + "%";
  confBar.style.background = color;
  scoreNumber.textContent = confidence + "%";
  scoreNumber.style.color = color;
  riskBadge.textContent = riskText;
  riskBadge.style.color = color;
  attackType.textContent = risk === "HIGH" ? "SYNTHETIC_CLONE" : "NONE";

  // Forensic Report Section (Section 03)
  $('forensic-ring-pct').textContent = confidence + "%";
  $('forensic-ring-pct').style.color = color;
  $('forensic-conf-pct').textContent = confidence + "%";
  $('confidence-bar').style.width = confidence + "%";
  $('confidence-bar').style.background = color;

  let humanScore = (100 - confidence).toFixed(1);
  $('forensic-human-pct').textContent = humanScore + "%";
  $('forensic-human-bar').style.width = humanScore + "%";

  // --- 3. METADATA ---
  metadataStrip.classList.remove('hidden');
  metaDuration.textContent = duration + "s";
  metaSnr.textContent = snr + " dB";
  metaEngine.textContent = engine || "Wav2Vec2 + Gemini";

  // --- 4. LISTS (Anomalies & Reasons) ---
  const reasonListEl = $('reasonList');
  const reasoningListEl = $('reasoning-list');
  reasonListEl.innerHTML = "";
  reasoningListEl.innerHTML = "";

  if (Array.isArray(reason)) {
      reason.forEach(r => {
          // Section 05 List
          const li = document.createElement('li');
          li.className = "font-mono text-xs text-white/70 flex items-start gap-2";
          li.innerHTML = `<span class="text-neon/40">></span> ${r}`;
          reasonListEl.appendChild(li);

          // Section 03 Anomaly Flags
          const fLi = document.createElement('li');
          fLi.className = "f-reason";
          fLi.innerHTML = `<span class="f-icon">[!]</span> <span>${r}</span>`;
          reasoningListEl.appendChild(fLi);
      });
  }

  // --- 5. REPORT SUMMARY TEXT ---
  $('reportType').textContent = risk === "HIGH" ? "AI_GENERATED" : "HUMAN_VOICE";
  $('reportType').style.color = color;
  $('reportConf').textContent = confidence + "%";
  $('reportRisk').textContent = riskText;
  $('reportRisk').style.color = color;

  // --- 6. TRANSCRIPT ---
  let text = transcript || "No reasoning provided.";
  if (highlighted_words && Array.isArray(highlighted_words)) {
      highlighted_words.forEach(w => {
        const re = new RegExp(`\\b${w}\\b`, "gi");
        text = text.replace(re, `<span class="suspicious">${w}</span>`);
      });
  }
  transcriptBox.innerHTML = text;

  // --- 7. ACTION ALERT ---
  if (risk === "HIGH" || confidence > 70) {
    actionTitle.textContent = "⚠ DO NOT TRUST";
    actionMessage.textContent = "High risk AI audio detected. Proceed with extreme caution.";
    actionAlert.style.borderColor = "#ff2222";
  } else {
    actionTitle.textContent = "✅ SAFE AUDIO";
    actionMessage.textContent = "Audio clears neural inspection. No synthetic markers found.";
    actionAlert.style.borderColor = "#00ff41";
  }
}