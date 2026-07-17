#!/usr/bin/env python3
"""
headless_shot.py — Offscreen QtWebEngine screenshot tool.

Same rendering engine TreasureHunt.py uses in PtolemyDesktop/Phaleron
(QWebEngineView, Chromium-based), run headless (QT_QPA_PLATFORM=offscreen,
no visible window, no GPU/sandbox since this runs as root in a proot
container) instead of inside the full Phaleron GUI. Generic tool: point it
at any local HTML file or URL to verify it actually renders, not just that
it opens without a Python traceback.

Usage: python3 headless_shot.py <file_or_url> <out.png> [width] [height] [delay_ms]
"""
import sys, os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")  # running as root, no chromium sandbox available
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")

from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

target = sys.argv[1]
out = sys.argv[2]
w = int(sys.argv[3]) if len(sys.argv) > 3 else 1400
h = int(sys.argv[4]) if len(sys.argv) > 4 else 900
delay = int(sys.argv[5]) if len(sys.argv) > 5 else 1500

app = QApplication(sys.argv[:1])
view = QWebEngineView()
view.resize(w, h)
s = view.settings()
s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

url = QUrl(target) if "://" in target else QUrl.fromLocalFile(os.path.abspath(target))
view.setUrl(url)

def grab():
    pix = view.grab()
    pix.save(out)
    print(f"-> {out}  ({pix.width()}x{pix.height()})")
    app.quit()

def loaded(ok):
    print("loadFinished:", ok)
    QTimer.singleShot(delay, grab)

view.loadFinished.connect(loaded)
view.show()
sys.exit(app.exec())
