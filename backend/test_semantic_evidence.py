"""Offline regression: source-based semantic equivalents without accepting unrelated quotes."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.retrieval import (
    EvidenceGrade, EvidenceReview, SearchFacet, select_verified_evidence,
)


def make_chunk(identifier, family, content):
    return {
        "id": identifier,
        "page_title": identifier,
        "text": content,
        "url": f"https://www.fnx.co.il/{family}/{identifier}/",
        "score": 0.7,
    }


class SemanticEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.facets = [
            SearchFacet(search_query="נזקי הצפה לרכב", key_terms=["הצפה", "רכב"], domain="car"),
            SearchFacet(search_query="נזקי הצפה לדירה", key_terms=["הצפה", "דירה"], domain="home"),
        ]
        self.driver = make_chunk("driver", "car-insurance", "הכיסוי ניתן לרכישה בפוליסות מקיף לנהג זמני")
        self.car = make_chunk("car-event", "car-insurance", "ביטוח מקיף לרכב מכסה גם נזקי מזג אוויר לרכב כתוצאה משיטפון")
        self.home = make_chunk("home-event", "apartment-insurance", "ביטוח דירה כולל כיסוי לנזקי הצפה מהביוב")
        self.lists = [[self.driver, self.car], [self.home]]

    def test_semantic_synonym_is_admitted_when_quote_is_grounded(self):
        review = EvidenceReview(grades=[
            EvidenceGrade(candidate_id=1, facet_id=1, relevance=3,
                          evidence_quote="הכיסוי ניתן לרכישה בפוליסות מקיף לנהג זמני",
                          supports_issue=False),
            EvidenceGrade(candidate_id=2, facet_id=1, relevance=3,
                          evidence_quote="נזקי מזג אוויר לרכב כתוצאה משיטפון",
                          supports_issue=True),
            EvidenceGrade(candidate_id=3, facet_id=2, relevance=3,
                          evidence_quote="כיסוי לנזקי הצפה מהביוב",
                          supports_issue=True),
        ])
        with patch("services.retrieval.gemini_client.models.generate_content",
                   return_value=SimpleNamespace(text=review.model_dump_json())):
            chosen = select_verified_evidence("השווה הצפה ברכב ובדירה", self.facets,
                                              self.lists, limit=5)
        self.assertEqual({chunk["id"] for chunk in chosen}, {"car-event", "home-event"})

    def test_fabricated_quote_rejected_even_if_marked_supported(self):
        review = EvidenceReview(grades=[
            EvidenceGrade(candidate_id=1, facet_id=1, relevance=3,
                          evidence_quote="מכסה נזקי שיטפון בכל התנאים", supports_issue=True),
            EvidenceGrade(candidate_id=2, facet_id=1, relevance=3,
                          evidence_quote="נזקי מזג אוויר לרכב כתוצאה משיטפון", supports_issue=True),
        ])
        with patch("services.retrieval.gemini_client.models.generate_content",
                   return_value=SimpleNamespace(text=review.model_dump_json())):
            chosen = select_verified_evidence("כיסוי נזקי הצפה לרכב", self.facets[:1],
                                              [self.lists[0]], limit=5)
        self.assertEqual([chunk["id"] for chunk in chosen], ["car-event"])

    def test_unverified_semantic_claim_rejected(self):
        review = EvidenceReview(grades=[
            EvidenceGrade(candidate_id=1, facet_id=1, relevance=3,
                          evidence_quote="הכיסוי ניתן לרכישה בפוליסות מקיף לנהג זמני",
                          supports_issue=None),
            EvidenceGrade(candidate_id=2, facet_id=1, relevance=3,
                          evidence_quote="נזקי מזג אוויר לרכב כתוצאה משיטפון",
                          supports_issue=True),
        ])
        with patch("services.retrieval.gemini_client.models.generate_content",
                   return_value=SimpleNamespace(text=review.model_dump_json())):
            chosen = select_verified_evidence("כיסוי נזקי הצפה לרכב", self.facets[:1],
                                              [self.lists[0]], limit=5)
        self.assertEqual([chunk["id"] for chunk in chosen], ["car-event"])


if __name__ == "__main__":
    unittest.main()
