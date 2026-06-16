import asyncio
import datetime
import logging
from config import Config
from storage.db import Database
from storage.models import Item
from fetcher.base import Fetcher
from summarizer.llm_summarizer import Summarizer

logger = logging.getLogger(__name__)


class UpdateScheduler:
    def __init__(
        self,
        config: Config,
        db: Database,
        fetchers: list[Fetcher],
        summarizer: Summarizer | None = None,
    ):
        self.config = config
        self.db = db
        self.fetchers = fetchers
        self.summarizer = summarizer or Summarizer(config)
        self.last_run: datetime.datetime | None = None

    async def run_all(self) -> int:
        """执行一次完整的抓取 + 摘要流程。返回新增条数。"""
        total_new = 0
        for fetcher in self.fetchers:
            try:
                items = await fetcher.fetch(self.db)
                for item in items:
                    self.db.insert(item)
                    total_new += 1
                logger.info(f"[{fetcher.name}] 新增 {len(items)} 条")
            except Exception as e:
                logger.warning(f"[{fetcher.name}] 抓取失败: {e}")
        # 生成摘要
        if total_new > 0:
            try:
                summary_count = await self.summarizer.summarize_new_items(self.db)
                logger.info(f"摘要生成: {summary_count} 条")
            except Exception as e:
                logger.warning(f"摘要生成失败: {e}")
        # 清理过期数据
        cleaned = self.db.cleanup(days=14)
        if cleaned > 0:
            logger.info(f"清理过期数据: {cleaned} 条")
        self.last_run = datetime.datetime.now()
        return total_new

    def _run_once(self):
        """同步包装，供测试和 QTimer 调用。"""
        asyncio.run(self.run_all())

    def _run_once_sync(self):
        """供 QTimer 在 GUI 线程调用的同步入口。"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_all())
            loop.close()
        except Exception as e:
            logger.error(f"定时任务异常: {e}")
