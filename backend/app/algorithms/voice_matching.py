"""Voice -> playbook proposal matcher.

Combines three string similarity signals and a TF-IDF cosine score from the
playbook ClauseMatcher into a single normalised score in [0, 1].

Math
----
Jaro(s1, s2)        = (1/3) * (m/|s1| + m/|s2| + (m - t/2)/m)
    m = matching characters within floor(max(|s1|, |s2|) / 2) - 1 window
    t = transpositions / 2

Jaro-Winkler(s1, s2) = Jaro(s1, s2) + p * l * (1 - Jaro(s1, s2))
    l = common prefix length, max 4;  p = 0.1

Wagner-Fischer normalised edit distance:
    edit_sim(s1, s2) = 1 - levenshtein(s1, s2) / max(|s1|, |s2|)

Combined score (weights sum to 1):
    score = w_jaro * Jaro-Winkler
          + w_tfidf * cosine_tfidf
          + w_edit * edit_sim
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import jellyfish

from .clause_matching import ClauseMatcher


@dataclass(frozen=True)
class VoiceMatch:
    position_id: str
    topic: str
    score: float
    jaro: float
    tfidf: float
    edit: float


class VoiceMatcher:
    def __init__(
        self,
        clause_matcher: ClauseMatcher,
        threshold: float = 0.55,
        jaro_weight: float = 0.4,
        tfidf_weight: float = 0.3,
        edit_weight: float = 0.3,
    ) -> None:
        total = jaro_weight + tfidf_weight + edit_weight
        if total <= 0:
            raise ValueError("Voice matcher weights must sum to a positive number")
        self.threshold = float(threshold)
        self.jaro_weight = float(jaro_weight) / total
        self.tfidf_weight = float(tfidf_weight) / total
        self.edit_weight = float(edit_weight) / total
        self.clause_matcher = clause_matcher

    @staticmethod
    def _normalised_edit(left: str, right: str) -> float:
        if not left and not right:
            return 1.0
        if not left or not right:
            return 0.0
        distance = jellyfish.levenshtein_distance(left, right)
        return 1.0 - distance / max(len(left), len(right))

    def score_pair(self, transcript: str, candidate: str) -> tuple[float, float, float, float]:
        if not transcript or not candidate:
            return 0.0, 0.0, 0.0, 0.0
        jaro = float(jellyfish.jaro_winkler_similarity(transcript.lower(), candidate.lower()))
        edit = self._normalised_edit(transcript.lower(), candidate.lower())
        tfidf_hits = self.clause_matcher.match(transcript, top_k=1)
        tfidf = float(tfidf_hits[0].score) if tfidf_hits and tfidf_hits[0].topic == candidate else 0.0
        score = (
            self.jaro_weight * jaro
            + self.tfidf_weight * tfidf
            + self.edit_weight * edit
        )
        return score, jaro, tfidf, edit

    def match(self, transcript: str, candidates: Iterable[tuple[str, str, str]], top_k: int = 3) -> list[VoiceMatch]:
        """`candidates` is an iterable of (position_id, topic, preferred_text)."""
        scored: list[VoiceMatch] = []
        if not transcript.strip():
            return scored
        tfidf_hits = {hit.position_id: hit.score for hit in self.clause_matcher.match(transcript, top_k=64)}
        for position_id, topic, preferred in candidates:
            jaro = float(jellyfish.jaro_winkler_similarity(transcript.lower(), preferred.lower()))
            edit = self._normalised_edit(transcript.lower(), preferred.lower())
            tfidf = float(tfidf_hits.get(position_id, 0.0))
            score = (
                self.jaro_weight * jaro
                + self.tfidf_weight * tfidf
                + self.edit_weight * edit
            )
            scored.append(
                VoiceMatch(
                    position_id=position_id,
                    topic=topic,
                    score=round(score, 4),
                    jaro=round(jaro, 4),
                    tfidf=round(tfidf, 4),
                    edit=round(edit, 4),
                )
            )
        scored.sort(key=lambda match: match.score, reverse=True)
        return [match for match in scored[: max(top_k, 1)] if match.score >= self.threshold]
