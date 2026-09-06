"""
Каталог ресурсов из coding_community.
Читает данные напрямую из links_catalog, переводит описания через Haiku.

Использование:
    uv run python chat_summaries/coding_community/resources_catalog.py
"""

import json
import re
import sqlite3
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parents[1]))
from llm_client import call_llm

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path(__file__).parent / 'messages.db'
OUT_DIR = Path(__file__).parent / 'output'
OUT_DIR.mkdir(exist_ok=True)
_ENV_PATH = Path(__file__).parents[2] / '.env'

RESOURCE_KINDS = (
    'github_repo', 'github', 'huggingface', 'arxiv', 'arxiv_other',
    'video', 'telegram_channel',
)

TRANSLATE_PROMPT = """Переведи описания ресурсов на русский язык. Переводи кратко и точно.
Для каждой строки верни: ключ: перевод
Только ключ, двоеточие, русский перевод. Без объяснений.

--- ОПИСАНИЯ ---
{descriptions}
--- КОНЕЦ ---"""


def load_catalog() -> list[dict]:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            f"""
            SELECT url_normalized, kind, title, description, metadata_json,
                   section_id, section_name, filtered_mentions, score
            FROM links_catalog
            WHERE kind IN ({','.join('?' * len(RESOURCE_KINDS))})
              AND filtered_mentions > 0
              AND enrich_status IN ('ok', 'offline_context')
            ORDER BY section_id, score DESC, filtered_mentions DESC, url_normalized
            """,
            RESOURCE_KINDS,
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def translate_descriptions(items: list[dict]) -> dict[str, str]:
    to_translate = {
        str(i): it['description']
        for i, it in enumerate(items)
        if it.get('description') and it['kind'] in ('github_repo', 'github', 'arxiv', 'arxiv_other')
    }
    if not to_translate:
        return {}
    compact = '\n'.join(f"{k}: {v[:200]}" for k, v in to_translate.items())
    prompt = TRANSLATE_PROMPT.format(descriptions=compact)
    print(f'  Промпт: {len(prompt):,} символов (~{len(prompt)//4:,} токенов)')
    raw, _model, usage = call_llm(
        messages=[{'role': 'user', 'content': prompt}],
        env_path=_ENV_PATH,
    )
    print(f'  in={usage.get("tokens_input","?")} out={usage.get("tokens_output","?")}')
    result = {}
    for line in raw.splitlines():
        m = re.match(r'^(\d+)\s*:\s*(.+)', line.strip())
        if m:
            result[m.group(1)] = m.group(2).strip()
    print(f'  Переведено: {len(result)} из {len(to_translate)}')
    return result


def meta(item: dict) -> dict:
    try:
        return json.loads(item['metadata_json']) if item['metadata_json'] else {}
    except Exception:
        return {}


def format_line(item: dict, desc_ru: str) -> str:
    url = item['url_normalized']
    kind = item['kind']
    title = item['title'] or urlparse(url).path.strip('/') or url
    m = meta(item)

    if kind == 'github_repo':
        stars = m.get('stars', '')
        lang = m.get('language', '')
        archived = ' [архив]' if m.get('archived') else ''
        stars_str = f' ⭐{stars}' if stars != '' else ''
        lang_str = f' | {lang}' if lang else ''
        desc_str = f' | {desc_ru}' if desc_ru else ''
        return f"[{title}]({url}){archived}{stars_str}{lang_str}{desc_str}"

    if kind == 'huggingface':
        likes = m.get('likes', '')
        downloads = m.get('downloads', '')
        pipeline = m.get('pipeline_tag', '')
        likes_str = f' ❤️{likes}' if likes != '' else ''
        dl_str = f' ⬇️{downloads:,}' if isinstance(downloads, int) else ''
        pipe_str = f' `{pipeline}`' if pipeline else ''
        return f"[{title}]({url}){likes_str}{dl_str}{pipe_str}"

    if kind in ('arxiv', 'arxiv_other'):
        published = m.get('published', '')
        pub_str = f' ({published})' if published else ''
        desc_str = f' — {desc_ru}' if desc_ru else ''
        return f"**[{title}]({url})**{pub_str}{desc_str}"

    if kind == 'telegram_channel':
        handle = urlparse(url).path.strip('/') or title
        return f"[@{handle}]({url}) | {item['filtered_mentions']} упом."

    if kind == 'video':
        return f"[{title}]({url}) | {item['filtered_mentions']} упом."

    return f"[{title}]({url})"


def main() -> None:
    print('Загружаем links_catalog...')
    items = load_catalog()
    print(f'Ресурсов: {len(items)}')

    print('\n── Перевод описаний (Haiku) ──')
    translations = translate_descriptions(items)

    # Группируем по секциям
    sections: dict[int, dict] = {}
    for i, item in enumerate(items):
        sid = item['section_id']
        if sid not in sections:
            sections[sid] = {'name': item['section_name'], 'items': []}
        desc_ru = translations.get(str(i), item.get('description') or '')
        sections[sid]['items'].append((item, desc_ru))

    # Формируем Markdown
    parts = [
        '# Каталог ресурсов coding_community',
        '',
        f'_{len(items)} ресурсов | только ok/offline_context | отсортировано по score_',
        '',
    ]
    for sid in sorted(sections):
        sec = sections[sid]
        cnt = len(sec['items'])
        parts.append(f"## {sid}. {sec['name']} ({cnt})")
        for item, desc_ru in sec['items']:
            line = format_line(item, desc_ru)
            parts.append(f'- {line}')
        parts.append('')

    out = OUT_DIR / 'resources_catalog.md'
    out.write_text('\n'.join(parts), encoding='utf-8')
    print(f'\nКаталог: {out} ({len(items)} ресурсов)')


if __name__ == '__main__':
    main()
