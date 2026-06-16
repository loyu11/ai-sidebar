import datetime
from fetcher.base import Fetcher, match_keywords
from storage.models import Item


class FakeFetcher(Fetcher):
    """返回固定数据的测试用 Fetcher"""

    def __init__(self):
        super().__init__(
            name="fake",
            category="ai_paper",
            keywords=["GPT", "LLM"],
        )
        self._items = [
            Item(
                id=None,
                title="GPT-5 发布",
                source="fake",
                url="https://fake.com/1",
                category="ai_paper",
                summary=None,
                published_at=datetime.datetime.now(),
                fetched_at=datetime.datetime.now(),
            ),
            Item(
                id=None,
                title="蛋白质折叠突破",
                source="fake",
                url="https://fake.com/2",
                category="ai_paper",
                summary=None,
                published_at=datetime.datetime.now(),
                fetched_at=datetime.datetime.now(),
            ),
        ]

    async def fetch(self, db):
        return self._items


def test_match_keywords():
    assert match_keywords("GPT-5 训练架构解析", ["GPT", "LLM"]) is True
    assert match_keywords("蛋白质折叠突破", ["GPT", "LLM"]) is False
    assert match_keywords("多模态大模型综述", ["多模态", "GPT"]) is True
    assert match_keywords("hello world", []) is True  # 空关键词 = 全收
    assert match_keywords("LLaMA 3 开源发布", ["LLM", "GPT", "LLaMA"]) is True


def test_fetcher_filter_by_keywords():
    f = FakeFetcher()
    items = f._items
    filtered = [i for i in items if match_keywords(i.title, f.keywords)]
    assert len(filtered) == 1
    assert filtered[0].title == "GPT-5 发布"


def test_fetcher_name_and_category():
    f = FakeFetcher()
    assert f.name == "fake"
    assert f.category == "ai_paper"
    assert f.keywords == ["GPT", "LLM"]
