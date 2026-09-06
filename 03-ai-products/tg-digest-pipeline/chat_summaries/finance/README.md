# finance

Рабочий контур финансового подпроекта строится вокруг `finance_messages.db`.

## Основные команды

Быстрый статус всего подпроекта:

```powershell
uv run python finance\refresh_finance.py --report
```

Локально обновить рабочие выгрузки без внешнего LLM/API:

```powershell
uv run python finance\refresh_finance.py --all-local
```

Собрать исходные сообщения из TG-папки `Финансы`:

```powershell
uv run python finance\collect_finance_messages.py --start 2026-01-01 --end 2026-07-25 --mark-read
```

Систематизировать финансовое ядро без внешнего API:

```powershell
uv run python finance\practical_finance.py --process-local
uv run python finance\practical_finance.py --process-local-videos
uv run python finance\practical_finance.py --export
```

Дешевый первый LLM-слой: только смысловая категория без полной карточки:

```powershell
uv run python finance\practical_finance.py --classify-only --batch-size 50
```

Полный LLM-слой для практических карточек:

```powershell
uv run python finance\practical_finance.py --process --batch-size 8
```

Проверить статус систематизации:

```powershell
uv run python finance\practical_finance.py --status
```

Проиндексировать ссылки и применить доменные правила:

```powershell
uv run python finance\index_links.py
```

Проиндексировать скачанные видео и проверить полноту:

```powershell
uv run python finance\index_video_files.py
```

## Активные файлы

- `collect_finance_messages.py` - сбор сообщений в `finance_messages.db`.
- `practical_finance.py` - классификация, практические карточки, экспорт инсайтов.
- `index_links.py` - нормализация URL, таблица `finance_links`, рабочие CSV по ссылкам.
- `domain_policy.py` - правила `keep` / `suppress` / `review` для доменов.
- `index_video_files.py` - каталогизация видеофайлов и сверка с сообщениями.
- `finance_health.py` - единый health-report и генерация `PROGRESS.md`.
- `refresh_finance.py` - оркестратор этапов пайплайна.
- `compress_finance_videos.ps1` - утилита сжатия видео.

## Ссылки

Все URL остаются в БД. Дальше они делятся доменной политикой:

- `keep` - использовать в рабочих выгрузках и UI.
- `suppress` - хранить в БД, но не использовать в рабочих выводах.
- `review` - еще не принято решение, по умолчанию не идет в рабочий вывод.

Основные выгрузки:

- `output/finance_links.csv` - только активные ссылки.
- `output/finance_links_all.csv` - все ссылки с политиками.
- `output/finance_links_report.json` - статистика по политике и доменам.
- `output/finance_domains_review.csv` - домены, ожидающие решения.

## Видео

Есть две папки с видео:

- `Финансы_видео/` - native Telegram-видео из постов.
- `Финансы_ссылки_видео/` - внешние видео, скачанные по ссылкам.

Файлы разложены по категориям, а не по каналам. Для связанных файлов в имени
есть префикс `sp_<source_peer_id>__msg_<message_id>__`, чтобы сохранялась
привязка к исходному сообщению.

Индексатор пишет таблицу `finance_video_files` в `finance_messages.db`.
Индексация ссылок и видео инкрементальная: актуальные записи получают `is_stale=0`, исчезнувшие остаются в БД как история с `is_stale=1`.

Отчеты:

- `output/video_files_report.json` - краткая статистика полноты.
- `output/video_files.csv` - все найденные файлы и связи с сообщениями.
- `output/missing_native_videos.csv` - TG-видео из БД, для которых нет связанного файла.
- `output/finance_health.json` и `output/finance_health.md` - общий статус пайплайна.

Полнота считается относительно текущей БД:

- TG-native: `messages.media_type = 'video'`.
- External: сообщения, где `links_json` содержит `vkvideo`, `rutube`, `youtube`, `youtu.be` или `vk.com/video`.

Очередь недостающих native-видео:

```powershell
uv run python finance\download_finance_videos.py --dry-run --session-name session2_finance
```

Скачать следующий батч native-видео:

```powershell
uv run python finance\download_finance_videos.py --limit 20 --session-name session2_finance --reconnect-attempts 4 --min-duration-sec 20
```

Старые CSV/download/enrich helper-скрипты удалены из рабочего контура.

## Служебная уборка

Посмотреть stale `.part`-файлы старше 12 часов:

```powershell
uv run python finance\download_finance_videos.py --cleanup-stale-parts --older-than-hours 12 --dry-run
```

Удалить их:

```powershell
uv run python finance\download_finance_videos.py --cleanup-stale-parts --older-than-hours 12
```
