# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for AI 信息看板 (AI Info Sidebar)."""

import sys
from pathlib import Path

# 项目根目录
PROJECT_DIR = Path(SPECPATH)  # noqa: F821 — SPECPATH is injected by PyInstaller

# 需要打包的静态资源
datas = [
    (str(PROJECT_DIR / "ui" / "assets" / "index.html"), "ui/assets"),
    (str(PROJECT_DIR / "ui" / "assets" / "style.css"), "ui/assets"),
]

# PySide6 + QtWebEngine 需要的隐藏导入
hiddenimports = [
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebChannel",
    "PySide6.QtWebEngineCore",
    "PySide6.QtNetwork",
]

a = Analysis(
    [str(PROJECT_DIR / "main.py")],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "xmlrpc",
        "pydoc",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AI-Info-Sidebar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可替换为 .ico 文件路径
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AI-Info-Sidebar",
)
