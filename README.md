# Annie Mie Client

Client application for Annie Mie multimodal assistant.

## Features

- 🎤 Audio capture via Rust recorder with VAD
- 🌐 WebSocket connection to server
- 📱 Real-time text display from AI
- 🎥 Camera support (optional)

## Requirements

- Python 3.10+
- Rust (for building recorder)
- Microphone
- USB Camera (optional)

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd client
```

2. **Create virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

4. **Build Rust recorder**:
```bash
cd recorder
maturin develop --release
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

### Start Client

**Make sure the server is running first!**

```bash
python main.py
```

**Expected output**:
```
==================== Annie Mie Client ====================
ℹ Initializing Native Recorder...
Native sample rate: 48000Hz, resampling to 16kHz
✅ Recorder initialized!
ℹ Connecting to server: ws://localhost:8765
✅ Connected to server!
ℹ Starting audio recorder...
✅ Recorder started! Speak to interact with Mie.
```

### Usage

1. **Speak into microphone** → VAD detects speech
2. **Audio sent to server** → Qwen processes
3. **Text response displayed** in terminal

Example:
```
ℹ Speech detected: audio_2025-12-02_10-15-23.wav

🤖 Mie: Chào chị! |emotion="happy"| |animate="wave"| Em là Mie đây!
```

## Project Structure

```
client/
├── config.py            # Settings
├── websocket_client.py  # WebSocket client
├── main.py              # Entry point
├── core/                # Core logic (speech, parser)
├── handlers/            # TTS handlers
├── identity/            # Face recognition
├── utils/               # Utilities
├── recorder/            # Rust recorder module
├── data/                # Client data (recordings, identities)
└── requirements.txt     # Python dependencies
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVER_URI` | WebSocket server URI | `ws://localhost:8765` |
| `RATE` | Audio sample rate | `16000` |
| `CAMERA_INDEX` | Camera device index | `0` |
| `VIDEO_ENABLED` | Enable video capture | `false` |
| `CHUNK_SIZE` | Audio chunk size | `512` |

## Deployment Guide

### Local Setup (Windows/Linux)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Build Rust recorder
cd recorder
# Install Rust if needed: https://rustup.rs/
cargo build --release
cd ..

# 3. Configure .env
# Set SERVER_URI to point to your server IP
```

### NX Orin (ARM) Setup

```bash
# 1. Install PyTorch for ARM
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build Rust recorder (ARM)
rustup target add aarch64-unknown-linux-gnu
cd recorder
maturin develop --release
cd ..
```

## Troubleshooting

### Cannot Connect to Server

- Ensure server is running: `cd ../server && python main.py`
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
- Adjust `SILENCE_LIMIT` in `.env`

## License

MIT License

## Author

Clover/hungt
