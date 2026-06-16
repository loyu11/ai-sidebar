import datetime
import xml.etree.ElementTree as ET
from typing import Optional
import httpx
from fetcher.base import Fetcher, match_keywords
from storage.models import Item
from storage.db import Database


ARXIV_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.CV"]
ARXIV_API_BASE = "http://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"


class ArxivFetcher(Fetcher):
    def __init__(self, keywords: list[str] | None = None):
        super().__init__(
            name="arXiv",
            category="ai_paper",
            keywords=keywords or [],
        )

    def _build_url(self) -> str:
        cat_query = "+OR+".join(f"cat:{c}" for c in ARXIV_CATEGORIES)
        url = (
            f"{ARXIV_API_BASE}?search_query={cat_query}"
            "&start=0&max_results=30&sortBy=submittedDate&sortOrder=descending"
        )
        return url

    async def fetch(self, db: Database) -> list[Item]:
        url = self._build_url()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
        root = ET.fromstring(response.text)
        entries = root.findall(f"{ATOM_NS}entry")
        new_items = []
        now = datetime.datetime.now()
        for entry in entries:
            item = parse_arxiv_entry(entry, self.keywords)
            if item is None:
                continue
            if db.exists_by_url(item.url):
                continue
            item.fetched_at = now
            new_items.append(item)
        return new_items

    @staticmethod
    def _extract_title(entry: ET.Element) -> str:
        title_el = entry.find(f"{ATOM_NS}title")
        if title_el is None or title_el.text is None:
            return "Untitled"
        return " ".join(title_el.text.strip().split())


def parse_arxiv_entry(entry: ET.Element, keywords: list[str]) -> Optional[Item]:
    title = ArxivFetcher._extract_title(entry)
    if not match_keywords(title, keywords):
        return None
    id_el = entry.find(f"{ATOM_NS}id")
    url = id_el.text.strip() if id_el is not None and id_el.text else ""
    published_el = entry.find(f"{ATOM_NS}published")
    published_str = (
        published_el.text.strip()
        if published_el is not None and published_el.text
        else datetime.datetime.now().isoformat()
    )
    published_at = datetime.datetime.fromisoformat(
        published_str.replace("Z", "+00:00")
    ).replace(tzinfo=None)
    return Item(
        id=None,
        title=title,
        source="arXiv",
        url=url,
        category="ai_paper",
        summary=None,
        published_at=published_at,
        fetched_at=datetime.datetime.now(),
    )
