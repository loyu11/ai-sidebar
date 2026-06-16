import datetime
import tempfile
from pathlib import Path
from storage.db import Database
from storage.models import Item


def test_insert_and_query():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        db.init()
        item = Item(
            id=None,
            title="测试标题",
            source="测试来源",
            url="https://example.com",
            category="ai_paper",
            summary=None,
            published_at=datetime.datetime(2026, 6, 15, 10, 0, 0),
            fetched_at=datetime.datetime(2026, 6, 16, 12, 0, 0),
        )
        saved = db.insert(item)
        assert saved.id == 1
        assert saved.title == "测试标题"

        results = db.query_recent(days=30)
        assert len(results) == 1
        assert results[0].title == "测试标题"


def test_deduplication():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        db.init()
        item = Item(
            id=None, title="dup", source="s", url="https://x.com/1",
            category="news", summary=None,
            published_at=datetime.datetime.now(),
            fetched_at=datetime.datetime.now(),
        )
        db.insert(item)
        assert db.exists_by_url("https://x.com/1")  # exists after insert


def test_update_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        db.init()
        item = Item(
            id=None, title="t", source="s", url="https://x.com/2",
            category="news", summary=None,
            published_at=datetime.datetime.now(),
            fetched_at=datetime.datetime.now(),
        )
        saved = db.insert(item)
        db.update_summary(saved.id, "这是一段 AI 摘要")
        results = db.query_recent(days=30)
        assert results[0].summary == "这是一段 AI 摘要"


def test_cleanup_old_items():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        db.init()
        old = Item(
            id=None, title="old", source="s", url="https://old.com",
            category="news", summary=None,
            published_at=datetime.datetime.now() - datetime.timedelta(days=20),
            fetched_at=datetime.datetime.now() - datetime.timedelta(days=20),
        )
        db.insert(old)
        db.cleanup(days=14)
        results = db.query_recent(days=30)
        assert len(results) == 0


def test_query_by_category():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        db.init()
        paper = Item(
            id=None, title="paper", source="arXiv", url="https://x.com/p",
            category="ai_paper", summary=None,
            published_at=datetime.datetime.now(),
            fetched_at=datetime.datetime.now(),
        )
        news = Item(
            id=None, title="news", source="新华社", url="https://x.com/n",
            category="news", summary=None,
            published_at=datetime.datetime.now(),
            fetched_at=datetime.datetime.now(),
        )
        db.insert(paper)
        db.insert(news)
        papers = db.query_by_category("ai_paper", days=7)
        assert len(papers) == 1
        assert papers[0].title == "paper"
