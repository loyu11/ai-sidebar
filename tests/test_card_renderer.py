import datetime
import json
from pathlib import Path
from ui.card_renderer import CardRenderer
from storage.models import Item


def test_render_items_to_json():
    items = [
        Item(
            id=1,
            title="GPT-5 发布",
            source="arXiv",
            url="https://arxiv.org/abs/2606.1",
            category="ai_paper",
            summary="GPT-5 在多模态理解上取得了突破。",
            published_at=datetime.datetime(2026, 6, 15, 10, 0, 0),
            fetched_at=datetime.datetime(2026, 6, 16, 12, 0, 0),
        ),
        Item(
            id=2,
            title="大新闻标题",
            source="新华社",
            url="https://xinhua.com/1",
            category="news",
            summary=None,
            published_at=datetime.datetime(2026, 6, 16, 8, 0, 0),
            fetched_at=datetime.datetime(2026, 6, 16, 12, 0, 0),
        ),
    ]
    json_str = CardRenderer.items_to_json(items)
    data = json.loads(json_str)
    assert len(data) == 2
    assert data[0]["title"] == "GPT-5 发布"
    assert data[0]["category_label"] == "AI 论文"
    assert data[1]["category_label"] == "国际/国内大新闻"
    assert data[0]["summary"] == "GPT-5 在多模态理解上取得了突破。"
    assert data[1]["summary"] is None
    assert "relative_time" in data[0]


def test_render_empty():
    json_str = CardRenderer.items_to_json([])
    data = json.loads(json_str)
    assert len(data) == 0
