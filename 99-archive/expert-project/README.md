# Expert project: URL → цепочка промптов → пост

**Что это:** Flask-приложение: по введённому URL строится цепочка промптов, ответы LLM агрегируются, на выходе — готовый рекламный пост.

**Стек:** Python, Flask, OpenAI API (модули `openai_module.py`, `openai_template.py`), Docker (опционально).

**Запуск (локально):**

```bash
pip install -r requirements.txt
# задать ключи в .env по образцу EnvExample
python main.py
```

Откройте в браузере адрес, который выведет Flask (обычно `http://127.0.0.1:5000`).

**Артефакты:** `templates/index.html`, `Dockerfile` для контейнерного запуска.
