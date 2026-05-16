"""Load and expose tunable algorithm parameters from YAML."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .config import settings


def _resolve_path() -> Path:
    raw = os.environ.get("LOU_ALGORITHM_CONFIG_PATH") or settings.ALGORITHM_CONFIG_PATH
    return Path(raw)


@dataclass(frozen=True)
class ClauseMatchingConfig:
    min_score: float
    top_k: int
    ngram_range: tuple[int, int]
    max_features: int
    sublinear_tf: bool


@dataclass(frozen=True)
class VoiceMatchingConfig:
    threshold: float
    jaro_weight: float
    tfidf_weight: float
    edit_weight: float


@dataclass(frozen=True)
class RiskScoringConfig:
    prior_alpha: tuple[float, ...]
    levels: tuple[str, ...]


@dataclass(frozen=True)
class HmmLogisticConfig:
    w_begin: tuple[float, ...]
    b_begin: float
    b_inside: float
    first_paragraph_bias: float


@dataclass(frozen=True)
class HmmSectionDetectorConfig:
    init_inside: float
    init_begin: float
    transition_inside_to_inside: float
    transition_begin_to_begin: float
    logistic: HmmLogisticConfig


@dataclass(frozen=True)
class Bm25Config:
    k1: float
    b: float


@dataclass(frozen=True)
class SemanticSearchConfig:
    bm25: Bm25Config
    rrf_k: int


@dataclass(frozen=True)
class BrainConfig:
    cache_ttl_seconds: int


@dataclass(frozen=True)
class AlgorithmConfig:
    clause_matching: ClauseMatchingConfig
    voice_matching: VoiceMatchingConfig
    risk_scoring: RiskScoringConfig
    hmm_section_detector: HmmSectionDetectorConfig
    semantic_search: SemanticSearchConfig
    brain: BrainConfig
    source_path: Path = field(default_factory=Path)


def load_algorithm_config(path: Path | None = None) -> AlgorithmConfig:
    target = Path(path) if path is not None else _resolve_path()
    if not target.exists():
        raise RuntimeError(
            f"Missing algorithm config at {target}. Set LOU_ALGORITHM_CONFIG_PATH or restore the file."
        )
    with target.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    cm = raw["clause_matching"]
    vm = raw["voice_matching"]
    vmw = vm["weights"]
    rs = raw["risk_scoring"]
    hmm = raw["hmm_section_detector"]
    hmm_logistic = hmm["logistic"]
    sem = raw["semantic_search"]
    bm = sem["bm25"]
    brain = raw["brain"]

    return AlgorithmConfig(
        clause_matching=ClauseMatchingConfig(
            min_score=float(cm["min_score"]),
            top_k=int(cm["top_k"]),
            ngram_range=tuple(int(x) for x in cm["ngram_range"]),  # type: ignore[arg-type]
            max_features=int(cm["max_features"]),
            sublinear_tf=bool(cm["sublinear_tf"]),
        ),
        voice_matching=VoiceMatchingConfig(
            threshold=float(vm["threshold"]),
            jaro_weight=float(vmw["jaro_winkler"]),
            tfidf_weight=float(vmw["tfidf"]),
            edit_weight=float(vmw["edit"]),
        ),
        risk_scoring=RiskScoringConfig(
            prior_alpha=tuple(float(x) for x in rs["prior_alpha"]),
            levels=tuple(str(x) for x in rs["levels"]),
        ),
        hmm_section_detector=HmmSectionDetectorConfig(
            init_inside=float(hmm["init"]["inside"]),
            init_begin=float(hmm["init"]["begin"]),
            transition_inside_to_inside=float(hmm["transition"]["inside_to_inside"]),
            transition_begin_to_begin=float(hmm["transition"]["begin_to_begin"]),
            logistic=HmmLogisticConfig(
                w_begin=tuple(float(x) for x in hmm_logistic["w_begin"]),
                b_begin=float(hmm_logistic["b_begin"]),
                b_inside=float(hmm_logistic["b_inside"]),
                first_paragraph_bias=float(hmm_logistic["first_paragraph_bias"]),
            ),
        ),
        semantic_search=SemanticSearchConfig(
            bm25=Bm25Config(k1=float(bm["k1"]), b=float(bm["b"])),
            rrf_k=int(sem["rrf_k"]),
        ),
        brain=BrainConfig(cache_ttl_seconds=int(brain["cache_ttl_seconds"])),
        source_path=target,
    )


algorithm_config = load_algorithm_config()
