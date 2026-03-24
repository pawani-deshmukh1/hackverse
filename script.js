/* ============================================
   AUDIOAUTH — script.js
   AI Voice Authenticity Detection Frontend
   ============================================ */

'use strict';

// ─── DOM Refs ───────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const recordBtn      = $('recordBtn');
const recordLabel    = $('recordLabel');
const recordTimer    = $('recordTimer');
const recordWaveform = $('recordWaveform');
const waveformBars   = $('waveformBars');
const audioUpload    = $('audioUpload');
const uploadLabel    = $('uploadLabel');
const fileInfo       = $('fileInfo');
const fileName       = $('fileName');
const analyzeBtn     = $('analyzeBtn');
const analyzeBtnText = $('analyzeBtnText');
const loadingSpinner = $('loadingSpinner');
const languageSelect = $('languageSelect');

// Results
const resultsSection  = $('resultsSection');
const spectroIdle     = $('spectroIdle');
const spectrogramImg  = $('spectrogramImg');
const scoreNumber     = $('scoreNumber');
const scoreCircle     = $('scoreCircle');
const confBar         = $('confBar');
const confLabel       = $('confLabel');
const riskBadge       = $('riskBadge');
const attackType      = $('attackType');
const reasonList      = $('reasonList');
const reportType      = $('reportType');
const reportConf      = $('reportConf');
const reportRisk      = $('reportRisk');
const reportLang      = $('reportLang');
const transcriptBox   = $('transcriptBox');
const wordCount       = $('wordCount');
const actionAlert     = $('actionAlert');
const actionTitle     = $('actionTitle');
const actionMessage   = $('actionMessage');
const alertIcon       = $('alertIcon');
const clock           = $('clock');

// ─── State ──────────────────────────────────────────────────────────────────
let audioFile        = null;
let mediaRecorder    = null;
let recordedChunks   = [];
let isRecording      = false;
let recordInterval   = null;
let recordSeconds    = 0;

