# Бизнес-кейсы на Python (EDA)

**Что это:** серия Jupyter-презентаций с разведочным анализом: банк, Amazon Marketplace, Netflix.

**Стек:** Python, Jupyter, pandas; `requirements.txt` в корне папки.

## Запуск

1. Клонировать репозиторий, перейти в `01-data-analytics/python-business-case/`.
2. `python -m venv .venv` → активировать, `pip install -r requirements.txt`.
3. Открыть нужный ноутбук в Jupyter / VS Code.

**nbviewer (основные ноутбуки):**

- [bank_analysis_portfolio.ipynb](https://nbviewer.org/github/kaluginvit/Portfolio/blob/main/01-data-analytics/python-business-case/bank_analysis_portfolio.ipynb)
- [amazon_market_eda_presentation.ipynb](https://nbviewer.org/github/kaluginvit/Portfolio/blob/main/01-data-analytics/python-business-case/amazon_market_eda_presentation.ipynb)
- [netflix_eda_presentation.ipynb](https://nbviewer.org/github/kaluginvit/Portfolio/blob/main/01-data-analytics/python-business-case/netflix_eda_presentation.ipynb)

### Smoke-чеклист

- [ ] `pip install -r requirements.txt` без ошибок.
- [ ] Выбранный ноутбук выполняет ячейки загрузки данных.

**Данные:** CSV для банка и маркетплейса прилагаются; сценарии описаны внутри ноутбуков.
