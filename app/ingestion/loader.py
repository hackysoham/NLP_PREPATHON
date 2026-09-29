import json
from typing import List
from ..utils.models import Event

def parse_jsonl(filepath: str) -> List[Event]:
    events = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    events.append(Event(**data))
                except Exception as e:
                    print(f"Error parsing line: {line.strip()} - {e}")
    return events

class StreamLoader:
    def __init__(self, history_path: str, live_path: str):
        self.history_events = parse_jsonl(history_path)
        self.live_events = parse_jsonl(live_path)

    def get_all_events_sorted(self) -> List[Event]:
        all_events = self.history_events + self.live_events
        # Sort by event_time to handle late/out-of-order events structurally
        all_events.sort(key=lambda x: x.event_time)
        return all_events
