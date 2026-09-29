from typing import Dict, Any, Tuple
from ..state.board import CustomerStateBoard

class EligibilityGate:
    def check_eligibility(self, candidate_action: str, board: CustomerStateBoard) -> bool:
        # Simple mock rules engine for eligibility
        if candidate_action == "personalized_offer":
            if board.features.get("total_spend", 0) < 100:
                return False
        return True

class ActionComposer:
    def compose(self, action_type: str, board: CustomerStateBoard) -> Dict[str, Any]:
        return {
            "type": action_type,
            "draft": f"Drafting action: {action_type} for customer {board.customer_id}",
            "cost_estimate": 50 if action_type == "personalized_offer" else 10
        }

class CritiqueRefiner:
    def evaluate(self, draft: Dict[str, Any]) -> Tuple[bool, str]:
        # Mock critique logic
        if draft["cost_estimate"] > 100:
            return False, "Cost too high"
        return True, "Passes rubric"

class Router:
    def route(self, action_type: str, confidence: str, cost: int) -> str:
        if confidence == "low" or cost > 40:
            return "escalated"
        return "auto_approved"
