import json
from typing import Dict, Any, List

class LLMProvider:
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode

    def generate(self, prompt: str, schema: Any = None) -> Dict[str, Any]:
        if self.mock_mode:
            # Deterministic mock fallback
            return self._mock_generate(prompt)
        else:
            raise NotImplementedError("Real LLM mode requires an API key configuration.")

    def _mock_generate(self, prompt: str) -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        if "retention vs upsell" in prompt_lower:
            return {"decision": "retention", "reasoning": "Mock debate resolved to retention"}
        if "life-event" in prompt_lower:
            if "hospital" in prompt_lower or "medical" in prompt_lower:
                return {"inferred_state": "medical_hardship", "confidence": "high"}
            if "baby" in prompt_lower or "child" in prompt_lower:
                return {"inferred_state": "new_child_life_event", "confidence": "high"}
            return {"inferred_state": "no_significant_event", "confidence": "medium"}
        
        return {"output": "mock_response"}
