"""HMM section-boundary detector with Viterbi decoding in log-space.

Math
----
States:        S in {INSIDE = 0, BEGIN = 1}
Emission:      log P(features | state) via hand-calibrated logistic
               weights against a 7-dim feature vector.
Transition:    log A   = log [[a_ii, a_ib],
                             [a_bi, a_bb]]
Init:          log pi  = log [pi_inside, pi_begin]

Viterbi recursion in log-space (O(N * K**2)):
    log delta_t(i) = max_j [log delta_{t-1}(j) + log A_{j,i}] + log b_i(o_t)
    backpointer psi_t(i) = argmax_j [log delta_{t-1}(j) + log A_{j,i}]
    backtrack: y_T = argmax_i log delta_T(i), then y_{t-1} = psi_t(y_t)

Feature vector per paragraph (length 7):
    [relative_position, numbering_pattern_score, all_caps_ratio,
     avg_word_length_norm, log_word_count_norm,
     ends_with_colon, section_keyword_score]
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Sequence

import numpy as np


_NUMBERING_PATTERNS = [
    re.compile(r"^\s*\d+\.\s"),
    re.compile(r"^\s*\d+\.\d+\s"),
    re.compile(r"^\s*\(?[a-z]\)\s", re.IGNORECASE),
    re.compile(r"^\s*[IVX]+\.\s"),
    re.compile(r"^\s*Article\s+\d+", re.IGNORECASE),
    re.compile(r"^\s*Section\s+\d+", re.IGNORECASE),
    re.compile(r"^\s*Clause\s+\d+", re.IGNORECASE),
]
_SECTION_KEYWORDS = {
    "article", "section", "clause", "preamble", "recitals", "definitions",
    "confidentiality", "termination", "warranty", "indemnification",
    "limitation", "liability", "miscellaneous", "general",
}

_INSIDE = 0
_BEGIN = 1


@dataclass(frozen=True)
class Section:
    index: int
    start_paragraph: int
    end_paragraph: int
    title: str
    text: str


def _feature_vector(paragraph: str, position_ratio: float) -> np.ndarray:
    stripped = paragraph.strip()
    words = stripped.split()
    word_count = len(words)
    if word_count == 0:
        return np.zeros(7, dtype=float)

    numbering = max((1.0 for pattern in _NUMBERING_PATTERNS if pattern.match(stripped)), default=0.0)
    letters = [ch for ch in stripped if ch.isalpha()]
    all_caps_ratio = sum(1 for ch in letters if ch.isupper()) / len(letters) if letters else 0.0
    avg_word_len = sum(len(word) for word in words) / word_count
    avg_word_len_norm = min(avg_word_len / 12.0, 1.0)
    log_word_count_norm = math.log1p(word_count) / math.log1p(400)
    ends_with_colon = 1.0 if stripped.rstrip().endswith(":") else 0.0
    keyword_hits = sum(1 for word in words[:4] if word.strip().lower() in _SECTION_KEYWORDS)
    keyword_score = min(keyword_hits / 2.0, 1.0)

    return np.array(
        [
            float(position_ratio),
            float(numbering),
            float(all_caps_ratio),
            float(avg_word_len_norm),
            float(log_word_count_norm),
            float(ends_with_colon),
            float(keyword_score),
        ],
        dtype=float,
    )


_DEFAULT_W_BEGIN: tuple[float, ...] = (-0.2, 3.8, 1.6, 0.4, -0.8, 0.7, 2.1)
_DEFAULT_B_BEGIN: float = -1.4
_DEFAULT_B_INSIDE: float = 0.4
_DEFAULT_FIRST_PARAGRAPH_BIAS: float = 0.5


def _log_emission(
    features: np.ndarray,
    w_begin: np.ndarray,
    b_begin: float,
    w_inside: np.ndarray,
    b_inside: float,
) -> tuple[float, float]:
    """Return (log P(features | INSIDE), log P(features | BEGIN)) up to a normalising constant."""
    z_begin = float(features @ w_begin + b_begin)
    z_inside = float(features @ w_inside + b_inside)
    # Log-softmax for numerical stability.
    m = max(z_begin, z_inside)
    log_norm = m + math.log(math.exp(z_begin - m) + math.exp(z_inside - m))
    return z_inside - log_norm, z_begin - log_norm


@dataclass
class HMMSectionDetector:
    init_inside: float = 0.30
    init_begin: float = 0.70
    transition_inside_to_inside: float = 0.90
    transition_begin_to_begin: float = 0.70
    w_begin: tuple[float, ...] = _DEFAULT_W_BEGIN
    b_begin: float = _DEFAULT_B_BEGIN
    b_inside: float = _DEFAULT_B_INSIDE
    first_paragraph_bias: float = _DEFAULT_FIRST_PARAGRAPH_BIAS

    def _log_init(self) -> np.ndarray:
        return np.log(np.array([self.init_inside, self.init_begin], dtype=float))

    def _log_transition(self) -> np.ndarray:
        a_ii = self.transition_inside_to_inside
        a_ib = 1.0 - a_ii
        a_bb = self.transition_begin_to_begin
        a_bi = 1.0 - a_bb
        return np.log(np.array([[a_ii, a_ib], [a_bi, a_bb]], dtype=float))

    def decode(self, paragraphs: Sequence[str]) -> list[int]:
        n = len(paragraphs)
        if n == 0:
            return []
        if n == 1:
            return [_BEGIN]

        w_begin = np.array(self.w_begin, dtype=float)
        w_inside = -1.0 * w_begin
        emissions = np.zeros((n, 2), dtype=float)
        for index, paragraph in enumerate(paragraphs):
            ratio = index / max(n - 1, 1)
            features = _feature_vector(paragraph, ratio)
            emissions[index, _INSIDE], emissions[index, _BEGIN] = _log_emission(
                features, w_begin, self.b_begin, w_inside, self.b_inside,
            )

        log_init = self._log_init()
        log_trans = self._log_transition()

        delta = np.full((n, 2), -np.inf, dtype=float)
        psi = np.zeros((n, 2), dtype=int)

        delta[0] = log_init + emissions[0]
        delta[0, _BEGIN] += self.first_paragraph_bias  # mild bias: paragraph 0 is almost always a BEGIN

        for t in range(1, n):
            for current in (_INSIDE, _BEGIN):
                scores = delta[t - 1] + log_trans[:, current]
                psi[t, current] = int(np.argmax(scores))
                delta[t, current] = float(scores[psi[t, current]] + emissions[t, current])

        path = [0] * n
        path[-1] = int(np.argmax(delta[-1]))
        for t in range(n - 1, 0, -1):
            path[t - 1] = int(psi[t, path[t]])
        path[0] = _BEGIN  # first paragraph always begins a section
        return path

    def segment(self, paragraphs: Sequence[str]) -> list[Section]:
        path = self.decode(paragraphs)
        if not path:
            return []
        boundaries: list[int] = [index for index, state in enumerate(path) if state == _BEGIN]
        if not boundaries or boundaries[0] != 0:
            boundaries = [0, *boundaries]
        boundaries.append(len(paragraphs))

        sections: list[Section] = []
        for section_index, start in enumerate(boundaries[:-1], start=1):
            end = boundaries[section_index]
            chunk = [paragraph for paragraph in paragraphs[start:end] if paragraph.strip()]
            if not chunk:
                continue
            title = _derive_title(chunk[0], section_index)
            text = "\n\n".join(chunk)
            sections.append(
                Section(
                    index=section_index,
                    start_paragraph=start,
                    end_paragraph=end,
                    title=title,
                    text=text,
                )
            )
        if not sections and paragraphs:
            sections.append(
                Section(
                    index=1,
                    start_paragraph=0,
                    end_paragraph=len(paragraphs),
                    title="Section 1",
                    text="\n\n".join(paragraph for paragraph in paragraphs if paragraph.strip()),
                )
            )
        return sections


def _derive_title(first_paragraph: str, fallback_index: int) -> str:
    stripped = first_paragraph.strip()
    if not stripped:
        return f"Section {fallback_index}"
    head = stripped.split("\n", 1)[0].strip(" .;:-")
    words = head.split()
    if not words:
        return f"Section {fallback_index}"
    snippet = " ".join(words[:8])
    return snippet[:80]
