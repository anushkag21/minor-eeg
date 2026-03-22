/**
 * NeuroGuard Clinic – Dashboard Controller
 * Real-time Chart.js graphs, camera feed, sensor polling, question handling
 */

// ============================================================
// State
// ============================================================
let testRunning = false;
let testPaused = false;
let timerInterval = null;
let pollInterval = null;
let elapsedSeconds = 0;
let answeredCount = 0;
let currentQuestionIndex = 0;
let cameraStream = null;

// Chart instances
let eegChart, hrvChart, fusionChart;

// Data buffers (keep last 40 points)
const MAX_POINTS = 40;
const eegAlpha = [], eegBeta = [], eegTheta = [], eegDelta = [];
const hrvBpm = [];
const fusionScores = [];
const timeLabels = [];

// ============================================================
// Initialization
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    initCamera();
});

// ============================================================
// Camera
// ============================================================
async function initCamera() {
    const video = document.getElementById('cameraFeed');
    const offlineMsg = document.getElementById('cameraOfflineMsg');
    const statusBadge = document.getElementById('cameraStatusBadge');

    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: 640, height: 480 }
        });
        video.srcObject = cameraStream;
        offlineMsg.style.display = 'none';
    } catch (err) {
        console.warn('Camera not available:', err.message);
        video.style.display = 'none';
        offlineMsg.style.display = 'flex';
        statusBadge.className = 'badge bg-danger-subtle text-danger';
        statusBadge.innerHTML = '<i class="bi bi-camera-video-off me-1"></i>OFFLINE';

        // Update sensor badge
        const camSensor = document.getElementById('sensor-camera');
        if (camSensor) {
            camSensor.querySelector('.sensor-dot').className = 'sensor-dot offline';
        }

        // Show fallback notice
        const notice = document.getElementById('fallbackNotice');
        notice.style.display = 'block';
        document.getElementById('fallbackMessage').textContent =
            'Camera offline – using EEG/HRV sensors + adaptive questions only';
    }
}

// ============================================================
// Charts (Chart.js)
// ============================================================
function initCharts() {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        plugins: {
            legend: { display: false },
            tooltip: { enabled: true, mode: 'index', intersect: false }
        },
        scales: {
            x: {
                display: false,
                grid: { display: false }
            },
            y: {
                grid: { color: 'rgba(255,255,255,0.04)' },
                ticks: { color: 'rgba(255,255,255,0.3)', font: { size: 10 } }
            }
        },
        elements: {
            point: { radius: 0 },
            line: { tension: 0.4 }
        }
    };

    // EEG Chart – 4 band lines
    const eegCtx = document.getElementById('eegChart').getContext('2d');
    eegChart = new Chart(eegCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Alpha', data: [], borderColor: '#00e5ff', borderWidth: 1.5, fill: false },
                { label: 'Beta',  data: [], borderColor: '#76ff03', borderWidth: 1.5, fill: false },
                { label: 'Theta', data: [], borderColor: '#ffab40', borderWidth: 1.5, fill: false },
                { label: 'Delta', data: [], borderColor: '#e040fb', borderWidth: 1.5, fill: false },
            ]
        },
        options: { ...commonOptions }
    });

    // HRV Chart – single BPM line
    const hrvCtx = document.getElementById('hrvChart').getContext('2d');
    hrvChart = new Chart(hrvCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'BPM',
                data: [],
                borderColor: '#f44336',
                backgroundColor: 'rgba(244, 67, 54, 0.1)',
                borderWidth: 2,
                fill: true
            }]
        },
        options: { ...commonOptions }
    });

    // Fusion Score Chart
    const fusionCtx = document.getElementById('fusionChart').getContext('2d');
    fusionChart = new Chart(fusionCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Fusion Score',
                data: [],
                borderColor: '#00e5ff',
                backgroundColor: 'rgba(0, 229, 255, 0.08)',
                borderWidth: 2,
                fill: true
            }]
        },
        options: {
            ...commonOptions,
            scales: {
                ...commonOptions.scales,
                y: {
                    ...commonOptions.scales.y,
                    min: 0,
                    max: 27,
                    ticks: {
                        color: 'rgba(255,255,255,0.3)',
                        font: { size: 10 },
                        stepSize: 9
                    }
                }
            }
        }
    });
}

function pushDataPoint(data) {
    const label = data.timestamp || '';

    // Keep buffers at max length
    if (timeLabels.length >= MAX_POINTS) {
        timeLabels.shift();
        eegAlpha.shift(); eegBeta.shift(); eegTheta.shift(); eegDelta.shift();
        hrvBpm.shift();
        fusionScores.shift();
    }

    timeLabels.push(label);
    eegAlpha.push(data.eeg.alpha);
    eegBeta.push(data.eeg.beta);
    eegTheta.push(data.eeg.theta);
    eegDelta.push(data.eeg.delta);
    hrvBpm.push(data.hrv.bpm);
    fusionScores.push(data.fusion_score);

    // Update EEG chart
    eegChart.data.labels = [...timeLabels];
    eegChart.data.datasets[0].data = [...eegAlpha];
    eegChart.data.datasets[1].data = [...eegBeta];
    eegChart.data.datasets[2].data = [...eegTheta];
    eegChart.data.datasets[3].data = [...eegDelta];
    eegChart.update('none');

    // Update HRV chart
    hrvChart.data.labels = [...timeLabels];
    hrvChart.data.datasets[0].data = [...hrvBpm];
    hrvChart.update('none');

    // Update Fusion chart
    fusionChart.data.labels = [...timeLabels];
    fusionChart.data.datasets[0].data = [...fusionScores];
    fusionChart.update('none');
}

