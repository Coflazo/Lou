"""BM25 (Okapi) lexical search, optional OpenAI dense embeddings, and RRF fusion.

Math
----
BM25(D, Q) = sum_{t in Q} IDF(t) * (f(t,D) * (k1 + 1)) / (f(t,D) + k1 * (1 - b + b * |D| / avgdl))
    IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)

Dense embedding cosine (L2-normalised text-embedding-3-small vectors):
    sim(q, d) = q . d

Reciprocal-rank fusion:
    score(d) = sum over rankers r of  1 / (60 + rank_r(d))

The embeddings path is only taken when an OpenAI API key is available; if not,
the engine returns BM25 results directly. RRF fusion makes the lexical and
semantic signals comparable without requiring score calibration.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from rank_bm25 import BM25Okapi

from ..provider_keys import current_openai_key


_TOKEN_PATTERN = re.compile(r"(?u)\b[a-z][a-z-]{2,}\b")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


@dataclass(frozen=True)
class SearchHit:
    document_id: str
    score: float
    method: str


class SemanticSearchEngine:
    def __init__(
        self,
        documents: Sequence[tuple[str, str]],
        k1: float = 1.5,
        b: float = 0.75,
        embedding_model: str = "text-embedding-3-small",
        openai_api_key: str | None = None,
    ) -> None:
        self.documents = list(documents)
        self._ids = [doc_id for doc_id, _ in self.documents]
        self._texts = [text for _, text in self.documents]
        tokenized = [_tokenize(text) for text in self._texts]
        self._bm25 = BM25Okapi(tokenized, k1=k1, b=b) if any(tokenized) else None
        self._embedding_model = embedding_model
        self._openai_key = openai_api_key or current_openai_key() or os.getenv("OPENAI_API_KEY")
        self._doc_embeddings: np.ndarray | None = None

    def _ensure_embeddings(self) -> None:
        if self._doc_embeddings is not None or not self._openai_key:
            return
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self._openai_key)
            response = client.embeddings.create(
                model=self._embedding_model,
                input=self._texts,
            )
            vectors = np.asarray([entry.embedding for entry in response.data], dtype=float)
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self._doc_embeddings = vectors / norms
        except Exception:
            self._doc_embeddings = None

    def _bm25_ranking(self, query: str) -> list[tuple[str, float]]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        order = np.argsort(scores)[::-1]
        return [(self._ids[int(idx)], float(scores[int(idx)])) for idx in order]

    def _embedding_ranking(self, query: str) -> list[tuple[str, float]]:
        self._ensure_embeddings()
        if self._doc_embeddings is None or not self._openai_key:
            return []
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self._openai_key)
            response = client.embeddings.create(model=self._embedding_model, input=[query])
            vector = np.asarray(response.data[0].embedding, dtype=float)
            norm = float(np.linalg.norm(vector))
            if norm == 0:
                return []
            vector = vector / norm
            scores = self._doc_embeddings @ vector
            order = np.argsort(scores)[::-1]
            return [(self._ids[int(idx)], float(scores[int(idx)])) for idx in order]
        except Exception:
            return []

    @staticmethod
    def _rrf(rankings: Iterable[list[tuple[str, float]]], k: int = 60) -> dict[str, float]:
        merged: dict[str, float] = {}
        for ranking in rankings:
            for rank, (doc_id, _score) in enumerate(ranking):
                merged[doc_id] = merged.get(doc_id, 0.0) + 1.0 / (k + rank)
        return merged

    def search(self, query: str, top_k: int = 10) -> list[SearchHit]:
        bm25_ranking = self._bm25_ranking(query)
        embedding_ranking = self._embedding_ranking(query)
        if not embedding_ranking:
            return [
                SearchHit(document_id=doc_id, score=round(score, 4), method="bm25")
                for doc_id, score in bm25_ranking[:top_k]
            ]
        fused = self._rrf([bm25_ranking, embedding_ranking])
        order = sorted(fused.items(), key=lambda item: item[1], reverse=True)
        return [
            SearchHit(document_id=doc_id, score=round(score, 4), method="rrf")
            for doc_id, score in order[:top_k]
        ]
