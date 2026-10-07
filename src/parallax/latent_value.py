"""
src/parallax/latent_value.py - State-Space Kalman Filter for Latent Fair Price.
Tracks unobservable latent log fair value x_t across rToken, Perpetual, and Native markets,
with session-dependent measurement variances and stale observation variance inflation.
"""

import numpy as np


class KalmanLatentPriceFilter:
    """
    1D State-Space Kalman Filter:
    State: x_t = latent log fair price
    Evolution: x_t = x_{t-1} + w_t, w_t ~ N(0, Q)
    Observations: y_i,t = x_t + v_i,t, v_i,t ~ N(0, R_i,t)
    """

    def __init__(
        self,
        process_variance_q: float = 1e-5,
        base_spot_variance_r: float = 1e-4,
        base_perp_variance_r: float = 5e-5,
        stale_inflation_rate: float = 0.25
    ):
        self.q = process_variance_q
        self.base_spot_r = base_spot_variance_r
        self.base_perp_r = base_perp_variance_r
        self.stale_inflation_rate = stale_inflation_rate

        self.x = None  # Estimated latent state
        self.p = 1e-3  # Estimation error variance

    def initialize(self, initial_price: float):
        self.x = float(np.log(initial_price))
        self.p = 1e-3

    def step(
        self,
        spot_price: float,
        perp_price: float,
        is_us_open: bool,
        reference_age_seconds: float = 0.0
    ) -> dict:
        """
        Executes one prediction-update cycle of the Kalman filter.
        Returns estimated latent log fair price, confidence intervals, and residuals.
        """
        log_spot = np.log(spot_price)
        log_perp = np.log(perp_price)

        if self.x is None:
            self.initialize((spot_price + perp_price) / 2.0)

        # 1. TIME UPDATE (PREDICT)
        x_pred = self.x
        p_pred = self.p + self.q

        # 2. MEASUREMENT NOISE MATRIX (R)
        r_spot = self.base_spot_r
        r_perp = self.base_perp_r

        # Inflate variance if underlying market is closed or stale
        if not is_us_open:
            hours_elapsed = reference_age_seconds / 3600.0
            inflation = 1.0 + self.stale_inflation_rate * (hours_elapsed ** 0.5)
            r_spot *= inflation
            r_perp *= 1.15  # Futures continue trading, modest inflation

        # 3. MEASUREMENT UPDATE (FUSE MULTI-VENUE OBSERVATIONS)
        # Combine spot and perp into optimal scalar measurement
        # Inverse-variance weighting
        w_spot = 1.0 / r_spot
        w_perp = 1.0 / r_perp
        w_total = w_spot + w_perp
        
        y_fused = (w_spot * log_spot + w_perp * log_perp) / w_total
        r_fused = 1.0 / w_total

        # Kalman Gain
        k = p_pred / (p_pred + r_fused)
        
        # State Update
        self.x = x_pred + k * (y_fused - x_pred)
        self.p = (1.0 - k) * p_pred

        fair_price = float(np.exp(self.x))
        std_err = float(np.sqrt(self.p))
        
        lower_fair = float(np.exp(self.x - 1.96 * std_err))
        upper_fair = float(np.exp(self.x + 1.96 * std_err))

        spot_residual_bps = float((log_spot - self.x) * 10000.0)
        perp_residual_bps = float((log_perp - self.x) * 10000.0)

        return {
            "fair_price": fair_price,
            "latent_x": float(self.x),
            "estimation_std_err": std_err,
            "fair_price_lower": lower_fair,
            "fair_price_upper": upper_fair,
            "spot_residual_bps": spot_residual_bps,
            "perp_residual_bps": perp_residual_bps,
            "k_gain": float(k)
        }
