import json
import tempfile
from pathlib import Path
from config import Config, load_config, save_config

def test_config_defaults():
    cfg = Config()
    assert cfg.refresh_interval_minutes == 30
    assert cfg.display_days == 7
    assert "LLM" in cfg.keywords
    assert cfg.categories_enabled == {"ai_paper": True, "ai_industry": True, "news": True}
    assert cfg.opacity == 0.8
    assert cfg.always_on_top is True
    assert cfg.auto_start is False
    assert cfg.enable_summary is True
    assert cfg.api_key == ""
    assert cfg.model == "deepseek-chat"

def test_save_and_load_config():
    cfg = Config()
    cfg.keywords = ["扩散模型", "MoE"]
    cfg.display_days = 3
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.json"
        save_config(cfg, path)
        loaded = load_config(path)
        assert loaded.keywords == ["扩散模型", "MoE"]
        assert loaded.display_days == 3
        assert loaded.refresh_interval_minutes == 30  # default preserved

def test_load_missing_file_returns_defaults():
    cfg = load_config(Path("/nonexistent/config.json"))
    assert cfg.refresh_interval_minutes == 30
    assert cfg.keywords == ["LLM", "GPT", "Agent", "RAG", "Transformer", "RLHF", "多模态"]

def test_keywords_serialized_as_list():
    cfg = Config()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.json"
        save_config(cfg, path)
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(raw["keywords"], list)
        assert "LLM" in raw["keywords"]
