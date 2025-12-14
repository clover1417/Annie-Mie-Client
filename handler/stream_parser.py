from typing import Callable, Optional, List, Dict
from enum import Enum


class ParserState(Enum):
    NORMAL = 0
    IN_TAG = 1
    IN_THINK = 2
    MAYBE_MARKER = 3
    IN_FUNCTION_CALL = 4


class StreamParser:
    
    def __init__(self):
        self.state = ParserState.NORMAL
        self.tag_buffer = ""
        self.think_buffer = ""
        self.function_buffer = ""
        self.marker_buffer = ""
        self.parsed_tags: List[Dict] = []
        self.parsed_functions: List[str] = []
        self.clean_text = ""
        
        self.on_text: Optional[Callable[[str], None]] = None
        self.on_tag: Optional[Callable[[Dict], None]] = None
        self.on_think_start: Optional[Callable[[], None]] = None
        self.on_think_end: Optional[Callable[[str], None]] = None
        self.on_function_call: Optional[Callable[[str], None]] = None

    def reset(self):
        self.state = ParserState.NORMAL
        self.tag_buffer = ""
        self.think_buffer = ""
        self.function_buffer = ""
        self.marker_buffer = ""
        self.parsed_tags = []
        self.parsed_functions = []
        self.clean_text = ""

    def feed(self, token: str):
        for char in token:
            self._process_char(char)

    def _process_char(self, char: str):
        if self.state == ParserState.IN_THINK:
            self._handle_in_think(char)
        elif self.state == ParserState.IN_TAG:
            self._handle_in_tag(char)
        elif self.state == ParserState.MAYBE_MARKER:
            self._handle_maybe_marker(char)
        elif self.state == ParserState.IN_FUNCTION_CALL:
            self._handle_in_function(char)
        else:
            self._handle_normal(char)

    def _handle_normal(self, char: str):
        if char == "|":
            self.state = ParserState.IN_TAG
            self.tag_buffer = ""
        elif char == "<":
            self.marker_buffer = "<"
            self.state = ParserState.MAYBE_MARKER
        else:
            self._emit_text(char)

    def _handle_in_tag(self, char: str):
        if char == "|":
            self._parse_and_emit_tag(self.tag_buffer)
            self.tag_buffer = ""
            self.state = ParserState.NORMAL
        else:
            self.tag_buffer += char

    def _handle_maybe_marker(self, char: str):
        self.marker_buffer += char
        
        if self.marker_buffer == "<think>":
            self.state = ParserState.IN_THINK
            self.think_buffer = ""
            self.marker_buffer = ""
            if self.on_think_start:
                self.on_think_start()
        elif self.marker_buffer == "<function_call>":
            self.state = ParserState.IN_FUNCTION_CALL
            self.function_buffer = ""
            self.marker_buffer = ""
        elif not ("<think>".startswith(self.marker_buffer) or "<function_call>".startswith(self.marker_buffer)):
            for c in self.marker_buffer:
                self._emit_text(c)
            self.marker_buffer = ""
            self.state = ParserState.NORMAL

    def _handle_in_think(self, char: str):
        self.think_buffer += char
        
        if self.think_buffer.endswith("</think>"):
            content = self.think_buffer[:-8]
            self.think_buffer = ""
            self.state = ParserState.NORMAL
            if self.on_think_end:
                self.on_think_end(content)

    def _handle_in_function(self, char: str):
        self.function_buffer += char
        
        if self.function_buffer.endswith("</function_call>"):
            content = self.function_buffer[:-16]
            self.function_buffer = ""
            self.state = ParserState.NORMAL
            self.parsed_functions.append(content)
            if self.on_function_call:
                self.on_function_call(content)

    def _emit_text(self, text: str):
        self.clean_text += text
        if self.on_text:
            self.on_text(text)

    def _parse_and_emit_tag(self, content: str):
        tag = None
        
        content = content.replace('\\"', '"')
        
        if content.startswith('emotion="') and content.endswith('"'):
            value = content[9:-1]
            tag = {"type": "emotion", "value": value}
        
        elif content.startswith('animate="'):
            if ':OnDelay(' in content:
                parts = content.split(':OnDelay(')
                value = parts[0][9:-1]
                delay_str = parts[1].rstrip(')"')
                try:
                    delay = float(delay_str)
                    tag = {"type": "animate", "value": value, "delay": delay}
                except ValueError:
                    tag = {"type": "animate", "value": value}
            elif content.endswith('"'):
                value = content[9:-1]
                tag = {"type": "animate", "value": value}

        if tag:
            tag["position"] = len(self.clean_text)
            self.parsed_tags.append(tag)
            if self.on_tag:
                self.on_tag(tag)

    def finish(self):
        if self.state == ParserState.MAYBE_MARKER and self.marker_buffer:
            for c in self.marker_buffer:
                self._emit_text(c)
            self.marker_buffer = ""
        
        return {
            "text": self.clean_text,
            "tags": self.parsed_tags,
            "function_calls": self.parsed_functions
        }

    def get_result(self) -> Dict:
        return {
            "text": self.clean_text,
            "tags": self.parsed_tags,
            "function_calls": self.parsed_functions
        }
