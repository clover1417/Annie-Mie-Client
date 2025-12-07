import re
from typing import List, Tuple, Dict
from utils.logger import logger


class TagParser:

    def __init__(self):
        self.emotion_pattern = re.compile(r'\|emotion="([^"]+)"\|')
        self.animate_pattern = re.compile(r'\|animate="([^"]+)"(?::OnDelay\((\d+(?:\.\d+)?)\))?\|')
        self.function_call_patterns = [
            re.compile(r'<function_call>\s*(\{.*?\})\s*</function_call>', re.DOTALL),
            re.compile(r'\[FUNCTION_CALL:\s*(\w+)\s*\((.*?)\)\]', re.DOTALL),
            re.compile(r'```function\s*\n(\{.*?\})\s*\n```', re.DOTALL),
        ]

    def parse(self, text: str) -> Tuple[str, List[Dict]]:
        clean_text = text
        tags = []
        offset = 0

        all_matches = []

        for match in self.emotion_pattern.finditer(text):
            all_matches.append({
                'type': 'emotion',
                'start': match.start(),
                'end': match.end(),
                'value': match.group(1),
                'delay': None,
                'match': match
            })

        for match in self.animate_pattern.finditer(text):
            all_matches.append({
                'type': 'animate',
                'start': match.start(),
                'end': match.end(),
                'value': match.group(1),
                'delay': float(match.group(2)) if match.group(2) else None,
                'match': match
            })

        all_matches.sort(key=lambda x: x['start'])

        for tag_info in all_matches:
            match = tag_info['match']
            position = match.start() - offset

            tag_data = {
                'type': tag_info['type'],
                'value': tag_info['value'],
                'position': position
            }

            if tag_info['delay'] is not None:
                tag_data['delay'] = tag_info['delay']

            tags.append(tag_data)

            clean_text = clean_text[:match.start() - offset] + clean_text[match.end() - offset:]
            offset += match.end() - match.start()

        return clean_text, tags

    def extract_function_calls(self, text: str) -> List[Dict]:
        function_calls = []
        
        for pattern in self.function_call_patterns:
            for match in pattern.finditer(text):
                function_calls.append({
                    'raw': match.group(0),
                    'content': match.group(1),
                    'start': match.start(),
                    'end': match.end()
                })
        
        return function_calls

    def has_function_calls(self, text: str) -> bool:
        for pattern in self.function_call_patterns:
            if pattern.search(text):
                return True
        return False

    def strip_function_calls(self, text: str) -> str:
        result = text
        for pattern in self.function_call_patterns:
            result = pattern.sub('', result)
        result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)
        return result.strip()

    def strip_tags(self, text: str) -> str:
        clean_text = self.emotion_pattern.sub('', text)
        clean_text = self.animate_pattern.sub('', clean_text)
        return clean_text

    def print_tags(self, tags: List[Dict], prefix: str = ""):
        if not tags:
            return

        logger.info(f"{prefix}Parsed tags:")
        for i, tag in enumerate(tags, 1):
            if tag['type'] == 'emotion':
                print(f"  [{i}] Emotion: {tag['value']} at position {tag['position']}")
            elif tag['type'] == 'animate':
                delay_str = f" (delay: {tag['delay']}s)" if 'delay' in tag else ""
                print(f"  [{i}] Animate: {tag['value']}{delay_str} at position {tag['position']}")

    def print_function_calls(self, text: str):
        calls = self.extract_function_calls(text)
        if not calls:
            return
        
        logger.info("Function calls detected:")
        for i, call in enumerate(calls, 1):
            print(f"  [{i}] {call['raw'][:80]}...")
