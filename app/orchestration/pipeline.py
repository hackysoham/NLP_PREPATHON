from typing import List, Dict, Any
from ..utils.models import Event, Checkpoint
from ..utils.llm import LLMProvider
from ..state.board import CustomerStateBoard
from ..guardrails.hard_stops import Guardrail
from ..agents.specialists import UsageAgent, SupportAgent, TransactionAgent, KYCAgent, LifeEventInferenceAgent
from .pipeline_utils import EligibilityGate, ActionComposer, CritiqueRefiner, Router

class Pipeline:
    def __init__(self, llm_provider: LLMProvider):
        self.guardrail = Guardrail()
        self.usage_agent = UsageAgent()
        self.support_agent = SupportAgent()
        self.tx_agent = TransactionAgent()
        self.kyc_agent = KYCAgent()
        self.life_event_agent = LifeEventInferenceAgent(llm_provider)
        
        self.eligibility = EligibilityGate()
        self.composer = ActionComposer()
        self.critique = CritiqueRefiner()
        self.router = Router()
        
        self.boards: Dict[str, CustomerStateBoard] = {}

    def get_board(self, customer_id: str) -> CustomerStateBoard:
        if customer_id not in self.boards:
            self.boards[customer_id] = CustomerStateBoard(customer_id)
        return self.boards[customer_id]

    def process_event(self, event: Event) -> Dict[str, Any]:
        board = self.get_board(event.customer_id)
        
        # 1. Hard Guardrail
        halt_reason = self.guardrail.check_event(event)
        if halt_reason:
            return {
                "checkpoint": Checkpoint(
                    as_of_time=event.event_time.isoformat(),
                    inferred_state="potential_fraud_or_takeover",
                    confidence_band="high",
                    action="compliance_fraud_hold",
                    hitl_status="escalated",
                    notes=f"Hard guardrail triggered: {halt_reason}"
                ),
                "trace": {"decision": "halted_by_guardrail", "reason": halt_reason}
            }
            
        # 2. Ingestion (Swarm)
        self.usage_agent.process_event(event, board)
        self.support_agent.process_event(event, board)
        self.tx_agent.process_event(event, board)
        self.kyc_agent.process_event(event, board)
        
        # 3. Life Event Inference
        inference = self.life_event_agent.infer(board)
        inferred_state = inference.get("inferred_state", "no_significant_event")
        confidence = inference.get("confidence", "medium")
        
        # 4. Deliberation / Arbitration (Mock logic for Retention vs Upsell)
        candidate_action = "no_action"
        if inferred_state != "no_significant_event":
            if "distress" in inferred_state or "loss" in inferred_state:
                candidate_action = "support_intervention"
            elif "child" in inferred_state or "marriage" in inferred_state:
                candidate_action = "personalized_offer"
            else:
                candidate_action = "proactive_retention_outreach"
                
        # 5. Eligibility Gate
        is_eligible = self.eligibility.check_eligibility(candidate_action, board)
        if not is_eligible:
            candidate_action = "no_action"
            
        # 6. Action Composer & Critique
        draft = self.composer.compose(candidate_action, board)
        passed, critique_msg = self.critique.evaluate(draft)
        
        if not passed:
            # Rejection logic (store reflection in a real impl, default to no_action for simplicity here)
            candidate_action = "no_action"
            
        # 7. Routing (HITL Gateway)
        hitl = self.router.route(candidate_action, confidence, draft.get("cost_estimate", 0))
        
        checkpoint = Checkpoint(
            as_of_time=event.event_time.isoformat(),
            inferred_state=inferred_state,
            confidence_band=confidence,
            action=candidate_action,
            hitl_status=hitl,
            notes=f"Processed via pipeline. Critique: {critique_msg}"
        )
        
        # Update board timestamp
        board.last_update = event.event_time
        
        return {
            "checkpoint": checkpoint,
            "trace": {
                "customer_id": event.customer_id,
                "trigger_event_id": event.event_id,
                "decision": candidate_action
            }
        }
