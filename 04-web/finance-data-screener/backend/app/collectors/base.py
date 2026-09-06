from abc import ABC, abstractmethod


class BaseCollector(ABC):
    async def collect(
        self,
        api_url: str,
        fields_to_keep: list[str],
        filters: dict,
    ) -> list[dict]:
        rows = await self._fetch(api_url)
        if fields_to_keep:
            rows = _filter_fields(rows, fields_to_keep)
        if filters:
            rows = _apply_filters(rows, filters)
        return rows

    @abstractmethod
    async def _fetch(self, api_url: str) -> list[dict]: ...


def _filter_fields(rows: list[dict], fields: list[str]) -> list[dict]:
    field_set = set(fields)
    return [{k: v for k, v in row.items() if k in field_set} for row in rows]


def _apply_filters(rows: list[dict], filters: dict) -> list[dict]:
    return [row for row in rows if _matches(row, filters)]


def _matches(row: dict, filters: dict) -> bool:
    ops = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<=", "eq": "=="}
    for field, condition in filters.items():
        value = row.get(field)
        if value is None:
            return False
        for op, threshold in condition.items():
            try:
                v = float(value)
                t = float(threshold)
            except (TypeError, ValueError):
                v, t = value, threshold
            if op == "gt" and not (v > t):
                return False
            elif op == "gte" and not (v >= t):
                return False
            elif op == "lt" and not (v < t):
                return False
            elif op == "lte" and not (v <= t):
                return False
            elif op == "eq" and not (v == t):
                return False
    return True