// ============================================================
// Sensor Data Polling
// ============================================================
function startPolling() {
    pollInterval = setInterval(async () => {
        if (testPaused) return;
        try {
            const res = await fetch('/api/sensor_data');
            const data = await res.json();
            updateDashboard(data);
        } catch (err) {
            console.error('Polling error:', err);
        }
    }, 600);   // poll every 600ms
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

function updateDashboard(data) {
    // Push chart data
    pushDataPoint(data);

    // Update camera metrics
    document.getElementById('blinkRate').textContent = data.camera.blink_rate.toFixed(0);

    // Determine dominant expression
    const expr = data.camera.facial_expression;
    const dominant = Object.entries(expr).sort((a, b) => b[1] - a[1])[0];
    document.getElementById('facialExpression').textContent =
        dominant[0].charAt(0).toUpperCase() + dominant[0].slice(1);

    document.getElementById('postureScore').textContent = data.camera.posture_score.toFixed(0) + '%';

    // Expression bars
    document.getElementById('exprNeutral').style.width = expr.neutral + '%';
    document.getElementById('exprNeutralPct').textContent = expr.neutral.toFixed(0) + '%';
    document.getElementById('exprSad').style.width = expr.sad + '%';
    document.getElementById('exprSadPct').textContent = expr.sad.toFixed(0) + '%';
    document.getElementById('exprHappy').style.width = expr.happy + '%';
    document.getElementById('exprHappyPct').textContent = expr.happy.toFixed(0) + '%';
    document.getElementById('exprAnxious').style.width = expr.anxious + '%';
    document.getElementById('exprAnxiousPct').textContent = expr.anxious.toFixed(0) + '%';

    // HRV values
    document.getElementById('bpmValue').textContent = data.hrv.bpm.toFixed(0);
    document.getElementById('rmssdValue').textContent = data.hrv.rmssd.toFixed(1);
    document.getElementById('spo2Value').textContent = data.spo2.toFixed(0) + '%';

    // Live score
    const score = Math.round(data.fusion_score);
    const scoreEl = document.querySelector('.score-value');
    scoreEl.textContent = score;

    // Color the score
    if (score <= 4) {
        scoreEl.style.color = '#4caf50';
        updateSeverityBadge('Normal', 'success');
    } else if (score <= 9) {
        scoreEl.style.color = '#ffeb3b';
        updateSeverityBadge('Mild', 'warning');
    } else if (score <= 14) {
        scoreEl.style.color = '#ff9800';
        updateSeverityBadge('Moderate', 'orange');
    } else if (score <= 19) {
        scoreEl.style.color = '#ff5722';
        updateSeverityBadge('Mod. Severe', 'danger');
    } else {
        scoreEl.style.color = '#f44336';
        updateSeverityBadge('Severe', 'danger');
    }

    // Confidence
    document.getElementById('confidenceText').textContent =
        'Confidence: ' + data.confidence.toFixed(1) + '%';
    document.querySelector('#liveConfidence strong').textContent =
        data.confidence.toFixed(1) + '%';
}

function updateSeverityBadge(text, colorClass) {
    const badge = document.getElementById('severityBadge');
    badge.textContent = text;

    const colors = {
        success: { bg: 'rgba(76,175,80,0.15)', color: '#4caf50' },
        warning: { bg: 'rgba(255,235,59,0.15)', color: '#ffeb3b' },
        orange:  { bg: 'rgba(255,152,0,0.15)',  color: '#ff9800' },
        danger:  { bg: 'rgba(244,67,54,0.15)',  color: '#f44336' },
    };
    const c = colors[colorClass] || colors.success;
    badge.style.background = c.bg;
    badge.style.color = c.color;
}

// ============================================================
// Timer
// ============================================================
function startTimer() {
    elapsedSeconds = 0;
    updateTimerDisplay();
    timerInterval = setInterval(() => {
        if (!testPaused) {
            elapsedSeconds++;
            updateTimerDisplay();
        }
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function updateTimerDisplay() {
    const min = Math.floor(elapsedSeconds / 60).toString().padStart(2, '0');
    const sec = (elapsedSeconds % 60).toString().padStart(2, '0');
    document.getElementById('sessionTimer').textContent = min + ':' + sec;
}

// ============================================================
// Test Controls
// ============================================================
async function startTest() {
    try {
        const res = await fetch('/api/start_test', { method: 'POST' });
        const data = await res.json();

        testRunning = true;
        testPaused = false;

        // Update buttons
        document.getElementById('btnStartTest').disabled = true;
        document.getElementById('btnPauseTest').disabled = false;
        document.getElementById('btnEndTest').disabled = false;

        // Update mode indicator
        document.getElementById('modeText').textContent =
            'Session active – ' + data.session_id;
        document.getElementById('modeIndicator').style.color = '#00e5ff';

        // Start timer & polling
        startTimer();
        startPolling();

    } catch (err) {
        console.error('Failed to start test:', err);
    }
}

function pauseTest() {
    testPaused = !testPaused;
    const btn = document.getElementById('btnPauseTest');
    if (testPaused) {
        btn.innerHTML = '<i class="bi bi-play-fill me-1"></i>Resume';
        document.getElementById('modeText').textContent = 'Session paused';
    } else {
        btn.innerHTML = '<i class="bi bi-pause-fill me-1"></i>Pause';
        document.getElementById('modeText').textContent = 'Session active';
    }
}

async function endTest() {
    if (!confirm('End the test and generate report?')) return;

    stopTimer();
    stopPolling();
    testRunning = false;

    // Update UI
    document.getElementById('btnStartTest').disabled = false;
    document.getElementById('btnPauseTest').disabled = true;
    document.getElementById('btnEndTest').disabled = true;
    document.getElementById('modeText').textContent = 'Generating report...';

    try {
        const res = await fetch('/api/end_test', { method: 'POST' });
        const data = await res.json();

        // Show result modal
        document.getElementById('resultScore').textContent = data.score;
        document.getElementById('resultSeverity').textContent = data.severity;
        document.getElementById('resultMessage').textContent = data.message;
        document.getElementById('resultReportLink').href = data.report_url;

        // Color the result circle
        const circle = document.getElementById('resultScoreCircle');
        if (data.score <= 4) circle.style.borderColor = '#4caf50';
        else if (data.score <= 9) circle.style.borderColor = '#ffeb3b';
        else if (data.score <= 14) circle.style.borderColor = '#ff9800';
        else circle.style.borderColor = '#f44336';

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('resultModal'));
        modal.show();

        // Show PDF download button
        document.getElementById('btnDownloadPdf').style.display = 'inline-block';
        document.getElementById('btnDownloadPdf').href = data.report_url;

        document.getElementById('modeText').textContent = 'Test complete – ' + data.severity;

    } catch (err) {
        console.error('Failed to end test:', err);
        document.getElementById('modeText').textContent = 'Error ending test';
    }
}

// ============================================================
// Question Handling
// ============================================================
async function submitAnswer(questionId, answerValue) {
    answeredCount++;

    // Update progress
    document.getElementById('questionProgress').textContent =
        answeredCount + ' / ' + TOTAL_QUESTIONS;
    const pct = (answeredCount / TOTAL_QUESTIONS) * 100;
    document.getElementById('questionProgressBar').style.width = pct + '%';

    // Submit to API
    try {
        const res = await fetch('/api/submit_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question_id: questionId, answer_value: answerValue })
        });
        const data = await res.json();

        // Show adaptive question if returned
        if (data.adaptive_question) {
            showAdaptiveQuestion(data.adaptive_question);
        }
    } catch (err) {
        console.error('Error submitting answer:', err);
    }

    // Show next question (after small delay for UX)
    setTimeout(() => {
        // Hide current question
        const current = document.getElementById('question-' + questionId);
        if (current) {
            current.style.opacity = '0.5';
            current.style.pointerEvents = 'none';
        }

        // Show next question
        currentQuestionIndex++;
        if (currentQuestionIndex < TOTAL_QUESTIONS) {
            const next = document.getElementById('question-' + QUESTIONS[currentQuestionIndex].id);
            if (next) {
                next.style.display = 'block';
                next.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }

        // Check if all done
        if (answeredCount >= TOTAL_QUESTIONS) {
            document.getElementById('questionsComplete').style.display = 'block';
        }
    }, 300);
}

function showAdaptiveQuestion(q) {
    const slot = document.getElementById('adaptiveQuestionSlot');
    document.getElementById('adaptiveQNum').textContent = 'Adaptive Question';
    document.getElementById('adaptiveQText').textContent = q.text;

    const optContainer = document.getElementById('adaptiveQOptions');
    optContainer.innerHTML = '';
    q.options.forEach(opt => {
        const label = document.createElement('label');
        label.className = 'option-label';
        label.innerHTML = `
            <input type="radio" name="q_adaptive_${q.id}" value="${opt.value}"
                   onchange="submitAdaptiveAnswer(${q.id}, ${opt.value})">
            <span class="option-custom-radio"></span>
            <span class="option-text">${opt.label}</span>
            <span class="option-score">${opt.value}</span>
        `;
        optContainer.appendChild(label);
    });

    slot.style.display = 'block';
    slot.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

async function submitAdaptiveAnswer(questionId, answerValue) {
    try {
        await fetch('/api/submit_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question_id: questionId, answer_value: answerValue })
        });
    } catch (err) {
        console.error('Error submitting adaptive answer:', err);
    }

    // Fade out after answer
    setTimeout(() => {
        const slot = document.getElementById('adaptiveQuestionSlot');
        slot.style.opacity = '0.5';
        slot.style.pointerEvents = 'none';
    }, 300);
}
