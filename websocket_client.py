import asyncio
import websockets
import json
import os
import sys
import base64
import wave
from pathlib import Path
import cv2
import numpy as np

import config
from config import MessageType, StatusType, StatsType
from utils.logger import logger
from core import SpeechDetector, StreamParser
from handlers import TTSHandler
from identity import IdentityManager

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from recorder import NativeRecorder


class AnnieMieClient:
    def __init__(self, server_uri=None):
        self.server_uri = server_uri or config.SERVER_URI
        self.websocket = None
        self.recorder = None
        self.speech_detector = SpeechDetector()
        self.stream_parser = StreamParser()
        self.tts_handler = TTSHandler()
        self.identity_manager = IdentityManager()
        self.running = False
        self.is_llm_busy = False
        self.current_identity = None
        self.is_thinking = False
        self._pending_stats = None

    async def connect(self):
        logger.info(f"Connecting to server: {self.server_uri}")

        try:
            self.websocket = await websockets.connect(
                self.server_uri,
                max_size=10 * 1024 * 1024,
                ping_interval=20,
                ping_timeout=60,
            )
            logger.success("Connected to server!")
            return True

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    def initialize_components(self):
        logger.info("Initializing Speech Detector...")
        self.speech_detector.initialize()

        logger.info("Initializing Identity Manager...")
        self.identity_manager.initialize()

        logger.info("Initializing Native Recorder...")
        recorder_config = config.get_recorder_config()
        self.recorder = NativeRecorder(recorder_config)

        self._setup_stream_parser()

        logger.success("All components initialized!")

    def _setup_stream_parser(self):
        def on_text(text):
            if not self.is_thinking:
                self.tts_handler.feed_text(text)

        def on_tag(tag):
            tag_type = tag.get("type")
            value = tag.get("value")
            delay = tag.get("delay")
            
            if tag_type == "emotion":
                logger.info(f"[Emotion: {value}]")
            elif tag_type == "animate":
                delay_str = f" delay={delay}s" if delay else ""
                logger.info(f"[Animate: {value}{delay_str}]")

        def on_think_start():
            self.is_thinking = True

        def on_think_end(content):
            self.is_thinking = False

        def on_function_call(content):
            logger.info(f"[Function: {content[:60]}...]")

        self.stream_parser.on_text = on_text
        self.stream_parser.on_tag = on_tag
        self.stream_parser.on_think_start = on_think_start
        self.stream_parser.on_think_end = on_think_end
        self.stream_parser.on_function_call = on_function_call

    async def handle_server_messages(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == MessageType.STATUS:
                    status = data.get("status")
                    if status == StatusType.GENERATING:
                        self.is_llm_busy = True
                        self.is_thinking = False
                        self.stream_parser.reset()
                        self.tts_handler.reset()
                        self._set_llm_busy(True)
                    elif status == StatusType.DONE:
                        await self._handle_stream_complete()
                        self._set_llm_busy(False)

                elif msg_type == MessageType.TEXT:
                    text = data.get("text", "")
                    if text:
                        self.stream_parser.feed(text)

                elif msg_type == "identity":
                    self._handle_identity_message(data)

                elif msg_type == MessageType.STATS:
                    stat = data.get("stat")
                    if stat == StatsType.FIRST_TOKEN:
                        time_val = data.get("time")
                        logger.info(f"First token: {time_val:.2f}s")
                    elif stat == StatsType.COMPLETE:
                        tokens = data.get("tokens")
                        time_val = data.get("time")
                        tok_per_sec = data.get("tok_per_sec")
                        self._pending_stats = f"Generated {tokens} tokens in {time_val:.2f}s ({tok_per_sec:.2f} tok/s)"

                elif msg_type == MessageType.ERROR:
                    error = data.get("error")
                    logger.error(f"Server error: {error}")
                    self.is_llm_busy = False

                elif msg_type == MessageType.PONG:
                    pass

        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection to server closed")

    def _handle_identity_message(self, data):
        identity_ids = data.get("identity_ids", [])
        profiles = data.get("profiles", [])
        
        self.current_identity = {
            "identity_ids": identity_ids,
            "profiles": profiles
        }
        
        for profile in profiles:
            identity_id = profile.get("identity_id", "unknown")
            name = profile.get("name")
            is_first = profile.get("is_first_meeting", False)
            
            if is_first:
                logger.info(f"New user: {identity_id}")
            else:
                display_name = name or identity_id
                logger.success(f"Recognized: {display_name}")

    async def _handle_stream_complete(self):
        self.stream_parser.finish()
        await self.tts_handler.flush()
        
        if self._pending_stats:
            logger.info(self._pending_stats)
            self._pending_stats = None
        
        self.is_llm_busy = False
        self.tts_handler.reset()

    def _set_llm_busy(self, busy: bool):
        flag_file = config.LLM_BUSY_FLAG
        if busy:
            flag_file.touch()
        else:
            flag_file.unlink(missing_ok=True)

    def _is_llm_busy_flag(self) -> bool:
        return config.LLM_BUSY_FLAG.exists()

    def _get_audio_duration(self, audio_path: str) -> float:
        if audio_path.endswith(".wav"):
            try:
                with wave.open(audio_path, "rb") as wf:
                    return wf.getnframes() / float(wf.getframerate())
            except Exception:
                pass
        elif audio_path.endswith(".flac"):
            try:
                with open(audio_path, "rb") as f:
                    data = f.read()
                    sample_rate = config.RATE
                    samples = len(data) * 8 // 16
                    return samples / sample_rate * 0.5
            except Exception:
                pass
        return 3.0

    async def _process_and_send_message(self, audio_path: str):
        from datetime import datetime

        duration = self._get_audio_duration(audio_path)

        frames_bytes = self.recorder.get_frames_for_duration(duration + 0.5)
        latest_frame = self.recorder.get_latest_frame()

        frame_for_identity = frames_bytes[-1] if frames_bytes else latest_frame

        decoded_frame = None
        if frame_for_identity:
            jpeg_array = np.frombuffer(frame_for_identity, dtype=np.uint8)
            decoded_frame = cv2.imdecode(jpeg_array, cv2.IMREAD_COLOR)

        identity_result = self.identity_manager.identify_speaker(decoded_frame)

        with open(audio_path, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")

        session_name = datetime.now().strftime("%d_%m_%y_%H%M%S")
        audio_format = self.recorder.get_audio_format()

        message = {
            "type": MessageType.AUDIO,
            "audio_base64": audio_base64,
            "audio_format": audio_format,
            "session_name": session_name,
            "identity_ids": identity_result["detected_ids"],
        }

        if identity_result["detected_ids"]:
            logger.info(f"Detected identities: {identity_result['detected_ids']}")
        
        if identity_result["new_ids"]:
            message["new_identity_ids"] = identity_result["new_ids"]
            logger.info(f"New identities created: {identity_result['new_ids']}")

        if frames_bytes:
            encoded_frames = [
                base64.b64encode(frame).decode("utf-8") for frame in frames_bytes
            ]
            message["video_frames"] = encoded_frames
            logger.info(
                f"{len(frames_bytes)} video frames captured ({duration:.1f}s @ {config.VIDEO_FPS} FPS)"
            )
        elif latest_frame:
            encoded_frame = base64.b64encode(latest_frame).decode("utf-8")
            message["video_frames"] = [encoded_frame]
            logger.warning("Only 1 frame available")
        else:
            logger.warning("No frames available")

        await self.websocket.send(json.dumps(message))
        logger.success("Message sent to server")

        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.info("Cleaned up recording")
            except Exception as e:
                logger.warning(f"Could not delete audio file: {e}")

    async def process_audio_events(self):
        logger.info("Starting audio recorder...")
        self.recorder.start()
        logger.success("Recorder started! Speak to interact with Mie.\n")

        while self.running:
            if self._is_llm_busy_flag():
                filepath = self.recorder.read_speech_event()
                if filepath and os.path.exists(filepath):
                    os.remove(filepath)
                await asyncio.sleep(0.1)
                continue

            filepath = self.recorder.read_speech_event()

            if filepath:
                logger.info(f"Processing: {os.path.basename(filepath)}")

                try:
                    is_speech = self.speech_detector.is_speech(filepath)

                    if not is_speech:
                        logger.info("No speech detected (Silero verification)")
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        print()
                        continue

                    logger.success("Speech detected - processing identity...")

                    await self._process_and_send_message(filepath)

                except Exception as e:
                    logger.error(f"Error processing audio: {e}")
                    if os.path.exists(filepath):
                        os.remove(filepath)

            await asyncio.sleep(0.1)

    async def start(self):
        logger.header("Annie Mie Client")

        self.initialize_components()

        if not await self.connect():
            logger.error("Could not connect to server. Is it running?")
            return

        await self.tts_handler.start()
        self.running = True

        try:
            await asyncio.gather(
                self.handle_server_messages(), self.process_audio_events()
            )

        except KeyboardInterrupt:
            logger.info("\nStopping client...")

        finally:
            await self.stop()

    async def stop(self):
        self.running = False
        self._set_llm_busy(False)

        await self.tts_handler.stop()

        if self.recorder:
            self.recorder.stop()
            logger.info("Recorder stopped")

        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from server")
