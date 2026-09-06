import httpx

from .base import BaseCollector

# Default endpoint if LLM omits a URL
_DEFAULT_URL = "https://www.cbr-xml-daily.ru/daily_json.js"


class CbrCollector(BaseCollector):
    async def _fetch(self, api_url: str) -> list[dict]:
        url = api_url or _DEFAULT_URL
        # verify=False: SSL-перехват корпоративного прокси/антивируса в dev-окружении
        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        return _parse_cbr_response(data)


def _parse_cbr_response(data: dict) -> list[dict]:
    # daily_json.js format: {"Date": "...", "PreviousDate": "...", "Valute": {"USD": {...}, ...}}
    if "Valute" in data:
        date = data.get("Date", "")
        rows = []
        for code, info in data["Valute"].items():
            rows.append({
                "CharCode": code,
                "Name": info.get("Name", ""),
                "Nominal": info.get("Nominal"),
                "Value": info.get("Value"),
                "Previous": info.get("Previous"),
                "Date": date,
            })
        return rows

    # Archive endpoint returns list directly
    if isinstance(data, list):
        return data

    return [data]
