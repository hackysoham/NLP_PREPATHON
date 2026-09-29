from typing import Dict, Any, List
from datetime import datetime
from ..utils.models import Event, MemoryItem

class CustomerStateBoard:
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        
        # 1. Working Memory (session-scoped)
        self.working_memory: Dict[str, Any] = {}
        
        # 2. Episodic Memory (per-customer history)
        self.episodic_memory: List[MemoryItem] = []
        
        # 3. Persistent life-event inferences
        self.life_events: Dict[str, Any] = {}
        
        # Streaming features
        self.features: Dict[str, Any] = {}
        
        # Specialist Findings
        self.specialist_findings: Dict[str, Any] = {}
        
        self.last_update: datetime = None

    def update_feature(self, key: str, value: Any):
        self.features[key] = value

    def add_episodic_memory(self, item: MemoryItem):
        self.episodic_memory.append(item)

    def add_specialist_finding(self, agent_name: str, finding: Any):
        self.specialist_findings[agent_name] = finding

    def get_state_snapshot(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "features": self.features.copy(),
            "life_events": self.life_events.copy(),
            "specialist_findings": self.specialist_findings.copy()
        }
