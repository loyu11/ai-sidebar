import datetime
import tempfile
from pathlib import Path
import pytest
from summarizer.llm_summarizer import Summarizer, build_summary_prompt
from storage.models import Item
from storage.db import Database
from config import Config


def test_build_summary_prompt():
    item = Item(
        id=1,
        title="GPT-5: Scaling Language Models with Multi-Modal Understanding",
        source="arXiv",
        url="https://arxiv.org/abs/2606.12345",
        category="ai_paper",
        summary=None,
        published_at=datetime.datetime.now(),
        fetched_at=datetime.datetime.now(),
    )
    prompt = build_summary_prompt(item)
    assert "GPT-5" in prompt
    assert "中文" in prompt
    assert "50-80字" in prompt
    assert item.url in prompt


def test_summarizer_disabled():
    cfg = Config(enable_summary=False)
    summarizer = Summarizer(cfg)
    assert not summarizer.enabled


def test_summarizer_empty_api_key():
    cfg = Config(enable_summary=True, api_key="")
    summarizer = Summarizer(cfg)
    assert not summarizer.enabled  # 无 API key 禁用


def test_summarizer_enabled():
    cfg = Config(enable_summary=True, api_key="sk-test123")
    summarizer = Summarizer(cfg)
    assert summarizer.enabled


def test_summarize_items_empty():
    cfg = Config(enable_summary=True, api_key="sk-test123")
    summarizer = Summarizer(cfg)
    # 在没有真实 API 的情况下，应该处理空列表而不报错
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        db.init()
        # 空数据库不应 crash
        items = db.query_without_summary(limit=10)
        assert len(items) == 0
