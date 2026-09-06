import asyncio
import ssl

import feedparser

from .base import BaseCollector

# РБК заблокировал server-side запросы (Qrator антибот) — используем ТАСС как fallback
_DEFAULT_URL = "https://tass.ru/rss/v2.xml"
_FALLBACK_URL = "https://tass.ru/rss/v2.xml"

# SSL-контекст без проверки сертификата (SSL-перехват корпоративного прокси/антивируса)
_NO_VERIFY_CTX = ssl.create_default_context()
_NO_VERIFY_CTX.check_hostname = False
_NO_VERIFY_CTX.verify_mode = ssl.CERT_NONE


def _fetch_feed(url: str):
    import urllib.request
    handler = urllib.request.HTTPSHandler(context=_NO_VERIFY_CTX)
    feed = feedparser.parse(url, handlers=[handler])
    # Если основной URL заблокирован — пробуем fallback
    if (feed.get("status") not in (200, 301) or not feed.entries) and url != _FALLBACK_URL:
        feed = feedparser.parse(_FALLBACK_URL, handlers=[handler])
    return feed


class RbcCollector(BaseCollector):
    async def _fetch(self, api_url: str) -> list[dict]:
        url = api_url or _DEFAULT_URL
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, _fetch_feed, url)
        return _parse_feed(feed)


def _parse_feed(feed) -> list[dict]:
    rows = []
    for entry in feed.entries:
        rows.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "published": entry.get("published", ""),
            "tags": [t.term for t in entry.get("tags", [])],
        })
    return rows
