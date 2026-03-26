from __future__ import annotations

from pathlib import Path
import pandas as pd

from data_processing import load_events, build_quality_checks, build_user_day_funnel, build_user_level_metrics
from ab_analysis import summarize_group_metrics, compare_groups
from sample_size import build_mde_grid, minimal_sample_for_relative_mde
from visualization import save_metric_bars, save_funnel_chart, save_mde_curve, save_boxplot, save_event_mix

RAW_FILE = "data_raw_fintech_credit_offer_20000.csv"


def build_final_report(comparison: pd.DataFrame, recommendation: pd.DataFrame, quality: pd.DataFrame, output_path: Path) -> None:
    primary = comparison.loc[comparison["metric"] == "cr_apply"].iloc[0]
    ctr = comparison.loc[comparison["metric"] == "ctr"].iloc[0]
    arpu = comparison.loc[comparison["metric"] == "arpu"].iloc[0]
    required_n = recommendation["recommended_sample_size_per_group"].iloc[0]

    text = f"""# Final report

## 1. Objective
Проверить, влияет ли перенос карточки `credit_of_day` вверх в ленте на ключевые продуктовые метрики, прежде всего на `CR_apply`.

## 2. Experiment setup
- A_control: карточка остается внизу ленты
- B_test: карточка переносится вверх
- unit of randomization: `client_id`
- primary metric: `CR_apply`
- secondary metrics: `CTR`, `CR_home_apply`, `ARPU`, `Approval Rate`
- target MDE from specification: `2.5%`

## 3. Data preparation
Сырые события преобразованы в user-day funnel и далее в user-level dataset. Дополнительно выполнены quality checks по дубликатам, offer_id и revenue.

## 4. Key results

### Primary metric — CR_apply
- control mean: {primary['control_mean']:.4f}
- test mean: {primary['test_mean']:.4f}
- absolute diff: {primary['absolute_diff']:.4f}
- relative uplift: {primary['relative_uplift'] * 100:.2f}%
- p-value: {primary['p_value']:.6g}
- 95% CI: [{primary['ci_low']:.4f}, {primary['ci_high']:.4f}]

### Secondary metrics
- CTR uplift: {ctr['relative_uplift'] * 100:.2f}%
- ARPU uplift: {arpu['relative_uplift'] * 100:.2f}%

## 5. Power and MDE
Для целевого `MDE = 2.5%` рекомендуемый размер выборки составляет примерно **{int(required_n):,} пользователей на группу**.  
Это существенно больше, чем доступный объем независимого реального трафика в окне 7 дней.

## 6. Interpretation
В анализируемых данных тестовая группа показывает сильный положительный сигнал по `CR_apply` и `CTR`.  
Однако сам эксперимент в условиях жесткого 7-дневного окна недостаточно мощный для надежной проверки столь малого MDE на реальном независимом трафике.  
Поэтому корректная интерпретация результата — **directional positive signal with limited inferential power for the target MDE**.

## 7. Recommendation
- считать изменение перспективным;
- не использовать текущий кейс как безусловное основание для полного rollout;
- подтвердить результат на реальном трафике большей мощности либо пересогласовать MDE.

## 8. Quality checks snapshot
{quality.to_markdown(index=False)}
"""
    output_path.write_text(text, encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    raw_dir = repo_root / "data" / "raw"
    processed_dir = repo_root / "data" / "processed"
    figures_dir = repo_root / "reports" / "figures"
    reports_dir = repo_root / "reports"
    processed_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    events = load_events(raw_dir / RAW_FILE)
    quality, event_mix, day_split = build_quality_checks(events)
    user_day = build_user_day_funnel(events)
    user_level = build_user_level_metrics(user_day)

    group_summary = summarize_group_metrics(user_level)
    comparison = compare_groups(user_level)

    control = user_level[user_level["ab_group"] == "A_control"]
    cr_apply_control = float(control["cr_apply"].mean())
    cr_apply_std = float(control["cr_apply"].std(ddof=1))

    mde_grid = build_mde_grid(mu=cr_apply_control, std=cr_apply_std, sample_sizes=list(range(1000, 2_000_001, 1000)))
    recommended_n = minimal_sample_for_relative_mde(mu=cr_apply_control, std=cr_apply_std, target_relative_mde_pct=2.5)

    recommendation = pd.DataFrame(
        {
            "baseline_metric": ["cr_apply"],
            "baseline_mean_control": [cr_apply_control],
            "baseline_std_control": [cr_apply_std],
            "target_relative_mde_pct": [2.5],
            "recommended_sample_size_per_group": [recommended_n],
            "actual_users_control": [int((user_level["ab_group"] == "A_control").sum())],
            "actual_users_test": [int((user_level["ab_group"] == "B_test").sum())],
        }
    )

    quality.to_csv(processed_dir / "quality_checks.csv", index=False)
    event_mix.to_csv(processed_dir / "event_mix_by_group.csv", index=False)
    day_split.to_csv(processed_dir / "day_split_by_group.csv", index=False)
    user_day.to_csv(processed_dir / "user_day_funnel.csv", index=False)
    user_level.to_csv(processed_dir / "user_level_metrics.csv", index=False)
    group_summary.to_csv(processed_dir / "group_metric_summary.csv", index=False)
    comparison.to_csv(processed_dir / "ab_results.csv", index=False)
    mde_grid.to_csv(processed_dir / "mde_grid.csv", index=False)
    recommendation.to_csv(processed_dir / "sample_size_recommendation.csv", index=False)

    save_metric_bars(comparison, figures_dir / "metric_uplift.png")
    save_funnel_chart(group_summary, figures_dir / "funnel_by_group.png")
    save_mde_curve(mde_grid, figures_dir / "mde_curve_cr_apply.png")
    save_boxplot(user_level, "cr_apply", figures_dir / "cr_apply_boxplot.png")
    save_boxplot(user_level, "arpu", figures_dir / "arpu_boxplot.png")
    save_event_mix(event_mix, figures_dir / "event_mix.png")

    build_final_report(comparison, recommendation, quality, reports_dir / "final_report.md")

    print("Generated files:")
    for path in [
        processed_dir / "quality_checks.csv",
        processed_dir / "event_mix_by_group.csv",
        processed_dir / "day_split_by_group.csv",
        processed_dir / "user_day_funnel.csv",
        processed_dir / "user_level_metrics.csv",
        processed_dir / "group_metric_summary.csv",
        processed_dir / "ab_results.csv",
        processed_dir / "mde_grid.csv",
        processed_dir / "sample_size_recommendation.csv",
        reports_dir / "final_report.md",
        figures_dir / "metric_uplift.png",
        figures_dir / "funnel_by_group.png",
        figures_dir / "mde_curve_cr_apply.png",
        figures_dir / "cr_apply_boxplot.png",
        figures_dir / "arpu_boxplot.png",
        figures_dir / "event_mix.png",
    ]:
        print(f"- {path}")


if __name__ == "__main__":
    main()
