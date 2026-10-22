"""Offline Compass contract tests. No live Gemini/Qdrant requests are made.

From backend/: python -m unittest test_compass.py -v
"""

import unittest
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from api import compass as compass_api
from schemas.chat import ChatResponse, Source
from schemas.compass import CompassState, CompassTurnRequest
from services import compass_engine
from services.compass_engine import CompassDecision


class CompassContractTests(unittest.TestCase):
    def request(self, text="יש לי שאלה על ביטוח רכב", count=0):
        return CompassTurnRequest(
            message=text,
            state=CompassState(clarification_count=count),
        )

    def test_dynamic_question_and_choices(self):
        decision = CompassDecision(
            next_step="ask",
            question="מה חשוב לברר לגבי ביטוח הרכב?",
            choices=["כיסוי", "תהליך תביעה", "משהו אחר"],
            topic="ביטוח רכב",
            goal="בירור",
        )
        with (
            patch.object(compass_api, "ENABLE_EVIDENCE_VERIFICATION", True),
            patch.object(compass_api, "decide_next_turn", return_value=(
                decision, CompassState(topic="ביטוח רכב", asked_questions=[decision.question], clarification_count=1)
            )),
            patch.object(compass_api, "chat") as rag,
        ):
            response = compass_api.compass_turn(self.request())
        self.assertEqual(response.kind, "question")
        self.assertEqual(response.choices, decision.choices)
        rag.assert_not_called()

    def test_answer_must_use_verified_chat(self):
        decision = CompassDecision(next_step="answer", retrieval_query="מה כולל ביטוח רכב?")
        verified = ChatResponse(
            answer="תשובה שנבדקה לפי המקורות.",
            sources=[Source(title="ביטוח רכב", url="https://www.fnx.co.il/car-insurance/")],
        )
        with (
            patch.object(compass_api, "ENABLE_EVIDENCE_VERIFICATION", True),
            patch.object(compass_api, "decide_next_turn", return_value=(decision, CompassState())),
            patch.object(compass_api, "chat", return_value=verified) as rag,
        ):
            response = compass_api.compass_turn(self.request())
        self.assertEqual(response.kind, "answer")
        self.assertEqual(response.sources, verified.sources)
        self.assertEqual(rag.call_args[0][0].question, "מה כולל ביטוח רכב?")

    def test_empty_sources_fail_closed(self):
        decision = CompassDecision(next_step="answer", retrieval_query="מה מכסה?", topic="ביטוח")
        with (
            patch.object(compass_api, "ENABLE_EVIDENCE_VERIFICATION", True),
            patch.object(compass_api, "decide_next_turn", return_value=(decision, CompassState())),
            patch.object(compass_api, "chat", return_value=ChatResponse(
                answer="טענה לא מבוססת על כיסוי אישי", sources=[])),
        ):
            response = compass_api.compass_turn(self.request())
        self.assertEqual(response.kind, "insufficient_evidence")
        self.assertEqual(response.sources, [])
        self.assertNotIn("כיסוי אישי", response.message)

    def test_verification_off_prevents_rag_call(self):
        with (
            patch.object(compass_api, "ENABLE_EVIDENCE_VERIFICATION", False),
            patch.object(compass_api, "chat") as rag,
        ):
            with self.assertRaises(HTTPException) as raised:
                compass_api.compass_turn(self.request())
        self.assertEqual(raised.exception.status_code, 503)
        rag.assert_not_called()

    def test_empty_message_rejected(self):
        with patch.object(compass_api, "ENABLE_EVIDENCE_VERIFICATION", True):
            with self.assertRaises(HTTPException) as raised:
                compass_api.compass_turn(self.request("   "))
        self.assertEqual(raised.exception.status_code, 422)

    def test_input_length_bounded(self):
        with self.assertRaises(ValidationError):
            self.request("א" * 1201)


class NavigatorGuardrailTests(unittest.TestCase):
    def model_result(self, decision):
        class FakeModels:
            def generate_content(self, **_kwargs):
                class Result:
                    text = decision.model_dump_json()
                return Result()
        class FakeClient:
            models = FakeModels()
        return FakeClient()

    def test_repeated_question_forces_answer(self):
        q = "מה חשוב לברר לגבי ביטוח רכב?"
        data = CompassTurnRequest(
            message="משהו אחר",
            state=CompassState(asked_questions=[q], clarification_count=1),
        )
        d = CompassDecision(next_step="ask", question=q, choices=["כן"])
        with (
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-dummy-key"}),
            patch.object(compass_engine.genai, "Client", return_value=self.model_result(d)),
        ):
            result, state = compass_engine.decide_next_turn(data)
        self.assertEqual(result.next_step, "answer")
        self.assertTrue(result.retrieval_query)
        self.assertEqual(state.clarification_count, 1)

    def test_three_clarifications_forces_answer(self):
        data = CompassTurnRequest(message="לא בטוח", state=CompassState(clarification_count=3))
        d = CompassDecision(next_step="ask", question="עוד שאלה?", choices=["א", "ב"])
        with (
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-dummy-key"}),
            patch.object(compass_engine.genai, "Client", return_value=self.model_result(d)),
        ):
            result, state = compass_engine.decide_next_turn(data)
        self.assertEqual(result.next_step, "answer")
        self.assertEqual(state.clarification_count, 3)

    def test_unique_choices_and_state(self):
        data = CompassTurnRequest(message="עזרה")
        d = CompassDecision(
            next_step="ask", question="איזה נושא מעניין?",
            choices=["רכב", "רכב", "דירה", "אחר"], topic="ביטוח",
        )
        with (
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-dummy-key"}),
            patch.object(compass_engine.genai, "Client", return_value=self.model_result(d)),
        ):
            result, state = compass_engine.decide_next_turn(data)
        self.assertEqual(result.choices, ["רכב", "דירה", "אחר"])
        self.assertEqual(state.asked_questions, ["איזה נושא מעניין?"])
        self.assertEqual(state.topic, "ביטוח")


if __name__ == "__main__":
    unittest.main()
