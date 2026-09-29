from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class InferredState(str, Enum):
    no_significant_event = "no_significant_event"
    new_child_life_event = "new_child_life_event"
    marriage_or_relationship_change = "marriage_or_relationship_change"
    job_change_or_promotion = "job_change_or_promotion"
    job_loss_or_income_disruption = "job_loss_or_income_disruption"
    medical_hardship = "medical_hardship"
    financial_distress_general = "financial_distress_general"
    relocation = "relocation"
    retirement_transition = "retirement_transition"
    wealth_growth_or_windfall = "wealth_growth_or_windfall"
    potential_fraud_or_takeover = "potential_fraud_or_takeover"
    elder_vulnerability_or_scam_risk = "elder_vulnerability_or_scam_risk"
    churn_risk = "churn_risk"
    small_business_cashflow_event = "small_business_cashflow_event"

class Action(str, Enum):
    no_action = "no_action"
    proactive_retention_outreach = "proactive_retention_outreach"
    relationship_manager_escalation = "relationship_manager_escalation"
    personalized_offer = "personalized_offer"
    support_intervention = "support_intervention"
    compliance_fraud_hold = "compliance_fraud_hold"

class HitlStatus(str, Enum):
    auto_approved = "auto_approved"
    escalated = "escalated"
    human_approved = "human_approved"
    human_rejected = "human_rejected"
    human_modified = "human_modified"

class ConfidenceBand(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Event(BaseModel):
    event_id: str
    event_time: datetime
    ingestion_time: datetime
    customer_id: str
    account_id: Optional[str] = None
    source_system: str
    event_type: str
    schema_version: str = "1.0"
    payload: Dict[str, Any]

class Checkpoint(BaseModel):
    as_of_time: str
    inferred_state: str
    confidence_band: str
    action: str
    action_subtype: Optional[str] = None
    hitl_status: str
    notes: Optional[str] = None

class MemoryItem(BaseModel):
    memory_id: str
    timestamp: datetime
    content: str
    importance: float
    relevance_tags: List[str]
    source: str

class DecisionTrace(BaseModel):
    customer_id: str
    checkpoint: str
    trigger_event_id: str
    state_before: Dict[str, Any]
    state_after: Dict[str, Any]
    new_evidence: List[Any]
    feature_deltas: Dict[str, Any]
    decision: Dict[str, Any]
