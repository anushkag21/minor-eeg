"""
NeuroGuard Clinic – Flask Backend
Serves all frontend pages with mock data for demo purposes.
"""
import os
import json
import random
import time
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, send_from_directory

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, 'templates'),
    static_folder=os.path.join(FRONTEND_DIR, 'static')
)
app.secret_key = 'neuroguard-clinic-secret-key-change-in-production'

# ---------------------------------------------------------------------------
# In-memory mock data store
# ---------------------------------------------------------------------------
MOCK_SESSIONS = [
    {
        'session_id': 'NG-2026-001',
        'patient_id': 'PAT-1001',
        'patient_name': 'Anushka G.',
        'timestamp': '2026-03-20 10:30:00',
        'duration': '3 min 42 sec',
        'score': 8,
        'severity': 'Mild',
        'confidence': 89.2,
        'mode': 'full_multimodal',
        'sensors_used': ['Camera', 'EEG', 'HRV'],
    },
    {
        'session_id': 'NG-2026-002',
        'patient_id': 'PAT-1002',
        'patient_name': 'Rahul K.',
        'timestamp': '2026-03-19 14:15:00',
        'duration': '4 min 11 sec',
        'score': 15,
        'severity': 'Moderate',
        'confidence': 91.5,
        'mode': 'camera_only',
        'sensors_used': ['Camera'],
    },
    {
        'session_id': 'NG-2026-003',
        'patient_id': 'PAT-1003',
        'patient_name': 'Priya S.',
        'timestamp': '2026-03-18 09:00:00',
        'duration': '2 min 56 sec',
        'score': 4,
        'severity': 'Normal',
        'confidence': 94.1,
        'mode': 'full_multimodal',
        'sensors_used': ['Camera', 'EEG', 'EMG', 'HRV'],
    },
    {
        'session_id': 'NG-2026-004',
        'patient_id': 'PAT-1004',
        'patient_name': 'Vikram M.',
        'timestamp': '2026-03-17 16:45:00',
        'duration': '4 min 33 sec',
        'score': 22,
        'severity': 'Severe',
        'confidence': 87.8,
        'mode': 'sensor_only',
        'sensors_used': ['EEG', 'HRV'],
    },
    {
        'session_id': 'NG-2026-005',
        'patient_id': 'PAT-1005',
        'patient_name': 'Meera R.',
        'timestamp': '2026-03-16 11:20:00',
        'duration': '3 min 05 sec',
        'score': 11,
        'severity': 'Moderate',
        'confidence': 90.3,
        'mode': 'full_multimodal',
        'sensors_used': ['Camera', 'EEG', 'HRV'],
    },
]

# PHQ-9 base questions (gold standard)
PHQ9_QUESTIONS = [
    "Little interest or pleasure in doing things?",
    "Feeling down, depressed, or hopeless?",
    "Trouble falling or staying asleep, or sleeping too much?",
    "Feeling tired or having little energy?",
    "Poor appetite or overeating?",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down?",
    "Trouble concentrating on things, such as reading the newspaper or watching television?",
    "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless?",
    "Thoughts that you would be better off dead, or of hurting yourself in some way?",
]

# Adaptive AI-generated questions (triggered by sensor signals)
ADAPTIVE_QUESTIONS = [
    "Have you been experiencing unusual fatigue or difficulty waking up in the morning?",
    "Do you find yourself withdrawing from social interactions more than usual?",
    "Have you noticed changes in your ability to focus or make decisions?",
    "Do you feel a persistent sense of emptiness or emotional numbness?",
    "Have you been experiencing unexplained physical symptoms like headaches or body aches?",
]

QUESTION_OPTIONS = [
    {"value": 0, "label": "Not at all"},
    {"value": 1, "label": "Several days"},
    {"value": 2, "label": "More than half the days"},
    {"value": 3, "label": "Nearly every day"},
]

