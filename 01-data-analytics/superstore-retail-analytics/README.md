# 📊 Retail Analytics — Sample Superstore

**Виталий** · аналитика данных · визуализация · упаковка инсайтов для команды и стейкхолдеров

Полный цикл на открытом датасете **Sample - Superstore** (розница, США): исследование в Python → интерактивный HTML-дашборд → презентация → при необходимости экспорт в PowerPoint.

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Pandas-EDA-150458?style=flat&logo=pandas&logoColor=white" alt="Pandas"/>
  <img src="https://img.shields.io/badge/Jupyter-ноутбук-F37626?style=flat&logo=jupyter&logoColor=white" alt="Jupyter"/>
  <img src="https://img.shields.io/badge/Plotly-дашборд-3F4F75?style=flat&logo=plotly&logoColor=white" alt="Plotly"/>
</p>

---

## 🎯 Что это даёт в портфолио

| | |
|:---|:---|
| **Таблицы и метрики** | Загрузка, типы, очистка, агрегации, заказы и маржинальность |
| **Бизнес-логика** | Регионы, категории, скидки vs прибыль, доставка, сегменты — не «графики ради графиков» |
| **Подача результата** | Дашборд в браузере + HTML-слайды + сценарий сборки PPTX |

---

## 💡 Ключевые выводы (по данным)

- **Категории:** высокая выручка не всегда даёт высокую долю прибыли (например, Furniture при сопоставимой выручке сильно отстаёт по марже).
- **Скидки:** глубокие скидки связаны с просадкой маржи — кандидат на пересмотр политики.
- **География и сегменты:** различия по регионам и типам клиентов — основа для приоритизации.

Подробности — в `superstore_eda.ipynb`, на слайдах `superstore_presentation.html` и в [**INSIGHTS.md**](INSIGHTS.md) (три вывода для стейкхолдеров).

---

## 🛠 Стек

| Слой | Инструменты |
|:--|:--|
| Анализ | Python, pandas, numpy, matplotlib, seaborn |
| Демо | Статический HTML, Plotly (CDN), фильтры и KPI без бэкенда |
| Презентация | HTML-слайды; опционально **Playwright** + **python-pptx** → `html_to_pptx.py` |

---

## 📂 Структура проекта

| Файл | Назначение |
|:--|:--|
| `Sample - Superstore.csv` | Исходные данные |
| `superstore_eda.ipynb` | EDA: метрики, география, динамика, скидки, сегменты, тепловые карты |
| `superstore-dashboard.html` | Интерактивный дашборд (CSV рядом с файлом) |
| `superstore_presentation.html` | Презентация в браузере |
| `html_to_pptx.py` | Рендер слайдов в PNG и сборка `superstore_presentation.pptx` |
| `requirements.txt` | Зависимости Python |

---

## 🚀 Быстрый старт

**1. Окружение и ноутбук**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook superstore_eda.ipynb
```

Файл `Sample - Superstore.csv` — в той же папке, что и ноутбук (или обновите путь в ячейке загрузки).

**2. Дашборд и слайды**

Откройте в браузере `superstore-dashboard.html` и `superstore_presentation.html` (при необходимости через Live Server в VS Code / Cursor).

**Live (GitHub Pages):** workflow [Deploy Superstore dashboard](../../.github/workflows/superstore-github-pages.yml) публикует дашборд как корень сайта. Включите **Settings → Pages → Build and deployment: GitHub Actions**. После успешного прогона URL: **[https://kaluginvit-svg.github.io/Portfolio/](https://kaluginvit-svg.github.io/Portfolio/)** (индекс = дашборд). Кнопка для README:

[![Superstore Pages](https://github.com/kaluginvit-svg/Portfolio/actions/workflows/superstore-github-pages.yml/badge.svg)](https://github.com/kaluginvit-svg/Portfolio/actions/workflows/superstore-github-pages.yml)

**3. PowerPoint (по желанию)**

```bash
playwright install chromium
python html_to_pptx.py
```

Появится `superstore_presentation.pptx`. Кнопка «Открыть дашборд» на слайде 4 откроет `superstore-dashboard.html`, если он лежит **в одной папке с PPTX**.

---

## О датасете

**Sample - Superstore** — учебный стандарт (Tableau и курсы аналитики). Ценность кейса в портфолио — в **структуре рассуждений, чистоте кода и подаче**, а не в эксклюзивности данных.

---

## Контакты

Подставьте свои ссылки перед публикацией репозитория: email · LinkedIn · Telegram.

---

<sub>Учебный кейс на датасете Sample Superstore.</sub>
