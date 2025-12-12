import asyncio
import json
import socket
import struct
import websockets
from websockets.server import serve

from utils.logger import logger
from network.llm_client import AnnieMieClient
import config


class BridgeServer:
    def __init__(self):
        self.client = AnnieMieClient()
        self.web_clients = set()
        self.cam_enabled = False
        self.camera_process = None
        self.frame_clients = []
        self.frame_server_socket = None
        
    async def start(self):
        self.client.initialize_components()
        await self.client.tts_handler.start()
        
        logger.info("Starting Rust Recorder (Audio + Video)...")
        self.client.recorder.start()
        self.client.recorder.stop_audio()
        self.client.running = True
        logger.success("Recorder ready! Toggle Mic/Camera in web UI.")
        
        self._start_frame_server()
        asyncio.create_task(self._process_audio_loop())
        
        connected = await self.client.connect()
        if not connected:
            logger.warning("Could not connect to LLM server. Will retry on sync.")
        else:
            asyncio.create_task(self.client.handle_server_messages())
        
        async with serve(self.handle_web_client, "localhost", 8768):
            logger.success("Bridge Server running on ws://localhost:8768")
            await asyncio.Future()
    
    async def _process_audio_loop(self):
        import os
        while self.client.running:
            if not self.client.is_mic_enabled:
                filepath = self.client.recorder.read_speech_event()
                if filepath and os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass
                await asyncio.sleep(0.1)
                continue
                
            filepath = self.client.recorder.read_speech_event()
            if filepath:
                try:
                    is_speech = self.client.speech_detector.is_speech(filepath)
                    if not is_speech:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        continue
                        
                    logger.success("Speech detected!")
                    
                    if self.client.websocket:
                        await self.client._process_and_send_message(filepath)
                    else:
                        logger.warning("LLM not connected - speech ignored")
                        if os.path.exists(filepath):
                            os.remove(filepath)
                            
                except Exception as e:
                    logger.error(f"Audio processing error: {e}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        
            await asyncio.sleep(0.1)
            
    async def handle_web_client(self, websocket):
        self.web_clients.add(websocket)
        logger.info(f"Web client connected. Total: {len(self.web_clients)}")
        
        connected = self.client.websocket is not None
        await self.send_to_web(websocket, {
            "type": "status", 
            "connected": connected,
            "mic_on": self.client.is_mic_enabled,
            "cam_on": self.cam_enabled
        })
        
        try:
            async for message in websocket:
                await self.process_web_message(websocket, json.loads(message))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.web_clients.discard(websocket)
            logger.info(f"Web client disconnected. Total: {len(self.web_clients)}")
            
    async def process_web_message(self, websocket, data):
        msg_type = data.get("type")
        logger.info(f"📨 Received: {msg_type}")
        
        if msg_type == "toggle_mic":
            enabled = data.get("enabled", False)
            self.client.is_mic_enabled = enabled
            
            if enabled:
                self.client.recorder.start_audio()
                logger.info("🎤 Microphone: ON (Rust recorder active)")
            else:
                self.client.recorder.stop_audio()
                logger.info("🎤 Microphone: OFF (Rust recorder paused)")
                
        elif msg_type == "toggle_cam":
            self.cam_enabled = data.get("enabled", False)
            self.client.is_cam_enabled = self.cam_enabled
            
            if self.cam_enabled:
                self.launch_camera_window()
                logger.info("📷 Camera: ON")
            else:
                await self.stop_camera_window()
                logger.info("📷 Camera: OFF")
                
        elif msg_type == "toggle_think":
            enabled = data.get("enabled", False)
            self.client.tts_handler.speak_thoughts = enabled
            status = "ON" if enabled else "OFF"
            logger.info(f"🧠 Think Mode: {status}")
                
        elif msg_type == "show_feed":
            if self.cam_enabled:
                if not self.camera_process or self.camera_process.poll() is not None:
                    self.launch_camera_window()
                    logger.info("👁️ Show Feed - reopening camera window")
                else:
                    logger.info("👁️ Show Feed - camera already visible")
            else:
                logger.info("👁️ Show Feed - turn on Camera first")
                
        elif msg_type == "text":
            text = data.get("text", "")
            if text and self.client.websocket:
                logger.info(f"💬 User: {text}")
                await self.client.websocket.send(json.dumps({
                    "type": "text",
                    "text": text
                }))
                
        elif msg_type == "sync":
            logger.info("🔄 Sync requested...")
            if not self.client.websocket:
                connected = await self.client.connect()
                if connected:
                    await self._run_client_tasks()
                    for client in self.web_clients:
                        await self.send_to_web(client, {"type": "connection", "status": "connected"})
                else:
                    for client in self.web_clients:
                        await self.send_to_web(client, {"type": "connection", "status": "disconnected"})
            else:
                logger.info("Already connected to LLM server")
                for client in self.web_clients:
                    await self.send_to_web(client, {"type": "connection", "status": "connected"})
                
    async def send_to_web(self, websocket, data):
        try:
            await websocket.send(json.dumps(data))
        except Exception:
            pass

    def launch_camera_window(self):
        import subprocess
        import os
        import sys
        
        client_dir = os.path.dirname(os.path.dirname(__file__))
        camera_script = os.path.join(client_dir, "handler", "camera_window.py")
        self.camera_process = subprocess.Popen(
            [sys.executable, camera_script],
            cwd=os.path.dirname(camera_script)
        )
        logger.info("📷 Camera window launched")
        
    async def stop_camera_window(self):
        if self.camera_process:
            self.camera_process.terminate()
            self.camera_process = None
            logger.info("📷 Camera window closed")

    def _start_frame_server(self):
        self.frame_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.frame_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.frame_server_socket.bind(('localhost', 8769))
        self.frame_server_socket.listen(5)
        self.frame_server_socket.setblocking(False)
        
        asyncio.create_task(self._frame_server_loop())
        logger.info("📷 Frame server started on port 8769")
        
    async def _frame_server_loop(self):
        import select
        import cv2
        import numpy as np
        
        frame_count = 0
        last_faces = []
        
        try:
            while self.client.running:
                try:
                    readable, _, _ = select.select([self.frame_server_socket], [], [], 0.001)
                    if readable:
                        client_sock, addr = self.frame_server_socket.accept()
                        client_sock.setblocking(False)
                        self.frame_clients.append(client_sock)
                        logger.info("📷 Frame client connected")
                except (OSError, SystemExit):
                    break
                except Exception:
                    pass
                
                if self.cam_enabled and self.frame_clients:
                    try:
                        frame_data = self.client.recorder.get_latest_frame()
                        if frame_data:
                            frame_count += 1
                            
                            nparr = np.frombuffer(frame_data, np.uint8)
                            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            
                            if frame is not None:
                                if frame_count % 5 == 0 and self.client.identity_manager.is_face_detection_available():
                                    try:
                                        faces = self.client.identity_manager.face_detector.detect_faces(frame)
                                        last_faces = []
                                        for face in faces:
                                            embedding = face.get("embedding")
                                            if embedding is not None:
                                                matched_id = self.client.identity_manager.identity_store.find_identity(embedding)
                                                face["identity_id"] = matched_id if matched_id else "unknown"
                                            else:
                                                face["identity_id"] = "unknown"
                                            last_faces.append(face)
                                    except Exception:
                                        last_faces = []
                                
                                if last_faces:
                                    for face in last_faces:
                                        bbox = face.get("bbox", [])
                                        if len(bbox) >= 4:
                                            x, y, x2, y2 = [int(v) for v in bbox[:4]]
                                            
                                            identity_id = face.get("identity_id", "?")
                                            short_id = identity_id[-8:] if len(identity_id) > 8 else identity_id
                                            score = face.get("det_score", 0.0)
                                            label = f"{short_id} {score:.0%}"
                                            
                                            color = (76, 175, 80)
                                            cv2.rectangle(frame, (x, y), (x2, y2), color, 2)
                                            
                                            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                                            cv2.rectangle(frame, (x, y - th - 10), (x + tw + 10, y), color, -1)
                                            cv2.putText(frame, label, (x + 5, y - 5), 
                                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                                
                                _, processed_data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                                frame_bytes = processed_data.tobytes()
                                
                                size = len(frame_bytes)
                                header = struct.pack('>I', size)
                                
                                dead_clients = []
                                for client in self.frame_clients:
                                    try:
                                        client.sendall(header + frame_bytes)
                                    except Exception:
                                        dead_clients.append(client)
                                
                                for client in dead_clients:
                                    self.frame_clients.remove(client)
                                    try:
                                        client.close()
                                    except:
                                        pass
                    except Exception:
                        pass
                
                await asyncio.sleep(0.016)
        except SystemExit:
            pass
