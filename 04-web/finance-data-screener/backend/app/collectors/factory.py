from .base import BaseCollector
from .cbr import CbrCollector
from .moex import MoexCollector
from .rbc import RbcCollector

_REGISTRY: dict[str, type[BaseCollector]] = {
    "moex": MoexCollector,
    "cbr": CbrCollector,
    "rbc": RbcCollector,
}


class CollectorFactory:
    @classmethod
    def get(cls, source: str) -> BaseCollector:
        collector_cls = _REGISTRY.get(source.lower())
        if collector_cls is None:
            available = list(_REGISTRY)
            raise ValueError(f"Unknown source {source!r}. Available: {available}")
        return collector_cls()

    @classmethod
    def sources(cls) -> list[str]:
        return list(_REGISTRY)
