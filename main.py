#!/usr/bin/env python3

import sys
sys.dont_write_bytecode = True

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import torchaudio
    if not hasattr(torchaudio, 'list_audio_backends'):
        torchaudio.list_audio_backends = lambda: ["soundfile"]
    if not hasattr(torchaudio, 'get_audio_backend'):
        torchaudio.get_audio_backend = lambda: "soundfile"
except ImportError:
    pass

import asyncio
from websocket_client import AnnieMieClient

def main():
    client = AnnieMieClient()
    
    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        print("\nClient stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
