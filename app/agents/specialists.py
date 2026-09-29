from typing import Dict, Any
from ..state.board import CustomerStateBoard
from ..utils.models import Event

class BaseSpecialist:
    def __init__(self, name: str):
        self.name = name

    def process_event(self, event: Event, board: CustomerStateBoard):
        pass

class UsageAgent(BaseSpecialist):
    def __init__(self):
        super().__init__("UsageAgent")
    
    def process_event(self, event: Event, board: CustomerStateBoard):
        if event.source_system == "web_app_events":
            board.update_feature("last_login", event.event_time)

class SupportAgent(BaseSpecialist):
    def __init__(self):
        super().__init__("SupportAgent")
    
    def process_event(self, event: Event, board: CustomerStateBoard):
        if event.source_system == "support_logs":
            board.add_specialist_finding(self.name, {"recent_ticket": True, "details": event.payload})

class TransactionAgent(BaseSpecialist):
    def __init__(self):
        super().__init__("TransactionAgent")
    
    def process_event(self, event: Event, board: CustomerStateBoard):
        if event.source_system in ["card_payments", "instant_payments", "core_banking_ledger"]:
            amount = event.payload.get("amount", 0)
            current_total = board.features.get("total_spend", 0)
            board.update_feature("total_spend", current_total + amount)

class KYCAgent(BaseSpecialist):
    def __init__(self):
        super().__init__("KYCAgent")
    
    def process_event(self, event: Event, board: CustomerStateBoard):
        if event.source_system == "loan_kyc":
            board.add_specialist_finding(self.name, {"kyc_updated": True, "details": event.payload})

class LifeEventInferenceAgent:
    def __init__(self, llm):
        self.llm = llm

    def infer(self, board: CustomerStateBoard) -> Dict[str, Any]:
        # Agent-dependent trigger: checks swarm findings
        findings_count = len(board.specialist_findings)
        if findings_count >= 1: # simplified threshold for mock
            prompt = f"Analyze life-event from findings: {board.specialist_findings} and features {board.features}"
            result = self.llm.generate(prompt)
            board.life_events["current_inference"] = result
            return result
        return {"inferred_state": "no_significant_event", "confidence": "medium"}
