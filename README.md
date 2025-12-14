# Annie Mie Client

Client application for Annie Mie multimodal AI assistant.

## Features

- 🎤 Audio capture via Rust recorder with VAD
- 🌐 WebSocket connection to LLM server
- 📱 Real-time text display from AI
- 🎥 Camera support with face recognition
- 🎭 Emotion and animation tag parsing

## Requirements

- Python 3.10+
- Rust (for building recorder)
- Node.js (for web UI)
- Microphone
- USB Camera (optional)

## Project Structure

```
client/
├── main.py                     # Entry point
├── config.py                   # Configuration settings
│
├── network/                    # Network communication
│   ├── llm_client.py           # WebSocket client for LLM server
│   └── bridge_server.py        # Bridge between Web UI and LLM
│
├── handler/                    # Processing & management
│   ├── stream_parser.py        # Real-time LLM output parser
│   ├── tts_sequence.py         # TTS sentence chunking
│   ├── identity_manager.py     # Face identity management
│   ├── identity_store.py       # Identity persistence
│   └── camera_window.py        # Camera feed window (PyQt6)
│
├── detector/                   # Detection modules
│   ├── speech_detector.py      # Silero VAD speech detection
│   ├── face_detector.py        # InsightFace face detection
│   └── semantic_recognition.py # Semantic turn detection
│
├── utils/                      # Utilities
│   └── logger.py               # Custom logger
│
├── recorder/                   # Rust audio/video recorder
│   ├── Cargo.toml
│   └── src/
│
├── web/                        # React/Vite Web UI
│   ├── package.json
│   └── ...
│
├── data/                       # Runtime data
│   └── identities/             # Face embeddings & profiles
│
├── .env.example
├── .gitignore
└── requirements.txt
```

## Installation

1. **Create virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Build Rust recorder**:
```bash
cd recorder
maturin develop --release
cd ..
```

4. **Install Web UI dependencies**:
```bash
cd web
npm install
cd ..
```

## Configuration

1. **Copy environment template**:
```bash
cp .env.example .env
```

2. **Edit `.env`** with your settings:
```env
SERVER_URI=ws://localhost:8765
RATE=16000
CAMERA_INDEX=0
VIDEO_ENABLED=false
```

## Running

**Make sure the LLM server is running first!**

```bash
python main.py
```

This will:
1. Start the Rust recorder (audio + video)
2. Launch the Web UI (npm run dev)
3. Start the bridge server (ws://localhost:8768)
4. Open browser at http://localhost:3000

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVER_URI` | LLM WebSocket server URI | `ws://localhost:8765` |
| `RATE` | Audio sample rate | `16000` |
| `CAMERA_INDEX` | Camera device index | `0` |
| `VIDEO_ENABLED` | Enable video capture | `false` |
| `CHUNK_SIZE` | Audio chunk size | `512` |

## Troubleshooting

### Cannot Connect to Server

- Ensure LLM server is running
- Check `SERVER_URI` in `.env`
- Verify network/firewall settings

### Recorder Build Failed

Install Rust first:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Then rebuild:
```bash
cd recorder
maturin develop --release
```

### No Audio Detected

- Check microphone permissions
- Test microphone with other apps

## License

MIT License

## Author

Clover
