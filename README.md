# NeuroGuard Clinic

**Real-time AI-powered Multimodal Depression Self-Analysis System**

## Quick Start

```bash
pip install -r requirements.txt
cd backend
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Pages

| Route | Description |
|---|---|
| `/` | Landing page |
| `/dashboard` | Live test (camera + sensors + questions) |
| `/report/<id>` | Full AI-generated report |
| `/history` | Past session history |
| `/settings` | Sensor & API configuration |

## Architecture

- **Frontend**: Bootstrap 5 + Chart.js + Jinja2
- **Backend**: Flask + MySQL
- **AI**: CNN-LSTM + EfficientNet + Attention Late Fusion
- **LLM**: Groq for adaptive questions & reports
- **Hardware**: ESP32 + BioAmp EXG Pill + MAX30105 + Mac Camera
