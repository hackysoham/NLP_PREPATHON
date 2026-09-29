import unittest
from app.utils.models import Event
from app.utils.llm import LLMProvider
from app.orchestration.pipeline import Pipeline
from datetime import datetime

class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.llm = LLMProvider(mock_mode=True)
        self.pipeline = Pipeline(self.llm)

    def test_guardrail(self):
        evt = Event(
            event_id="t1", event_time=datetime.now(), ingestion_time=datetime.now(),
            customer_id="c1", source_system="support_logs", event_type="ticket_created",
            payload={"raw_text": "I will file a lawsuit for fraud"}
        )
        res = self.pipeline.process_event(evt)
        self.assertEqual(res["checkpoint"].action, "compliance_fraud_hold")
        self.assertEqual(res["checkpoint"].hitl_status, "escalated")

    def test_normal_ingestion(self):
        evt = Event(
            event_id="t2", event_time=datetime.now(), ingestion_time=datetime.now(),
            customer_id="c2", source_system="web_app_events", event_type="login",
            payload={"feature_or_page": "dashboard"}
        )
        res = self.pipeline.process_event(evt)
        self.assertNotEqual(res["checkpoint"].action, "compliance_fraud_hold")

if __name__ == '__main__':
    unittest.main()
