# SEO MCP Bot — MCP-серверы для Yandex Wordstat

**Проблема:** подбирать семантику и смотреть частотности удобнее прямо из ИИ-ассистента (Cursor / Claude), без ручного копирования из Wordstat.

**Решение:** один или два Python MCP-сервера поверх **Yandex Wordstat API** — инструменты вызываются из чата по протоколу MCP.

**Стек:** FastAPI / MCP, OAuth-токен Яндекса, см. подпапки.

---

## Структура репозитория

| Папка | Роль |
|--------|------|
| **`yandex-wordstat-mcp/`** | **Основной** MCP-сервер Wordstat — сюда идите первым: venv, `.env`, OAuth, `python mcp_server.py`, Docker (`yandex-wordstat-mcp/Dockerfile`). |
| **`mcp/`** | **Legacy / альтернативная** сборка — только если нужны сценарии из [`mcp/README.md`](./mcp/README.md); для новых подключений используйте `yandex-wordstat-mcp`. |

Начните с **`yandex-wordstat-mcp/README.md`**.

---

## Подключение в Cursor

1. Запустите MCP-сервер локально (порт/stdio — как в README подпроекта).
2. Откройте настройки MCP в Cursor и добавьте сервер, например:

```json
{
  "mcpServers": {
    "yandex-wordstat": {
      "command": "python",
      "args": ["C:/path/to/Portfolio/03-ai-products/seo-mcp-bot/yandex-wordstat-mcp/mcp_server.py"],
      "env": {
        "WORDSTAT_OAUTH_TOKEN": "y0_..."
      }
    }
  }
}
```

Подставьте **абсолютные пути** к вашему клону и активируйте venv через обёртку или `command`: `"C:/.../.venv/Scripts/python.exe"`. Точные переменные окружения — в `.env.example` соответствующей подпапки.

---

## Зачем MCP для SEO

Ассистент может запрашивать частотности и связанные формулировки в диалоге («подбери кластер под страницу X»), не переключаясь между вкладками.

---

## Ограничения

- Нужен действующий OAuth-токен Яндекса и доступ к Wordstat API по правилам Яндекса.
- Квоты и биллинг — на стороне Yandex Cloud.
