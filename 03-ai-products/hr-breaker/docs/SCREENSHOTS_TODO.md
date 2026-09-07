# Screenshots TODO — hr-breaker

3 скриншота. Запустить: `uv sync && uv run hr-breaker serve` → http://localhost:8899

---

## 1. Web UI — загрузка резюме

**Файл:** `docs/screenshots/01-upload-resume.png`

**Шаги:**
1. Открыть http://localhost:8899
2. Перетащить `sample-data/resume.txt` в зону загрузки
3. Сделать скриншот с созданным профилем

---

## 2. Процесс оптимизации (SSE прогресс)

**Файл:** `docs/screenshots/02-optimization-progress.png`

**Шаги:**
1. Вставить содержимое `sample-data/job-description.txt` в поле вакансии
2. Нажать Optimize
3. Во время работы (SSE стриминг) сделать скриншот прогресс-бара с шагами фильтрации

---

## 3. Готовый PDF результат

**Файл:** `docs/screenshots/03-pdf-result.png`

**Шаги:**
1. Дождаться завершения оптимизации
2. Сделать скриншот превью PDF и кнопки Download
3. Опционально: открыть PDF и сделать скриншот первой страницы
