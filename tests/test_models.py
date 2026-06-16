import datetime
from storage.models import Item

def test_item_creation():
    now = datetime.datetime(2026, 6, 16, 12, 0, 0)
    item = Item(
        id=None,
        title="GPT-5 训练架构解析",
        source="arXiv",
        url="https://arxiv.org/abs/2606.12345",
        category="ai_paper",
        summary=None,
        published_at=now,
        fetched_at=now,
    )
    assert item.title == "GPT-5 训练架构解析"
    assert item.category == "ai_paper"
    assert item.summary is None
    assert item.id is None

def test_item_relative_time():
    import datetime as dt
    now = dt.datetime.now()
    one_hour_ago = now - dt.timedelta(hours=1)
    item = Item(
        id=1, title="test", source="test", url="http://x",
        category="news", summary=None,
        published_at=one_hour_ago, fetched_at=now,
    )
    rel = item.relative_time()
    assert "小时前" in rel or "分钟" in rel  # at minimum contains a time description

def test_item_relative_time_days():
    import datetime as dt
    now = dt.datetime.now()
    three_days_ago = now - dt.timedelta(days=3)
    item = Item(
        id=1, title="test", source="test", url="http://x",
        category="news", summary=None,
        published_at=three_days_ago, fetched_at=now,
    )
    rel = item.relative_time()
    assert "天前" in rel

def test_item_category_labels():
    item = Item(
        id=1, title="test", source="test", url="http://x",
        category="ai_paper", summary=None,
        published_at=datetime.datetime.now(),
        fetched_at=datetime.datetime.now(),
    )
    assert item.category_label() == "AI 论文"
    item.category = "ai_industry"
    assert item.category_label() == "AI 产业动态"
    item.category = "news"
    assert item.category_label() == "国际/国内大新闻"
