# 🤖 J.A.R.V.I.S. (Just A Rather Very Intelligent System)

> An autonomous, spatial, voice-controlled, and tool-augmented personal AI assistant modeled after Tony Stark's iconic AI.

---

## 🌟 Overview & Architecture

JARVIS is built from the ground up as an async-first, event-driven intelligent operating environment combining:

1. **Neural Reasoning Core**: State-driven conversation management and tool dispatching using OpenAI function calling.
2. **Real-time Spatial Tracking**: 3D hand tracking with gesture recognition (pinch trigger, open palm) and exponential landmark smoothing.
3. **Voice Interaction Pipeline**: Wake-word activation (`Hey JARVIS`), voice activity detection (VAD), speech-to-text transcription (Faster-Whisper), neural text-to-speech (Edge-TTS), and real-time barge-in interruption.
4. **Autonomous Tools Ecosystem**: Native integrations with Smart Home (Home Assistant, MQTT), Staff Automations (Email, Webhooks, Google Suite, Document Ops), and Desktop OS Control.
5. **Holographic 3D Web HUD**: Three.js WebGL holographic Arc Reactor visualizer with real-time telemetry, state-reactive animations, and spatial pointer.
6. **Zero-Trust Security Gate**: Policy engine (`auto_approve`, `require_confirmation`, `deny`) guarding high-risk actions.

```
                  +-----------------------------------+
                  |        User Interaction           |
                  |  (Voice / Spatial Hands / Web HUD)|
                  +-----------------+-----------------+
                                    |
          +-------------------------+-------------------------+
          |                         |                         |
          v                         v                         v
+------------------+      +------------------+      +------------------+
|  Voice Pipeline  |      | Spatial Vision   |      |  Holographic HUD |
|  - Wake Word     |      |  - MediaPipe     |      |  - Three.js Core |
|  - Silero VAD    |      |  - Pinch/Palm    |      |  - WebSocket     |
|  - Whisper STT   |      |  - Smoothing     |      |  - Telemetry Log |
|  - Edge-TTS      |      |  - Cam Stream    |      |  - Command Line  |
+--------+---------+      +--------+---------+      +--------+---------+
         |                         |                         |
         +-------------------------+-------------------------+
                                   | (Async Event Bus)
                                   v
                  +-----------------------------------+
                  |            Core Agent             |
                  |  - State Engine (IDLE, THINKING..)|
                  |  - SQLite Conversation Memory     |
                  |  - OpenAI Function Calling Loop   |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |      Security Permission Gate     |
                  |     (config/permissions.yaml)     |
                  +-----------------+-----------------+
                                    |
          +-------------------------+-------------------------+
          |                         |                         |
          v                         v                         v
+-------------------+     +-------------------+     +-------------------+
|    Smart Home     |     | Staff Automation  |     |   System & OS     |
| - Home Assistant  |     | - Email / SMTP    |     | - CPU/Disk Stats  |
| - MQTT Broker     |     | - Slack/Webhooks  |     | - Desktop Mouse   |
|                   |     | - Documents / I/O |     | - Key Automations |
+-------------------+     +-------------------+     +-------------------+
```

---

## 📁 Repository Structure

