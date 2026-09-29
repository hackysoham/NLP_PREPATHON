import json
from typing import List
from ..ingestion.loader import StreamLoader
from ..utils.llm import LLMProvider
from ..orchestration.pipeline import Pipeline

class ReplayEngine:
    def __init__(self, history_path: str, live_path: str, config_path: str = None):
        self.loader = StreamLoader(history_path, live_path)
        self.llm = LLMProvider(mock_mode=True)
        self.pipeline = Pipeline(self.llm)
        self.checkpoints = []
        self.traces = []

    def run(self):
        events = self.loader.get_all_events_sorted()
        for evt in events:
            result = self.pipeline.process_event(evt)
            if result:
                self.checkpoints.append(result["checkpoint"].model_dump())
                self.traces.append(result["trace"])

    def export_results(self, output_file: str):
        with open(output_file, 'w') as f:
            json.dump(self.checkpoints, f, indent=2)

    def export_traces(self, output_file: str):
        with open(output_file, 'w') as f:
            json.dump(self.traces, f, indent=2)
