"""TF-IDF cosine-similarity clause matcher.

Math
----
TF(t, d)        = count(t, d) / |d|
IDF(t, D)       = log((|D| + 1) / (df(t) + 1)) + 1            (Scikit-learn smoothed)
TF-IDF(t, d, D) = TF(t, d) * IDF(t, D)
cosine(A, B)    = (A . B) / (||A|| * ||B||)                   in [0, 1] for non-negative TF-IDF

Each playbook position is embedded as a sparse TF-IDF vector formed from
the concatenation of its topic, preferred position, fallback position,
and keywords (the corpus). Incoming contract clauses are projected into
the same vector space and cosine-compared against every position.
Returns the top-k hits above a configurable minimum score.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..models import PlaybookPosition


_TOKEN_PATTERN = re.compile(r"(?u)\b[a-z][a-z-]{2,}\b")


def _position_corpus_entry(position: PlaybookPosition) -> str:
    pieces = [
        position.topic,
        position.preferred_position,
        position.fallback_position,
        " ".join(position.keywords or []),
    ]
    return " ".join(piece for piece in pieces if piece)


@dataclass(frozen=True)
class ClauseMatch:
    position_id: str
    topic: str
    score: float
    method: str = "tfidf"


class ClauseMatcher:
    """Fit-once / match-many TF-IDF clause matcher."""

    def __init__(
        self,
        min_score: float = 0.05,
        ngram_range: tuple[int, int] = (1, 2),
        max_features: int | None = 4096,
    ) -> None:
        self.min_score = float(min_score)
        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            token_pattern=_TOKEN_PATTERN.pattern,
            ngram_range=ngram_range,
            sublinear_tf=True,
            norm="l2",
            max_features=max_features,
        )
        self._matrix: csr_matrix | None = None
        self._positions: list[PlaybookPosition] = []
        self._fitted = False

    @property
    def vocabulary_size(self) -> int:
        if not self._fitted:
            return 0
        return len(self._vectorizer.vocabulary_)

    def fit(self, positions: Iterable[PlaybookPosition]) -> "ClauseMatcher":
        self._positions = list(positions)
        corpus = [_position_corpus_entry(position) for position in self._positions]
        if not corpus or not any(corpus):
            self._matrix = None
            self._fitted = False
            return self
        self._matrix = self._vectorizer.fit_transform(corpus)
        self._fitted = True
        return self

    def is_fitted(self) -> bool:
        return self._fitted and self._matrix is not None

    def transform(self, texts: Iterable[str]) -> csr_matrix:
        if not self.is_fitted():
            raise RuntimeError("ClauseMatcher must be fitted before transform()")
        return self._vectorizer.transform(list(texts))

    def match(self, clause_text: str, top_k: int = 3) -> list[ClauseMatch]:
        if not self.is_fitted() or not clause_text.strip():
            return []
        query = self._vectorizer.transform([clause_text])
        scores = cosine_similarity(query, self._matrix).ravel()
        order = np.argsort(scores)[::-1]
        hits: list[ClauseMatch] = []
        for idx in order[: max(top_k, 1)]:
            score = float(scores[int(idx)])
            if score < self.min_score:
                break
            position = self._positions[int(idx)]
            hits.append(
                ClauseMatch(
                    position_id=position.id,
                    topic=position.topic,
                    score=round(score, 4),
                )
            )
        return hits

    def best_match(self, clause_text: str) -> ClauseMatch | None:
        hits = self.match(clause_text, top_k=1)
        return hits[0] if hits else None
