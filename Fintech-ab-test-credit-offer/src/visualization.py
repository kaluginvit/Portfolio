from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def _save(path: str | Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=140, bbox_inches="tight")
    plt.close()


def save_metric_bars(comparison: pd.DataFrame, path: str | Path) -> None:
    df = comparison.copy()
    plt.figure(figsize=(10, 5))
    plt.bar(df["metric"], df["relative_uplift"] * 100)
    plt.axhline(0, linewidth=1)
    plt.ylabel("Relative uplift, %")
    plt.title("Metric uplift: B_test vs A_control")
    _save(path)


def save_funnel_chart(group_summary: pd.DataFrame, path: str | Path) -> None:
    df = group_summary[["ab_group", "home_view_total", "impressions_total", "clicks_total", "applies_total", "approvals_total"]].copy()
    steps = ["home_view_total", "impressions_total", "clicks_total", "applies_total", "approvals_total"]

    plt.figure(figsize=(10, 6))
    for _, row in df.iterrows():
        plt.plot(steps, [row[s] for s in steps], marker="o", label=row["ab_group"])
    plt.ylabel("Total events")
    plt.title("Funnel by A/B group")
    plt.legend()
    _save(path)


def save_mde_curve(mde_grid: pd.DataFrame, path: str | Path) -> None:
    plt.figure(figsize=(10, 5))
    plt.plot(mde_grid["sample_size_per_group"], mde_grid["mde_relative_pct"])
    plt.axhline(2.5, linestyle="--", linewidth=1)
    plt.xlabel("Sample size per group")
    plt.ylabel("Relative MDE, %")
    plt.title("MDE curve for CR_apply")
    _save(path)


def save_boxplot(user_level: pd.DataFrame, metric: str, path: str | Path) -> None:
    groups = [g[metric].astype(float).values for _, g in user_level.groupby("ab_group")]
    labels = [name for name, _ in user_level.groupby("ab_group")]
    plt.figure(figsize=(7, 5))
    plt.boxplot(groups, tick_labels=labels, showfliers=False)
    plt.ylabel(metric)
    plt.title(f"{metric} distribution by group")
    _save(path)


def save_event_mix(event_mix: pd.DataFrame, path: str | Path) -> None:
    pivot = event_mix.pivot(index="event_type", columns="ab_group", values="share_within_group").fillna(0)
    pivot.plot(kind="bar", figsize=(10, 5))
    plt.ylabel("Share within group")
    plt.title("Event mix by group")
    _save(path)
