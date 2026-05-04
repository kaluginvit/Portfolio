export interface ServicePackage {
  slug: string;
  title: string;
  tagline: string;
  problem: string;
  deliverables: string[];
  timeline: string;
  repoFolder: string;
}

export const packages: ServicePackage[] = [
  {
    slug: 'analytics',
    title: 'Аналитика и решения',
    tagline: 'От данных к решению для руководства.',
    problem:
      'Нужны ясные выводы из данных: отчёты, гипотезы, A/B, юнит-экономика — без «красивых картинок ради картинок».',
    deliverables: [
      'EDA и проверка качества данных',
      'Дашборды и сценарии для стейкхолдеров',
      'A/B-тесты, MDE, продуктовые рекомендации',
      'Юнит-экономика и отчёты под решение',
    ],
    timeline: '1–3 недели в зависимости от объёма',
    repoFolder: '01-data-analytics',
  },
  {
    slug: 'automation',
    title: 'Автоматизация процессов',
    tagline: 'n8n, интеграции, скрапинг — меньше ручного труда.',
    problem:
      'Потоки лидов, бронирования, синхронизация хранилищ и уведомления должны работать без Excel и ночных ручных выгрузок.',
    deliverables: [
      'Сценарии n8n и связанные workflow',
      'Интеграции: Tally, Supabase, Sheets, Drive и др.',
      'Скрапинг и регулярные задачи по расписанию',
      'Docker / GHCR при необходимости',
    ],
    timeline: '1–2 недели на типовой сценарий',
    repoFolder: '02-automation',
  },
  {
    slug: 'ai-products',
    title: 'ИИ-продукты',
    tagline: 'Боты, MCP, RAG и агенты — до продакшена.',
    problem:
      'Нужен рабочий контур: Telegram, корпоративный чат, MCP для инструментов, RAG по вашим документам.',
    deliverables: [
      'Telegram-боты под анкеты, лиды, расчёты',
      'MCP-серверы под внутренние данные и API',
      'RAG (Haystack / Pinecone и др.)',
      'Агенты на OpenAI / Anthropic по задаче',
    ],
    timeline: '2–4 недели',
    repoFolder: '03-ai-products',
  },
  {
    slug: 'web-mvp',
    title: 'Веб-MVP',
    tagline: 'Next.js / Angular + бэкенд + БД + деплой.',
    problem:
      'Нужен быстрый веб-продукт: формы, квиз, личный кабинет, интеграция с ботом — с понятным деплоем.',
    deliverables: [
      'Фронт и API под ваш сценарий',
      'Postgres и миграции по необходимости',
      'Домен, HTTPS, CI/CD по шаблону',
    ],
    timeline: '2–4 недели',
    repoFolder: '04-web',
  },
  {
    slug: 'consulting',
    title: 'ИИ-консалтинг и стратегия',
    tagline: 'Аудит, дорожная карта, обучение команды.',
    problem:
      'Нужно понять, куда внедрять ИИ в процессах и с чего начать пилот без лишнего хайпа.',
    deliverables: [
      'Аудит процесса и ограничений',
      'Дорожная карта внедрения',
      'Формат обучения / воркшоп под команду',
    ],
    timeline: 'От одной встречи до плана',
    repoFolder: '05-ai-consulting',
  },
];
