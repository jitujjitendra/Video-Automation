# AI Video Automation Agent

> Transform your ideas into stunning music videos and short films using AI. Describe your concept, and the agent handles everything from scriptwriting to final video assembly.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-blue)](https://jitujjitendra.github.io/Video-Automation/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)

## Features

- **AI Script Generation** - Generates lyrics, stories, and scene-by-scene screenplays using Google Gemini Pro
- **Visual Prompt Generation** - Creates detailed prompts for Veo 3.1 / Imagen video and image generation
- **Audio Generation** - Text-to-speech with Edge TTS (Hindi, English, Hinglish) + Suno AI music guide
- **Lip Sync** - Realistic mouth movements with Wav2Lip via Google Colab (free GPU)
- **Auto Editing** - Automated video assembly with FFmpeg
- **Web Interface** - Modern dark-themed UI with real-time progress tracking
- **Demo Mode** - Try the full UI on GitHub Pages without any setup
- **One-Click Install** - Windows batch scripts for easy setup

## How It Works

```
1. Enter API Key    -->    2. Describe Idea    -->    3. AI Generates    -->    4. Download
   (Google Gemini)          (any language)            (full pipeline)           (video ready)
```

The AI pipeline runs through 5 stages:
1. **Script Generation** - Gemini creates lyrics/story and a full screenplay with scene descriptions
2. **Visual Generation** - Generates image and video prompts for each scene (Veo 3.1 / Imagen)
3. **Audio Generation** - Edge TTS creates voiceover; Suno AI guide for background music
4. **Lip Sync** - Wav2Lip processes via Google Colab notebook (optional, requires GPU)
5. **Final Editing** - FFmpeg assembles scenes, audio, and effects into the final video

## Requirements

| Requirement | Details |
|-------------|---------|
| Python | 3.9 or higher |
| OS | Windows 10/11 (scripts), any OS (manual) |
| RAM | 4GB minimum, 8GB recommended |
| Internet | Required for AI API calls |
| GPU | Not required locally (Colab handles GPU tasks) |
| FFmpeg | Required for video assembly |
| Gemini API Key | Free from Google AI Studio |

## Quick Start

### Online Demo (No Setup Required)

Visit the live demo: **https://jitujjitendra.github.io/Video-Automation/**

The demo simulates the full pipeline with realistic sample output. No API key or backend needed.

### Local Installation (Windows)

```bash
# 1. Clone the repository
git clone https://github.com/jitujjitendra/Video-Automation.git
cd Video-Automation

# 2. Run the installer
install.bat

# 3. Add your Gemini API key to .env

# 4. Start the application
start.bat
```

### Manual Setup (Any OS)

```bash
# 1. Clone and enter directory
git clone https://github.com/jitujjitendra/Video-Automation.git
cd Video-Automation

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 4. Run the server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Open http://localhost:8000 in your browser
```

### Getting a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with "AIza...")
5. Paste it into the app or your `.env` file

## Supported Content

| Type | Languages | Best For |
|------|-----------|----------|
| Songs | Hindi, English, Hinglish | Romantic, emotional, party themes |
| Stories | Hindi, English, Hinglish | Short films, narratives, educational |
| Music Videos | All | Full visual + audio experience |

### Video Styles

- **Realistic** - Photorealistic AI-generated scenes (best quality, slower)
- **Animated** - Cartoon/anime style visuals (faster, creative)
- **Mixed** - Combination of realistic and animated elements

## Architecture

```
+------------------+         +-------------------+
|   Web Frontend   |  HTTP   |   FastAPI Backend  |
|  (SPA, Dark UI)  | <-----> |  (Python Server)   |
+------------------+   WS    +-------------------+
        |                            |
        |                    +-------+-------+
        |                    |               |
        v              +-----+-----+   +-----+-----+
  GitHub Pages         | Orchestrator|   |  Services  |
  (Demo Mode)          +-----+-----+   +-----+-----+
                             |               |
                    +--------+--------+      |
                    |    |    |    |   |      |
                   Script Visual Audio Lip  Editor
                   Agent  Agent  Agent Sync Agent
                                       Agent
                                         |
                                    Google Colab
                                    (Free GPU)
```

## Project Structure

```
Video-Automation/
├── frontend/                    # Web UI source (vanilla HTML/CSS/JS)
│   ├── index.html              # Single-page application
│   ├── css/style.css           # Dark theme styling
│   └── js/
│       ├── app.js              # Main app logic + routing
│       ├── api.js              # Backend API communication
│       ├── demo.js             # Demo mode simulation
│       └── progress.js         # WebSocket live updates
├── docs/                        # GitHub Pages (identical to frontend/)
├── backend/                     # FastAPI server
│   ├── main.py                 # API endpoints + static serving + WebSocket
│   ├── orchestrator.py         # Pipeline orchestrator
│   ├── agents/                 # AI agent modules
│   │   ├── script_agent.py    # Lyrics/story/screenplay generation
│   │   ├── visual_agent.py    # Video/image prompt generation
│   │   ├── audio_agent.py     # TTS + music generation
│   │   ├── lipsync_agent.py   # Lip sync via Colab
│   │   └── editor_agent.py    # FFmpeg video assembly
│   ├── services/              # External service integrations
│   │   ├── gemini_service.py  # Google Gemini API wrapper
│   │   ├── tts_service.py     # Edge TTS service
│   │   ├── ffmpeg_service.py  # FFmpeg operations
│   │   └── colab_service.py   # Colab notebook service
│   └── utils/                 # Utilities
│       ├── config.py          # Configuration management
│       └── file_manager.py    # File operations
├── colab_notebooks/            # Google Colab notebooks
│   ├── lipsync_processing.ipynb    # Wav2Lip lip sync
│   ├── video_enhancement.ipynb     # Video upscaling
│   └── video_automation_test.ipynb # Integration test
├── templates/                  # JSON output templates
│   ├── song_template.json     # Song generation template
│   └── story_template.json    # Story generation template
├── tests/                      # Test suite
│   └── test_pipeline.py       # Pipeline integration tests
├── outputs/                    # Generated video outputs (gitignored)
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
├── install.bat                # Windows one-click installer
├── start.bat                  # Windows launcher
├── LICENSE                    # MIT License
├── CHANGELOG.md               # Version history
└── README.md                  # This file
```

## Testing

```bash
# Run the test suite
python -m pytest tests/ -v

# Test specific pipeline
python -m pytest tests/test_pipeline.py -v

# Test with coverage (if pytest-cov installed)
python -m pytest tests/ --cov=backend -v
```

## Configuration

Environment variables (`.env` file):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `HOST` | No | `0.0.0.0` | Server bind address |
| `PORT` | No | `8000` | Server port |
| `OUTPUT_DIR` | No | `outputs` | Output directory |
| `MAX_CONCURRENT_TASKS` | No | `2` | Max parallel tasks |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/validate-key` | Validate Gemini API key |
| POST | `/api/generate` | Start video generation pipeline |
| GET | `/api/status/{task_id}` | Get task progress |
| GET | `/api/download/{task_id}` | Download generated result |
| GET | `/api/health` | Health check |
| WS | `/ws/progress/{task_id}` | Live progress via WebSocket |

## Usage Examples

### Hindi Love Song

```
Idea: "A romantic Hindi song about monsoon rain in Mumbai, a couple meeting at Marine Drive during a sudden downpour"
Language: Hindi
Music Type: AI Generated Song
Style: Realistic
```

### English Story

```
Idea: "A short sci-fi story about an astronaut discovering ancient ruins on Mars, mysterious symbols glowing in the dark"
Language: English
Music Type: Background Music + Voiceover
Style: Mixed
```

### Hinglish Rap

```
Idea: "A Hinglish rap about hustling in Delhi, street food, metro rides, and chasing dreams in the big city"
Language: Hinglish
Music Type: AI Generated Song
Style: Animated
```

## Tips for Best Results

- **Be descriptive** - Include specific locations, emotions, and visual details
- **Hindi songs** - Work best with emotional, romantic, or devotional themes
- **Realistic style** - Takes longer but produces cinematic quality
- **Shorter ideas** - 2-3 sentences are processed faster than long paragraphs
- **Lip sync** - Only needed for scenes with singing/speaking characters
- **Check prompts** - Review the generated visual prompts before using them with Veo 3.1

## Security

- API keys are stored only in your browser's localStorage (never sent to third parties)
- The backend processes keys in-memory only
- No user data is collected or transmitted beyond Google's Gemini API
- All processing happens locally or through your own API credentials

## Pipeline Details

### Script Agent
Uses Gemini Pro to generate:
- Lyrics (for songs) or narrative (for stories)
- Scene-by-scene screenplay with descriptions
- Visual prompts for each scene
- Dialogue/lyrics timing
- Camera movement suggestions

### Visual Agent
Generates prompts optimized for:
- Veo 3.1 video generation
- Imagen image generation
- Includes negative prompts for quality
- Camera direction and aspect ratio specifications

### Audio Agent
- Edge TTS for voiceover (multiple voices per language)
- Suno AI guide with style tags, BPM, and formatted lyrics
- Scene-by-scene audio file generation

### Lip Sync Agent
- Generates Google Colab notebook for Wav2Lip processing
- Works with free T4 GPU on Colab
- Processes uploaded video + audio to sync lips

### Editor Agent
- FFmpeg-based video assembly
- Scene concatenation with transitions
- Audio mixing (voiceover + background music)
- Final export in MP4 format

## Contributing

Contributions are welcome! Here is how to get started:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/jitujjitendra/Video-Automation.git
cd Video-Automation
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY to .env
python -m uvicorn backend.main:app --reload
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Google Gemini](https://ai.google.dev/) - AI text and content generation
- [Veo 3.1](https://deepmind.google/technologies/veo/) - AI video generation
- [Edge TTS](https://github.com/rany2/edge-tts) - Text-to-speech
- [Wav2Lip](https://github.com/Rudrabha/Wav2Lip) - Lip sync technology
- [FFmpeg](https://ffmpeg.org/) - Video processing
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [Suno AI](https://suno.ai/) - Music generation (guide output)
- [Google Colab](https://colab.research.google.com/) - Free GPU for processing
