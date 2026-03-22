# NeuroGuard Clinic – Data Models (Stub)
# TODO: Implement data models for sessions, sensor readings, reports

class Session:
    """Represents a single patient test session."""
    def __init__(self, session_id, patient_id, timestamp, score, severity, confidence):
        self.session_id = session_id
        self.patient_id = patient_id
        self.timestamp = timestamp
        self.score = score
        self.severity = severity
        self.confidence = confidence

class SensorReading:
    """Represents a single timestamped sensor reading."""
    def __init__(self, timestamp, eeg=None, emg=None, hrv=None, spo2=None,
                 blink_rate=None, facial_expression=None, posture_score=None):
        self.timestamp = timestamp
        self.eeg = eeg
        self.emg = emg
        self.hrv = hrv
        self.spo2 = spo2
        self.blink_rate = blink_rate
        self.facial_expression = facial_expression
        self.posture_score = posture_score
