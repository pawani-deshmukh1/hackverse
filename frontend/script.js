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

  const formData = new FormData();
  formData.append('audio', audioFile);
  formData.append('language', languageSelect.value);

  try {
    const res = await fetch('http://localhost:8000/api/v1/analyze', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) throw new Error();

    const data = await res.json();
    renderResults(data);

  } catch (err) {
    alert("⚠ Backend error. Using demo data.");

    renderResults({
      type: "AI-GENERATED",
      confidence: 85,
      risk: "HIGH",
      reason: ["Unnatural pitch", "No breathing variation"],
      transcript: "This is a fake generated voice",
      highlighted_words: ["fake", "generated"],
      spectrogram: null,
      duration: 4.5,
      snr: 18,
      engine: "Fallback"
    });
  }

  setLoading(false);
});

// ─── Loading ─────────────────────────────────────────────────────────────────
function setLoading(val) {
  analyzeBtn.disabled = val;
  analyzeBtnText.classList.toggle('hidden', val);
  loadingSpinner.classList.toggle('hidden', !val);
}

// ─── Render ──────────────────────────────────────────────────────────────────
function renderResults(data) {
  const { confidence, risk, spectrogram } = data;

  resultsSection.classList.remove('hidden');

  // 🧠 FIX 1: Spectrogram fallback
  if (spectrogram) {
    spectrogramImg.src = `data:image/png;base64,${spectrogram}`;
    spectrogramImg.classList.remove('hidden');

    spectrogramRender.src = `data:image/png;base64,${spectrogram}`;
    spectrogramRender.classList.remove('hidden');

    spectroIdle.classList.add('hidden');
  } else {
    spectrogramRender.classList.add('hidden');
    spectrogramImg.classList.add('hidden');
    spectroIdle.classList.remove('hidden');
  }

  // 🧠 FIX 2: Better color logic
  let color = "#00ff41";
  if (confidence > 70) color = "#ff2222";
  else if (confidence > 40) color = "#ffcc00";

  confBar.style.width = confidence + "%";
  confBar.style.background = color;

  scoreNumber.textContent = confidence + "%";
  scoreNumber.style.color = color;

  // Metadata
  metadataStrip.classList.remove('hidden');
  metaDuration.textContent = data.duration + "s";
  metaSnr.textContent = data.snr + " dB";
  metaEngine.textContent = data.engine;

  // Transcript
  let text = data.transcript;
  data.highlighted_words.forEach(w => {
    const re = new RegExp(`\\b${w}\\b`, "gi");
    text = text.replace(re, `<span class="suspicious">${w}</span>`);
  });
  transcriptBox.innerHTML = text;

  // Action
  if (risk === "HIGH") {
    actionTitle.textContent = "⚠ DO NOT TRUST";
    actionMessage.textContent = "High risk AI audio detected.";
  } else {
    actionTitle.textContent = "✅ SAFE AUDIO";
    actionMessage.textContent = "Audio seems authentic.";
  }
}