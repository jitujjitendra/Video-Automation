# AI Video Automation Agent

Transform your ideas into stunning music videos and short films using AI. Simply describe your concept, and the agent handles everything - from scriptwriting to final video assembly.

## Features

- **AI Script Generation** - Generates lyrics, stories, and scene-by-scene screenplays using Google Gemini Pro
- **Visual Generation** - Creates video clips using Veo 3.1 (Coming Soon)
- **Audio Generation** - Text-to-speech with Edge TTS and AI music (Coming Soon)
- **Lip Sync** - Realistic mouth movements with Wav2Lip (Coming Soon)
- **Auto Editing** - Automated video assembly with FFmpeg (Coming Soon)
- **Web Interface** - Modern dark-themed UI with real-time progress tracking

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Vanilla HTML/CSS/JS (Single Page App) |
| Backend | Python FastAPI |
| AI Model | Google Gemini Pro |
| Video Gen | Veo 3.1 (via Google AI) |
| TTS | Edge TTS |
| Lip Sync | Wav2Lip (via Colab) |
| Editing | FFmpeg |
| Hosting | GitHub Pages (UI) + Google Colab (GPU) |

## Quick Start (Windows)

### One-Click Install

1. Clone the repository:
   ```
   git clone https://github.com/jitujjitendra/Video-Automation.git
   cd Video-Automation
   ```

2. Run the installer:
   ```
   install.bat
   ```

3. Add your Gemini API key to the `.env` file

4. Start the application:
   ```
   start.bat
   ```

### Manual Setup

1. Install Python 3.10+
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your Gemini API key
4. Run the server:
   ```
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
5. Open `http://localhost:8000/static/index.html` in your browser

## Getting a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with "AIza...")
5. Paste it into the app when prompted

## Project Structure

```
Video-Automation/
├── frontend/                    # Web UI (vanilla HTML/CSS/JS)
│   ├── index.html              # Single-page application
│   ├── css/style.css           # Dark theme styling
│   └── js/
│       ├── app.js              # Main app logic + routing
│       ├── api.js              # Backend API communication
│       └── progress.js         # WebSocket live updates
├── backend/                    # FastAPI server
│   ├── main.py                 # API endpoints + WebSocket
│   ├── orchestrator.py         # Pipeline orchestrator
│   ├── agents/                 # AI agent modules
│   │   ├── script_agent.py    # Lyrics/story/screenplay generation
│   │   ├── visual_agent.py    # Video generation (placeholder)
│   │   ├── audio_agent.py     # TTS + music (placeholder)
│   │   ├── lipsync_agent.py   # Lip sync (placeholder)
│   │   └── editor_agent.py    # Auto editing (placeholder)
│   ├── services/              # External service integrations
│   │   ├── gemini_service.py  # Google Gemini API
│   │   ├── tts_service.py     # Edge TTS (placeholder)
│   │   ├── ffmpeg_service.py  # FFmpeg (placeholder)
│   │   └── colab_service.py   # Colab (placeholder)
│   └── utils/                 # Utilities
│       ├── config.py          # Configuration management
│       └── file_manager.py    # File operations
├── outputs/                    # Generated video outputs
├── templates/                  # JSON output templates
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
├── install.bat                # Windows installer
├── start.bat                  # Windows launcher
└── README.md                  # This file
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/validate-key` | Validate Gemini API key |
| POST | `/api/generate` | Start video generation |
| GET | `/api/status/{task_id}` | Get task progress |
| GET | `/api/download/{task_id}` | Download result |
| WS | `/ws/progress/{task_id}` | Live progress updates |

## Current Status

### Phase 1 (Complete)
- Project structure and configuration
- Web UI with all pages (Setup, Dashboard, Progress, Gallery, Settings)
- FastAPI backend skeleton with all endpoints
- WebSocket live progress support

### Phase 2 (Complete)
- Full Gemini API integration with retry logic
- Script Agent: lyrics, stories, screenplays, scene descriptions
- Pipeline orchestrator with progress tracking
- Frontend-backend integration

### Phase 3 (Planned)
- Visual generation with Veo 3.1
- Audio generation with Edge TTS
- Background music integration

### Phase 4 (Planned)
- Lip sync with Wav2Lip via Colab
- FFmpeg video editing and assembly
- Final export pipeline

### Phase 5 (Planned)
- Google Colab integration for GPU tasks
- Performance optimization
- Advanced features and polish

## Testing the UI

The frontend works standalone for UI testing (GitHub Pages compatible):
1. Open `frontend/index.html` directly in a browser
2. Enter any key starting with "AIza" to proceed past setup
3. Explore all UI pages and interactions

For full functionality, run the backend server.

## System Requirements

- **Minimum**: Windows 10, Python 3.10+, 4GB RAM
- **Recommended**: 8GB RAM, stable internet connection
- **GPU**: Not required locally (heavy processing runs on Google Colab)

## License

MIT License
