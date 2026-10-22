"""Offline evidence selection tests; no Gemini/Qdrant network requests.

From backend/: .\\.venv\\Scripts\\python.exe -m unittest test_ranking.py test_multifacet.py test_evidence_selector.py
"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.retrieval import (
    EvidenceGrade, EvidenceReview, SearchFacet, select_verified_evidence,
)


def passage(id_, domain, title, text):
    section = "car-insurance" if domain == "car" else "apartment-insurance"
    return {
        "id": id_,
        "page_title": title,
        "text": text,
        "url": f"https://www.fnx.co.il/{section}/{id_}/",
        "score": .7,
    }


class EvidenceSelectorTests(unittest.TestCase):
    def setUp(self):
        self.facets = [
            SearchFacet(search_query="כיסוי הצפה לרכב", key_terms=["הצפה"], domain="car"),
            SearchFacet(search_query="כיסוי הצפה לדירה", key_terms=["הצפה"], domain="home"),
        ]
        self.car_generic = passage("driver", "car", "ביטוח לנהג זמני", "מוצר לנהג זמני")
        self.car_supported = passage("car", "car", "ביטוח מקיף לרכב", "ביטוח מקיף מכסה הצפה ברכב")
        self.home_generic = passage("home-about", "home", "מידע על דירות", "כללים על מבנה")
        self.home_supported = passage("home", "home", "ביטוח דירה", "ביטוח דירה מכסה הצפות בהתאם לתנאים")
        self.lists = [[self.car_generic, self.car_supported],
                      [self.home_generic, self.home_supported]]

    def test_direct_evidence_beats_related_page_and_preserves_facets(self):
        review = EvidenceReview(grades=[
            EvidenceGrade(candidate_id=1, facet_id=1, relevance=1),
            EvidenceGrade(candidate_id=2, facet_id=1, relevance=3),
            EvidenceGrade(candidate_id=3, facet_id=2, relevance=1),
            EvidenceGrade(candidate_id=4, facet_id=2, relevance=3),
        ])
        with patch("services.retrieval.gemini_client.models.generate_content",
                   return_value=SimpleNamespace(text=review.model_dump_json())):
            results = select_verified_evidence("השווה כיסוי הצפה לרכב ולדירה",
                                               self.facets, self.lists, limit=5)
        self.assertEqual({c["id"] for c in results}, {"car", "home"})

    def test_falls_back_to_original_when_reviewer_unavailable(self):
        with patch("services.retrieval.gemini_client.models.generate_content",
                   side_effect=RuntimeError("network unavailable")):
            results = select_verified_evidence("השווה כיסוי הצפה לרכב ולדירה",
                                               self.facets, self.lists, limit=5)
        self.assertEqual(len(results), 4)


if __name__ == "__main__":
    unittest.main()
