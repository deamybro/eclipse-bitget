"""
src/shockwave/factor_model.py - Dynamic Rolling Ridge Factor Model.
Decomposes rToken returns into systematic equity, crypto risk, and idiosyncratic residuals:
R_rtoken,t = beta_perp * R_perp,t + beta_btc * R_btc,t + beta_eth * R_eth,t + epsilon_t
"""

import numpy as np
from sklearn.linear_model import Ridge


class DynamicRollingFactorModel:
    """Estimates causal dynamic betas over rolling windows without future lookahead."""

    def __init__(self, window_size: int = 72, ridge_alpha: float = 1.0):
        self.window_size = window_size
        self.ridge_alpha = ridge_alpha
        self.history = []

    def update(
        self,
        rtoken_return: float,
        perp_return: float,
        btc_return: float,
        eth_return: float
    ) -> dict:
        """
        Appends new bar returns, updates rolling ridge regression,
        and computes factor-predicted return and idiosyncratic residual.
        """
        self.history.append({
            "y": rtoken_return,
            "x_perp": perp_return,
            "x_btc": btc_return,
            "x_eth": eth_return
        })

        if len(self.history) > self.window_size:
            self.history.pop(0)

        if len(self.history) < 24:
            # Insufficient warm-up history
            return {
                "predicted_return": 0.0,
                "residual": 0.0,
                "betas": {"perp": 1.0, "btc": 0.0, "eth": 0.0},
                "r2": 0.0,
                "sample_count": len(self.history)
            }

        # Build X and y arrays from past history (strictly up to current bar)
        y = np.array([row["y"] for row in self.history])
        X = np.array([[row["x_perp"], row["x_btc"], row["x_eth"]] for row in self.history])

        # Fit causal rolling ridge
        model = Ridge(alpha=self.ridge_alpha, fit_intercept=False)
        model.fit(X, y)

        current_x = np.array([[perp_return, btc_return, eth_return]])
        pred = float(model.predict(current_x)[0])
        residual = float(rtoken_return - pred)

        return {
            "predicted_return": pred,
            "residual": residual,
            "betas": {
                "perp": float(model.coef_[0]),
                "btc": float(model.coef_[1]),
                "eth": float(model.coef_[2])
            },
            "r2": float(model.score(X, y)),
            "sample_count": len(self.history)
        }
