import asyncio
from config import Config
from storage.models import Item
from storage.db import Database
from openai import AsyncOpenAI


def build_summary_prompt(item: Item) -> str:
    return (
        f"请用中文对以下内容生成一段50-80字的简短摘要，"
        f"让读者快速了解核心内容。不要包含\"本文\"\"这篇文章\"等开头语。\n\n"
        f"标题：{item.title}\n"
        f"来源：{item.source}\n"
        f"链接：{item.url}"
    )


class Summarizer:
    def __init__(self, config: Config):
        self.config = config

    @property
    def enabled(self) -> bool:
        return self.config.enable_summary and bool(self.config.api_key.strip())

    async def summarize_item(self, item: Item) -> str:
        client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url="https://api.deepseek.com/v1",
        )
        try:
            response = await client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的信息摘要助手，输出简洁准确的中文摘要。"},
                    {"role": "user", "content": build_summary_prompt(item)},
                ],
                max_tokens=200,
                temperature=0.3,
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except Exception as e:
            return f"[摘要生成失败: {e}]"

    async def summarize_new_items(self, db: Database) -> int:
        if not self.enabled:
            return 0
        items = db.query_without_summary(limit=20)
        if not items:
            return 0
        count = 0
        for item in items:
            summary = await self.summarize_item(item)
            if summary and not summary.startswith("[摘要生成失败"):
                db.update_summary(item.id, summary)
                count += 1
            await asyncio.sleep(0.5)  # 限流
        return count
