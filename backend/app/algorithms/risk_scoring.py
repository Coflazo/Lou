"""Bayesian risk scoring via the Dirichlet-Categorical posterior.

Math
----
Prior:          pi ~ Dirichlet(alpha),   alpha = [a_L, a_M, a_H]
Likelihood:     each finding contributes a soft count w_k in {0..1}
                where w_k is the cosine match score that gated the assignment.
Posterior:      pi | data ~ Dirichlet(alpha + n . w)
Posterior mean: E[pi_k | data] = (alpha_k + sum_k(w_k)) / sum_j(alpha_j + sum_j(w_j))
Marginal CI:    pi_k | data ~ Beta(alpha_k_post, sum_{j != k} alpha_j_post)
                95% credible interval via scipy.stats.beta.ppf.

Reporting matching uncertainty as a prior weight lets us propagate uncertainty
from the upstream clause matcher into the dominant-risk verdict and into the
credible-interval widths the UI uses as confidence bars.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np
from scipy.stats import beta as beta_dist


@dataclass(frozen=True)
class RiskObservation:
    risk_label: str
    weight: float


@dataclass
class RiskPosterior:
    levels: list[str]
    mean: list[float]
    dominant: str
    credible_intervals: dict[str, tuple[float, float]]
    effective_n: float
    alpha_posterior: list[float]
    alpha_prior: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "levels": self.levels,
            "mean": [round(value, 4) for value in self.mean],
            "dominant": self.dominant,
            "credible_intervals": {
                key: (round(low, 4), round(high, 4))
                for key, (low, high) in self.credible_intervals.items()
            },
            "effective_n": round(self.effective_n, 4),
            "alpha_posterior": [round(value, 4) for value in self.alpha_posterior],
            "alpha_prior": [round(value, 4) for value in self.alpha_prior],
        }


class BayesianRiskScorer:
    def __init__(
        self,
        levels: Sequence[str] = ("Low", "Medium", "High"),
        prior_alpha: Sequence[float] = (2.0, 2.0, 2.0),
        credible_mass: float = 0.95,
    ) -> None:
        if len(levels) != len(prior_alpha):
            raise ValueError("levels and prior_alpha must have the same length")
        self.levels = list(levels)
        self.prior_alpha = np.asarray(prior_alpha, dtype=float)
        if (self.prior_alpha <= 0).any():
            raise ValueError("Dirichlet prior alpha entries must be positive")
        self.credible_mass = float(credible_mass)
        self._level_to_index = {label.lower(): index for index, label in enumerate(self.levels)}

    def score(self, observations: Iterable[RiskObservation]) -> RiskPosterior:
        counts = np.zeros_like(self.prior_alpha)
        for observation in observations:
            index = self._level_to_index.get(observation.risk_label.lower())
            if index is None:
                continue
            weight = max(0.0, min(1.0, float(observation.weight)))
            counts[index] += weight
        alpha_post = self.prior_alpha + counts
        total = float(alpha_post.sum())
        mean = (alpha_post / total).tolist()

        lower_q = (1.0 - self.credible_mass) / 2.0
        upper_q = 1.0 - lower_q
        credible: dict[str, tuple[float, float]] = {}
        for index, label in enumerate(self.levels):
            a = float(alpha_post[index])
            b = float(alpha_post.sum() - alpha_post[index])
            low = float(beta_dist.ppf(lower_q, a, b)) if b > 0 else 0.0
            high = float(beta_dist.ppf(upper_q, a, b)) if b > 0 else 1.0
            credible[label] = (low, high)

        dominant = self.levels[int(np.argmax(mean))]
        return RiskPosterior(
            levels=list(self.levels),
            mean=mean,
            dominant=dominant,
            credible_intervals=credible,
            effective_n=float(counts.sum()),
            alpha_posterior=alpha_post.tolist(),
            alpha_prior=self.prior_alpha.tolist(),
        )
