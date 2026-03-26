from __future__ import annotations

import math
import numpy as np
import pandas as pd
from scipy import stats


def var_ratio(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mean_x = np.mean(x)
    mean_y = np.mean(y)
    if mean_y == 0:
        return float("nan")
    var_x = np.var(x, ddof=1)
    var_y = np.var(y, ddof=1)
    cov_xy = np.cov(x, y, ddof=1)[0, 1]
    return float(var_x / mean_y**2 + var_y * mean_x**2 / mean_y**4 - 2 * mean_x * cov_xy / mean_y**3)


def get_mde(mu: float, std: float, sample_size: int, n_groups: int = 2, target_share: float = 0.5, r: float = 1.0, alpha: float = 0.05, beta: float = 0.2) -> tuple[float, float]:
    t_alpha = stats.norm.ppf(1 - alpha / 2)
    t_beta = stats.norm.ppf(1 - beta)
    sample_ratio_correction = r + 2 + 1 / r
    denominator = math.sqrt(sample_size * (1 - target_share * (n_groups - 1)))
    mde = math.sqrt(sample_ratio_correction) * (t_alpha + t_beta) * std / denominator
    relative = (mde * 100 / mu) if mu else float("nan")
    return float(mde), float(relative)


def build_mde_grid(mu: float, std: float, sample_sizes: list[int] | np.ndarray, alpha: float = 0.05, beta: float = 0.2) -> pd.DataFrame:
    rows = []
    for n in sample_sizes:
        abs_mde, rel_mde = get_mde(mu=mu, std=std, sample_size=int(n), alpha=alpha, beta=beta)
        rows.append({"sample_size_per_group": int(n), "mde_absolute": abs_mde, "mde_relative_pct": rel_mde})
    return pd.DataFrame(rows)


def minimal_sample_for_relative_mde(mu: float, std: float, target_relative_mde_pct: float, alpha: float = 0.05, beta: float = 0.2, max_n: int = 2_000_000) -> int | None:
    for n in range(100, max_n + 1, 100):
        _, rel_mde = get_mde(mu=mu, std=std, sample_size=n, alpha=alpha, beta=beta)
        if rel_mde <= target_relative_mde_pct:
            return n
    return None
