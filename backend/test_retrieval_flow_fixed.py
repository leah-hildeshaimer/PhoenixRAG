"""Regression tests for the evidence selector. Run from backend directory."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services import retrieval as r


class EvidenceSelectorRegressionTests(unittest.TestCase):
    def test_evidence_quote_in_schema(self):
        self.assertIn("evidence_quote", r.EvidenceGrade.model_fields)
        obj = r.EvidenceGrade(candidate_id=1, facet_id=1, relevance=3,
                              evidence_quote="בדיקה עם ציטוט אמיתי")
        self.assertEqual(obj.evidence_quote, "בדיקה עם ציטוט אמיתי")

    def test_selection_uses_review_not_original_fallback(self):
        car_wrong = {
            "id": "car-wrong", "url": "https://www.fnx.co.il/car-insurance/daily/",
            "page_title": "ביטוח נהג זמני", "text": "נהג זמני למשך מספר ימים"
        }
        car_right = {
            "id": "car-right", "url": "https://www.fnx.co.il/car-insurance/article/",
            "page_title": "נזקי טבע לרכב",
            "text": "ביטוח מקיף לרכב מכסה נזקי מזג אוויר לרכב כתוצאה משיטפון."
        }
        home_wrong = {
            "id": "home-wrong", "url": "https://www.fnx.co.il/apartment-insurance/contact/",
            "page_title": "שירות לקוחות", "text": "יצירת קשר לביטוח דירה"
        }
        home_right = {
            "id": "home-right", "url": "https://www.fnx.co.il/apartment-insurance/article/",
            "page_title": "נזקי מים בדירה",
            "text": "ביטוח תכולת דירה מעניק כיסוי במקרה של הצפה פתאומית מהביוב."
        }
        review = {
            "grades": [
                {"candidate_id": 2, "facet_id": 1, "relevance": 3,
                 "evidence_quote": "ביטוח מקיף לרכב מכסה נזקי מזג אוויר לרכב כתוצאה משיטפון.",
                 "supports_issue": True},
                {"candidate_id": 4, "facet_id": 2, "relevance": 3,
                 "evidence_quote": "ביטוח תכולת דירה מעניק כיסוי במקרה של הצפה פתאומית מהביוב.",
                 "supports_issue": True},
            ]
        }
        fake_client = SimpleNamespace(models=SimpleNamespace(
            generate_content=lambda **kwargs: SimpleNamespace(
                text=json.dumps(review, ensure_ascii=False)
            )
        ))
        facets = [
            r.SearchFacet(search_query="כיסוי הצפה רכב", key_terms=["הצפה"],
                          alternate_terms=["שיטפון"], domain="car"),
            r.SearchFacet(search_query="כיסוי הצפה דירה", key_terms=["הצפה"],
                          domain="home"),
        ]
        with patch.object(r, "gemini_client", fake_client):
            selected = r.select_verified_evidence(
                "מה ההבדל בין הצפה ברכב לבין הצפה בדירה?",
                facets,
                [[car_wrong, car_right], [home_wrong, home_right]],
                limit=2,
            )
        self.assertEqual([item["id"] for item in selected],
                         ["car-right", "home-right"])


if __name__ == "__main__":
    unittest.main()