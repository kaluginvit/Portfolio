from __future__ import annotations

import math
import numpy as np
import pandas as pd
from scipy import stats

METRIC_COMPONENTS = {
    "cr_apply": ("applies", "impressions"),
    "ctr": ("clicks", "impressions"),
    "cr_home_apply": ("applies", "home_view"),
    "approval_rate": ("approvals", "applies"),
    "arpu": None,
}


def summarize_group_metrics(user_level: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for group, grp in user_level.groupby("ab_group"):
        totals = {
            "users": grp["client_id"].nunique(),
            "home_view_total": grp["home_view"].sum(),
            "impressions_total": grp["impressions"].sum(),
            "clicks_total": grp["clicks"].sum(),
            "applies_total": grp["applies"].sum(),
            "approvals_total": grp["approvals"].sum(),
            "revenue_total": grp["revenue"].sum(),
        }
        row = {"ab_group": group, **totals}
        for metric, components in METRIC_COMPONENTS.items():
            row[f"mean_{metric}"] = float(grp[metric].mean())
            row[f"var_{metric}"] = float(grp[metric].var(ddof=1))
            if components is None:
                row[f"group_{metric}"] = float(grp["revenue"].sum() / grp["client_id"].nunique())
            else:
                num, den = components
                den_sum = grp[den].sum()
                row[f"group_{metric}"] = float(grp[num].sum() / den_sum) if den_sum else 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def welch_test(control: pd.Series, treatment: pd.Series) -> tuple[float, float, tuple[float, float]]:
    x = control.astype(float).to_numpy()
    y = treatment.astype(float).to_numpy()
    stat, pvalue = stats.ttest_ind(y, x, equal_var=False, nan_policy="omit")
    mean_diff = float(np.nanmean(y) - np.nanmean(x))
    var_x = np.nanvar(x, ddof=1)
    var_y = np.nanvar(y, ddof=1)
    n_x = np.sum(~np.isnan(x))
    n_y = np.sum(~np.isnan(y))
    se = math.sqrt(var_x / n_x + var_y / n_y) if n_x > 1 and n_y > 1 else float("nan")
    df_num = (var_x / n_x + var_y / n_y) ** 2
    df_den = ((var_x / n_x) ** 2) / (n_x - 1) + ((var_y / n_y) ** 2) / (n_y - 1) if n_x > 1 and n_y > 1 else float("nan")
    dof = df_num / df_den if df_den else float("nan")
    t_crit = stats.t.ppf(0.975, df=dof) if not math.isnan(dof) else float("nan")
    ci = (mean_diff - t_crit * se, mean_diff + t_crit * se) if not math.isnan(t_crit) else (float("nan"), float("nan"))
    return float(stat), float(pvalue), (float(ci[0]), float(ci[1]))


def compare_groups(user_level: pd.DataFrame) -> pd.DataFrame:
    control = user_level[user_level["ab_group"] == "A_control"].copy()
    treatment = user_level[user_level["ab_group"] == "B_test"].copy()

    rows = []
    for metric in METRIC_COMPONENTS:
        stat, pvalue, ci = welch_test(control[metric], treatment[metric])
        control_mean = float(control[metric].mean())
        test_mean = float(treatment[metric].mean())
        diff = test_mean - control_mean
        uplift = diff / control_mean if control_mean else float("nan")
        rows.append(
            {
                "metric": metric,
                "is_primary": metric == "cr_apply",
                "control_mean": control_mean,
                "test_mean": test_mean,
                "absolute_diff": diff,
                "relative_uplift": uplift,
                "t_stat": stat,
                "p_value": pvalue,
                "ci_low": ci[0],
                "ci_high": ci[1],
                "significant_05": bool(pvalue < 0.05),
            }
        )
    return pd.DataFrame(rows)
