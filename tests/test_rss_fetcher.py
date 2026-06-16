import datetime
import tempfile
from pathlib import Path
from fetcher.rss_fetcher import RssFetcher, parse_rss_entry
from storage.db import Database

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>机器之心</title>
    <item>
        <title>OpenAI 发布 GPT-5：多模态能力全面升级</title>
        <link>https://jiqizhixin.com/articles/2026-06-15-1</link>
        <description>详细报道...</description>
        <pubDate>Mon, 15 Jun 2026 10:00:00 +0800</pubDate>
    </item>
    <item>
        <title>某明星恋情曝光</title>
        <link>https://example.com/entertainment</link>
        <description>娱乐新闻...</description>
        <pubDate>Mon, 15 Jun 2026 09:00:00 +0800</pubDate>
    </item>
</channel>
</rss>"""

EXCLUDE_KEYWORDS = ["娱乐", "体育", "八卦", "恋情", "综艺"]


def test_rss_fetcher_creation():
    fetcher = RssFetcher(
        name="机器之心",
        url="https://rss.example.com/feed",
        category="ai_industry",
    )
    assert fetcher.name == "机器之心"
    assert fetcher.url == "https://rss.example.com/feed"
    assert fetcher.category == "ai_industry"


def test_parse_rss_entry():
    import feedparser
    feed = feedparser.parse(SAMPLE_RSS)
    assert len(feed.entries) == 2
    item = parse_rss_entry(
        feed.entries[0],
        category="ai_industry",
        source="机器之心",
        exclude_keywords=EXCLUDE_KEYWORDS,
    )
    assert item is not None
    assert "GPT-5" in item.title
    assert item.source == "机器之心"
    assert item.category == "ai_industry"
    assert item.url == "https://jiqizhixin.com/articles/2026-06-15-1"


def test_parse_rss_entry_excluded():
    import feedparser
    feed = feedparser.parse(SAMPLE_RSS)
    # 第二条是娱乐新闻，应被过滤
    item = parse_rss_entry(
        feed.entries[1],
        category="news",
        source="test",
        exclude_keywords=EXCLUDE_KEYWORDS,
    )
    assert item is None


def test_parse_rss_entry_no_exclude_keywords():
    import feedparser
    feed = feedparser.parse(SAMPLE_RSS)
    # 不传 exclude_keywords 应全收
    item = parse_rss_entry(
        feed.entries[1],
        category="news",
        source="test",
    )
    assert item is not None
    assert "恋情" in item.title
