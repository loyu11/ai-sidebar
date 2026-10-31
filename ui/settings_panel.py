# ai-sidebar/ui/settings_panel.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QCheckBox, QComboBox, QLineEdit, QGroupBox,
    QFormLayout, QDialogButtonBox, QMessageBox, QListWidget,
    QListWidgetItem, QInputDialog,
)
from config import Config, save_config


class SettingsPanel(QDialog):
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("设置")
        self.setMinimumWidth(380)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 刷新频率
        refresh_group = QGroupBox("📡 刷新频率")
        refresh_layout = QHBoxLayout()
        self.refresh_combo = QComboBox()
        self.refresh_combo.addItems(["15 分钟", "30 分钟", "1 小时"])
        self.refresh_combo.setCurrentIndex(
            {15: 0, 30: 1, 60: 2}.get(self.config.refresh_interval_minutes, 1)
        )
        refresh_layout.addWidget(self.refresh_combo)
        refresh_group.setLayout(refresh_layout)
        layout.addWidget(refresh_group)

        # 显示范围
        display_group = QGroupBox("📅 显示范围")
        display_layout = QHBoxLayout()
        self.display_combo = QComboBox()
        self.display_combo.addItems(["3 天", "7 天", "14 天"])
        self.display_combo.setCurrentIndex(
            {3: 0, 7: 1, 14: 2}.get(self.config.display_days, 1)
        )
        display_layout.addWidget(self.display_combo)
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        # 关注关键词
        kw_group = QGroupBox("🏷 关注关键词（用逗号分隔）")
        kw_layout = QHBoxLayout()
        self.keywords_input = QLineEdit()
        self.keywords_input.setText("，".join(self.config.keywords))
        self.keywords_input.setPlaceholderText("LLM, GPT, Agent, RAG...")
        kw_layout.addWidget(self.keywords_input)
        kw_group.setLayout(kw_layout)
        layout.addWidget(kw_group)

        # 分类开关
        cat_group = QGroupBox("📂 分类开关")
        cat_layout = QVBoxLayout()
        self.cb_paper = QCheckBox("AI 论文")
        self.cb_paper.setChecked(self.config.categories_enabled.get("ai_paper", True))
        self.cb_industry = QCheckBox("AI 产业动态")
        self.cb_industry.setChecked(self.config.categories_enabled.get("ai_industry", True))
        self.cb_news = QCheckBox("国际/国内大新闻")
        self.cb_news.setChecked(self.config.categories_enabled.get("news", True))
        cat_layout.addWidget(self.cb_paper)
        cat_layout.addWidget(self.cb_industry)
        cat_layout.addWidget(self.cb_news)
        cat_group.setLayout(cat_layout)
        layout.addWidget(cat_group)

        # 自定义 RSS 源
        rss_group = QGroupBox("📡 自定义 RSS 源")
        rss_layout = QVBoxLayout()

        self.rss_list = QListWidget()
        self._refresh_rss_list()
        rss_layout.addWidget(self.rss_list)

        rss_btn_layout = QHBoxLayout()
        add_btn = QPushButton("＋ 添加")
        add_btn.clicked.connect(self._add_rss)
        del_btn = QPushButton("✕ 删除")
        del_btn.clicked.connect(self._del_rss)
        rss_btn_layout.addWidget(add_btn)
        rss_btn_layout.addWidget(del_btn)
        rss_btn_layout.addStretch()
        rss_layout.addLayout(rss_btn_layout)

        rss_group.setLayout(rss_layout)
        layout.addWidget(rss_group)

        # 外观
        appearance_group = QGroupBox("🎨 外观")
        form = QFormLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(int(self.config.opacity * 100))
        self.opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.opacity_slider.setTickInterval(10)
        form.addRow("透明度", self.opacity_slider)

        self.font_combo = QComboBox()
        self.font_combo.addItems(["小", "中", "大"])
        self.font_combo.setCurrentIndex(
            {"small": 0, "medium": 1, "large": 2}.get(self.config.font_size, 1)
        )
        form.addRow("字号", self.font_combo)

        self.cb_ontop = QCheckBox()
        self.cb_ontop.setChecked(self.config.always_on_top)
        form.addRow("窗口置顶", self.cb_ontop)

        self.cb_autostart = QCheckBox()
        self.cb_autostart.setChecked(self.config.auto_start)
        form.addRow("开机自启", self.cb_autostart)
        appearance_group.setLayout(form)
        layout.addWidget(appearance_group)

        # AI 摘要
        ai_group = QGroupBox("🤖 AI 摘要")
        ai_form = QFormLayout()
        self.cb_summary = QCheckBox()
        self.cb_summary.setChecked(self.config.enable_summary)
        ai_form.addRow("启用摘要", self.cb_summary)

        self.api_key_input = QLineEdit()
        self.api_key_input.setText(self.config.api_key)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        ai_form.addRow("API Key", self.api_key_input)

        self.model_input = QLineEdit()
        self.model_input.setText(self.config.model)
        ai_form.addRow("模型", self.model_input)
        ai_group.setLayout(ai_form)
        layout.addWidget(ai_group)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_rss_list(self):
        """刷新 RSS 列表显示。"""
        self.rss_list.clear()
        for entry in self.config.custom_rss:
            name = entry.get("name", "")
            url = entry.get("url", "")
            cat = entry.get("category", "ai_industry")
            cat_label = "AI 产业" if cat == "ai_industry" else "大新闻"
            text = f"{name}  →  {url}  [{cat_label}]"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.rss_list.addItem(item)

    def _add_rss(self):
        """弹出添加 RSS 对话框。"""
        import re

        # 名称
        name, ok = QInputDialog.getText(self, "添加 RSS 源", "名称（如：某科技博客）：")
        if not ok or not name.strip():
            return

        # URL
        url, ok = QInputDialog.getText(self, "添加 RSS 源", "RSS 地址（完整 URL）：")
        if not ok or not url.strip():
            return
        if not re.match(r"^https?://", url.strip()):
            QMessageBox.warning(self, "格式错误", "请输入以 http:// 或 https:// 开头的完整地址")
            return

        # 分类
        cat, ok = QInputDialog.getItem(
            self, "添加 RSS 源", "分类：",
            ["AI 产业动态 (ai_industry)", "国际/国内大新闻 (news)"],
            0, False,
        )
        if not ok:
            return
        cat_key = "ai_industry" if "ai_industry" in cat else "news"

        # 保存到临时列表
        entry = {"name": name.strip(), "url": url.strip(), "category": cat_key}
        self.config.custom_rss.append(entry)
        self._refresh_rss_list()

    def _del_rss(self):
        """删除选中的 RSS 条目。"""
        current = self.rss_list.currentItem()
        if not current:
            QMessageBox.information(self, "提示", "请先选择要删除的 RSS 源")
            return
        entry = current.data(Qt.ItemDataRole.UserRole)
        if entry in self.config.custom_rss:
            self.config.custom_rss.remove(entry)
        self._refresh_rss_list()

    def _save(self):
        # 刷新间隔
        interval_map = {0: 15, 1: 30, 2: 60}
        self.config.refresh_interval_minutes = interval_map.get(
            self.refresh_combo.currentIndex(), 30
        )
        # 显示范围
        days_map = {0: 3, 1: 7, 2: 14}
        self.config.display_days = days_map.get(self.display_combo.currentIndex(), 7)
        # 关键词
        raw_kw = self.keywords_input.text()
        self.config.keywords = [
            kw.strip() for kw in raw_kw.replace("，", ",").split(",") if kw.strip()
        ]
        if not self.config.keywords:
            QMessageBox.warning(self, "提示", "关键词不能为空")
            return
        # 分类开关
        self.config.categories_enabled = {
            "ai_paper": self.cb_paper.isChecked(),
            "ai_industry": self.cb_industry.isChecked(),
            "news": self.cb_news.isChecked(),
        }
        # 外观
        self.config.opacity = self.opacity_slider.value() / 100.0
        font_map = {0: "small", 1: "medium", 2: "large"}
        self.config.font_size = font_map.get(self.font_combo.currentIndex(), "medium")
        self.config.always_on_top = self.cb_ontop.isChecked()
        self.config.auto_start = self.cb_autostart.isChecked()
        # AI
        self.config.enable_summary = self.cb_summary.isChecked()
        self.config.api_key = self.api_key_input.text()
        self.config.model = self.model_input.text() or "deepseek-chat"

        save_config(self.config)
        self._handle_autostart()
        self.accept()

    def _handle_autostart(self):
        import os
        import sys
        startup_dir = os.path.join(
            os.environ.get("APPDATA", ""),
            r"Microsoft\Windows\Start Menu\Programs\Startup",
        )
        shortcut_path = os.path.join(startup_dir, "AI信息看板.lnk")
        if self.config.auto_start:
            try:
                import pythoncom
                from win32com.client import Dispatch
                pythoncom.CoInitialize()
                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortcut(shortcut_path)
                shortcut.TargetPath = sys.executable
                shortcut.WorkingDirectory = os.path.dirname(sys.executable)
                shortcut.Description = "AI 信息看板"
                shortcut.Save()
            except ImportError:
                # win32com 未安装，尝试简单批处理方式
                bat_path = os.path.join(startup_dir, "AI信息看板.bat")
                with open(bat_path, "w") as f:
                    f.write(f'@echo off\nstart "" "{sys.executable}"\n')
            except Exception:
                pass  # 静默失败，不影响主流程
        else:
            # 移除快捷方式
            for ext in [".lnk", ".bat"]:
                p = shortcut_path.replace(".lnk", ext) if ext != ".lnk" else shortcut_path
                if os.path.exists(p):
                    os.remove(p)
