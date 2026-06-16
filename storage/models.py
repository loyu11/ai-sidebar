import datetime
from dataclasses import dataclass
from typing import Optional


CATEGORY_LABELS = {
    "ai_paper": "AI 论文",
    "ai_industry": "AI 产业动态",
    "news": "国际/国内大新闻",
}


@dataclass
class Item:
    id: Optional[int]
    title: str
    source: str
    url: str
    category: str
    summary: Optional[str]
    published_at: datetime.datetime
    fetched_at: datetime.datetime

    def relative_time(self) -> str:
        now = datetime.datetime.now()
        diff = now - self.published_at.replace(tzinfo=None)
        minutes = int(diff.total_seconds() / 60)
        if minutes < 1:
            return "刚刚"
        elif minutes < 60:
            return f"{minutes} 分钟前"
        elif minutes < 1440:
            return f"{minutes // 60} 小时前"
        else:
            return f"{minutes // 1440} 天前"

    def category_label(self) -> str:
        return CATEGORY_LABELS.get(self.category, self.category)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "category": self.category,
            "category_label": self.category_label(),
            "summary": self.summary,
            "published_at": self.published_at.isoformat(),
            "relative_time": self.relative_time(),
        }
