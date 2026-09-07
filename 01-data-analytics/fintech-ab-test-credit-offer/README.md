# A/B Test: Credit Card Offer Placement in Fintech App

**Live demo:** https://kaluginvit.github.io/Portfolio/fintech-ab-test/

Полный аналитический кейс: A/B-тест переноса карточки «Кредитка дня» в верхнюю часть домашнего экрана финтех-приложения.

Проверяет, улучшает ли изменение позиции ключевые метрики — CR_apply, CTR, ARPU — и можно ли считать результат достаточным для rollout.

## Business Problem

На домашнем экране финтех-приложения показывается лента спецпредложений. Карточка «Кредитка дня» находится в нижней части ленты. Гипотеза: её перемещение выше увеличит видимость и конверсию в заявку.

Задача: оценить статистическую значимость эффекта, рассчитать MDE и дать продуктовую рекомендацию.

## Solution

Полный воспроизводимый аналитический pipeline:

1. **Data layer:** raw CSV → bootstrap-расширение траекторий пользователей → processed datasets
2. **SQL layer:** user-level funnel (4 SQL-запроса с window functions и CTEs)
3. **Analysis:** user-level метрики → Welch t-test → MDE grid → sample size calculation
4. **Visualization:** 6 ключевых графиков
5. **Report:** итоговый Markdown-отчёт с продуктовой рекомендацией

## Key Features

- **Методологически корректный подход:** user-level aggregation → Welch t-test (не Mann-Whitney — объяснено почему)
- **MDE и power analysis:** расчёт требуемого размера выборки при MDE=2.5%, мощность 80%
- **Честная интерпретация:** разница между directional signal и статистически подтверждённым результатом
- **Полностью воспроизводимо:** `make all` восстанавливает все артефакты с нуля
- **SQL + Python pipeline:** четыре SQL-запроса документируют логику агрегации независимо от Python

## Architecture

```
data/raw/
├── data_raw_fintech_credit_offer_seed.csv     # исходный датасет
└── data_raw_fintech_credit_offer_20000.csv    # расширенный (bootstrap)

Makefile pipeline:
  make data     → augment_dataset.py → data/processed/
  make analysis → ab_analysis.py + sample_size.py → ab_results.csv, mde_grid.csv
  make report   → run_analysis.py + visualization.py → final_report.md + figures/

sql/
├── 01_user_day_funnel.sql
├── 02_user_level_metrics.sql
├── 03_group_metric_summary.sql
└── 04_srm_check.sql
```

## Tech Stack

| Компонент | Технология |
|-----------|-----------|
| Language | Python 3.10+ |
| Analysis | pandas, scipy (Welch t-test), statsmodels |
| Visualization | matplotlib, seaborn |
| Data | CSV, SQL (window functions, CTEs) |
| Pipeline | Makefile |
| Tests | pytest |
| Notebook | Jupyter (showcase) |

## Business / Domain Logic

**Primary metric:** `CR_apply = offer_apply / offer_impression`

Выбрана как основная потому что: ближе к бизнес-результату чем CTR, более чувствительная чем downstream revenue.

**Secondary metrics:** CTR, CR_home_apply, ARPU, Approval Rate

**Statistical approach:**
- User-level Welch t-test: устойчив к неравенству дисперсий между группами
- Уровень значимости α=0.05, мощность 80%
- MDE=2.5% (задан по условию задачи)

**Dataset augmentation:** исходный датасет расширен через bootstrap целых пользовательских траекторий — не построчный sampling. Сохраняет: типовую последовательность событий, связь impression→click→apply→approved, 7-дневное окно, близкие пропорции событий.

**Ключевой вывод:** при MDE=2.5% и 7-дневном окне теста доступная выборка не обеспечивает достаточную статистическую мощность. Наблюдаемый uplift по CR_apply и CTR — **directional signal, не окончательное доказательство для rollout**.

## Project Structure

```
fintech-ab-test-credit-offer/
├── src/
│   ├── data_processing.py    # очистка и валидация
│   ├── augment_dataset.py    # bootstrap расширение
│   ├── ab_analysis.py        # Welch t-test, результаты
│   ├── sample_size.py        # MDE grid, расчёт размера выборки
│   ├── visualization.py      # 6 графиков
│   └── run_analysis.py       # пайплайн и отчёт
├── sql/                      # 4 SQL-запроса
├── data/
│   ├── raw/                  # исходные данные
│   └── processed/            # артефакты пайплайна
├── reports/
│   ├── final_report.md
│   └── figures/              # PNG графики
├── notebooks/
│   └── ab_test_analysis_showcase.ipynb
├── docs/
│   ├── experiment_design.md
│   ├── metrics_definition.md
│   ├── limitations.md
│   └── event_tracking.md
├── tests/test_data.py
└── Makefile
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

make all
```

Или по шагам:
```bash
make data       # подготовка данных
make analysis   # A/B анализ
make report     # финальный отчёт
```

**Ожидаемые артефакты:**
- `data/processed/ab_results.csv` — результаты тестов по метрикам
- `data/processed/mde_grid.csv` — MDE vs sample size
- `reports/final_report.md` — продуктовый отчёт
- `reports/figures/*.png` — графики

## Notebook

Интерактивный разбор: [открыть в nbviewer](https://nbviewer.org/github/kaluginvit/Portfolio/blob/main/01-data-analytics/fintech-ab-test-credit-offer/notebooks/ab_test_analysis_showcase.ipynb)

## Tests

```bash
pytest tests/ -v
```

## Main Findings

По расширенному датасету тестовая группа показывает:
- Статистически значимый рост `CR_apply` (p < 0.05)
- Рост `CTR` и `ARPU`

**Caveat:** при MDE=2.5% и реальной вариативности исходных данных 7-дневное окно теста недостаточно мощное для уверенного подтверждения эффекта на реальном трафике.

## Engineering Decisions

**Welch t-test вместо Mann-Whitney:** Welch устойчив к неравенству дисперсий (что типично при AB тестах), прост в интерпретации и имеет понятные предположения. Mann-Whitney — непараметрический, хорош для медианных сдвигов, но менее информативен для среднего ARPU. Задача — оценить средние метрики → Welch корректен.

**Bootstrap augmentation, не random sampling:** построчный sampling ломает пользовательские траектории. Bootstrap целых сессий сохраняет реалистичную последовательность событий. Датасет используется для воспроизводимости кейса, не как замена реальному трафику.

**Makefile pipeline:** воспроизводимость важнее интерактивности для аналитического кейса. `make all` гарантирует детерминированный результат.

## Limitations

- Синтетически расширенный датасет не заменяет независимый реальный трафик
- 7-дневное окно недостаточно для MDE=2.5% при стандартных параметрах мощности
- Downstream-метрики (approved, revenue) требуют более длинного горизонта наблюдения
- Не проверялась каннибализация других карточек в ленте

## Reuse / Customization

Тип: **Analytical case study → Reusable pipeline template**

Pipeline переиспользуем для аналогичных A/B задач:
1. Заменить входной CSV с нужной схемой (`dt | user_id | ab_group | event_type | value`)
2. Обновить определения метрик в `ab_analysis.py`
3. Обновить MDE в `sample_size.py`
4. `make all`

## Final Recommendation

- Изменение перспективно по направлению эффекта
- Не использовать как безусловное основание для rollout
- Подтвердить на реальном трафике или пересогласовать MDE/сроки теста
- Проверить эффект по сегментам (new/returning, iOS/Android)

## Roadmap

- Байесовский анализ вместо/в дополнение к frequentist
- Sequential testing для раннего stopping
- Сегментный анализ (cohorts, platforms)
