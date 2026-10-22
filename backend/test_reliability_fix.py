r"""Offline regression tests for the PhoenixRAG retrieval / repair pipeline.

Run from backend:
    .\.venv\Scripts\python.exe -m unittest test_reliability_fix.py
All external Gemini/Qdrant calls are patched out. No requests are sent.
"""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from api import chat as chat_module
from services import retrieval as retrieval_module
from services.evidence_verifier import VerificationResult
from services.generation import GeneratedAnswer


CAR_URL = "https://www.fnx.co.il/car-insurance/car_information/kinds-of-car-insurance/"
HOME_URL = "https://www.fnx.co.il/apartment-insurance/apartment-information/apartment-flood-costs/"


def item(cid, url, text, title="source"):
    return {"id": cid, "url": url, "text": text, "page_title": title}


class RetrievalEvidenceTests(unittest.TestCase):
    def test_coverage_question_does_not_select_safety_tips_over_coverage_proof(self):
        specialist = item(
            "specialist", "https://www.fnx.co.il/car-insurance/comprehensive/insure-my-tesla/",
            "הסוללה מכוסה בביטוח הייעודי לנזקי הצפה ושיטפון.", "InsureMyTesla",
        )
        car = item(
            "car", CAR_URL,
            "ביטוח מקיף לרכב מכסה נזקי מזג אוויר כתוצאה משיטפון.", "ביטוח רכב",
        )
        car_advice = item(
            "car-tip", "https://www.fnx.co.il/car-insurance/car_information/flood-tips/",
            "בעת שיטפון יש להימנע ממעבר בשלוליות עמוקות.", "טיפים בשיטפון",
        )
        home_advice = item(
            "home-tip", "https://www.fnx.co.il/apartment-insurance/apartment-information/flood-tips/",
            "בעת הצפה בבית יש לנתק את זרם החשמל הראשי.", "בטיחות בעת הצפה",
        )
        home = item(
            "home", HOME_URL,
            "ביטוח תכולת דירה כולל הרחבה לסיכוני מים והצפה פתאומית.", "כיסוי הצפות בדירה",
        )
        candidate_grades = [
            (1, 1, specialist["text"]),
            (2, 1, car["text"]),
            (3, 1, car_advice["text"]),
            (4, 2, home_advice["text"]),
            (5, 2, home["text"]),
        ]
        model_result = {"grades": [
            {"candidate_id": cid, "facet_id": fid, "relevance": 3,
             "evidence_quote": quote, "supports_issue": True}
            for cid, fid, quote in candidate_grades
        ]}
        fake_client = SimpleNamespace(models=SimpleNamespace(
            generate_content=lambda **kwargs: SimpleNamespace(
                text=json.dumps(model_result, ensure_ascii=False)
            ),
        ))
        facets = [
            retrieval_module.SearchFacet(
                search_query="כיסוי נזקי הצפה לרכב", key_terms=["הצפה"],
                alternate_terms=["שיטפון"], domain="car",
            ),
            retrieval_module.SearchFacet(
                search_query="כיסוי נזקי הצפה לדירה", key_terms=["הצפה"],
                domain="home",
            ),
        ]
        with patch.object(retrieval_module, "gemini_client", fake_client):
            result = retrieval_module.select_verified_evidence(
                "מה ההבדל בין כיסוי הצפה לרכב לבין כיסוי הצפה בדירה?",
                facets,
                [[specialist, car, car_advice], [home_advice, home]],
                limit=2,
            )
        self.assertEqual([c["id"] for c in result], ["car", "home"])

    def test_specific_vehicle_coverage_can_use_specialist_source(self):
        special = item(
            "battery", "https://www.fnx.co.il/car-insurance/comprehensive/insure-my-tesla/",
            "סוללת הרכב מכוסה בביטוח הייעודי מפני נזקי הצפה.",
        )
        fake_review = {"grades": [
            {"candidate_id": 1, "facet_id": 1, "relevance": 3,
             "evidence_quote": special["text"], "supports_issue": True},
        ]}
        fake_client = SimpleNamespace(models=SimpleNamespace(
            generate_content=lambda **kwargs: SimpleNamespace(
                text=json.dumps(fake_review, ensure_ascii=False)
            ),
        ))
        facet = retrieval_module.SearchFacet(
            search_query="כיסוי סוללת רכב חשמלי", key_terms=["סוללה"],
            alternate_terms=["סוללת"], domain="car",
        )
        with patch.object(retrieval_module, "gemini_client", fake_client):
            result = retrieval_module.select_verified_evidence(
                "האם כיסוי הסוללה ברכב טסלה כולל הצפה?",
                [facet], [[special, item("neutral", CAR_URL, "מידע כללי על ביטוח רכב")]],
                limit=2,
            )
        self.assertEqual(result[0]["id"], "battery")

    def test_car_product_in_question_overrides_planner_home_guess(self):
        bad_plan = {
            "search_query": "רעידת אדמה מסלולי ביטוח דירה",
            "domain": "home",
            "facets": [{"search_query": "כיסוי רעידת אדמה בדירה", "domain": "home"}],
        }
        fake_client = SimpleNamespace(models=SimpleNamespace(
            generate_content=lambda **kwargs: SimpleNamespace(
                text=json.dumps(bad_plan, ensure_ascii=False)
            ),
        ))
        with patch.object(retrieval_module, "gemini_client", fake_client):
            plan = retrieval_module.plan_query(
                "האם ביטוח מקיף לרכב מכסה רעידת אדמה בכל המסלולים?"
            )
        self.assertEqual(plan.domain, "car")
        self.assertEqual(plan.facets[0].domain, "car")
        self.assertIn("ביטוח רכב", plan.facets[0].search_query)


class ChatRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            item("car", CAR_URL, "ביטוח מקיף לרכב מכסה נזקי מזג אוויר כתוצאה משיטפון."),
            item("home", HOME_URL, "ביטוח תכולת דירה כולל הרחבה לסיכוני מים והצפה."),
        ]
        self.original = GeneratedAnswer(
            answerable=True,
            answer="תשובה עם פרט לא מתאים [SOURCE 1]",
            source_ids=[1, 2],
        )
        self.repaired = GeneratedAnswer(
            answerable=True,
            answer="לרכב כיסוי שיטפון; לדירה הרחבה לסיכוני מים.",
            source_ids=[1, 2],
        )
        self.unverified = VerificationResult(
            verified=False,
            issues=["טענה אחת בתשובה לא נתמכת במקור המתאים"],
            supported_source_ids=[1],
        )
        self.verified = VerificationResult(
            verified=True,
            issues=[],
            supported_source_ids=[1, 2],
        )

    def call_with(self, verifier_side_effect, repaired=None, original=None):
        with (
            patch.object(chat_module, "check_scope", return_value=SimpleNamespace(classification="in_scope")),
            patch.object(chat_module, "search_chunks", return_value=self.chunks),
            patch.object(chat_module, "build_context", return_value="[SOURCE 1]... [SOURCE 2]..."),
            patch.object(chat_module, "generate_answer", return_value=original or self.original),
            patch.object(chat_module, "repair_answer", return_value=repaired or self.repaired) as repair,
            patch.object(chat_module, "verify_answer", side_effect=verifier_side_effect) as verify,
            patch.object(chat_module, "ENABLE_EVIDENCE_VERIFICATION", True),
        ):
            output = chat_module.chat(SimpleNamespace(
                question="מה ההבדל בין כיסוי הצפה לרכב לבין כיסוי הצפה בדירה?"
            ))
            return output, repair.call_count, verify.call_count

    def test_failed_first_draft_is_repaired_once_and_reverified(self):
        output, repair_count, verify_count = self.call_with(
            [self.unverified, self.verified]
        )
        self.assertEqual(output.answer, self.repaired.answer)
        self.assertEqual(len(output.sources), 2)
        self.assertEqual(repair_count, 1)
        self.assertEqual(verify_count, 2)

    def test_second_rejection_fails_closed_no_infinite_loop(self):
        output, repair_count, verify_count = self.call_with(
            [self.unverified, self.unverified]
        )
        self.assertEqual(output.sources, [])
        self.assertIn("לא הצלחתי לאמת", output.answer)
        self.assertEqual(repair_count, 1)
        self.assertEqual(verify_count, 2)

    def test_first_pass_is_returned_without_repair(self):
        output, repair_count, verify_count = self.call_with([self.verified])
        self.assertEqual(len(output.sources), 2)
        self.assertEqual(repair_count, 0)
        self.assertEqual(verify_count, 1)
        self.assertNotIn("[SOURCE", output.answer)

    def test_unanswerable_private_info_never_calls_verifier_or_repair(self):
        original = GeneratedAnswer(
            answerable=False,
            answer="אין לי גישה לפרטי התביעה האישית שלך.",
            source_ids=[],
        )
        output, repair_count, verify_count = self.call_with(
            [], original=original
        )
        self.assertEqual(output.sources, [])
        self.assertIn("אין לי גישה", output.answer)
        self.assertEqual(repair_count, 0)
        self.assertEqual(verify_count, 0)


if __name__ == "__main__":
    unittest.main()