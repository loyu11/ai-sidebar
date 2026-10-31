import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


DEFAULT_KEYWORDS = ["LLM", "GPT", "Agent", "RAG", "Transformer", "RLHF", "多模态"]

DEFAULT_CATEGORIES = {
    "ai_paper": True,
    "ai_industry": True,
    "news": True,
}


@dataclass
class Config:
    refresh_interval_minutes: int = 30
    display_days: int = 7
    keywords: list[str] = field(default_factory=lambda: DEFAULT_KEYWORDS.copy())
    categories_enabled: dict[str, bool] = field(
        default_factory=lambda: DEFAULT_CATEGORIES.copy()
    )
    opacity: float = 0.8
    font_size: str = "medium"
    always_on_top: bool = True
    auto_start: bool = False
    enable_summary: bool = True
    api_key: str = ""
    model: str = "deepseek-chat"
    custom_rss: list[dict] = field(default_factory=list)

    @staticmethod
    def default_path() -> Path:
        import os
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        return Path(appdata) / "ai-sidebar" / "config.json"


def load_config(path: Optional[Path] = None) -> Config:
    if path is None:
        path = Config.default_path()
    if not path.exists():
        return Config()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Config(**{k: v for k, v in raw.items() if k in Config.__dataclass_fields__})


def save_config(config: Config, path: Optional[Path] = None) -> None:
    if path is None:
        path = Config.default_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
