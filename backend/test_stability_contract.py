r"""No-network contract tests. Run from backend:
.\.venv\Scripts\python.exe -m unittest test_stability_contract.py
"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.evidence_verifier import (
    EvidenceQuote,
    ClaimSupport,
    VerificationResult,
    _enforce_verification_contract,
    _source_texts_in_context,
    _source_ids_in_context,
)
from services.generation import GeneratedAnswer
from api import chat as chat_module


CONTEXT = (
    "[SOURCE 1]\nTitle: Car\nURL: https://www.fnx.co.il/car-insurance/a\n"
    "Content:\nביטוח מקיף לרכב מכסה נזקי מזג אוויר כתוצאה משיטפון.\n[/SOURCE 1]\n\n"
    "[SOURCE 2]\nTitle: Home\nURL: https://www.fnx.co.il/apartment-insurance/b\n"
    "Content:\nביטוח תכולת דירה כולל הרחבה לסיכוני מים ונוזלים אחרים.\n[/SOURCE 2]"
)


def claim(text, source_id, quote):
    return ClaimSupport(
        claim=text, source_ids=[source_id],
        evidence_quotes=[EvidenceQuote(source_id=source_id, quote=quote)],
    )


def contract(result):
    return _enforce_verification_contract(
        result, _source_ids_in_context(CONTEXT), _source_texts_in_context(CONTEXT),
    )


class EvidenceContractTests(unittest.TestCase):
    def test_comparison_has_independent_proofs(self):
        result = contract(VerificationResult(
            verified=True,
            # Model's summary is NOT authoritative.
            supported_source_ids=[1],
            claim_supports=[
                claim('car flood', 1, 'מכסה נזקי מזג אוויר כתוצאה משיטפון'),
                claim('home water', 2, 'כולל הרחבה לסיכוני מים ונוזלים אחרים'),
            ],
        ))
        self.assertTrue(result.verified, result.issues)
        self.assertEqual(result.supported_source_ids, [1, 2])

    def test_invented_quote_rejected_even_if_model_says_verified(self):
        result = contract(VerificationResult(
            verified=True,
            claim_supports=[claim('unlimited compensation', 1, 'כיסוי ללא מגבלות בכל המסלולים')],
        ))
        self.assertFalse(result.verified)
        self.assertEqual(result.supported_source_ids, [])

    def test_missing_quote_rejected(self):
        result = contract(VerificationResult(
            verified=True,
            claim_supports=[ClaimSupport(claim='car flood', source_ids=[1])],
        ))
        self.assertFalse(result.verified)

    def test_quote_from_title_only_is_not_evidence(self):
        result = contract(VerificationResult(
            verified=True,
            claim_supports=[claim('car title', 1, 'https://www.fnx.co.il/car-insurance/a')],
        ))
        self.assertFalse(result.verified)

    def test_unknown_source_number_rejected(self):
        result = contract(VerificationResult(
            verified=True,
            claim_supports=[claim('flood', 99, 'מכסה נזקי מזג אוויר כתוצאה משיטפון')],
        ))
        self.assertFalse(result.verified)

    def test_unrequested_special_product_flag_rejects(self):
        result = contract(VerificationResult(
            verified=True,
            claim_supports=[claim('car flood', 1, 'מכסה נזקי מזג אוויר כתוצאה משיטפון')],
            scope_issues=['הוכנס מידע על מוצר ייעודי שלא נשאל'],
        ))
        self.assertFalse(result.verified)

    def test_missing_requested_comparison_part_rejects(self):
        result = contract(VerificationResult(
            verified=True,
            claim_supports=[claim('car flood', 1, 'מכסה נזקי מזג אוויר כתוצאה משיטפון')],
            unaddressed_parts=['כיסוי בדירה'],
        ))
        self.assertFalse(result.verified)

    def test_half_supported_answer_rejected(self):
        result = contract(VerificationResult(
            verified=True,
            claim_supports=[
                claim('car flood', 1, 'מכסה נזקי מזג אוויר כתוצאה משיטפון'),
                ClaimSupport(claim='earthquake free in all plans'),
            ],
        ))
        self.assertFalse(result.verified)

    def test_quote_whitespace_variance_ok(self):
        result = contract(VerificationResult(
            verified=True,
            claim_supports=[claim('car flood', 1, 'מכסה נזקי מזג אוויר\nכתוצאה משיטפון')],
        ))
        self.assertTrue(result.verified, result.issues)


class ApiResponseTests(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            {'id': 'car', 'url': 'https://www.fnx.co.il/car-insurance/a', 'page_title': 'Car', 'text': 'car'},
            {'id': 'home', 'url': 'https://www.fnx.co.il/apartment-insurance/b', 'page_title': 'Home', 'text': 'home'},
        ]
        self.generated = GeneratedAnswer(
            answerable=True, answer='כיסוי רכב וגם כיסוי דירה [SOURCE 1]', source_ids=[1],
        )

    def run_chat(self, verification):
        with (
            patch.object(chat_module, 'check_scope', return_value=SimpleNamespace(classification='in_scope')),
            patch.object(chat_module, 'search_chunks', return_value=self.chunks),
            patch.object(chat_module, 'build_context', return_value=CONTEXT),
            patch.object(chat_module, 'generate_answer', return_value=self.generated),
            patch.object(chat_module, 'verify_answer', return_value=verification),
            patch.object(chat_module, 'repair_answer', return_value=GeneratedAnswer(
                answerable=False, answer='לא הצלחתי לאמת', source_ids=[])),
            patch.object(chat_module, 'ENABLE_EVIDENCE_VERIFICATION', True),
        ):
            return chat_module.chat(SimpleNamespace(question='השוואת רכב ודירה'))

    def test_citations_from_verified_claims_not_generator_intersection(self):
        verified = contract(VerificationResult(
            verified=True,
            claim_supports=[
                claim('car flood', 1, 'מכסה נזקי מזג אוויר כתוצאה משיטפון'),
                claim('home water', 2, 'כולל הרחבה לסיכוני מים ונוזלים אחרים'),
            ],
        ))
        response = self.run_chat(verified)
        self.assertEqual(len(response.sources), 2)
        self.assertNotIn('[SOURCE', response.answer)

    def test_rejected_scope_does_not_publish_answer(self):
        rejected = contract(VerificationResult(
            verified=True,
            claim_supports=[claim('car flood', 1, 'מכסה נזקי מזג אוויר כתוצאה משיטפון')],
            scope_issues=['נוסף מידע בלתי רלוונטי על מסלול ייעודי'],
        ))
        response = self.run_chat(rejected)
        self.assertEqual(response.sources, [])
        self.assertNotIn('כיסוי רכב', response.answer)


if __name__ == '__main__':
    unittest.main()