# PPTX Redesigner

Скрипты для анализа структуры PowerPoint-презентаций и автоматического редизайна под корпоративный шаблон.

## Стек

Python, python-pptx

## Быстрый старт

```bash
pip install -r requirements.txt
python tools/redesign_pptx_v2.py <путь_к_файлу.pptx>
```

## Инструменты (`tools/`)

| Файл | Назначение |
|------|-----------|
| `analyze_colors.py` | Извлечение цветовой палитры |
| `analyze_shapes.py` | Анализ фигур и макетов |
| `analyze_pptx.py` | Общий разбор структуры |
| `extract_images.py` | Извлечение изображений |
| `redesign_pptx.py` | Редизайн v1 |
| `redesign_pptx_v2.py` | Редизайн v2 (актуальная версия) |

> Результат проверяйте вручную перед использованием в важных презентациях.