```
.
├── config/                     # System & Tool configurations
│   ├── permissions.yaml        # Security permissions policy
│   ├── secrets.example.env     # Environment variable template
│   ├── settings.py             # Global Pydantic settings
│   └── tools_config.yaml       # Modular tool parameters
├── core/                       # Core brain and orchestrator
│   ├── agent.py                # JarvisAgent with function calling
│   ├── event_bus.py            # Central pub/sub event bus
│   ├── interrupt.py            # Real-time barge-in interruption
│   ├── memory.py               # SQLite conversation history
│   ├── permissions.py          # Security policy gate
│   ├── prompts.py              # Persona and system prompts
│   └── state.py                # System state machine
├── storage/                    # Local persistent storage
│   ├── sqlite/                 # Conversation database
│   ├── vector_db/              # Knowledge embeddings
│   └── logs/                   # System runtime logs
├── tools/                      # Tool registry and implementations
│   ├── base_tool.py            # BaseTool abstract interface
│   ├── registry.py             # Dynamic auto-discovery registry
│   ├── smart_home/             # Home Assistant & MQTT tools
│   ├── staff_automations/      # Email, Webhook, Calendar, Document tools
│   └── system/                 # OS diagnostics & Desktop bot
├── ui/                         # User Interface layers
│   ├── desktop_overlay/        # Transparent PyQt6 desktop HUD
│   ├── server.py               # FastAPI web server + WebSockets
│   └── web/                    # Holographic Three.js Web HUD
│       ├── index.html          # HUD Interface
│       ├── css/hud.css         # Sci-Fi theme styling
│       └── js/                 # scene.js, hand_cursor.js, websocket.js, app.js
├── vision/                     # Spatial computer vision
│   ├── camera.py               # Resilient camera capture manager
│   ├── gestures.py             # Pinch and Open Palm classifiers
│   ├── smoothing.py            # Exponential coordinate smoothing
│   └── tracker.py              # MediaPipe async hand tracking loop
├── voice/                      # Audio & speech processing
│   ├── audio_io.py             # Microphone PyAudio stream
│   ├── stt.py                  # Faster-Whisper transcriber
│   ├── tts.py                  # Edge-TTS synthesizer
│   ├── vad.py                  # Silero voice activity detection
│   └── wake_word.py            # OpenWakeWord engine
├── tests/                      # Automated unit test suite
│   ├── test_agent.py           # Core agent logic tests
│   ├── test_memory.py          # SQLite memory tests
│   ├── test_permissions.py     # Security gate tests
│   ├── test_tools.py           # Tool execution tests
│   ├── test_vision.py          # Gesture & camera tests
│   └── test_voice.py           # Voice & barge-in tests
├── Dockerfile                  # Container deployment image
├── main.py                     # Main application entry point
├── requirements.txt            # Python dependencies
└── README.md                   # Documentation
```

---

## ⚡ Quick Start

### 1. Prerequisites

- **Python 3.10+** (Python 3.12 recommended)
- **FFmpeg & PortAudio** (for voice synthesis and microphone input):

  ```bash
  # On Ubuntu/Debian:
  sudo apt-get install -y portaudio19-dev ffmpeg libgl1

  # On macOS:
  brew install portaudio ffmpeg
  ```

### 2. Environment Configuration

Create a `.env` file from the provided example:

```bash
cp config/secrets.example.env .env
```

Edit `.env` to supply your OpenAI API key and service endpoints:

```env
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
HOME_ASSISTANT_URL=http://localhost:8123
HOME_ASSISTANT_TOKEN=your_token
MQTT_BROKER=localhost
MQTT_PORT=1883
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run JARVIS

```bash
python main.py
```

- Open your browser to **`http://localhost:8000`** to view the **3D Holographic Arc Reactor HUD**.
- Interact via terminal input, vocal speech, or the interactive HUD bottom console!

---

## 🧪 Running Automated Tests

Execute the complete test suite with `unittest`:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 🐳 Docker Deployment

To build and run JARVIS in an isolated container:

```bash
# Build image
docker build -t jarvis-assistant .

# Run container
docker run -d -p 8000:8000 --env-file .env --name jarvis jarvis-assistant
```

---

## 🛡️ Security & Permissions Policy

Sensitive tools require confirmation or explicit policy authorization configured in `config/permissions.yaml`:

- `auto_approve`: Executes automatically without pausing dialogue.
- `require_confirmation`: Asks for user confirmation before dispatching.
- `deny`: Prohibits execution completely.

Example snippet from `config/permissions.yaml`:

```yaml
default_policy: require_confirmation

tools:
  get_system_status: auto_approve
  home_assistant_control: auto_approve
  mqtt_publish: auto_approve
  read_document: auto_approve

  # High Risk Operations
  desktop_click_and_type: require_confirmation
  send_email: require_confirmation
```

---

## 📜 License

MIT License. Built for advanced agentic intelligence and human-AI collaboration.
