import asyncio
import subprocess
import webbrowser
import signal
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.speech_detection import SpeechDetector
from identity.identity_manager import IdentityManager
from handlers.tts_handler import TTSHandler
from backend.bridge_server import BridgeServer
from utils.logger import logger
import config


async def main():
    logger.info("=" * 60)
    logger.info("  Starting Annie Mie Client (Hybrid Mode)")
    logger.info("=" * 60)
    
    logger.info("Initializing Speech Detector...")
    speech_detector = SpeechDetector()
    
    logger.info("Initializing Identity Manager...")
    identity_manager = IdentityManager()
    
    logger.info("Initializing TTS Handler...")
    tts_handler = TTSHandler()
    
    logger.success("All components initialized!")
    
    logger.info("Starting Bridge Server on ws://localhost:8768...")
    bridge_server = BridgeServer(
        speech_detector=speech_detector,
        identity_manager=identity_manager,
        tts_handler=tts_handler,
        llm_server_url=config.SERVER_URI
    )
    
    server_task = asyncio.create_task(bridge_server.start())
    
    logger.info("Starting Web UI (npm run dev)...")
    web_dir = os.path.join(os.path.dirname(__file__), "web")
    
    npm_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=web_dir,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    await asyncio.sleep(3)
    
    logger.info("Opening browser at http://localhost:3000...")
    webbrowser.open("http://localhost:3000")
    
    logger.success("Annie Mie is ready! Logs will appear below.")
    logger.info("-" * 60)
    
    def handle_exit(sig, frame):
        logger.info("Shutting down...")
        npm_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    try:
        await server_task
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        npm_process.terminate()


if __name__ == "__main__":
    asyncio.run(main())
