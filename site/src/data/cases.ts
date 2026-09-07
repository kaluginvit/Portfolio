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
  // ── TIER A — Core Showcase (7 проектов, featured) ───────────────────────

  {
    id: 'hr-breaker',
    category: '03',
    categoryLabel: 'ИИ-продукты',
    title: 'HR-Breaker — оптимизация резюме',
    result: 'Pydantic-AI + FastAPI: любой формат резюме → ATS-оптимизированный PDF. 192 теста, 8 фильтров, без галлюцинаций.',
    repoPath: '03-ai-products/hr-breaker',
    liveLabel: 'FastAPI + CLI',
    liveUrl: `${tree}/03-ai-products/hr-breaker`,
    featured: true,
  },
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
    id: 'svo-bot',
    category: '03',
    categoryLabel: 'ИИ-продукты',
    title: 'Telegram-бот выплат (СВО)',
    result: 'Production FSM-бот: анкета, расчёт, заявки; Docker, CI/CD, GHCR.',
    repoPath: '03-ai-products/svo-payments-bot',
    liveLabel: 'GHCR',
    liveUrl: 'https://github.com/kaluginvit/Portfolio/pkgs/container/svo-payments-bot',
    featured: true,
  },
  {
    id: 'svo-web',
    category: '04',
    categoryLabel: 'Веб',
    title: 'Сайт СВО — выплаты семьям',
    result: 'Production Next.js 14 + TypeScript: квиз, лид-форма, Playwright E2E, CI/CD → VPS.',
    repoPath: '04-web/svo-payouts-website',
    liveLabel: 'svorazbor.ru',
    liveUrl: 'https://svorazbor.ru',
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
    id: 'leadgen-n8n',
    category: '02',
    categoryLabel: 'Автоматизация',
    title: 'Лидогенерация на n8n',
    result: '11 воркфлоу: интент → обогащение → Multi-LLM консенсус → human-in-the-loop → nurture → отчётность.',
    repoPath: '02-automation/leadgen-n8n-system',
    liveLabel: 'docker compose',
    liveUrl: `${tree}/02-automation/leadgen-n8n-system`,
    featured: true,
  },
  {
    id: 'fedresurs',
    category: '01',
    categoryLabel: 'Аналитика',
    title: 'Fedresurs MVP — оценка лотов банкротства',
    result: 'P25/P50/P75 по аналогам + LLM-агент с web-поиском. 64 теста бизнес-логики, 4 ценовых сценария.',
    repoPath: '01-data-analytics/fedresurs-mvp',
    liveLabel: 'Flask UI',
    liveUrl: `${tree}/01-data-analytics/fedresurs-mvp`,
    featured: true,
  },
  {
    id: 'fintech-ab',
    category: '01',
    categoryLabel: 'Аналитика',
    title: 'A/B-тест в финтех',
    result: 'Welch t-test, MDE, power-анализ, SQL pipeline — методологически корректный кейс с продуктовой рекомендацией.',
    repoPath: '01-data-analytics/fintech-ab-test-credit-offer',
    liveLabel: 'nbviewer',
    liveUrl:
      'https://nbviewer.org/github/kaluginvit/Portfolio/blob/main/01-data-analytics/fintech-ab-test-credit-offer/notebooks/ab_test_analysis_showcase.ipynb',
    featured: true,
  },

  // ── TIER B — More Projects (5 проектов) ──────────────────────────────────

  {
    id: 'rf-macro-risk',
    category: '03',
    categoryLabel: 'ИИ-продукты',
    title: 'RF Macro Outlook AI',
    result: 'LangChain-агент: 35 макро-критериев → риск кризисного сценария на 6 месяцев + еженедельный live-отчёт.',
    repoPath: '03-ai-products/rf-macro-risk-ai',
    liveLabel: 'Live-отчёт',
    liveUrl: 'https://kaluginvit.github.io/rf-macro-risk-ai/',
  },
  {
    id: 'mini-crm',
    category: '04',
    categoryLabel: 'Веб',
    title: 'Мини-CRM + Google',
    result: 'FastAPI + React, OAuth Drive/Sheets, выгрузка отчётов в Google Таблицы.',
    repoPath: '04-web/mini-crm-fastapi-react',
    liveLabel: 'Репозиторий',
    liveUrl: `${tree}/04-web/mini-crm-fastapi-react`,
  },
  {
    id: 'team-bot',
    category: '03',
    categoryLabel: 'ИИ-продукты',
    title: 'RAG-бот команды (Haystack + Pinecone)',
    result: 'Корпоративный AI-ассистент: база знаний команды, семантический поиск, Telegram-интерфейс.',
    repoPath: '03-ai-products/team-ai-bot',
    liveLabel: 'Репозиторий',
    liveUrl: `${tree}/03-ai-products/team-ai-bot`,
  },
  {
    id: 'hotel-booking-n8n',
    category: '02',
    categoryLabel: 'Автоматизация',
    title: 'Автобронирование отелей (n8n)',
    result: 'n8n + Supabase: заявка → проверка номеров → бронь → email клиенту → ежедневный отчёт менеджеру.',
    repoPath: '02-automation/hotel-booking-n8n',
    liveLabel: 'Репозиторий',
    liveUrl: `${tree}/02-automation/hotel-booking-n8n`,
  },
  {
    id: 'superstore',
    category: '01',
    categoryLabel: 'Аналитика',
    title: 'Retail-аналитика Superstore',
    result: 'Интерактивный дашборд Plotly + инсайты по прибыльности категорий и сегментов.',
    repoPath: '01-data-analytics/superstore-retail-analytics',
    liveLabel: 'Дашборд',
    liveUrl: 'https://kaluginvit.github.io/Portfolio/superstore/',
  },
];

export const categoryFilters: { id: CaseCategory | 'all'; label: string }[] = [
  { id: 'all', label: 'Все' },
  { id: '01', label: '01 Аналитика' },
  { id: '02', label: '02 Автоматизация' },
  { id: '03', label: '03 ИИ-продукты' },
  { id: '04', label: '04 Веб' },
];