// ─── Clock ──────────────────────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  const pad = n => String(n).padStart(2, '0');
  clock.textContent =
    `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
}
setInterval(updateClock, 1000);
updateClock();

// ─── Idle spectrogram bars ───────────────────────────────────────────────────
(function buildIdleBars() {
  const bars = $('idleBars');
  for (let i = 0; i < 28; i++) {
    const b = document.createElement('div');
    b.className = 'ibar';
    const h = 10 + Math.random() * 50;
    b.style.height = h + 'px';
    b.style.animationDelay = (Math.random() * 2) + 's';
    b.style.animationDuration = (1.5 + Math.random() * 1.5) + 's';
    bars.appendChild(b);
  }
})();

// ─── Waveform bars ───────────────────────────────────────────────────────────
(function buildWaveformBars() {
  for (let i = 0; i < 30; i++) {
    const b = document.createElement('div');
    b.className = 'bar';
    b.style.height = (8 + Math.random() * 24) + 'px';
    b.style.animationDelay = (Math.random() * 0.5) + 's';
    b.style.animationDuration = (0.3 + Math.random() * 0.4) + 's';
    waveformBars.appendChild(b);
  }
})();

// ─── Drag & Drop ─────────────────────────────────────────────────────────────
['dragenter', 'dragover'].forEach(evt =>
  uploadLabel.addEventListener(evt, e => {
    e.preventDefault();
    uploadLabel.classList.add('drag-over');
  })
);
['dragleave', 'drop'].forEach(evt =>
  uploadLabel.addEventListener(evt, e => {
    e.preventDefault();
    uploadLabel.classList.remove('drag-over');
    if (evt === 'drop') {
      const f = e.dataTransfer.files[0];
      if (f && f.type.startsWith('audio/')) setAudioFile(f);
    }
  })
);

// ─── File Upload ─────────────────────────────────────────────────────────────
audioUpload.addEventListener('change', e => {
  const f = e.target.files[0];
  if (f) setAudioFile(f);
});

function setAudioFile(f) {
  audioFile = f;
  fileName.textContent = f.name;
  fileInfo.classList.remove('hidden');
  fileInfo.classList.add('flex');
  analyzeBtn.disabled = false;
}

// ─── Record ──────────────────────────────────────────────────────────────────
recordBtn.addEventListener('click', async () => {
  if (!isRecording) {
    await startRecording();
  } else {
    stopRecording();
  }
});

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    recordedChunks = [];

    mediaRecorder.addEventListener('dataavailable', e => {
      if (e.data.size > 0) recordedChunks.push(e.data);
    });

    mediaRecorder.addEventListener('stop', () => {
      const blob = new Blob(recordedChunks, { type: 'audio/webm' });
      const file = new File([blob], 'recorded_audio.webm', { type: 'audio/webm' });
      setAudioFile(file);
      stream.getTracks().forEach(t => t.stop());
    });

    mediaRecorder.start();
    isRecording = true;
    recordBtn.classList.add('recording');
    recordLabel.textContent = 'STOP RECORDING';
    recordTimer.classList.remove('hidden');
    recordWaveform.classList.remove('hidden');
    recordSeconds = 0;
    recordInterval = setInterval(() => {
      recordSeconds++;
      const m = String(Math.floor(recordSeconds / 60)).padStart(2, '0');
      const s = String(recordSeconds % 60).padStart(2, '0');
      recordTimer.textContent = `${m}:${s}`;
    }, 1000);
  } catch (err) {
    console.error('Mic error:', err);
    alert('⚠ Microphone access denied. Please allow microphone permissions.');
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;
    clearInterval(recordInterval);
    recordBtn.classList.remove('recording');
    recordLabel.textContent = 'RECORD AUDIO';
    recordTimer.classList.add('hidden');
    recordWaveform.classList.add('hidden');
  }
}

// ─── Analyze ─────────────────────────────────────────────────────────────────
analyzeBtn.addEventListener('click', async () => {
  if (!audioFile) return;
  setLoadingState(true);

  const formData = new FormData();
  formData.append('audio', audioFile);
  formData.append('language', languageSelect.value);

  try {
    const response = await fetch('http://localhost:8000/analyze', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) throw new Error(`Server error: ${response.status}`);
    const data = await response.json();
    renderResults(data);
  } catch (err) {
    console.warn('Backend unreachable — using demo data:', err);
    // Demo fallback for hackathon testing
    const demo = {
      type: 'AI-GENERATED',
      confidence: 87,
      risk: 'HIGH',
      reason: [
        'Unnatural pitch consistency across phonemes',
        'No respiratory variation between sentences',
        'Spectral artifacts in 3-5kHz range',
        'Missing micro-tremor in vowel transitions',
      ],
      transcript: 'Hello, this is an automated system. Please press one to confirm your identity and provide your account details.',
      highlighted_words: ['automated', 'confirm', 'identity', 'account', 'details'],
      spectrogram: null,
    };
    renderResults(demo);
  } finally {
    setLoadingState(false);
  }
});

// ─── Loading State ────────────────────────────────────────────────────────────
function setLoadingState(loading) {
  analyzeBtn.disabled = loading;
  analyzeBtnText.classList.toggle('hidden', loading);
  loadingSpinner.classList.toggle('hidden', !loading);
}

// ─── Render Results ───────────────────────────────────────────────────────────
function renderResults(data) {
  const { type, confidence, risk, reason, transcript, highlighted_words, spectrogram } = data;
  const lang = languageSelect.options[languageSelect.selectedIndex].text;

  // Show section
  resultsSection.classList.remove('hidden');
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // Spectrogram
  if (spectrogram) {
    spectroIdle.classList.add('hidden');
    spectrogramImg.classList.remove('hidden');
    spectrogramImg.src = `data:image/png;base64,${spectrogram}`;
  }

  // Score circle
  const pct = Math.min(100, Math.max(0, confidence));
  const circumference = 2 * Math.PI * 58; // 364.4
  const offset = circumference - (pct / 100) * circumference;
  scoreCircle.style.strokeDashoffset = offset;

  // Score color
  const color = pct >= 70 ? '#ff2222' : pct >= 40 ? '#ffcc00' : '#00ff41';
  scoreCircle.style.stroke = color;
  scoreNumber.style.color  = color;

  // Animate number
  animateNumber(scoreNumber, 0, pct, 1200, v => `${v}%`);

  // Confidence bar
  confBar.style.width = pct + '%';
  confBar.style.background = color;
  confBar.style.color = color;
  confLabel.textContent = pct + '%';
  confLabel.style.color = color;

  // Risk badge
  riskBadge.textContent = risk || 'UNKNOWN';
  riskBadge.className = 'font-display text-sm font-bold tracking-widest px-3 py-1 rounded risk-badge';
  if (risk === 'HIGH')        riskBadge.classList.add('risk-high');
  else if (risk === 'MEDIUM') riskBadge.classList.add('risk-medium');
  else                        riskBadge.classList.add('risk-low');

  // Attack type
  attackType.textContent = type || '--';

  // Report
  reportType.textContent = type || '--';
  reportConf.textContent = pct + '%';
  reportRisk.textContent = risk || '--';
  reportRisk.style.color = color;
  reportLang.textContent = lang.toUpperCase();

  // Reasons
  reasonList.innerHTML = '';
  if (reason && reason.length) {
    reason.forEach((r, i) => {
      const li = document.createElement('li');
      li.className = 'reason-item';
      li.style.animationDelay = (i * 0.1) + 's';
      li.innerHTML = `<span class="r-icon">▸</span><span>${r}</span>`;
      reasonList.appendChild(li);
    });
  }

  // Transcript
  renderTranscript(transcript || '', highlighted_words || []);

  // Action alert
  renderActionAlert(risk, pct);
}

// ─── Transcript ───────────────────────────────────────────────────────────────
function renderTranscript(text, highlights) {
  if (!text) {
    transcriptBox.innerHTML = '<span style="color:rgba(255,255,255,0.2);font-family:\'Share Tech Mono\',monospace;font-size:12px;">NO TRANSCRIPT AVAILABLE</span>';
    wordCount.textContent = '';
    return;
  }

  // Sort highlights by length descending (avoid partial-word replacements)
  const sortedHL = [...highlights].sort((a, b) => b.length - a.length);

  let html = text;
  sortedHL.forEach(word => {
    const escaped = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp(`\\b(${escaped})\\b`, 'gi');
    html = html.replace(re, `<span class="suspicious" title="Suspicious keyword">$1</span>`);
  });

  transcriptBox.innerHTML = html;
  wordCount.textContent = highlights.length
    ? `${highlights.length} SUSPICIOUS KEYWORD${highlights.length > 1 ? 'S' : ''} FLAGGED`
    : '';
}

// ─── Action Alert ─────────────────────────────────────────────────────────────
function renderActionAlert(risk, confidence) {
  actionAlert.className = 'action-alert panel-card';

  if (risk === 'HIGH' || confidence >= 70) {
    actionAlert.classList.add('alert-high');
    alertIcon.style.color = '#ff2222';
    actionTitle.style.color = '#ff2222';
    actionTitle.textContent = '⚠ IMMEDIATE THREAT — DO NOT TRUST THIS AUDIO';
    actionMessage.textContent =
      'High-confidence AI generation detected. This voice recording exhibits strong synthetic artifacts. '
    + 'Do not proceed with any authentication, financial transactions, or sensitive information sharing. '
    + 'Report this attempt to your security team immediately.';
  } else if (risk === 'MEDIUM' || confidence >= 40) {
    actionAlert.classList.add('alert-medium');
    alertIcon.style.color = '#ffcc00';
    actionTitle.style.color = '#ffcc00';
    actionTitle.textContent = '⚡ CAUTION — VERIFY IDENTITY THROUGH SECONDARY CHANNEL';
    actionMessage.textContent =
      'Moderate synthetic indicators detected. Audio authenticity is inconclusive. '
    + 'Request additional verification before proceeding. Consider a callback to a known verified number '
    + 'or challenge-response protocol.';
  } else {
    actionAlert.classList.add('alert-low');
    alertIcon.style.color = '#00ff41';
    actionTitle.style.color = '#00ff41';
    actionTitle.textContent = '✓ LOW RISK — AUDIO APPEARS AUTHENTIC';
    actionMessage.textContent =
      'No significant synthetic markers detected. Voice characteristics are consistent with natural human speech. '
    + 'Standard security protocols remain in effect. Continue with normal verification procedures.';
  }
}

// ─── Animate Number ────────────────────────────────────────────────────────────
function animateNumber(el, from, to, duration, format) {
  const start = performance.now();
  function step(now) {
    const p = Math.min(1, (now - start) / duration);
    const ease = 1 - Math.pow(1 - p, 3);
    el.textContent = format(Math.round(from + (to - from) * ease));
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}
