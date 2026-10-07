"""
src/regimes/online_filter.py - Strict Causal Forward Filtering Engine.
Computes online state probabilities P(S_t = j | y_1:t) at timestamp t
using only past and current observations. NEVER uses backward smoothed posteriors.
"""

from typing import Dict, Any
from datetime import datetime
import numpy as np
from scipy.stats import norm
from src.contracts import RegimeState, DataQuality
from src.regimes.hmm import MarketRegimeHMM


class CausalRegimeFilter:
    """Computes online causal forward probabilities without future lookahead."""

    def __init__(self, fitted_hmm: MarketRegimeHMM):
        self.hmm = fitted_hmm
        self.n_states = fitted_hmm.n_states
        
        # State transition matrix A and stationary initial distribution pi
        self.trans_mat = fitted_hmm.model.transmat_
        self.start_prob = fitted_hmm.model.startprob_
        self.means = fitted_hmm.model.means_
        self.covars = fitted_hmm.model.covars_  # diagonal covariances

        # Initialize forward variable alpha_0
        self.current_alpha = np.copy(self.start_prob)

    def _emission_prob(self, x: np.ndarray, state_idx: int) -> float:
        """Computes Gaussian emission density P(x | S = state_idx) under diagonal covariance."""
        mean = self.means[state_idx]
        var = self.covars[state_idx]
        std = np.sqrt(np.maximum(1e-8, var))
        prob = np.prod(norm.pdf(x, loc=mean, scale=std))
        return float(max(1e-12, prob))

    def step(self, current_features: np.ndarray, timestamp_utc: datetime) -> RegimeState:
        """
        Executes one forward filtering step:
        alpha_t(j) = P(x_t | S_t = j) * sum_i [alpha_{t-1}(i) * A_{i, j}]
        """
        x = np.asarray(current_features, dtype=float)
        
        # Prediction step
        prior = np.dot(self.current_alpha, self.trans_mat)
        
        # Update step with current emission
        emissions = np.array([self._emission_prob(x, j) for j in range(self.n_states)])
        unnorm_alpha = prior * emissions
        
        # Normalization
        denom = np.sum(unnorm_alpha)
        if denom > 1e-12:
            self.current_alpha = unnorm_alpha / denom
        else:
            self.current_alpha = prior / np.sum(prior)

        active_state = int(np.argmax(self.current_alpha))
        probs_dict = {
            self.hmm.state_names[j]: float(self.current_alpha[j])
            for j in range(self.n_states)
        }

        return RegimeState(
            timestamp_utc=timestamp_utc,
            regime_id=active_state,
            regime_name=self.hmm.state_names[active_state],
            probabilities=probs_dict,
            structural_break_detected=False,
            break_metric=0.0,
            quality=DataQuality.DERIVED
        )
