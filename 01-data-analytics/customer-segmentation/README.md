# Сегментация пользователей

**Что это:** аналитический ноутбук по сегментации пользователей на основе датасета, генерация отчёта в DOCX.

**Стек:** Python, Jupyter, pandas; скрипт `build_report_docx.py`.

## Запуск

1. Клонировать репозиторий, перейти в `01-data-analytics/customer-segmentation/`.
2. `python -m venv .venv` → активировать, затем `pip install -r requirements.txt`.
3. Открыть `User_Segmentation_Analysis.ipynb` в Jupyter / VS Code и выполнить ячейки; при необходимости `python build_report_docx.py`.

**Просмотр ноутбука онлайн (nbviewer):**  
[User_Segmentation_Analysis.ipynb](https://nbviewer.org/github/kaluginvit-svg/Portfolio/blob/main/01-data-analytics/customer-segmentation/User_Segmentation_Analysis.ipynb)

### Smoke-чеклист

- [ ] `pip install -r requirements.txt` успешно.
- [ ] Первые ячейки ноутбука читают `User_Data_Dataset.csv` без ошибки.
- [ ] Скрипт отчёта (если используете) завершается и создаёт DOCX.

**Артефакты:** `User_Data_Dataset.csv`, ноутбук, выгрузка отчёта через `build_report_docx.py`.
