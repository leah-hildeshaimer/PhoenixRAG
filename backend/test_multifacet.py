"""Fast, offline regression tests for evidence coverage across sub-questions.

From backend/: .\\.venv\\Scripts\\python.exe -m unittest test_ranking.py test_multifacet.py
"""
import unittest
from unittest.mock import patch

from services.retrieval import (
    QueryPlan,
    SearchFacet,
    search_chunks,
    select_multifacet_evidence,
)


def make_chunk(identifier, domain, url_suffix="page"):
    path = "car-insurance" if domain == "car" else "apartment-insurance"
    return {
        "id": identifier,
        "page_title": identifier,
        "text": "כיסוי הצפה בהתאם לתנאי הפוליסה",
        "url": f"https://www.fnx.co.il/{path}/{url_suffix}/",
        "score": 0.7,
    }


class MultiFacetEvidenceTests(unittest.TestCase):
    def test_diverse_sources_cover_both_domains(self):
        car = [make_chunk(f"car{i}", "car", str(i)) for i in range(5)]
        home = [make_chunk(f"home{i}", "home", str(i)) for i in range(5)]
        chosen = select_multifacet_evidence([car, home], limit=5)
        self.assertEqual(len(chosen), 5)
        self.assertGreaterEqual(sum("/car-insurance/" in c["url"] for c in chosen), 2)
        self.assertGreaterEqual(sum("/apartment-insurance/" in c["url"] for c in chosen), 2)

    def test_duplicate_evidence_removed(self):
        duplicate = make_chunk("same", "car")
        chosen = select_multifacet_evidence([[duplicate], [duplicate]], limit=5)
        self.assertEqual([item["id"] for item in chosen], ["same"])

    def test_search_executes_both_facets(self):
        facets = [
            SearchFacet(search_query="נזקי הצפה בביטוח רכב", key_terms=["הצפה"], domain="car"),
            SearchFacet(search_query="נזקי הצפה בביטוח דירה", key_terms=["הצפה"], domain="home"),
        ]
        plan = QueryPlan(search_query="השוואת כיסוי הצפה רכב ודירה", domain="other", facets=facets)
        def retrieval(facet, limit):
            return ([make_chunk(facet.domain, facet.domain)],
                    dict(embedding=0, qdrant=0, ranking=0,
                         semantic=1, focused=0, lexical=0, candidates=1))
        with patch("services.retrieval.plan_query", return_value=plan), \
             patch("services.retrieval._retrieve_facet", side_effect=retrieval) as mocked:
            chosen = search_chunks("מה ההבדל בין ביטוח רכב לדירה בהצפה?", limit=5)
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual({c["id"] for c in chosen}, {"car", "home"})


if __name__ == "__main__":
    unittest.main()