# Active test state
active_test = {
    'running': False,
    'session_id': None,
    'start_time': None,
    'answers': {},
    'sensor_mode': 'full_multimodal',
    'current_question_index': 0,
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def get_severity(score):
    """PHQ-9 severity classification."""
    if score <= 4:
        return 'Normal'
    elif score <= 9:
        return 'Mild'
    elif score <= 14:
        return 'Moderate'
    elif score <= 19:
        return 'Moderately Severe'
    else:
        return 'Severe'


def get_severity_color(severity):
    """Return CSS color class for severity level."""
    colors = {
        'Normal': 'success',
        'Mild': 'warning',
        'Moderate': 'orange',
        'Moderately Severe': 'danger',
        'Severe': 'danger',
    }
    return colors.get(severity, 'secondary')


def generate_mock_sensor_data():
    """Generate realistic-looking mock sensor data for demo."""
    t = time.time()
    return {
        'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
        'eeg': {
            'raw': round(random.gauss(0, 50), 2),
            'alpha': round(8 + random.gauss(0, 2), 2),
            'beta': round(15 + random.gauss(0, 3), 2),
            'theta': round(5 + random.gauss(0, 1.5), 2),
            'delta': round(2 + random.gauss(0, 0.8), 2),
            'asymmetry': round(random.gauss(0.1, 0.05), 3),
        },
        'emg': {
            'raw': round(random.gauss(0, 20), 2),
            'rms': round(abs(random.gauss(15, 5)), 2),
        },
        'hrv': {
            'bpm': round(72 + random.gauss(0, 5), 1),
            'rmssd': round(42 + random.gauss(0, 8), 1),
            'sdnn': round(55 + random.gauss(0, 10), 1),
        },
        'spo2': round(min(100, max(94, 97 + random.gauss(0, 1))), 1),
        'camera': {
            'blink_rate': round(max(0, 15 + random.gauss(0, 4)), 1),
            'facial_expression': {
                'neutral': round(max(0, min(100, 45 + random.gauss(0, 15))), 1),
                'sad': round(max(0, min(100, 25 + random.gauss(0, 10))), 1),
                'happy': round(max(0, min(100, 20 + random.gauss(0, 8))), 1),
                'anxious': round(max(0, min(100, 10 + random.gauss(0, 5))), 1),
            },
            'posture_score': round(max(0, min(100, 70 + random.gauss(0, 10))), 1),
        },
        'fusion_score': round(max(0, min(27, 8 + random.gauss(0, 3))), 1),
        'confidence': round(max(60, min(99, 88 + random.gauss(0, 4))), 1),
    }


# ---------------------------------------------------------------------------
# Page Routes
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    """Landing page."""
    stats = {
        'total_sessions': len(MOCK_SESSIONS),
        'avg_confidence': round(sum(s['confidence'] for s in MOCK_SESSIONS) / len(MOCK_SESSIONS), 1),
        'sensors_active': 4,
    }
    return render_template('index.html', stats=stats)


@app.route('/dashboard')
def dashboard():
    """Main live test dashboard."""
    patient_id = request.args.get('patient_id', f'PAT-{random.randint(1000, 9999)}')

    # Build question list (PHQ-9 base)
    questions = []
    for i, q in enumerate(PHQ9_QUESTIONS):
        questions.append({
            'id': i,
            'text': q,
            'options': QUESTION_OPTIONS,
            'source': 'PHQ-9',
        })

    # Sensor status (demo: all online)
    sensor_status = {
        'camera': {'online': True, 'label': 'Mac Camera'},
        'eeg': {'online': True, 'label': 'EEG (BioAmp)'},
        'emg': {'online': True, 'label': 'EMG (BioAmp)'},
        'hrv': {'online': True, 'label': 'HRV (MAX30105)'},
        'spo2': {'online': True, 'label': 'SpO₂ (MAX30105)'},
    }

    return render_template('dashboard.html',
                           patient_id=patient_id,
                           questions=questions,
                           sensor_status=sensor_status,
                           question_options=QUESTION_OPTIONS)


@app.route('/report/<session_id>')
def report(session_id):
    """Full report page for a session."""
    # Find the session or create a demo one
    session = None
    for s in MOCK_SESSIONS:
        if s['session_id'] == session_id:
            session = s
            break

    if not session:
        session = {
            'session_id': session_id,
            'patient_id': 'PAT-DEMO',
            'patient_name': 'Demo Patient',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'duration': '3 min 15 sec',
            'score': 12,
            'severity': 'Moderate',
            'confidence': 91.2,
            'mode': 'full_multimodal',
            'sensors_used': ['Camera', 'EEG', 'HRV'],
        }

    # Mock detailed report data
    report_data = {
        'session': session,
        'severity_color': get_severity_color(session['severity']),
        'sensor_insights': {
            'eeg_asymmetry': 'Mild left-frontal alpha asymmetry detected (0.12), consistent with sub-clinical depressive patterns.',
            'blink_rate': 'Blink rate of 18.3/min – slightly elevated, may indicate fatigue or cognitive load.',
            'hrv_analysis': 'RMSSD = 38.2ms (below average of 42ms), SDNN = 48.1ms – reduced parasympathetic tone noted.',
            'facial_analysis': 'Predominant neutral expression (52%), with intermittent sad micro-expressions (23%). Reduced spontaneous smiling.',
            'posture': 'Forward head posture detected 68% of test duration. Slight shoulder slump consistent with fatigue.',
        },
        'llm_report': """
            <p>Based on the comprehensive multimodal analysis conducted during this 3-minute session,
            the patient demonstrates indicators consistent with <strong>moderate depressive symptoms</strong>
            (PHQ-9 equivalent score: 12/27).</p>

            <p><strong>Key Observations:</strong></p>
            <ul>
                <li>EEG analysis reveals mild left-frontal alpha asymmetry (0.12), a biomarker
                    frequently associated with depressive tendencies in peer-reviewed literature.</li>
                <li>Heart rate variability metrics (RMSSD: 38.2ms) fall below the healthy baseline,
                    suggesting reduced autonomic flexibility often seen in mood disorders.</li>
                <li>Facial expression analysis detected predominant neutral affect with recurring
                    sad micro-expressions, coupled with reduced spontaneous positive expressions.</li>
                <li>Self-reported questionnaire responses align with physiological findings,
                    strengthening the overall assessment confidence to 91.2%.</li>
            </ul>

            <p><strong>Recommendations:</strong></p>
            <ul>
                <li>Consult with a qualified mental health professional for clinical evaluation.</li>
                <li>Consider regular physical activity (30 min/day) which research shows improves HRV and mood.</li>
                <li>Practice mindfulness or breathing exercises to improve autonomic balance.</li>
                <li>Maintain a consistent sleep schedule and monitor sleep quality.</li>
                <li>Schedule a follow-up NeuroGuard assessment in 2 weeks to track changes.</li>
            </ul>

            <p><em>Disclaimer: This report is generated by an AI system for informational purposes
            only and does not constitute a medical diagnosis. Please consult a healthcare
            professional for clinical assessment and treatment.</em></p>
        """,
        'question_answers': [
            {'question': PHQ9_QUESTIONS[0], 'answer': 'Several days', 'score': 1},
            {'question': PHQ9_QUESTIONS[1], 'answer': 'More than half the days', 'score': 2},
            {'question': PHQ9_QUESTIONS[2], 'answer': 'Several days', 'score': 1},
            {'question': PHQ9_QUESTIONS[3], 'answer': 'More than half the days', 'score': 2},
            {'question': PHQ9_QUESTIONS[4], 'answer': 'Not at all', 'score': 0},
            {'question': PHQ9_QUESTIONS[5], 'answer': 'Several days', 'score': 1},
            {'question': PHQ9_QUESTIONS[6], 'answer': 'More than half the days', 'score': 2},
            {'question': PHQ9_QUESTIONS[7], 'answer': 'Several days', 'score': 1},
            {'question': PHQ9_QUESTIONS[8], 'answer': 'More than half the days', 'score': 2},
        ],
    }

    return render_template('report.html', **report_data)


@app.route('/history')
def history():
    """Past sessions history page."""
    return render_template('history.html', sessions=MOCK_SESSIONS)


@app.route('/settings')
def settings():
    """Settings page."""
    current_settings = {
        'groq_api_key': '',
        'serial_port': '/dev/cu.usbserial-0001',
        'baud_rate': 115200,
        'camera_index': 0,
        'test_duration': 180,
        'enable_camera': True,
        'enable_eeg': True,
        'enable_emg': True,
        'enable_hrv': True,
        'enable_spo2': True,
        'enable_adaptive_questions': True,
    }
    return render_template('settings.html', settings=current_settings)


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------
@app.route('/api/sensor_data')
def api_sensor_data():
    """Return mock real-time sensor data (polled by dashboard.js)."""
    data = generate_mock_sensor_data()
    return jsonify(data)


@app.route('/api/start_test', methods=['POST'])
def api_start_test():
    """Start a new test session."""
    active_test['running'] = True
    active_test['session_id'] = f'NG-{datetime.now().strftime("%Y")}-{random.randint(100, 999)}'
    active_test['start_time'] = time.time()
    active_test['answers'] = {}
    active_test['current_question_index'] = 0

    return jsonify({
        'status': 'started',
        'session_id': active_test['session_id'],
        'message': 'Test session started. Sensors initializing...',
    })


@app.route('/api/submit_answer', methods=['POST'])
def api_submit_answer():
    """Submit an answer to a question."""
    data = request.get_json()
    question_id = data.get('question_id')
    answer_value = data.get('answer_value')

    active_test['answers'][question_id] = answer_value
    answered_count = len(active_test['answers'])

    # Check if we should add adaptive questions
    adaptive_question = None
    if answered_count == 5 or answered_count == 7:
        # Simulate Groq generating an adaptive question
        idx = min(answered_count - 5, len(ADAPTIVE_QUESTIONS) - 1)
        adaptive_question = {
            'id': 100 + idx,
            'text': ADAPTIVE_QUESTIONS[idx],
            'options': QUESTION_OPTIONS,
            'source': 'AI-Generated',
        }

    return jsonify({
        'status': 'recorded',
        'answered': answered_count,
        'total': 9,
        'adaptive_question': adaptive_question,
    })


@app.route('/api/end_test', methods=['POST'])
def api_end_test():
    """End the current test and return summary."""
    active_test['running'] = False

    # Calculate mock results
    total_score = sum(active_test['answers'].values()) if active_test['answers'] else random.randint(5, 20)
    severity = get_severity(total_score)

    session_id = active_test['session_id'] or f'NG-{datetime.now().strftime("%Y")}-{random.randint(100, 999)}'

    return jsonify({
        'status': 'completed',
        'session_id': session_id,
        'score': total_score,
        'severity': severity,
        'confidence': round(random.uniform(85, 96), 1),
        'report_url': f'/report/{session_id}',
        'message': f'Test complete. Severity: {severity} ({total_score}/27)',
    })


@app.route('/api/settings', methods=['POST'])
def api_save_settings():
    """Save settings (stub)."""
    data = request.get_json()
    return jsonify({'status': 'saved', 'message': 'Settings updated successfully.'})


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  NeuroGuard Clinic – Starting Server")
    print("  Open http://127.0.0.1:5000 in your browser")
    print("=" * 60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5001)
