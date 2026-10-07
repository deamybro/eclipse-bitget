"""
src/credibility/deflated_sharpe.py - Bailey & López de Prado Deflated Sharpe Ratio.
Calculates DSR to adjust for selection bias, multiple testing, non-normality,
and sample length: DSR = P(SR* <= SR | N, skew, kurt, T).
"""

import numpy as np
from scipy.stats import norm


def compute_expected_max_sharpe(n_trials: int, variance_sharpes: float) -> float:
    """
    Computes expected maximum Sharpe ratio under the null hypothesis of no alpha,
    given N independent/correlated trials and their Sharpe variance:
    E[max_N] ~ sqrt(V) * ((1 - euler) * Z^-1(1 - 1/N) + euler * Z^-1(1 - 1/(N*e)))
    """
    if n_trials <= 1 or variance_sharpes <= 1e-8:
        return 0.0

    euler_gamma = 0.57721566490153286
    z1 = norm.ppf(1.0 - 1.0 / n_trials)
    z2 = norm.ppf(1.0 - 1.0 / (n_trials * np.e))
    exp_max = np.sqrt(variance_sharpes) * ((1.0 - euler_gamma) * z1 + euler_gamma * z2)
    return float(max(0.0, exp_max))


def compute_deflated_sharpe_ratio(
    observed_sharpe: float,
    sample_length: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    n_trials: int = 1,
    variance_sharpes: float = 0.0
) -> float:
    """
    Computes Deflated Sharpe Ratio (DSR) in [0.0, 1.0].
    Values > 0.95 indicate statistical credibility after correcting for multiple testing.
    """
    if sample_length <= 2:
        return 0.0

    # 1. Benchmark Sharpe from multiple testing
    sr_star = compute_expected_max_sharpe(n_trials, variance_sharpes)

    # 2. Standard error under non-normality (Mertens 2002 / Lo 2002)
    # sigma_SR = sqrt((1 - skew*SR + (kurt - 1)/4 * SR^2) / (T - 1))
    sr = observed_sharpe
    sr_var = (1.0 - skewness * sr + ((kurtosis - 1.0) / 4.0) * (sr ** 2)) / max(1, sample_length - 1)
    
    if sr_var <= 1e-12:
        return 0.5

    sr_std = np.sqrt(sr_var)
    z_stat = (sr - sr_star) / sr_std
    dsr = float(norm.cdf(z_stat))
    return dsr
