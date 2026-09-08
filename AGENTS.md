# Agents — инструкции для AI-агентов

Этот файл описывает правила работы AI-агентов (Claude Code и subagents) с данным репозиторием.

---

## Автономные операции (без подтверждения)

- Чтение любых файлов репозитория
- HTTP-проверка live URLs (curl)
- Запросы к GitHub API (gh repo view, gh api) — только чтение
- Анализ, аудит, подготовка рекомендаций
- TypeScript/npm build проверки (npx tsc --noEmit, npm run build)

---

## Операции, требующие явного подтверждения

- **Любые git-операции:** commit, push, pull, fetch, force push, reset, checkout
- **Изменение metadata репозиториев** (gh repo edit: description, topics, homepage, visibility)
- **Изменение файлов сайта:** site/src/data/cases.ts, site/src/data/certs.ts
- **Изменение README.md** (корневого)
- **Изменение workflow** (.github/workflows/)
- **Создание или удаление репозиториев**
- **subtree split и push** в standalone repos

---

## Запрещено без прямого указания владельца

- Менять Tier-классификацию (A/B/C/D) проектов
- Добавлять Tier C/D на сайт или Pages
- Удалять файлы или папки из репозитория
- Изменять бизнес-логику существующих проектов
- Force push в main без документирования причины
- Создавать демо или Pages для новых проектов
- Переименовывать репозитории

---

## Параллелизация агентов

При делегировании задач subagents:

**Параллельно разрешено:**
- Чтение файлов (Read, Glob, Grep)
- Анализ README разных проектов
- Проверка HTTP-статусов
- Запросы к GitHub API по разным repos

**Только последовательно:**
- Любые мутации (один агент — одна мутация за раз)
- git операции (никогда параллельно)
- Изменения в одном файле (исключить race conditions)

Принцип: **parallelize analysis, serialize mutations.**

---

## Subtree sync — процедура

При необходимости обновить standalone Tier A repo из monorepo:

```bash
# 1. Split
git subtree split --prefix=<path/to/project> -b sync/<name>

# 2. Push (force только при несовместимых историях — документировать причину)
git push https://github.com/kaluginvit/<name>.git sync/<name>:main [--force]

# 3. Cleanup
git branch -D sync/<name>
```

Никогда не делать subtree split для Tier B/C/D без явного запроса.

---

## Монорепо — что не трогать

- `_Portfolio_back/` — архив Tier D, не восстанавливать
- `05-ai-consulting/` — отдельный контекст, не выставлять публично
- `.github/workflows/portfolio-github-pages.yml` — единственный Pages workflow, не дублировать
- Tier C проекты — оставить как есть (GitHub-only, не на сайте)

---

## Ссылки на контекст

- `CLAUDE.md` — быстрый контекст проекта (Tier-структура, правила, ключевые файлы)
- `MANIFEST.md` — текущее состояние repos и URLs
- `PORTFOLIO_FINAL_CLASSIFICATION.md` — полная Tier A/B/C/D таблица с M2
- `PORTFOLIO_FINAL_USER_AUDIT.md` — аудит глазами работодателя/клиента/интервьюера
