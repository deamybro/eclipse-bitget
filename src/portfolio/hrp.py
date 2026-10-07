"""
src/portfolio/hrp.py - Hierarchical Risk Parity (HRP) Portfolio Allocator.
Implements correlation clustering, quasi-diagonalization, and recursive bisection (López de Prado 2016).
Does not rely on unstable covariance matrix inversion.
"""

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, to_tree


class HierarchicalRiskParity:
    """Computes robust risk-parity weights across strategy sleeves or assets."""

    @staticmethod
    def compute_distance_matrix(corr: np.ndarray) -> np.ndarray:
        """d_i,j = sqrt(0.5 * (1 - rho_i,j))"""
        return np.sqrt(np.clip(0.5 * (1.0 - corr), 0.0, 1.0))

    @staticmethod
    def quasi_diagonalize(link: np.ndarray) -> list[int]:
        """Sorts clustered items so similar items are placed consecutively."""
        tree = to_tree(link, rd=False)
        return tree.pre_order(lambda x: x.id)

    @staticmethod
    def get_cluster_variance(cov: np.ndarray, cluster_items: list[int]) -> float:
        """Computes variance of an inverse-variance weighted sub-cluster."""
        sub_cov = cov[np.ix_(cluster_items, cluster_items)]
        ivp = 1.0 / np.diag(sub_cov)
        ivp /= np.sum(ivp)
        return float(np.dot(np.dot(ivp, sub_cov), ivp))

    def allocate(self, returns_matrix: pd.DataFrame) -> dict[str, float]:
        """
        Computes HRP portfolio weights summing to 1.0.
        returns_matrix: DataFrame of sleeve returns (T periods x K sleeves).
        """
        cols = list(returns_matrix.columns)
        n = len(cols)
        if n == 1:
            return {cols[0]: 1.0}

        cov = returns_matrix.cov().values
        corr = returns_matrix.corr().fillna(0.0).values
        dist = self.compute_distance_matrix(corr)

        # 1. Tree Clustering
        from scipy.spatial.distance import squareform
        condensed_dist = squareform(dist, checks=False)
        link = linkage(condensed_dist, method="single")

        # 2. Quasi-Diagonalization
        sort_order = self.quasi_diagonalize(link)
        sorted_cols = [cols[i] for i in sort_order]

        # 3. Recursive Bisection
        weights = pd.Series(1.0, index=sort_order)
        clusters = [sort_order]

        while len(clusters) > 0:
            new_clusters = []
            for cluster in clusters:
                if len(cluster) > 1:
                    mid = len(cluster) // 2
                    c1 = cluster[:mid]
                    c2 = cluster[mid:]

                    var1 = self.get_cluster_variance(cov, c1)
                    var2 = self.get_cluster_variance(cov, c2)

                    alpha = 1.0 - var1 / (var1 + var2 + 1e-12)
                    weights[c1] *= alpha
                    weights[c2] *= (1.0 - alpha)

                    new_clusters.append(c1)
                    new_clusters.append(c2)
            clusters = new_clusters

        res = {cols[idx]: float(weights[idx]) for idx in range(n)}
        # Normalize sum to 1.0
        total_w = sum(res.values())
        return {k: v / total_w for k, v in res.items()}
