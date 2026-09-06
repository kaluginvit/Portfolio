"""
Fetches Pesochnitsa Zerocoders channel messages since June 4
and generates a markdown analysis following pesochnitsa_analysis.md template.
"""
import asyncio, sys, json, re
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path

BASE = Path("C:/_рабочая_папка/проекты_программирование/tg_digest")
sys.path.insert(0, str(BASE / ".venv/Lib/site-packages"))

env_vars = {}
with open(BASE / ".env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env_vars[k.strip()] = v.strip().strip('"').strip("'")

api_id = int(env_vars['TG_API_ID'])
api_hash = env_vars['TG_API_HASH']

from telethon import TelegramClient
from telethon.tl.types import User, Channel

SINCE = datetime(2026, 6, 4, tzinfo=timezone.utc)
CHANNEL_ID = 1748730883

# ── FETCH ──────────────────────────────────────────────────────────────

async def fetch():
    client = TelegramClient(str(BASE / "session2"), api_id, api_hash)
    await client.connect()
    msgs = []
    async for msg in client.iter_messages(CHANNEL_ID, limit=1000):
        if msg.date < SINCE:
            break
        if msg.text and msg.text.strip():
            sender_name = ''
            if msg.sender:
                s = msg.sender
                if isinstance(s, Channel):
                    sender_name = s.title
                elif isinstance(s, User):
                    sender_name = f"{s.first_name or ''} {s.last_name or ''}".strip()
                    if s.username:
                        sender_name += f" (@{s.username})"
            msgs.append({
                'id': msg.id,
                'date': msg.date.isoformat(),
                'sender': sender_name,
                'text': msg.text,
                'views': getattr(msg, 'views', None),
            })
    await client.disconnect()
    msgs.reverse()
    print(f"Fetched: {len(msgs)} messages")
    return msgs

# ── PARSE ──────────────────────────────────────────────────────────────

def clean(t):
    return re.sub(r'[\*_]', '', str(t)).strip()

def first_line(text):
    return clean(next((l for l in text.split('\n') if l.strip()), ''))

def get_budget(text):
    for line in text.split('\n'):
        cl = clean(line)
        if re.search(r'бюджет|оплата|💲|зарплата', cl, re.I):
            return re.sub(r'💲', '', cl).strip()[:80]
    return ''

def get_link(text):
    tl = text.lower()
    if 'career.habr' in tl:
        m = re.search(r'https://career\.habr\.com/vacancies/[^\s\)\]]+', text)
        return ('Habr Career', m.group().rstrip(')') if m else '—')
    if 'hh.ru/vacancy' in tl:
        m = re.search(r'https://hh\.ru/vacancy/\d+', text)
        return ('hh.ru', m.group() if m else '—')
    if 'kwork.ru' in tl:
        m = re.search(r'https://kwork\.ru/[^\s\)\]]+', text)
        return ('Kwork', m.group().rstrip(')') if m else '—')
    if 'uslugi.yandex' in tl:
        m = re.search(r'https://uslugi\.yandex\.ru/order/[^\s\)\]]+', text)
        return ('Я.Исполнители', m.group().rstrip(')') if m else '—')
    usernames = re.findall(r'@(\w{4,})', text)
    if usernames:
        return ('Telegram', f"@{usernames[0]}")
    return ('', '')

def classify(msgs):
    vacancies, projects, requests, editorial, other = [], [], [], [], []
    for m in msgs:
        text, tl = m['text'], m['text'].lower()
        title = first_line(text)
        budget = get_budget(text)
        lt, lu = get_link(text)
        entry = {**m, 'title': title, 'budget': budget, 'link_type': lt, 'link_url': lu}
        if re.search(r'оплата\s+(от|до)\s+\d|зарплата|оплата\s+\d{2}', tl):
            vacancies.append(entry)
        elif re.search(r'бюджет\s+(до|от|по)', tl):
            projects.append(entry)
        elif re.search(r'запрос из чата|находится в поисках', tl):
            requests.append(entry)
        elif re.search(r'^(как |советы|гайд|способ|топ-\d|что такое|\d+ (способ|ошибк|инструмент|совет))', tl[:60]):
            editorial.append(entry)
        else:
            other.append(entry)
    return vacancies, projects, requests, editorial, other

# ── STACK ANALYSIS ──────────────────────────────────────────────────────

SKILL_MAP = {
    'Python': ['python'],
    'JavaScript / TypeScript': ['javascript', 'typescript'],
    'Dart / Flutter / FlutterFlow': ['dart', 'flutter', 'flutterflow'],
    'PHP / WordPress': ['php', 'wordpress'],
    'OpenAI API / ChatGPT': ['openai', 'chatgpt', 'gpt'],
    'Claude / Anthropic': ['claude', 'anthropic'],
    'DeepSeek': ['deepseek'],
    'LLM (общее)': ['llm'],
    'RAG': [' rag', 'retrieval'],
    'AI-агенты': ['агент', 'ai-агент'],
    'MCP': ['mcp'],
    'Промпт-инжиниринг': ['промпт', 'prompt'],
    'PostgreSQL / pgvector': ['postgresql', 'pgvector', 'postgres'],
    'SQL': [' sql'],
    'FastAPI': ['fastapi'],
    'REST API': ['rest api'],
    'n8n': ['n8n'],
    'Make / Zapier': ['make.com', 'zapier'],
    'Tilda': ['tilda'],
    'Figma': ['figma'],
    'Salebot': ['salebot'],
    'Docker / Git': ['docker', ' git '],
    'UI/UX дизайн': ['ui/ux', 'ux/ui'],
    'HTML/CSS': ['html', ' css'],
    'SEO': [' seo'],
    'Видеомонтаж': ['монтаж', 'рилс'],
    'Telegram Bot API': ['aiogram', 'telegram bot'],
    'ВКонтакте API': ['вконтакте api', 'vk api'],
    'RuStore / AppStore': ['rustore', 'app store'],
}

SKILL_CATEGORIES = {
    'Языки программирования': ['Python','JavaScript / TypeScript','Dart / Flutter / FlutterFlow','PHP / WordPress'],
    'AI / LLM': ['OpenAI API / ChatGPT','Claude / Anthropic','DeepSeek','LLM (общее)','RAG','AI-агенты','MCP','Промпт-инжиниринг'],
    'Базы данных / Backend': ['PostgreSQL / pgvector','SQL','FastAPI','REST API'],
    'No-code / Платформы': ['n8n','Make / Zapier','Tilda','Figma','Salebot'],
    'DevOps / Инфра': ['Docker / Git','RuStore / AppStore'],
    'Дизайн / Фронтенд': ['UI/UX дизайн','HTML/CSS','SEO'],
    'Интеграции': ['Telegram Bot API','ВКонтакте API'],
    'Не ваш профиль': ['Видеомонтаж'],
}

def count_skills(items):
    full = '\n'.join(p['text'] for p in items).lower()
    return {skill: sum(full.count(kw) for kw in kws)
            for skill, kws in SKILL_MAP.items()}

# ── BUDGET ESTIMATION ───────────────────────────────────────────────────

def estimate(title, text, budget_raw):
    tl = (title + ' ' + text).lower()
    nums = re.findall(r'\d{2,6}', budget_raw.replace(' ', ''))
    valid = [int(n) for n in nums if 10000 <= int(n) <= 500000]
    bnum = max(valid) if valid else 0

    if any(w in tl for w in ['генератор','скрипт']) and any(w in tl for w in ['chatgpt','openai','gpt','api']):
        return '2–8 часов', '30–50К', 'GOLD'
    if any(w in tl for w in ['автоматизац','публикаци','постинг']):
        return '4–8 часов', '30–45К', 'OK'
    if any(w in tl for w in ['telegram','бот','ассистент','консультант']) and any(w in tl for w in ['llm','gpt','chatgpt','ии','ai']):
        return '1–2 дня', '50–80К', 'OK'
    if any(w in tl for w in ['rag','подбор по','поиск по','семантическ']):
        return '2–4 дня', '60–100К', 'WARN' if bnum < 60000 else 'OK'
    if any(w in tl for w in ['лендинг','одностраничн']):
        return '4–8 часов', '20–40К', 'OK'
    if 'wordpress' in tl and 'платформ' not in tl:
        return '4–8 часов', '20–40К', 'OK'
    if 'tilda' in tl or ('сайт' in tl and any(w in tl for w in ['косметолог','клиник','центр','студи','школ'])):
        return '2–4 дня', '80–150К', 'OK' if bnum >= 80000 else 'WARN'
    if any(w in tl for w in ['образовательн','платформ','lms']):
        return '1–2 недели', '120–200К', 'WARN' if bnum < 100000 else 'OK'
    if any(w in tl for w in ['мобильн','android','ios','flutter']):
        return '1–2 недели', '150–250К', 'OK' if bnum >= 150000 else 'WARN'
    if any(w in tl for w in ['crm','система управлени','жкх']):
        return '2–4 недели', '200–400К', 'WARN' if bnum < 200000 else 'OK'
    if any(w in tl for w in ['python','backend','разработчик','fastapi']):
        return '—', '150–250К/мес', 'OK'
    if any(w in tl for w in ['дизайн','figma',' ui ',' ux ']):
        return '2–5 дней', '40–80К', 'OK' if bnum >= 40000 else 'WARN'
    return '2–5 дней', 'по задаче', 'WARN'

VERDICT = {'GOLD': '✅ Золото', 'OK': '✅ Брать', 'WARN': '⚠️ Торговаться', 'NO': '❌ Не брать'}

# ── MARKDOWN GENERATION ─────────────────────────────────────────────────

def build_md(vacancies, projects, requests, editorial, other, skill_counts):
    total = len(vacancies) + len(projects) + len(requests) + len(editorial) + len(other)
    all_actionable = vacancies + projects + requests

    md = []

    # Заголовок
    md += [
        "# Анализ канала «Песочница Зерокодеров» — 4 июня — 19 июля 2026\n",
        "---\n",
        f"## 1. Обзор канала — {total} сообщений с 4 июня\n",
        "**Канал:** Песочница Зерокодеров (id=1748730883), аккаунт @KaluginVit\n",
        "**Формат:** микс заказов/вакансий от агрегатора + запросы участников + редакционные статьи.\n",
        "",
        "| Тип контента | Кол-во |",
        "|---|---|",
        f"| Вакансии (с окладом) | {len(vacancies)} |",
        f"| Фриланс-проекты (с бюджетом) | {len(projects)} |",
        f"| Запросы участников | {len(requests)} |",
        f"| Редакционные статьи/советы | {len(editorial)} |",
        f"| Прочее | {len(other)} |",
        f"| **Итого** | **{total}** |",
        "",
    ]

    # Вакансии
    md += [
        f"### Вакансии с окладом ({len(vacancies)} постов)\n",
        "| Дата | Позиция | Оплата |",
        "|------|---------|--------|",
    ]
    for p in vacancies:
        md.append(f"| {p['date']} | {clean(p['title'])[:60]} | {clean(p['budget'])[:50]} |")
    md.append("")

    # Проекты
    md += [
        f"### Фриланс-проекты ({len(projects)} постов)\n",
        "| Дата | Проект | Бюджет |",
        "|------|--------|--------|",
    ]
    for p in projects:
        md.append(f"| {p['date']} | {clean(p['title'])[:65]} | {clean(p['budget'])[:50]} |")
    md.append("")

    # Запросы участников
    md.append(f"### Запросы участников ({len(requests)} постов)\n")
    for p in requests:
        usernames = re.findall(r'@(\w{4,})', p['text'])
        contact = f"@{usernames[0]}" if usernames else "—"
        lines = [clean(l) for l in p['text'].split('\n')
                 if len(clean(l)) > 10 and 'http' not in l and 'откликнуть' not in l.lower()]
        desc = lines[1][:120] if len(lines) > 1 else ''
        md.append(f"- **{p['date']}** | {clean(p['title'])[:70]} | Контакт: {contact}")
        if desc:
            md.append(f"  _{desc}_")
    md.append("")

    # Редакционные
    md.append(f"### Редакционные статьи ({len(editorial)} постов)\n")
    for p in sorted(editorial, key=lambda x: x['date']):
        md.append(f"- {p['date']} — {clean(p['title'])[:90]}")
    md.append("")

    # ── ОТКЛИКИ ──
    md += ["---\n", "## 2. Все посты — способы отклика\n"]

    by_platform = defaultdict(list)
    for p in all_actionable:
        by_platform[p['link_type'] or ''].append(p)

    platform_order = ['hh.ru', 'Habr Career', 'Telegram', 'Kwork', 'Я.Исполнители', '']
    platform_labels = {
        'hh.ru': '### hh.ru',
        'Habr Career': '### Habr Career',
        'Telegram': '### Telegram — написать в ЛС',
        'Kwork': '### Kwork',
        'Я.Исполнители': '### Яндекс.Исполнители',
        '': '### Без явного контакта',
    }
    for plat in platform_order:
        items = by_platform.get(plat, [])
        if not items:
            continue
        md += [
            f"\n{platform_labels.get(plat, '### ' + plat)} ({len(items)})\n",
            "| Дата | Позиция/Проект | Бюджет | Ссылка |",
            "|------|----------------|--------|--------|",
        ]
        for p in items:
            url = (p['link_url'] or '—')[:80]
            md.append(f"| {p['date']} | {clean(p['title'])[:55]} | {clean(p['budget'])[:35]} | {url} |")
    md.append("")

    # ── СТЕК ──
    md += ["---\n", "## 3. Стек — что нужно знать\n",
           "### Полная карта навыков\n",
           "| Навык | Упоминаний | Спрос |",
           "|-------|-----------|-------|"]

    for cat, skills in SKILL_CATEGORIES.items():
        shown = [(s, skill_counts.get(s, 0)) for s in skills if skill_counts.get(s, 0) > 0]
        if not shown:
            continue
        md.append(f"| **{cat}** | | |")
        for skill, cnt in sorted(shown, key=lambda x: -x[1]):
            fire = '🔥🔥🔥' if cnt >= 10 else ('🔥🔥' if cnt >= 4 else '🔥')
            md.append(f"| {skill} | {cnt} | {fire} |")
    md.append("")

    md += [
        "### Минимальный стек для профиля «финансист + ИТ»\n",
        "```",
        "1. Python — уверенный уровень",
        "   +-- FastAPI для простых API",
        "   +-- aiogram для Telegram-ботов",
        "",
        "2. OpenAI API",
        "   +-- Chat Completions, Function Calling, Assistants API",
        "   +-- Embeddings для RAG",
        "",
        "3. Промпт-инжиниринг",
        "   +-- системные промпты, цепочки, few-shot",
        "",
        "4. Базовый RAG",
        "   +-- LangChain или LlamaIndex",
        "   +-- pgvector или ChromaDB",
        "",
        "5. n8n (бонус)",
        "   +-- автоматизации без кода, быстрая сборка пайплайнов",
        "```",
        "",
    ]

    # ── БЮДЖЕТЫ ──
    md += [
        "---\n",
        "## 4. Время и адекватный бюджет — пересчёт с учётом вайбкодинга\n",
        "**Правило:** AI-разработка (Claude Code, Cursor) сжимает время в 3–10x по сравнению с ручным кодом.\n",
        "| Проект | Заявлено | Срок (вайбкод) | Адекватная цена | Вердикт |",
        "|--------|----------|----------------|-----------------|---------|",
    ]
    for p in vacancies + projects:
        title = clean(p['title'])[:60]
        budget = clean(p['budget'])[:35]
        t, price, v = estimate(p['title'], p.get('text', ''), p['budget'])
        md.append(f"| **{title}** | {budget} | {t} | {price} | {VERDICT.get(v, v)} |")
    md += [
        "",
        "### Главный вывод\n",
        "При вайбкодинге большинство AI/LLM-задач укладываются в 1–2 дня, сайты — в часы.",
        "Самый высокий ROI — короткие автоматизации и Telegram-боты с LLM: 2–8 часов работы → 30–60К.",
        "Крупные платформы без нормального бюджета — торговаться или не брать.",
    ]

    return '\n'.join(md)


# ── MAIN ────────────────────────────────────────────────────────────────

async def main():
    msgs = await fetch()
    vacancies, projects, requests, editorial, other = classify(msgs)
    skill_counts = count_skills(vacancies + projects + requests)
    md = build_md(vacancies, projects, requests, editorial, other, skill_counts)
    out = BASE / "chat_summaries/pesochnitsa_channel_analysis.md"
    out.write_text(md, encoding='utf-8')
    print(f"Saved: {out}")
    print(f"Вакансии: {len(vacancies)}, Проекты: {len(projects)}, Запросы: {len(requests)}, Редакционные: {len(editorial)}, Прочее: {len(other)}")

asyncio.run(main())
