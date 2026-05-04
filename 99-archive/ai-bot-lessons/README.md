# AI bot lessons

**Что это:** крупный учебный Telegram-бот: генерация видео (Sora API), сессии, прайсинг, память диалога, конфигурация.

**Стек:** Python, aiogram; модули `video_api.py`, `pricing.py`, `memory.py`, `cbr.py`, `config.py`.

**Запуск:**

```bash
pip install -r requirements.txt
copy .env.example .env   # Windows; заполните переменные
python main.py
```

**Примечание:** в архиве портфолио; для продакшена вынесите секреты только в `.env` и не публикуйте токены.
