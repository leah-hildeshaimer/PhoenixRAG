"""Offline regression tests for grounded multifacet evidence selection."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.retrieval import (
    EvidenceGrade, EvidenceReview, SearchFacet, QueryPlan,
    _selection_excerpt, _quote_is_grounded, rerank_chunks,
    select_verified_evidence, plan_query,
)


def chunk(cid, domain, text):
    family = 'car-insurance' if domain == 'car' else 'apartment-insurance'
    return dict(id=cid, page_title=cid, text=text,
                url=f'https://www.fnx.co.il/{family}/{cid}/', score=.75)


class GroundedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.facets = [
            SearchFacet(search_query='כיסוי הצפה ברכב', key_terms=['הצפה', 'רכב'],
                        alternate_terms=['שיטפון'], domain='car'),
            SearchFacet(search_query='כיסוי הצפה בדירה', key_terms=['הצפה', 'דירה'],
                        alternate_terms=['שיטפון'], domain='home'),
        ]
        self.driver = chunk('driver', 'car', 'הכיסוי ניתן לרכישה בפוליסות מקיף לנהג זמני')
        self.car = chunk('car-flood', 'car',
                         'ביטוח מקיף לרכב מכסה גם נזקי מזג אוויר לרכב כתוצאה משיטפון')
        self.home = chunk('home-flood', 'home',
                          'פוליסת ביטוח הדירה מכסה הצפה פתאומית מהביוב וכן שיטפון')
        self.home_generic = chunk('home-other', 'home', 'ביטוח דירה הוא פתרון מגוון')
        self.lists = [[self.driver, self.car], [self.home_generic, self.home]]

    def test_full_excerpt_does_not_hide_event_after_1100_characters(self):
        long_passage = chunk('test', 'car', 'כיסוי לרכב ' * 130 +
                             'ביטוח מקיף מכסה נזקי שיטפון לרכב ')
        excerpt = _selection_excerpt(long_passage, ['הצפה', 'רכב'])
        self.assertIn('שיטפון', excerpt)

    def test_grounded_quote_rescues_semantic_synonym_and_rejects_generic_page(self):
        grades = EvidenceReview(grades=[
            EvidenceGrade(candidate_id=1, facet_id=1, relevance=3,
                          evidence_quote='הכיסוי ניתן לרכישה בפוליסות מקיף לנהג זמני'),
            EvidenceGrade(candidate_id=2, facet_id=1, relevance=3,
                          evidence_quote='נזקי מזג אוויר לרכב כתוצאה משיטפון'),
            EvidenceGrade(candidate_id=3, facet_id=2, relevance=3,
                          evidence_quote='ביטוח דירה הוא פתרון מגוון'),
            EvidenceGrade(candidate_id=4, facet_id=2, relevance=3,
                          evidence_quote='מכסה הצפה פתאומית מהביוב וכן שיטפון'),
        ])
        with patch('services.retrieval.gemini_client.models.generate_content',
                   return_value=SimpleNamespace(text=grades.model_dump_json())):
            chosen = select_verified_evidence('השווה כיסוי הצפה ברכב ובדירה',
                                              self.facets, self.lists, 5)
        self.assertEqual({item['id'] for item in chosen}, {'car-flood', 'home-flood'})

    def test_hallucinated_quote_is_rejected(self):
        grades = EvidenceReview(grades=[
            EvidenceGrade(candidate_id=1, facet_id=1, relevance=3,
                          evidence_quote='הפוליסה מכסה שיטפון'),
            EvidenceGrade(candidate_id=2, facet_id=1, relevance=3,
                          evidence_quote='נזקי מזג אוויר לרכב כתוצאה משיטפון'),
        ])
        with patch('services.retrieval.gemini_client.models.generate_content',
                   return_value=SimpleNamespace(text=grades.model_dump_json())):
            chosen = select_verified_evidence('כיסוי שיטפון לרכב',
                                              self.facets[:1], [self.lists[0]], 5)
        self.assertEqual([item['id'] for item in chosen], ['car-flood'])

    def test_alternate_terms_improve_ranking_without_question_specific_code(self):
        plan = QueryPlan(search_query='כיסוי הצפה רכב', key_terms=['הצפה','רכב'],
                         alternate_terms=['שיטפון'], domain='car')
        ranked = rerank_chunks('כיסוי', [self.driver.copy(), self.car.copy()],
                               limit=2, plan=plan)
        self.assertEqual(ranked[0]['id'], 'car-flood')

    def test_quote_must_be_actual_source_text(self):
        self.assertTrue(_quote_is_grounded('נזקי מזג אוויר לרכב', self.car['text']))
        self.assertFalse(_quote_is_grounded('כיסוי לכל אירוע אפשרי', self.car['text']))


if __name__ == '__main__':
    unittest.main()
