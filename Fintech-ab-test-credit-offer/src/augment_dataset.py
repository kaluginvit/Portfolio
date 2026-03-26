from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

TARGET_ROWS = 20_000
TARGET_USERS_PER_GROUP = 5_000
SEED = 42
OUTPUT_NAME = "data_raw_fintech_credit_offer_20000.csv"


def _prepare_templates(seed_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    templates = []
    for group, grp in seed_df.groupby("ab_group"):
        for _, user_df in grp.sort_values("dt").groupby("client_id"):
            t = user_df.sort_values("dt").copy()
            t["dt_offset_sec"] = (t["dt"] - t["dt"].min()).dt.total_seconds().astype(int)
            templates.append(
                pd.DataFrame(
                    {
                        "template_group": [group],
                        "template_client_id": [int(user_df["client_id"].iloc[0])],
                        "template_len": [len(t)],
                        "payload": [t[["event_type", "offer_id", "value", "dt_offset_sec", "dt"]].reset_index(drop=True)],
                    }
                )
            )
    template_df = pd.concat(templates, ignore_index=True)
    return {group: template_df[template_df["template_group"] == group].reset_index(drop=True) for group in template_df["template_group"].unique()}


def _adjust_to_target_lengths(lengths: np.ndarray, options: np.ndarray, target_rows: int, rng: np.random.Generator) -> np.ndarray:
    total = int(lengths.sum())
    for _ in range(100_000):
        diff = target_rows - total
        if diff == 0:
            return lengths
        if diff > 0:
            candidates = np.where(lengths < options.max())[0]
            idx = int(rng.choice(candidates))
            bigger = options[options > lengths[idx]]
            replacement = int(bigger[np.argmin(np.abs(bigger - (lengths[idx] + diff)))])
        else:
            candidates = np.where(lengths > options.min())[0]
            idx = int(rng.choice(candidates))
            smaller = options[options < lengths[idx]]
            replacement = int(smaller[np.argmin(np.abs(smaller - (lengths[idx] + diff)))])
        total += replacement - int(lengths[idx])
        lengths[idx] = replacement
    raise ValueError(f"Could not adjust lengths to target_rows={target_rows}; got {int(lengths.sum())}")


def _select_templates_exact_rows(group_templates: pd.DataFrame, target_users: int, target_rows: int, rng: np.random.Generator) -> pd.DataFrame:
    length_probs = group_templates["template_len"].value_counts(normalize=True).sort_index()
    sampled_lengths = rng.choice(length_probs.index.to_numpy(), size=target_users, replace=True, p=length_probs.to_numpy())
    sampled_lengths = _adjust_to_target_lengths(sampled_lengths.astype(int), group_templates["template_len"].unique(), target_rows, rng)

    selected = []
    for template_len in sampled_lengths:
        candidates = group_templates[group_templates["template_len"] == int(template_len)]
        chosen = candidates.iloc[int(rng.integers(0, len(candidates)))]
        selected.append(chosen)
    return pd.DataFrame(selected).reset_index(drop=True)


def _instantiate_templates(selected: pd.DataFrame, start_client_id: int, rng: np.random.Generator) -> pd.DataFrame:
    parts = []
    next_client_id = start_client_id
    for _, row in selected.iterrows():
        payload = row["payload"].copy()
        jitter = int(rng.integers(-120, 121))
        payload["dt"] = payload["dt"].min() + pd.to_timedelta(jitter, unit="s") + pd.to_timedelta(payload["dt_offset_sec"], unit="s")
        payload["client_id"] = next_client_id
        payload["ab_group"] = row["template_group"]
        payload = payload[["dt", "client_id", "ab_group", "event_type", "offer_id", "value"]]
        parts.append(payload)
        next_client_id += 1
    return pd.concat(parts, ignore_index=True)


def build_validation(seed_df: pd.DataFrame, expanded_df: pd.DataFrame) -> pd.DataFrame:
    def summarize(df: pd.DataFrame, label: str) -> pd.DataFrame:
        rows = []
        for group, grp in df.groupby("ab_group"):
            per_user = grp.groupby("client_id").size()
            event_mix = grp["event_type"].value_counts(normalize=True).to_dict()
            row = {
                "dataset": label,
                "ab_group": group,
                "rows": int(len(grp)),
                "users": int(grp["client_id"].nunique()),
                "mean_events_per_user": float(per_user.mean()),
            }
            for event in ["home_view", "offer_impression", "offer_click", "offer_apply", "offer_approved", "revenue"]:
                row[f"share_{event}"] = float(event_mix.get(event, 0.0))
            rows.append(row)
        return pd.DataFrame(rows)
    return pd.concat([summarize(seed_df, "seed"), summarize(expanded_df, "expanded")], ignore_index=True)


def expand_dataset(seed_df: pd.DataFrame, target_rows: int = TARGET_ROWS, seed: int = SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    templates = _prepare_templates(seed_df)

    generated_groups = []
    next_client_id = int(seed_df["client_id"].max()) + 1

    mean_events = seed_df.groupby(["ab_group", "client_id"]).size().groupby("ab_group").mean().sort_index()
    groups = sorted(templates)
    target_rows_map = {}
    allocated = 0
    for idx, group in enumerate(groups):
        if idx < len(groups) - 1:
            target_rows_map[group] = int(round(TARGET_USERS_PER_GROUP * mean_events[group]))
            allocated += target_rows_map[group]
        else:
            target_rows_map[group] = target_rows - allocated

    for group in groups:
        selected = _select_templates_exact_rows(templates[group], TARGET_USERS_PER_GROUP, target_rows_map[group], rng)
        group_df = _instantiate_templates(selected, next_client_id, rng)
        next_client_id += TARGET_USERS_PER_GROUP
        generated_groups.append(group_df)

    expanded = pd.concat(generated_groups, ignore_index=True).sort_values(["dt", "client_id", "event_type"]).reset_index(drop=True)
    expanded["offer_id"] = np.where(expanded["event_type"] == "home_view", None, "credit_of_day")
    expanded["value"] = np.where(expanded["event_type"] == "revenue", pd.to_numeric(expanded["value"], errors="coerce"), np.nan)

    validation = build_validation(seed_df, expanded)
    return expanded, validation


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    raw_dir = repo_root / "data" / "raw"
    processed_dir = repo_root / "data" / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    seed_path = raw_dir / "data_raw_fintech_credit_offer_seed.csv"
    seed_df = pd.read_csv(seed_path, parse_dates=["dt"])
    expanded, validation = expand_dataset(seed_df)

    expanded.to_csv(raw_dir / OUTPUT_NAME, index=False)
    validation.to_csv(processed_dir / "augmentation_validation.csv", index=False)

    print(f"Saved expanded dataset: {raw_dir / OUTPUT_NAME}")
    print(f"Saved validation file: {processed_dir / 'augmentation_validation.csv'}")


if __name__ == "__main__":
    main()
