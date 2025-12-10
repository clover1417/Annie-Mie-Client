import asyncio
import json
import base64
import websockets
from websockets.server import serve
import numpy as np

from utils.logger import logger
import config


class BridgeServer:
    def __init__(self, speech_detector, identity_manager, tts_handler, llm_server_url):
        self.speech_detector = speech_detector
        self.identity_manager = identity_manager
        self.tts_handler = tts_handler
        self.llm_server_url = llm_server_url
        
        self.llm_websocket = None
        self.web_clients = set()
        
        self.mic_enabled = False
        self.cam_enabled = False
        self.think_mode = False
        
        self.camera_window = None
        self.camera_process = None
        
    async def start(self):
        async with serve(self.handle_web_client, "localhost", 8768):
            logger.success("Bridge Server running on ws://localhost:8768")
            await asyncio.Future()
            
    async def handle_web_client(self, websocket):
        self.web_clients.add(websocket)
        logger.info(f"Web client connected. Total clients: {len(self.web_clients)}")
        
        await self.send_to_web(websocket, {"type": "status", "connected": True})
        
        try:
            async for message in websocket:
                await self.process_web_message(websocket, json.loads(message))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.web_clients.discard(websocket)
            logger.info(f"Web client disconnected. Total clients: {len(self.web_clients)}")
            
    async def process_web_message(self, websocket, data):
        msg_type = data.get("type")
        
        if msg_type == "toggle_mic":
            self.mic_enabled = data.get("enabled", False)
            status = "ON" if self.mic_enabled else "OFF"
            logger.info(f"🎤 Microphone: {status}")
            
        elif msg_type == "toggle_cam":
            self.cam_enabled = data.get("enabled", False)
            status = "ON" if self.cam_enabled else "OFF"
            logger.info(f"📷 Camera: {status}")
            
            if self.cam_enabled:
                if not self.camera_process or self.camera_process.poll() is not None:
                    self.launch_camera_window()
            else:
                await self.stop_camera_window()
                
        elif msg_type == "toggle_think":
            self.think_mode = data.get("enabled", False)
            status = "ON" if self.think_mode else "OFF"
            logger.info(f"🧠 Think Mode (TTS speaks thoughts): {status}")
            
        elif msg_type == "show_feed":
            if self.cam_enabled:
                if not self.camera_process or self.camera_process.poll() is not None:
                    self.launch_camera_window()
                    logger.info("👁️ Show Feed - reopening camera window")
                else:
                    logger.info("👁️ Show Feed - camera window already visible")
            else:
                logger.info("👁️ Show Feed - please turn on Camera first")
                
        elif msg_type == "audio":
            if self.mic_enabled:
                await self.process_audio(data)
                
        elif msg_type == "video_frame":
            if self.cam_enabled:
                await self.process_video_frame(data)
                
        elif msg_type == "text":
            text = data.get("text", "")
            if text:
                logger.info(f"💬 User: {text}")
                await self.send_to_llm({"type": "text", "text": text})
                
        elif msg_type == "sync":
            logger.info("🔄 Sync requested, connecting to LLM server...")
            await self.connect_to_llm()
            
    async def process_audio(self, data):
        audio_base64 = data.get("audio_base64")
        if not audio_base64:
            return
            
        try:
            audio_bytes = base64.b64decode(audio_base64)
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_float = audio_int16.astype(np.float32) / 32768.0
            
            is_speech = self.speech_detector.detect_speech(audio_float)
            
            if is_speech:
                logger.debug("🔊 Speech detected, forwarding to LLM...")
                await self.send_to_llm({
                    "type": "audio",
                    "audio_base64": audio_base64,
                    "audio_format": "pcm"
                })
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            
    async def process_video_frame(self, data):
        frame_base64 = data.get("frame_base64")
        if not frame_base64:
            return
            
        try:
            import cv2
            frame_bytes = base64.b64decode(frame_base64)
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is not None and self.identity_manager.is_face_detection_available():
                faces = self.identity_manager.face_detector.detect_faces(frame)
                if faces:
                    for face in faces:
                        identity = self.identity_manager.identify_face(face)
                        if identity:
                            logger.info(f"👤 Identified: {identity['name']}")
                            
                if self.camera_window:
                    self.camera_window.update_frame(frame, faces)
                    
            await self.send_to_llm({
                "type": "video_frame",
                "frame_base64": frame_base64
            })
        except Exception as e:
            logger.error(f"Video processing error: {e}")
            
    async def connect_to_llm(self):
        try:
            self.llm_websocket = await websockets.connect(self.llm_server_url)
            logger.success(f"Connected to LLM server at {self.llm_server_url}")
            
            for client in self.web_clients:
                await self.send_to_web(client, {"type": "connection", "status": "connected"})
                
            asyncio.create_task(self.listen_to_llm())
        except Exception as e:
            logger.error(f"Failed to connect to LLM server: {e}")
            for client in self.web_clients:
                await self.send_to_web(client, {"type": "connection", "status": "disconnected"})
                
    async def listen_to_llm(self):
        if not self.llm_websocket:
            return
            
        try:
            async for message in self.llm_websocket:
                data = json.loads(message)
                
                if data.get("type") == "text":
                    text = data.get("text", "")
                    logger.info(f"🤖 Mie: {text}")
                    
                    if self.think_mode and "<think>" in text:
                        full_text = text
                    else:
                        full_text = text.split("</think>")[-1] if "</think>" in text else text
                        
                    for client in self.web_clients:
                        await self.send_to_web(client, {"type": "text", "text": full_text})
                        
                elif data.get("type") == "audio":
                    for client in self.web_clients:
                        await self.send_to_web(client, data)
                        
        except websockets.exceptions.ConnectionClosed:
            logger.warning("LLM server connection closed")
            for client in self.web_clients:
                await self.send_to_web(client, {"type": "connection", "status": "disconnected"})
                
    async def send_to_llm(self, data):
        if self.llm_websocket:
            try:
                await self.llm_websocket.send(json.dumps(data))
            except Exception as e:
                logger.error(f"Failed to send to LLM: {e}")
                
    async def send_to_web(self, websocket, data):
        try:
            await websocket.send(json.dumps(data))
        except Exception:
            pass
            
    async def start_camera_window(self):
        pass
        
    async def stop_camera_window(self):
        if self.camera_process:
            self.camera_process.terminate()
            self.camera_process = None

    def launch_camera_window(self):
        import subprocess
        import os
        import sys
        camera_script = os.path.join(os.path.dirname(__file__), "..", "camera_app", "main.py")
        self.camera_process = subprocess.Popen(
            [sys.executable, camera_script],
            cwd=os.path.dirname(camera_script)
        )
        logger.info("📷 Camera window launched")
