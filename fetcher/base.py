from abc import ABC, abstractmethod

from storage.models import Item
from storage.db import Database


def match_keywords(title: str, keywords: list[str]) -> bool:
    """标题包含任意关键词即返回 True。空关键词列表视为全匹配。"""
    if not keywords:
        return True
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in keywords)


class Fetcher(ABC):
    def __init__(self, name: str, category: str, keywords: list[str] | None = None):
        self.name = name
        self.category = category
        self.keywords = keywords or []

    @abstractmethod
    async def fetch(self, db: Database) -> list[Item]:
        """拉取数据，返回新条目列表。由子类实现。"""
        ...
