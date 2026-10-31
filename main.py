# ai-sidebar/main.py
import sys
import os
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from config import Config, load_config
from storage.db import Database
from storage.models import Item
from fetcher.arxiv_fetcher import ArxivFetcher
from fetcher.rss_fetcher import RssFetcher
from summarizer.llm_summarizer import Summarizer
from scheduler import UpdateScheduler
from ui.sidebar import SidebarWindow

logger = logging.getLogger(__name__)


def _setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
        ],
    )


def create_default_fetchers(config: Config) -> list:
    """根据配置创建数据源采集器列表。"""
    fetchers = []

    # arXiv AI 论文
    fetchers.append(ArxivFetcher(keywords=config.keywords))

    # AI 产业 RSS
    industry_feeds = [
        ("机器之心", "https://www.jiqizhixin.com/rss"),
        ("量子位", "https://www.qbitai.com/feed"),
        ("36氪", "https://36kr.com/feed"),
    ]
    for name, url in industry_feeds:
        fetchers.append(RssFetcher(
            name=name,
            url=url,
            category="ai_industry",
        ))

    # 大新闻 RSS
    news_feeds = [
        ("人民网", "http://www.people.com.cn/rss/politics.xml"),
        ("环球网", "https://www.huanqiu.com/rss/china.xml"),
    ]
    for name, url in news_feeds:
        fetchers.append(RssFetcher(
            name=name,
            url=url,
            category="news",
            exclude_keywords=["娱乐", "体育", "八卦", "恋情", "综艺", "选秀", "真人秀", "足球", "篮球"],
        ))

    # 用户自定义 RSS
    for entry in config.custom_rss:
        name = entry.get("name", "").strip()
        url = entry.get("url", "").strip()
        category = entry.get("category", "ai_industry")
        if name and url and category in ("ai_industry", "news"):
            fetchers.append(RssFetcher(
                name=name,
                url=url,
                category=category,
            ))

    return fetchers


def main():
    # 确保数据目录存在
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    data_dir = Path(appdata) / "ai-sidebar"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 初始化日志
    _setup_logging(data_dir)

    # 加载配置
    config = load_config()

    # 初始化数据库
    db_path = data_dir / "data.db"
    db = Database(db_path)
    db.init()

    # 创建采集器
    fetchers = create_default_fetchers(config)

    # 创建摘要器
    summarizer = Summarizer(config)

    # 创建调度器
    scheduler = UpdateScheduler(
        config=config,
        db=db,
        fetchers=fetchers,
        summarizer=summarizer,
    )

    # 启动 Qt 应用
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出程序

    # 创建并显示侧边栏
    sidebar = SidebarWindow(config, db, scheduler)
    sidebar.show()

    logger.info("AI 信息看板已启动")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
