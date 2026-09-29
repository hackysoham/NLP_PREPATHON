import re
from typing import Optional
from ..utils.models import Event

class Guardrail:
    def __init__(self):
        # Basic hard-stop rules
        self.legal_fraud_patterns = [
            r"(?i)\blawsuit\b",
            r"(?i)\battorney\b",
            r"(?i)\blegal action\b",
            r"(?i)\bfraud\b",
            r"(?i)\bscam\b",
            r"(?i)\bhacked\b",
            r"(?i)\bstolen\b",
        ]

    def check_event(self, event: Event) -> Optional[str]:
        # Fast path deterministic regex/keyword match
        payload_str = str(event.payload)
        for pattern in self.legal_fraud_patterns:
            if re.search(pattern, payload_str):
                return "HALT_LEGAL_FRAUD_ESCALATION"
        return None
