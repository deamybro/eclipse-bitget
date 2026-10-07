"""
src/credibility/pbo.py - Probability of Backtest Overfitting (PBO) Engine.
Implements Combinatorial Purged Cross-Validation (CSCV) methodology:
PBO = P(OOS Rank of Best IS Strategy < Median Rank).
"""

from itertools import combinations
import numpy as np
import pandas as pd


def compute_cscv_pbo(matrix_returns: np.ndarray, n_slices: int = 8) -> float:
    """
    matrix_returns: (T, N) where T is time periods and N is number of candidate strategy variants.
    n_slices: Number of temporal slices to split T into (e.g. 8 or 10).
    Returns PBO in [0.0, 1.0]. Lower is better (PBO < 0.25 indicates low overfitting risk).
    """
    t, n = matrix_returns.shape
    if t < n_slices * 4 or n < 2:
        return 0.5  # Insufficient dimensions for CSCV

    slice_size = t // n_slices
    slices = [matrix_returns[i * slice_size : (i + 1) * slice_size] for i in range(n_slices)]

    half_slices = n_slices // 2
    combos = list(combinations(range(n_slices), half_slices))

    below_median_count = 0
    total_evaluations = len(combos)

    for train_indices in combos:
        test_indices = [i for i in range(n_slices) if i not in train_indices]

        # Stack train and test subsets
        train_mat = np.vstack([slices[i] for i in train_indices])
        test_mat = np.vstack([slices[i] for i in test_indices])

        # Compute annualized Sharpe for each candidate in IS train
        is_means = np.mean(train_mat, axis=0)
        is_stds = np.std(train_mat, axis=0) + 1e-8
        is_sharpes = is_means / is_stds

        # Find best IS strategy index
        best_is_idx = int(np.argmax(is_sharpes))

        # Compute OOS Sharpes for all candidates in test
        oos_means = np.mean(test_mat, axis=0)
        oos_stds = np.std(test_mat, axis=0) + 1e-8
        oos_sharpes = oos_means / oos_stds

        # Compute rank of best_is_idx in OOS
        sorted_ranks = np.argsort(oos_sharpes)
        relative_rank = np.where(sorted_ranks == best_is_idx)[0][0] / float(n)

        # If best IS strategy falls below median OOS, count as overfitting
        if relative_rank < 0.5:
            below_median_count += 1

    pbo = float(below_median_count / total_evaluations) if total_evaluations > 0 else 0.5
    return pbo
