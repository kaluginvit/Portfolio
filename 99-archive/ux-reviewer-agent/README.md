# UX Reviewer Agent

**Что это:** сервис анализа UX страницы по URL: бэкенд (FastAPI/Uvicorn) + фронтенд (Vite/React). По описанию задачи — отчёт с сильными/слабыми сторонами и рекомендациями (см. `Проект.txt`).

**Стек:** Python backend, React/Vite frontend, Docker Compose.

**Запуск (Docker):**

```bash
# В корне проекта: создайте .env для API-ключей (OpenAI и т.д.)
docker compose up --build
```

- Backend: http://localhost:8000  
- Frontend dev: http://localhost:3000  

**Ключи API:** локальный файл с ключом не коммитится — используйте шаблон `UX-reviewer.example.txt` и переименуйте/скопируйте в `UX-reviewer.txt` (файл в `.gitignore`). Для фронта см. `frontend/.env.example`.
