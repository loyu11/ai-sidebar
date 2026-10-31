import datetime
from typing import Optional
import httpx
import feedparser
from fetcher.base import Fetcher
from storage.models import Item
from storage.db import Database


EXCLUDE_PATTERNS = ["娱乐", "体育", "八卦", "恋情", "综艺", "选秀", "真人秀"]


class RssFetcher(Fetcher):
    def __init__(
        self,
        name: str,
        url: str,
        category: str,
        exclude_keywords: list[str] | None = None,
    ):
        super().__init__(name=name, category=category, keywords=[])
        self.url = url
        self.exclude_keywords = exclude_keywords or EXCLUDE_PATTERNS

    async def fetch(self, db: Database) -> list[Item]:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                self.url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36"
                    ),
                },
            )
            response.raise_for_status()
        feed = feedparser.parse(response.text)
        new_items = []
        now = datetime.datetime.now()
        for entry in feed.entries:
            item = parse_rss_entry(
                entry,
                category=self.category,
                source=self.name,
                exclude_keywords=self.exclude_keywords,
            )
            if item is None:
                continue
            if db.exists_by_url(item.url):
                continue
            new_items.append(item)
        return new_items


def parse_rss_entry(
    entry: dict,
    category: str,
    source: str,
    exclude_keywords: list[str] | None = None,
) -> Optional[Item]:
    title = entry.get("title", "").strip()
    if not title:
        return None
    # 排除关键词
    if exclude_keywords:
        title_lower = title.lower()
        if any(kw.lower() in title_lower for kw in exclude_keywords):
            return None
    url = entry.get("link", "")
    published_at = datetime.datetime.now()
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            published_at = datetime.datetime(*entry.published_parsed[:6])
        except Exception:
            pass
    return Item(
        id=None,
        title=title,
        source=source,
        url=url,
        category=category,
        summary=None,
        published_at=published_at,
        fetched_at=datetime.datetime.now(),
    )
