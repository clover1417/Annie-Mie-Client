import asyncio
import subprocess
import webbrowser
import signal
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from network.bridge_server import BridgeServer
from utils.logger import logger


npm_process = None


async def main():
    global npm_process
    
    logger.info("=" * 60)
    logger.info("  Starting Annie Mie Client (Hybrid Mode)")
    logger.info("=" * 60)
    
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
    
    bridge_server = BridgeServer()
    
    asyncio.create_task(open_browser_delayed())
    
    await bridge_server.start()


async def open_browser_delayed():
    await asyncio.sleep(5)
    logger.info("Opening browser at http://localhost:3000...")
    webbrowser.open("http://localhost:3000")


def handle_exit(sig, frame):
    global npm_process
    logger.info("Shutting down...")
    if npm_process:
        npm_process.terminate()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        handle_exit(None, None)
