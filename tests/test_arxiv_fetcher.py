import datetime
import tempfile
from pathlib import Path
import pytest
from fetcher.arxiv_fetcher import ArxivFetcher, parse_arxiv_entry
from storage.db import Database


SAMPLE_XML_ENTRY = """<entry xmlns="http://www.w3.org/2005/Atom">
    <id>http://arxiv.org/abs/2606.12345v1</id>
    <title>GPT-5: Scaling Language Models with Multi-Modal Understanding</title>
    <published>2026-06-15T00:00:00Z</published>
    <summary>This paper presents GPT-5 architecture.</summary>
</entry>"""

SAMPLE_XML_FEED = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>ArXiv Query</title>
    {SAMPLE_XML_ENTRY}
    <entry>
        <id>http://arxiv.org/abs/2606.99999v1</id>
        <title>Protein Folding without AI</title>
        <published>2026-06-14T00:00:00Z</published>
        <summary>Biology paper.</summary>
    </entry>
</feed>"""


def test_parse_arxiv_entry():
    import xml.etree.ElementTree as ET
    entry = ET.fromstring(SAMPLE_XML_ENTRY)
    item = parse_arxiv_entry(entry, keywords=["GPT", "LLM"])
    assert item is not None
    assert "GPT-5" in item.title
    assert item.source == "arXiv"
    assert item.category == "ai_paper"
    assert item.url == "http://arxiv.org/abs/2606.12345v1"


def test_parse_entry_filtered_out():
    import xml.etree.ElementTree as ET
    # 第二条是生物学论文，不应匹配 AI 关键词
    entries = ET.fromstring(SAMPLE_XML_FEED).findall(
        "{http://www.w3.org/2005/Atom}entry"
    )
    items = [parse_arxiv_entry(e, ["GPT", "LLM"]) for e in entries]
    items = [i for i in items if i is not None]
    assert len(items) == 1
    assert "GPT-5" in items[0].title


def test_build_query_url():
    fetcher = ArxivFetcher(keywords=["GPT", "LLM"])
    url = fetcher._build_url()
    assert "cs.AI" in url or "cs.CL" in url or "cs.LG" in url
    assert "arxiv.org" in url


def test_extract_title_from_entry():
    import xml.etree.ElementTree as ET
    entry = ET.fromstring(SAMPLE_XML_ENTRY)
    title = ArxivFetcher._extract_title(entry)
    assert "GPT-5" in title
    assert "\n" not in title  # 换行应被清理
