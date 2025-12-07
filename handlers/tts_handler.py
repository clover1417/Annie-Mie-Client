import asyncio
import re
from utils.logger import logger


class TTSHandler:

    def __init__(self):
        self.is_speaking = False
        self.sentence_buffer = ""
        self.chunk_count = 0
        self._speak_queue = asyncio.Queue()
        self._speaker_task = None

    async def start(self):
        self._speaker_task = asyncio.create_task(self._speaker_loop())

    async def stop(self):
        if self._speaker_task:
            self._speaker_task.cancel()
            try:
                await self._speaker_task
            except asyncio.CancelledError:
                pass

    async def _speaker_loop(self):
        while True:
            try:
                sentence = await self._speak_queue.get()
                if sentence:
                    self.is_speaking = True
                    self.chunk_count += 1
                    logger.info(f"🔊 Chunk {self.chunk_count}: {sentence}")
                    await self._synthesize_and_play(sentence)
                    self.is_speaking = False
                    self._speak_queue.task_done()
            except asyncio.CancelledError:
                break

    def feed_text(self, text: str):
        self.sentence_buffer += text
        
        sentences = re.split(r'(?<=[.!?])(?!\.)\s+', self.sentence_buffer)
        
        if len(sentences) > 1:
            for sentence in sentences[:-1]:
                sentence = sentence.strip()
                if sentence:
                    asyncio.create_task(self._speak_queue.put(sentence))
            
            self.sentence_buffer = sentences[-1]

    async def flush(self):
        if self.sentence_buffer.strip():
            await self._speak_queue.put(self.sentence_buffer.strip())
            self.sentence_buffer = ""
        
        await self._speak_queue.join()
        
        if self.chunk_count > 0:
            logger.success("TTS completed")
        self.chunk_count = 0

    async def _synthesize_and_play(self, text: str):
        await asyncio.sleep(len(text) * 0.05)

    def reset(self):
        self.sentence_buffer = ""
        self.chunk_count = 0

    def is_currently_speaking(self) -> bool:
        return self.is_speaking
