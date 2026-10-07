"""
src/regimes/hmm.py - Gaussian Hidden Markov Model for Market Regimes.
Fitted strictly on In-Sample training history with 3 distinct economic states:
State 0: Low-Vol Dispersion (Favorable for PARALLAX)
State 1: Directional Trending / High-Vol (Favorable for SHOCKWAVE)
State 2: Stable Basis Carry (Favorable for CARRY)
"""

import numpy as np
from hmmlearn.hmm import GaussianHMM


class MarketRegimeHMM:
    """3-State Gaussian HMM fitted strictly on training data."""

    def __init__(self, n_states: int = 3, random_state: int = 42):
        self.n_states = n_states
        self.model = GaussianHMM(
            n_components=n_states,
            covariance_type="diag",
            n_iter=200,
            random_state=random_state
        )
        self.is_fitted = False
        self.state_names = {
            0: "Low-Vol Dispersion",
            1: "High-Vol Dislocation",
            2: "Stable Basis Carry"
        }

    def fit(self, feature_matrix: np.ndarray):
        """
        Fits HMM strictly on In-Sample training observations.
        feature_matrix: (T, K) e.g. [realized_vol, btc_vol, abs_basis, funding_rate]
        """
        self.model.fit(feature_matrix)
        self.is_fitted = True

        # Inspect state means to assign human-interpretable labels
        means = self.model.means_
        # Sort states by volatility feature (column 0)
        vol_order = np.argsort(means[:, 0])
        self.state_names[int(vol_order[0])] = "Low-Vol Dispersion"
        self.state_names[int(vol_order[1])] = "Stable Basis Carry"
        self.state_names[int(vol_order[2])] = "High-Vol Dislocation"

    def predict_in_sample(self, feature_matrix: np.ndarray) -> np.ndarray:
        return self.model.predict(feature_matrix)
