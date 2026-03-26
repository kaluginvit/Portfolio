from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


def load_events(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["dt"])
    df["offer_id"] = df["offer_id"].fillna("")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.sort_values(["dt", "client_id", "event_type"]).reset_index(drop=True)


def build_quality_checks(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    duplicate_rows = int(events.duplicated().sum())
    missing_group = int(events["ab_group"].isna().sum())
    bad_offer_rows = int(((events["event_type"] != "home_view") & (events["offer_id"] == "")).sum())
    bad_home_offer_rows = int(((events["event_type"] == "home_view") & (events["offer_id"] != "")).sum())
    revenue_nonpositive = int(((events["event_type"] == "revenue") & (events["value"].fillna(0) <= 0)).sum())

    quality = pd.DataFrame(
        [
            {"check_name": "duplicate_rows", "value": duplicate_rows},
            {"check_name": "missing_ab_group", "value": missing_group},
            {"check_name": "bad_offer_rows", "value": bad_offer_rows},
            {"check_name": "bad_home_offer_rows", "value": bad_home_offer_rows},
            {"check_name": "nonpositive_revenue_rows", "value": revenue_nonpositive},
            {"check_name": "unique_users", "value": int(events["client_id"].nunique())},
            {"check_name": "total_rows", "value": int(len(events))},
        ]
    )

    event_mix = (
        events.groupby(["ab_group", "event_type"], as_index=False)
        .size()
        .rename(columns={"size": "events"})
        .sort_values(["ab_group", "event_type"])
        .reset_index(drop=True)
    )
    event_mix["share_within_group"] = event_mix["events"] / event_mix.groupby("ab_group")["events"].transform("sum")

    day_split = (
        events.assign(dt_day=events["dt"].dt.date.astype(str))
        .groupby(["dt_day", "ab_group"], as_index=False)
        .size()
        .rename(columns={"size": "events"})
        .sort_values(["dt_day", "ab_group"])
        .reset_index(drop=True)
    )
    return quality, event_mix, day_split


def build_user_day_funnel(events: pd.DataFrame) -> pd.DataFrame:
    df = events.copy()
    df["dt_day"] = df["dt"].dt.date.astype(str)

    grouped = (
        df.groupby(["dt_day", "client_id", "ab_group", "event_type"], as_index=False)
        .agg(
            event_count=("event_type", "size"),
            revenue_value=("value", lambda s: float(pd.to_numeric(s, errors="coerce").fillna(0).sum())),
        )
    )

    counts = grouped.loc[grouped["event_type"] != "revenue"].pivot_table(
        index=["dt_day", "client_id", "ab_group"],
        columns="event_type",
        values="event_count",
        fill_value=0,
        aggfunc="sum",
    )
    counts.columns.name = None
    counts = counts.reset_index()

    revenue = (
        grouped.loc[grouped["event_type"] == "revenue", ["dt_day", "client_id", "ab_group", "revenue_value"]]
        .rename(columns={"revenue_value": "revenue"})
    )

    funnel = counts.merge(revenue, on=["dt_day", "client_id", "ab_group"], how="left")
    funnel["revenue"] = funnel["revenue"].fillna(0.0)

    rename_map = {
        "offer_impression": "impressions",
        "offer_click": "clicks",
        "offer_apply": "applies",
        "offer_approved": "approvals",
    }
    funnel = funnel.rename(columns=rename_map)

    for column in ["home_view", "impressions", "clicks", "applies", "approvals"]:
        if column not in funnel.columns:
            funnel[column] = 0

    cols = ["dt_day", "client_id", "ab_group", "home_view", "impressions", "clicks", "applies", "approvals", "revenue"]
    return funnel[cols].sort_values(["dt_day", "client_id"]).reset_index(drop=True)


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    numerator = numerator.astype(float)
    denominator = denominator.astype(float)
    return pd.Series(
        np.divide(
            numerator,
            denominator,
            out=np.zeros(len(numerator), dtype=float),
            where=denominator > 0,
        )
    )


def build_user_level_metrics(user_day_funnel: pd.DataFrame) -> pd.DataFrame:
    user_level = (
        user_day_funnel.groupby(["client_id", "ab_group"], as_index=False)
        .agg(
            home_view=("home_view", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            applies=("applies", "sum"),
            approvals=("approvals", "sum"),
            revenue=("revenue", "sum"),
        )
    )

    user_level["ctr"] = _safe_ratio(user_level["clicks"], user_level["impressions"])
    user_level["cr_apply"] = _safe_ratio(user_level["applies"], user_level["impressions"])
    user_level["cr_home_apply"] = _safe_ratio(user_level["applies"], user_level["home_view"])
    user_level["approval_rate"] = _safe_ratio(user_level["approvals"], user_level["applies"])
    user_level["arpu"] = user_level["revenue"].astype(float)
    return user_level.sort_values(["ab_group", "client_id"]).reset_index(drop=True)
