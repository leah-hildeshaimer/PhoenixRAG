r"""Offline regression checks for claim-level verification and citation coverage.

Run from backend: .\.venv\Scripts\python.exe -m unittest test_claim_citations.py
Tests patch live services: NO Qdrant/Gemini API requests are made.
"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.evidence_verifier import (
    ClaimSupport,
    VerificationResult,
    _enforce_verification_contract,
    _source_ids_in_context,
)
from api import chat as chat_module


class VerifierContractTests(unittest.TestCase):
    def test_distinct_claims_retain_distinct_sources(self):
        context = "[SOURCE 1]\ncar\n[/SOURCE 1]\n[SOURCE 2]\nhome\n[/SOURCE 2]"
        result = VerificationResult(
            verified=True,
            supported_source_ids=[1],  # model's summary accidentally omitted home
            claim_supports=[
                ClaimSupport(claim="car flooding", source_ids=[1]),
                ClaimSupport(claim="home flooding", source_ids=[2]),
            ],
        )
        processed = _enforce_verification_contract(result, _source_ids_in_context(context))
        self.assertTrue(processed.verified)
        self.assertEqual(processed.supported_source_ids, [1, 2])

    def test_unsupported_claim_fails_closed(self):
        result = VerificationResult(
            verified=True,
            claim_supports=[
                ClaimSupport(claim="car flooding", source_ids=[1]),
                ClaimSupport(claim="free worldwide coverage", source_ids=[]),
            ],
        )
        processed = _enforce_verification_contract(result, {1, 2})
        self.assertFalse(processed.verified)
        self.assertTrue(processed.issues)

    def test_unaddressed_question_part_fails_closed(self):
        result = VerificationResult(
            verified=True,
            claim_supports=[ClaimSupport(claim="car flooding", source_ids=[1])],
            unaddressed_parts=["home flooding"],
        )
        processed = _enforce_verification_contract(result, {1, 2})
        self.assertFalse(processed.verified)

    def test_nonexistent_source_id_fails_closed(self):
        result = VerificationResult(
            verified=True,
            claim_supports=[ClaimSupport(claim="some claim", source_ids=[99])],
        )
        processed = _enforce_verification_contract(result, {1, 2})
        self.assertFalse(processed.verified)


class ChatCitationTests(unittest.TestCase):
    def test_verified_source_ids_not_intersected_with_generation_ids(self):
        chunks = [
            {"id": "1", "url": "https://www.fnx.co.il/car-insurance/a", "page_title": "car", "text": "car"},
            {"id": "2", "url": "https://www.fnx.co.il/apartment-insurance/b", "page_title": "home", "text": "home"},
        ]
        generated = SimpleNamespace(
            answerable=True,
            answer="מידע על רכב ומידע על דירה [SOURCE 1]",
            source_ids=[1],
        )
        verified = VerificationResult(
            verified=True,
            supported_source_ids=[1, 2],
            claim_supports=[
                ClaimSupport(claim="car", source_ids=[1]),
                ClaimSupport(claim="home", source_ids=[2]),
            ],
        )
        with (
            patch.object(chat_module, "check_scope", return_value=SimpleNamespace(classification="in_scope")),
            patch.object(chat_module, "search_chunks", return_value=chunks),
            patch.object(chat_module, "build_context", return_value="[SOURCE 1]\ncar\n[SOURCE 2]\nhome"),
            patch.object(chat_module, "generate_answer", return_value=generated),
            patch.object(chat_module, "verify_answer", return_value=verified),
            patch.object(chat_module, "ENABLE_EVIDENCE_VERIFICATION", True),
        ):
            response = chat_module.chat(SimpleNamespace(question="compare"))
        self.assertEqual(len(response.sources), 2)
        self.assertNotIn("[SOURCE", response.answer)


if __name__ == "__main__":
    unittest.main()