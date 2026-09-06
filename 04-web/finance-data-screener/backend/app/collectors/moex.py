from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import httpx

from .base import BaseCollector


class MoexCollector(BaseCollector):
    async def _fetch(self, api_url: str) -> list[dict]:
        url = _prepare_url(api_url)
        # verify=False: SSL-перехват корпоративного прокси/антивируса в dev-окружении
        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        return _parse_iss_response(data)


def _prepare_url(api_url: str) -> str:
    parsed = urlparse(api_url)
    path = parsed.path
    if not path.endswith(".json"):
        path += ".json"

    params = parse_qs(parsed.query, keep_blank_values=True)
    params.setdefault("iss.meta", ["off"])

    query = urlencode(params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, query, parsed.fragment))


def _parse_iss_response(data: dict) -> list[dict]:
    # MOEX ISS returns columnar sections: {"securities": {"columns": [...], "data": [...]}, ...}
    # We collect rows from each section and merge same-length sections side by side.
    skip = {"metadata", "history.cursor", "marketdata_yields", "securities.cursor",
            "marketdata.cursor", "trades.cursor", "orderbook.cursor"}

    sections: list[list[dict]] = []
    for key, section in data.items():
        if key in skip:
            continue
        if not isinstance(section, dict):
            continue
        columns = section.get("columns")
        raw_data = section.get("data")
        if not columns or raw_data is None:
            continue
        rows = [dict(zip(columns, row)) for row in raw_data]
        if rows:
            sections.append(rows)

    if not sections:
        return []

    # Use the first section as the base; merge sections of equal length (e.g. securities + marketdata)
    base = sections[0]
    for extra in sections[1:]:
        if len(extra) == len(base):
            for i, row in enumerate(extra):
                base[i].update(row)

    return base
