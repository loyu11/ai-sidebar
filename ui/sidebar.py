# ai-sidebar/ui/sidebar.py
import json
import logging
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QObject, Slot
from PySide6.QtGui import QScreen
from PySide6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from config import Config
from storage.db import Database
from ui.card_renderer import CardRenderer
from scheduler import UpdateScheduler

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent / "assets"


class Backend(QObject):
    """QWebChannel 通信桥梁：Python ↔ JavaScript"""

    def __init__(self, db: Database, config: Config):
        super().__init__()
        self.db = db
        self.config = config

    @Slot(str)
    def log(self, message: str):
        logger.info(f"[JS] {message}")

    @Slot(result=str)
    def getItemsJson(self) -> str:
        """返回当前展示天数的所有条目 JSON。QWebChannel 的回调由内部处理。"""
        items = []
        for cat, enabled in self.config.categories_enabled.items():
            if not enabled:
                continue
            items.extend(self.db.query_by_category(cat, days=self.config.display_days))
        # 按时间倒序
        items.sort(key=lambda x: x.published_at, reverse=True)
        return CardRenderer.items_to_json(items)

    @Slot(result=str)
    def refresh(self) -> str:
        """JS 调用刷新，返回最新数据。"""
        return self.getItemsJson()


class SidebarWindow(QMainWindow):
    def __init__(self, config: Config, db: Database, scheduler: UpdateScheduler):
        super().__init__()
        self.config = config
        self.db = db
        self.scheduler = scheduler
        self._init_ui()
        self._init_tray()

    def _init_ui(self):
        self.setWindowTitle("AI 信息看板")
        # 无边框 + 透明背景 + 置顶
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # 尺寸和位置
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            width = 320
            height = int(geom.height() * 0.7)
            x = geom.right() - width
            y = (geom.height() - height) // 2
            self.setGeometry(x, y, width, height)
        else:
            self.resize(320, 600)

        # WebEngine 视图
        self.webview = QWebEngineView(self)
        self.webview.setStyleSheet("background: transparent;")
        self.webview.page().setBackgroundColor(Qt.GlobalColor.transparent)
        self.setCentralWidget(self.webview)

        # QWebChannel 桥接
        self.channel = QWebChannel()
        self.backend = Backend(self.db, self.config)
        self.channel.registerObject("backend", self.backend)
        self.webview.page().setWebChannel(self.channel)

        # 加载 HTML
        html_path = ASSETS_DIR / "index.html"
        self.webview.setUrl(f"file:///{html_path.as_posix()}")

        # 定时刷新 UI（不重新抓取，只从数据库更新卡片）
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._refresh_ui)
        self.ui_timer.start(60_000)  # 每分钟刷新 UI

        # 定时抓取新数据
        interval_ms = self.config.refresh_interval_minutes * 60 * 1000
        self.fetch_timer = QTimer(self)
        self.fetch_timer.timeout.connect(self._run_fetch)
        self.fetch_timer.start(interval_ms)

        # 首次启动立即抓取一次
        QTimer.singleShot(2000, self._run_fetch)

    def _init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("AI 信息看板")
        # 使用系统默认图标
        from PySide6.QtGui import QIcon
        self.tray_icon.setIcon(QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_ComputerIcon
        ))

        menu = QMenu()
        menu.addAction("显示/隐藏", self._toggle_visible)
        menu.addAction("设置", self._open_settings)
        menu.addSeparator()
        menu.addAction("退出", self._quit)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activate)
        self.tray_icon.show()

    def _refresh_ui(self):
        """刷新 WebView 内容（不重新抓取数据）。"""
        js = "if(typeof loadCards === 'function') loadCards();"
        self.webview.page().runJavaScript(js)

    def _run_fetch(self):
        """后台抓取 + 摘要 + 刷新 UI。"""
        logger.info("定时抓取开始…")
        self.scheduler._run_once_sync()
        self._refresh_ui()

    def _toggle_visible(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self._refresh_ui()

    def _open_settings(self):
        from ui.settings_panel import SettingsPanel
        panel = SettingsPanel(self.config, parent=self)
        if panel.exec():
            # 设置已保存，重新加载配置
            self._apply_config()
            self._refresh_ui()

    def _on_tray_activate(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_visible()

    def _apply_config(self):
        # 更新置顶属性
        if self.config.always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        # 更新定时器间隔
        interval_ms = self.config.refresh_interval_minutes * 60 * 1000
        self.fetch_timer.setInterval(interval_ms)
        self.show()

    def _quit(self):
        self.tray_icon.hide()
        QApplication.quit()
