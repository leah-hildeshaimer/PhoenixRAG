"""Offline ranking tests. These tests do not call Gemini or Qdrant APIs.
Run from backend/: python -m unittest test_ranking.py
"""
import unittest

from services.retrieval import QueryPlan, build_context, rerank_chunks


class RetrievalRankingTests(unittest.TestCase):
    def test_topic_and_correct_domain_beat_generic_or_wrong_domain(self):
        chunks = [
            dict(id="home", text="ביטוח דירה מכסה שיטפון והצפה בדירה",
                 page_title="דירה", url="https://www.fnx.co.il/apartment-insurance/test/",
                 score=.69, semantic_rank=2),
            dict(id="car", text="ביטוח מקיף לרכב כולל כיסוי שיטפון והצפה",
                 page_title="ביטוח מקיף לרכב",
                 url="https://www.fnx.co.il/car-insurance/comprehensive/",
                 score=.62, focused_rank=3),
            dict(id="car_alt", text="ביטוח מקיף לרכב מכסה נזקי שיטפון",
                 page_title="סוגי ביטוח רכב",
                 url="https://www.fnx.co.il/car-insurance/kinds/", score=0.0),
            dict(id="generic", text="ביטוח רכב מכסה נזקי תאונה",
                 page_title="ביטוח רכב",
                 url="https://www.fnx.co.il/car-insurance/other/",
                 score=.72, semantic_rank=1),
        ]
        plan = QueryPlan(search_query="ביטוח מקיף לרכב שיטפון הצפה",
                         key_terms=["שיטפון", "הצפה"], domain="car")
        results = rerank_chunks("שאלה", chunks, limit=4, plan=plan)
        self.assertEqual([r["id"] for r in results[:2]], ["car", "car_alt"])
        self.assertEqual(results[-1]["id"], "home")

    def test_max_two_chunks_from_same_url_when_alternatives_exist(self):
        chunks = [
            dict(id=str(i), text=f"שיטפון ביטוח מקיף לרכב {i}",
                 page_title="מקיף", url="https://www.fnx.co.il/car-insurance/a/",
                 score=0.78 - i * 0.01, semantic_rank=i)
            for i in range(4)
        ]
        chunks.append(dict(id="other", text="שיטפון ביטוח רכב",
                           page_title="נזקי טבע",
                           url="https://www.fnx.co.il/car-insurance/b/",
                           score=.66, focused_rank=4))
        plan = QueryPlan(search_query="שיטפון רכב", key_terms=["שיטפון"], domain="car")
        results = rerank_chunks("שאלה", chunks, limit=3, plan=plan)
        self.assertIn("other", [r["id"] for r in results])
        self.assertEqual(len(results), 3)

    def test_source_ids_stay_aligned_with_context(self):
        context = build_context([dict(page_title="כותרת", url="https://www.fnx.co.il/test/",
                                     section_title="סעיף", text="כיסוי מפורש", id="1")])
        self.assertIn("[SOURCE 1]", context)
        self.assertIn("[/SOURCE 1]", context)
        self.assertIn("כיסוי מפורש", context)


if __name__ == "__main__":
    unittest.main()
