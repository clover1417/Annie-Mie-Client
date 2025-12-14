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
        
        while True:
            buffer = self.sentence_buffer
            
            if len(buffer) < 2:
                break
            
            ELLIPSIS_PLACEHOLDER = '\x00\x00\x00'
            DECIMAL_PLACEHOLDER = '\x01'
            
            temp = buffer.replace('...', ELLIPSIS_PLACEHOLDER)
            temp = re.sub(r'(\d)\.(\d)', rf'\1{DECIMAL_PLACEHOLDER}\2', temp)
            
            best_match = None
            for match in re.finditer(r'[.!?。！？]', temp):
                pos = match.end()
                
                if pos < len(temp):
                    next_char = temp[pos]
                    if next_char in ' \n\t\r':
                        best_match = match
                        break
                else:
                    pass
            
            if not best_match:
                break
            
            end_pos = best_match.end()
            
            sentence = buffer[:end_pos].strip()
            self.sentence_buffer = buffer[end_pos:].lstrip()
            
            if sentence and len(sentence) > 1:
                asyncio.create_task(self._speak_queue.put(sentence))

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
