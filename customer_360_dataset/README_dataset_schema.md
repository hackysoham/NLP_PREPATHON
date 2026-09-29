# Customer 360 Dataset Schema & Guidelines

Welcome to the Customer 360 Agentic Evaluation Dataset. This package provides synthetic, realistic financial event timelines used to evaluate systems that monitor banking activity to infer life events and recommend appropriate interventions.

## 📂 Package Structure

When you receive a scenario, it will contain the following files:

- `entities.json`: Master data detailing the customer's profile, demographic information, and their associated accounts.
- `history_seed.jsonl`: A pre-loaded backstory of historical events (in JSON Lines format). This provides a realistic baseline of the customer's ordinary activity over a span of months prior to the live evaluation.
- `live_stream.jsonl`: The primary event timeline to be consumed by your system. This contains the "live" story your agent must interpret.
- `replay_config.json`: Configuration settings outlining the pacing and time boundaries for replaying the live stream.
- `instructions.md`: Specific instructions or caveats for the given scenario.

---

## 🧾 Event Schema

Events in both `history_seed.jsonl` and `live_stream.jsonl` share a common JSON schema. Each line in these files represents a single JSON object.

### Common Envelope
```json
{
  "event_id": "EVT_000173",
  "event_time": "2026-03-14T09:12:03Z",
  "ingestion_time": "2026-03-14T09:12:07Z",
  "customer_id": "CUST_00042",
  "account_id": "ACC_CHK_001",
  "source_system": "card_payments",
  "event_type": "card_transaction",
  "schema_version": "1.0",
  "payload": {}
}
```
- **`event_id`**: A unique identifier for the event.
- **`event_time`**: The simulated time the event actually occurred. *Note: You should evaluate events based on this timestamp.*
- **`ingestion_time`**: When the event was received by the system. Some events may arrive late or out-of-order to simulate real-world streaming conditions.
- **`account_id`**: The associated account (may be `null` for customer-level events like a support call).
- **`source_system`**: The domain of the event (see payload shapes below).
- **`payload`**: An object containing domain-specific fields.

### Payload Shapes by Source System

Depending on the `source_system` and `event_type`, the `payload` object will contain different fields:

| `source_system` | Event Types | Key Payload Fields |
|---|---|---|
| **`card_payments`** | `purchase`, `refund`, `decline` | `merchant_name`, `mcc_category`, `amount`, `currency`, `is_international`, `card_present`, `decline_reason` |
| **`instant_payments` / `ach_wire`** | `inbound_transfer`, `outbound_transfer` | `direction`, `amount`, `currency`, `counterparty_name`, `counterparty_country`, `transfer_type`, `status` |
| **`core_banking_ledger`** | `deposit`, `withdrawal`, `standing_instruction`, `fee`, `interest_credit` | `amount`, `balance_after`, `transaction_type` |
| **`trading_brokerage`** | `buy`, `sell`, `dividend`, `deposit_to_brokerage` | `instrument_type`, `risk_category`, `amount`, `portfolio_value_after` |
| **`loan_kyc`** | `loan_application`, `loan_disbursed`, `kyc_update`, `address_change`, `marital_status_change`, `dependents_change` | `event_subtype`, `old_value`, `new_value` |
| **`web_app_events`** | `login`, `search_query`, `feature_used`, `session_duration` | `feature_or_page`, `search_text`, `device_type`, `session_length_sec` |
| **`support_logs`** | `ticket_created`, `ticket_resolved`, `call_transcript` | `channel`, `category`, `raw_text`, `resolution_status` |
| **`social_signal_consented`** | `life_event_mention` | `platform`, `raw_text`, `consent_flag` |

---

## 🎯 Reporting Final Answers

Your agentic system is expected to output its findings at various time checkpoints as it processes the `live_stream.jsonl`. 

You must report the state and action your system infers using **strictly these fixed enum values**. Do not invent or derive custom labels for these fields.

### Allowed Enums

**1. `inferred_state`** (What is happening to the customer?):
- `no_significant_event`
- `new_child_life_event`
- `marriage_or_relationship_change`
- `job_change_or_promotion`
- `job_loss_or_income_disruption`
- `medical_hardship`
- `financial_distress_general`
- `relocation`
- `retirement_transition`
- `wealth_growth_or_windfall`
- `potential_fraud_or_takeover`
- `elder_vulnerability_or_scam_risk`
- `churn_risk`
- `small_business_cashflow_event`
- or others if very unique scenario

**2. `action`** (What intervention should be taken?):
- `no_action`
- `proactive_retention_outreach`
- `relationship_manager_escalation`
- `personalized_offer`
- `support_intervention`
- `compliance_fraud_hold`

**3. `hitl_status`** (Human-in-the-loop routing):
- `auto_approved`
- `escalated`
- `human_approved`
- `human_rejected`
- `human_modified`

**4. `confidence_band`**:
- `low`
- `medium`
- `high`

### Expected Output Format

Your system should generate a JSON array of `checkpoints` representing its assessment at given points in time. 

If your system wants to provide narrative-specific nuances, use the free-text `action_subtype` or `notes` fields. Do not modify the core enums.

```json
[
  {
    "as_of_time": "2026-02-20T00:00:00Z",
    "inferred_state": "new_child_life_event",
    "confidence_band": "medium",
    "action": "no_action",
    "action_subtype": null,
    "hitl_status": "auto_approved",
    "notes": "Signal detected in recent grocery and pharmacy spend, but not yet strong enough to trigger an intervention."
  },
  {
    "as_of_time": "2026-03-10T00:00:00Z",
    "inferred_state": "new_child_life_event",
    "confidence_band": "high",
    "action": "personalized_offer",
    "action_subtype": "childcare_savings_or_insurance_offer",
    "hitl_status": "escalated",
    "notes": "Dependents change in KYC combined with sustained healthcare spend justifies an offer. Routed to HITL due to offer value thresholds."
  }
]
```

### Evaluation Criteria

Your outputs will be evaluated against a hidden `ground_truth.json` file on the backend. You will be scored on:
1. **Accuracy of Inference**: Correctly identifying the `inferred_state` and filtering out red herrings / false positives.
2. **Timeliness**: Reaching a high `confidence_band` at the correct moment (not too early on weak signals, not too late).
3. **Appropriate Action**: Selecting the correct bounded `action` and routing logic (`hitl_status`).
