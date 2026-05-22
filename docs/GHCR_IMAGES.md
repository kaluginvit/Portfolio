# Образы GHCR (монорепозиторий Portfolio)

Workflow: [`build-images.yml`](../.github/workflows/build-images.yml)  
Бейдж: [![Build Docker images](https://github.com/kaluginvit/Portfolio/actions/workflows/build-images.yml/badge.svg)](https://github.com/kaluginvit/Portfolio/actions/workflows/build-images.yml)

Владелец репозитория: **`kaluginvit`**. Замените при форке.

## Pull / run (шаблон)

```bash
docker pull ghcr.io/kaluginvit/<image>:latest
docker run --rm -it --env-file .env ghcr.io/kaluginvit/<image>:latest
```

Порты и переменные — в README соответствующего проекта.

## Имя образа → путь в репозитории

| Image (`docker pull …`) | Контекст сборки |
|-------------------------|-----------------|
| `mortgage-calculator` | `02-automation/mortgage-calculator` |
| `weather-api` | `02-automation/weather-api` |
| `currency-travel-api` | `02-automation/currency-travel-api` |
| `bankrot-trades-scraper` | `02-automation/bankrot-trades-scraper` |
| `yandex-google-sync` | `02-automation/yandex-google-sync` |
| `github-actions-setup` | `02-automation/github-actions-setup` |
| `weather-tg-bot` | `03-ai-products/weather-tg-bot` |
| `team-tg-bot-vc` | `03-ai-products/team-tg-bot-vc` |
| `smart-text-helper` | `03-ai-products/smart-text-helper` |
| `tg-catalog-analyzer` | `03-ai-products/tg-catalog-analyzer` |
| `mcp-lesson-mcp-server` | `03-ai-products/mcp-lesson/mcp_server` |
| `mcp-lesson-telegram-bot` | `03-ai-products/mcp-lesson/telegram_bot` |
| `pdf-checker` | `03-ai-products/pdf-checker` |
| `audio-transcriber` | `03-ai-products/audio-transcriber` |
| `finance-mcp-server` | `03-ai-products/finance-mcp-server/product-mcp` |
| `yandex-wordstat-mcp` | `03-ai-products/seo-mcp-bot/yandex-wordstat-mcp` |
| `team-ai-bot` | `03-ai-products/team-ai-bot` |
| `personal-rag-assistant` | `03-ai-products/personal-rag-assistant` |
| `memory-bot` | `03-ai-products/memory-bot` |
| `svo-payments-bot` | `03-ai-products/svo-payments-bot` |
| `crewai-multiagent` | `03-ai-products/crewai-multiagent` |
| `autonomous-agents-backend` | `03-ai-products/autonomous-agents/backend` |
| `svo-payouts-website` | `04-web/svo-payouts-website/web` (прод: [svorazbor.ru](https://svorazbor.ru)) |
| `dostaffkin-backend` | `04-web/dostaffkin` (`Dockerfile.backend`) — фронт-демо: [kaluginvit72.github.io/dostaffkin](https://kaluginvit72.github.io/dostaffkin/) |
