from __future__ import annotations

import math

from app.algorithms.clause_matching import ClauseMatcher
from app.algorithms.company_brain import CompanyBrainMindMap
from app.algorithms.risk_scoring import BayesianRiskScorer, RiskObservation
from app.algorithms.section_detector import HMMSectionDetector
from app.algorithms.semantic_search import SemanticSearchEngine
from app.algorithms.voice_matching import VoiceMatcher
from app.models import Playbook, PlaybookPosition


def _make_positions() -> list[PlaybookPosition]:
    return [
        PlaybookPosition(
            id="p1",
            playbook_id="pb",
            topic="Confidentiality scope",
            preferred_position="Confidentiality limited to defined information",
            fallback_position="Confidentiality limited to written information",
            risk="Medium",
            keywords=["confidentiality", "defined", "information"],
            columns={},
        ),
        PlaybookPosition(
            id="p2",
            playbook_id="pb",
            topic="Termination notice",
            preferred_position="Thirty-day written notice of termination",
            fallback_position="Fifteen-day written notice of termination",
            risk="High",
            keywords=["termination", "notice", "thirty"],
            columns={},
        ),
        PlaybookPosition(
            id="p3",
            playbook_id="pb",
            topic="Indemnification",
            preferred_position="Mutual indemnification with capped liability",
            fallback_position="Mutual indemnification with carved out IP",
            risk="High",
            keywords=["indemnification", "liability", "carved"],
            columns={},
        ),
    ]


def _make_playbook(playbook_id: str = "pb", name: str = "Standard NDA Playbook") -> Playbook:
    positions = _make_positions()
    for position in positions:
        position.playbook_id = playbook_id
    return Playbook(
        id=playbook_id,
        slug=playbook_id,
        name=name,
        category="NDA",
        description="Demo playbook",
        owner="Legal Ops",
        version=1,
        columns=["Topic", "Preferred Position", "Fallback 1", "Red Line", "Deal Breaker"],
        positions=positions,
    )


def test_clause_matcher_returns_top_k_with_cosine_in_unit_interval():
    matcher = ClauseMatcher(min_score=0.0).fit(_make_positions())
    hits = matcher.match("Termination requires thirty-day written notice.", top_k=2)
    assert len(hits) <= 2
    assert all(0.0 <= hit.score <= 1.0 for hit in hits)
    assert hits[0].topic == "Termination notice"


def test_clause_matcher_handles_empty_corpus_without_crashing():
    matcher = ClauseMatcher().fit([])
    assert matcher.match("anything", top_k=3) == []


def test_clause_matcher_best_match_respects_min_score():
    matcher = ClauseMatcher(min_score=0.9).fit(_make_positions())
    assert matcher.best_match("Lunchroom seating arrangements") is None


def test_bayesian_risk_posterior_sums_to_one_and_dominant_label_is_consistent():
    scorer = BayesianRiskScorer(prior_alpha=(2.0, 2.0, 2.0))
    posterior = scorer.score(
        [
            RiskObservation("High", 0.9),
            RiskObservation("High", 0.6),
            RiskObservation("Medium", 0.3),
        ]
    )
    assert math.isclose(sum(posterior.mean), 1.0, abs_tol=1e-6)
    assert posterior.dominant == "High"
    assert all(0.0 <= low <= high <= 1.0 for low, high in posterior.credible_intervals.values())


def test_bayesian_credible_interval_shrinks_with_more_evidence():
    scorer = BayesianRiskScorer()
    short = scorer.score([RiskObservation("High", 0.5)])
    long = scorer.score([RiskObservation("High", 0.95) for _ in range(20)])
    short_width = short.credible_intervals["High"][1] - short.credible_intervals["High"][0]
    long_width = long.credible_intervals["High"][1] - long.credible_intervals["High"][0]
    assert long_width < short_width


def test_hmm_section_detector_marks_first_paragraph_and_returns_segments():
    detector = HMMSectionDetector()
    paragraphs = [
        "1. CONFIDENTIALITY",
        "The receiving party shall keep information confidential.",
        "2. TERMINATION",
        "Either party may terminate with thirty days notice.",
    ]
    path = detector.decode(paragraphs)
    assert path[0] == 1  # BEGIN sentinel
    sections = detector.segment(paragraphs)
    assert sections
    assert sections[0].title


def test_voice_matcher_returns_unit_score_for_identical_strings_and_zero_for_empty():
    matcher = VoiceMatcher(ClauseMatcher().fit(_make_positions()), threshold=0.0)
    score, jaro, _tfidf, edit = matcher.score_pair("hello world", "hello world")
    assert 0.5 <= score <= 1.0
    assert math.isclose(jaro, 1.0, abs_tol=1e-6)
    assert math.isclose(edit, 1.0, abs_tol=1e-6)

    score, jaro, tfidf, edit = matcher.score_pair("", "")
    assert score == 0.0
    assert jaro == 0.0
    assert tfidf == 0.0
    assert edit == 0.0


def test_voice_matcher_threshold_filters_low_scores():
    matcher = VoiceMatcher(ClauseMatcher().fit(_make_positions()), threshold=0.95)
    matches = matcher.match(
        "lunchroom seating arrangements",
        candidates=[("p1", "Confidentiality scope", "Confidentiality limited to defined information")],
        top_k=3,
    )
    assert matches == []


def test_semantic_search_falls_back_to_bm25_without_openai_key():
    engine = SemanticSearchEngine(
        documents=[
            ("doc1", "termination thirty day notice"),
            ("doc2", "confidentiality scope definitions"),
            ("doc3", "indemnification liability capped"),
        ],
        openai_api_key=None,
    )
    hits = engine.search("termination notice")
    assert hits
    assert hits[0].document_id == "doc1"
    assert hits[0].method == "bm25"


def test_company_brain_emits_playbook_first_mm_style_tree():
    brain = CompanyBrainMindMap()
    snapshot = brain.from_playbooks(
        [
            _make_playbook("pb-nda", "Standard NDA Playbook"),
            _make_playbook("pb-dpa", "Supplier DPA Playbook"),
        ],
        use_cache=False,
    )
    ids = {node["id"] for node in snapshot.nodes}
    assert {"company-brain", "pb-nda", "pb-dpa"}.issubset(ids)
    assert snapshot.tree["name"] == "Company Brain"
    assert snapshot.tree["type"] == "branch"
    assert snapshot.tree["children"]
    assert snapshot.tree["children"][0]["kind"] == "playbook"
    assert snapshot.tree["children"][0]["children"][0]["kind"] == "topic"
    assert all(node["type"] in {"branch", "leaf"} for node in snapshot.nodes)


def test_single_playbook_brain_expands_topics_into_negotiation_logic():
    brain = CompanyBrainMindMap()
    snapshot = brain.from_playbook(_make_playbook())
    first_topic = snapshot.tree["children"][0]
    child_names = {child["name"] for child in first_topic["children"]}
    assert snapshot.tree["kind"] == "playbook"
    assert first_topic["kind"] == "topic"
    assert {"Preferred", "Fallback"}.issubset(child_names)
