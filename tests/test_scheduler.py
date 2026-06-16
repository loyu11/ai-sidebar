import datetime
import tempfile
from pathlib import Path
import pytest
from scheduler import UpdateScheduler
from config import Config
from storage.db import Database
from fetcher.base import Fetcher
from storage.models import Item


class FakeAsyncFetcher(Fetcher):
    """返回两条测试数据的异步 Fetcher"""
    def __init__(self, name, category):
        super().__init__(name=name, category=category)
        self.fetch_count = 0

    async def fetch(self, db):
        self.fetch_count += 1
        now = datetime.datetime.now()
        return [
            Item(
                id=None, title=f"Test {self.fetch_count}A", source=self.name,
                url=f"https://x.com/{self.name}/{self.fetch_count}a", category=self.category,
                summary=None, published_at=now, fetched_at=now,
            ),
            Item(
                id=None, title=f"Test {self.fetch_count}B", source=self.name,
                url=f"https://x.com/{self.name}/{self.fetch_count}b", category=self.category,
                summary=None, published_at=now, fetched_at=now,
            ),
        ]


def test_scheduler_run_fetchers():
    config = Config(enable_summary=False)
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        db.init()
        fetchers = [
            FakeAsyncFetcher("test1", "ai_paper"),
            FakeAsyncFetcher("test2", "ai_industry"),
        ]
        scheduler = UpdateScheduler(config=config, db=db, fetchers=fetchers)
        # 直接调同步入口
        scheduler._run_once()
        for f in fetchers:
            assert f.fetch_count == 1
        items = db.query_recent(days=7)
        assert len(items) == 4


def test_scheduler_cleanup():
    config = Config(enable_summary=False)
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        db.init()
        # 插入一条过期数据
        old = Item(
            id=None, title="old", source="s", url="https://old.com",
            category="news", summary=None,
            published_at=datetime.datetime.now() - datetime.timedelta(days=20),
            fetched_at=datetime.datetime.now() - datetime.timedelta(days=20),
        )
        db.insert(old)
        fetchers = [FakeAsyncFetcher("test", "news")]
        scheduler = UpdateScheduler(config=config, db=db, fetchers=fetchers)
        scheduler._run_once()
        # 过期数据应被清理
        remaining = db.query_recent(days=30)
        assert all("old" not in r.title for r in remaining)
