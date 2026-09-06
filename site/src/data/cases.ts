export type CaseCategory = '01' | '02' | '03' | '04';

export interface CaseItem {
  id: string;
  category: CaseCategory;
  categoryLabel: string;
  title: string;
  result: string;
  repoPath: string;
  liveLabel: string;
  liveUrl: string;
  featured?: boolean;
}

const tree = 'https://github.com/kaluginvit/Portfolio/tree/main';

export const cases: CaseItem[] = [
  // ── ВИТРИНА (12 проектов, featured) ─────────────────────────────────────

  // score 9
  {
    id: 'hr-breaker',
    category: '03',
    categoryLabel: 'ИИ-продукты',
    title: 'HR-Breaker — оптимизация резюме',
    result: 'Pydantic-AI + FastAPI: любой формат резюме → ATS-оптимизированный PDF. 32 теста, 8 фильтров, без галлюцинаций.',
    repoPath: '03-ai-products/hr-breaker',
    liveLabel: 'FastAPI + CLI',
    liveUrl: `${tree}/03-ai-products/hr-breaker`,
    featured: true,
  },
  {
    id: 'finance-data-screener',
    category: '04',
    categoryLabel: 'Веб',
    title: 'ИИ-скринер финансовых данных',
    result: 'FastAPI + React + LLM: текстовый запрос → данные MOEX/ЦБ/ТАСС + интерактивный график + аудит запросов.',
    repoPath: '04-web/finance-data-screener',
    liveLabel: 'docker compose',
    liveUrl: `${tree}/04-web/finance-data-screener`,
    featured: true,
  },
  {
    id: 'svo-bot',
    category: '03',
    categoryLabel: 'ИИ-продукты',
    title: 'Telegram-бот выплат (СВО)',
    result: 'Production FSM-бот: анкета, расчёт, заявки; 57 файлов, Docker, CI/CD.',
    repoPath: '03-ai-products/svo-payments-bot',
    liveLabel: 'GHCR',
    liveUrl: 'https://github.com/kaluginvit/Portfolio/pkgs/container/svo-payments-bot',
    featured: true,
  },

  // score 8
  {
    id: 'finance-mcp-server',
    category: '03',
    categoryLabel: 'ИИ-продукты',
    title: 'Finance MCP Server',
    result: '19 MCP-инструментов: P&L, Cash Flow, KPI, платежи — AI-ассистент работает с данными без экспорта.',
    repoPath: '03-ai-products/finance-mcp-server',
    liveLabel: 'Claude / Cursor',
    liveUrl: `${tree}/03-ai-products/finance-mcp-server`,
    featured: true,
  },
  {
    id: 'svo-web',
    category: '04',
    categoryLabel: 'Веб',
    title: 'Сайт СВО — выплаты семьям',
    result: 'Production Next.js 15 + TypeScript: квиз, лид-форма, органика; пара с Telegram-ботом.',
    repoPath: '04-web/svo-payouts-website',
    liveLabel: 'svorazbor.ru',
    liveUrl: 'https://svorazbor.ru',
    featured: true,
  },
  {
    id: 'rf-macro-risk',
    category: '03',
    categoryLabel: 'ИИ-продукты',
    title: 'RF Macro Outlook AI',
    result: 'LangChain-агент: 35 макро-критериев → риск кризисного сценария на 6 месяцев + еженедельный live-отчёт.',
    repoPath: '03-ai-products/rf-macro-risk-ai',
    liveLabel: 'Live-отчёт',
    liveUrl: 'https://kaluginvit.github.io/rf-macro-risk-ai/',
    featured: true,
  },

  // score 7
  {
    id: 'fintech-ab',
    category: '01',
    categoryLabel: 'Аналитика',
    title: 'A/B-тест в финтех',
    result: 'Статистический отчёт с MDE, power-анализом и продуктовой рекомендацией.',
    repoPath: '01-data-analytics/fintech-ab-test-credit-offer',
    liveLabel: 'nbviewer',
    liveUrl:
      'https://nbviewer.org/github/kaluginvit/Portfolio/blob/main/01-data-analytics/fintech-ab-test-credit-offer/notebooks/ab_test_analysis_showcase.ipynb',
    featured: true,
  },
  {
    id: 'tg-digest',
    category: '03',
    categoryLabel: 'ИИ-продукты',
    title: 'ИнфоПовод — RAG-пайплайн',
    result: 'Neo4j + Pinecone + LLM-vision: глубокий анализ Telegram-канала, граф знаний, подготовка к файнтюну.',
    repoPath: '03-ai-products/tg-digest-pipeline',
    liveLabel: 'Репозиторий',
    liveUrl: `${tree}/03-ai-products/tg-digest-pipeline`,
    featured: true,
  },

  // score 6
  {
    id: 'finsight',
    category: '04',
    categoryLabel: 'Веб',
    title: 'ФинАналитик',
    result: 'FastAPI + React + Claude: загрузи CSV/Excel — топ-3 инсайта и чат с данными за 30 секунд.',
    repoPath: '04-web/finsight',
    liveLabel: 'GitHub',
    liveUrl: 'https://github.com/kaluginvit/finsight',
    featured: true,
  },
  {
    id: 'fedresurs',
    category: '01',
    categoryLabel: 'Аналитика',
    title: 'Fedresurs MVP — оценка лотов банкротства',
    result: 'Chrome-закладки → P25/P50/P75 по аналогам + LLM-агент с web-поиском для любых типов активов.',
    repoPath: '01-data-analytics/fedresurs-mvp',
    liveLabel: 'Flask UI',
    liveUrl: `${tree}/01-data-analytics/fedresurs-mvp`,
    featured: true,
  },
  {
    id: 'leadgen-n8n',
    category: '02',
    categoryLabel: 'Автоматизация',
    title: 'Лидогенерация на n8n',
    result: '11 воркфлоу: интент → обогащение → касание → отчётность.',
    repoPath: '02-automation/leadgen-n8n-system',
    liveLabel: 'docker compose',
    liveUrl: `${tree}/02-automation/leadgen-n8n-system`,
    featured: true,
  },

  // score 5
  {
    id: 'superstore',
    category: '01',
    categoryLabel: 'Аналитика',
    title: 'Retail-аналитика Superstore',
    result: 'Интерактивный дашборд Plotly + инсайты для стейкхолдеров.',
    repoPath: '01-data-analytics/superstore-retail-analytics',
    liveLabel: 'Дашборд на Pages',
    liveUrl: 'https://kaluginvit.github.io/Portfolio/superstore/',
    featured: true,
  },

  // ── ОСТАЛЬНЫЕ (каталог, без featured) ────────────────────────────────────

  {
    id: 'bankrot-scraper',
    category: '02',
    categoryLabel: 'Автоматизация',
    title: 'Парсер торгов банкротства',
    result: 'Мониторинг лотов Федресурса: фильтры, уведомления, история торгов.',
    repoPath: '02-automation/bankrot-trades-scraper',
    liveLabel: 'Репозиторий',
    liveUrl: `${tree}/02-automation/bankrot-trades-scraper`,
  },
  {
    id: 'wb',
    category: '01',
    categoryLabel: 'Аналитика',
    title: 'Коммерческий анализ Wildberries',
    result: 'Кейс продавца: маржа, точки роста.',
    repoPath: '01-data-analytics/wb-sales-commercial-analysis',
    liveLabel: 'Репозиторий',
    liveUrl: `${tree}/01-data-analytics/wb-sales-commercial-analysis`,
  },
  {
    id: 'yandex-google',
    category: '02',
    categoryLabel: 'Автоматизация',
    title: 'Яндекс.Диск ↔ Google Drive',
    result: 'Двусторонний sync, конфликты, cron.',
    repoPath: '02-automation/yandex-google-sync',
    liveLabel: 'GHCR',
    liveUrl: 'https://github.com/kaluginvit/Portfolio/pkgs/container/yandex-google-sync',
  },
  {
    id: 'seo-mcp',
    category: '03',
    categoryLabel: 'ИИ-продукты',
    title: 'MCP + Yandex Wordstat',
    result: 'Семантика и частотности в Cursor / Claude.',
    repoPath: '03-ai-products/seo-mcp-bot',
    liveLabel: 'GHCR',
    liveUrl: 'https://github.com/kaluginvit/Portfolio/pkgs/container/yandex-wordstat-mcp',
  },
  {
    id: 'team-bot',
    category: '03',
    categoryLabel: 'ИИ-продукты',
    title: 'RAG-бот команды (Haystack + Pinecone)',
    result: 'Память команды, корпоративный контур.',
    repoPath: '03-ai-products/team-ai-bot',
    liveLabel: 'GHCR',
    liveUrl: 'https://github.com/kaluginvit/Portfolio/pkgs/container/team-ai-bot',
  },
  {
    id: 'personal-rag',
    category: '03',
    categoryLabel: 'ИИ-продукты',
    title: 'Персональный RAG в Telegram',
    result: 'Ассистент по личной базе (Pinecone).',
    repoPath: '03-ai-products/personal-rag-assistant',
    liveLabel: 'GHCR',
    liveUrl: 'https://github.com/kaluginvit/Portfolio/pkgs/container/personal-rag-assistant',
  },
  {
    id: 'autonomous-agents',
    category: '03',
    categoryLabel: 'ИИ-продукты',
    title: 'ИИ-агент SEO-ядра по URL',
    result: 'Парсинг + кластеризация через ProxyAPI.',
    repoPath: '03-ai-products/autonomous-agents',
    liveLabel: 'GHCR',
    liveUrl: 'https://github.com/kaluginvit/Portfolio/pkgs/container/autonomous-agents-backend',
  },
  {
    id: 'dostaffkin',
    category: '04',
    categoryLabel: 'Веб',
    title: 'Dostaffkin — доставка',
    result: 'Angular + Express, трекинг статусов; демо онлайн.',
    repoPath: '04-web/dostaffkin',
    liveLabel: 'GitHub Pages',
    liveUrl: 'https://kaluginvit72.github.io/dostaffkin/',
  },
  {
    id: 'mini-crm',
    category: '04',
    categoryLabel: 'Веб',
    title: 'Мини-CRM + Google',
    result: 'FastAPI + React, OAuth Drive/Sheets, выгрузка отчётов.',
    repoPath: '04-web/mini-crm-fastapi-react',
    liveLabel: 'Репозиторий',
    liveUrl: `${tree}/04-web/mini-crm-fastapi-react`,
  },
];

export const categoryFilters: { id: CaseCategory | 'all'; label: string }[] = [
  { id: 'all', label: 'Все' },
  { id: '01', label: '01 Аналитика' },
  { id: '02', label: '02 Автоматизация' },
  { id: '03', label: '03 ИИ-продукты' },
  { id: '04', label: '04 Веб' },
];
