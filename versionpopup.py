import requests
import json
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt5.QtCore import Qt
import markdown
from PyQt5.QtWidgets import QTextBrowser
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class VersionPopup(QDialog):
    def __init__(self, repo_url, version=None, parent=None, version_path=None, theme_css=None, html_colors=None):
        super().__init__(parent)
        self.repo_url = repo_url
        self.version_path = version_path or os.path.join(os.getcwd(), "version.json")
        self.setMinimumSize(500, 400)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._drag_pos = None
        if theme_css:
            self.setStyleSheet(theme_css)
        else:
            self.setStyleSheet("""
                QWidget { background: #23272e; color: #fff; font: 12px Consolas; }
                QTextEdit { background: #2d3138; border: 1px solid #444; color: #ccc; }
                QPushButton {
                    background: #44475a;
                    color: #fff;
                    padding: 6px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #5a5e7a;
                }
                QScrollBar:vertical, QScrollBar:horizontal {
                    background: rgba(60,60,70,0.35);
                    border-radius: 8px;
                    width: 12px;
                    margin: 2px;
                }
                QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                    background: rgba(120,120,140,0.5);
                    min-height: 24px;
                    border-radius: 8px;
                }
                QScrollBar::add-line, QScrollBar::sub-line {
                    background: none;
                    border: none;
                    height: 0px;
                }
                QScrollBar::add-page, QScrollBar::sub-page {
                    background: none;
                }
                QProgressBar { border:1px solid #444; background:#2a2a2a; border-radius:4px; text-align:center; }
                QProgressBar::chunk { background:#00bcf2; }
            """)
        layout = QVBoxLayout(self)
        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.release_notes = QWebEngineView()
        layout.addWidget(self.release_notes)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)
        self.html_colors = html_colors or {}
        self.load_release_notes(repo_url, version)

    def load_release_notes(self, repo_url, version=None):
        api_url = f"https://api.github.com/repos/{repo_url}/releases"
        try:
            resp = requests.get(api_url, timeout=10)
            if resp.status_code == 200:
                releases = resp.json()
                if not releases:
                    self.label.setText("No releases available.")
                    self.release_notes.setHtml("")
                    return
                if version:
                    release = next((r for r in releases if r['tag_name'] == version), releases[0])
                else:
                    release = releases[0]
                notes = release.get('body', 'No release notes.')
                tag = release.get('tag_name', '')
                self.label.setText(f"Release notes of {tag}")

                # Convertimos markdown a HTML
                import markdown
                html = markdown.markdown(notes, extensions=["fenced_code", "tables"])

                # Usa colores del tema si se pasan
                bg = self.html_colors.get('background', '#23272e')
                fg = self.html_colors.get('foreground', '#dcdcdc')
                code_bg = self.html_colors.get('code_bg', '#2d2d2d')
                link = self.html_colors.get('link', '#4ea1f2')

                styled_html = f"""
                <html><head><style>
                    body {{ background: {bg}; color: {fg}; font-family: Consolas, monospace; font-size: 13px; }}
                    h1, h2, h3 {{ color: #ffffff; }}
                    code {{ background-color: {code_bg}; padding: 2px 4px; border-radius: 4px; }}
                    pre {{ background-color: {code_bg}; padding: 10px; border-radius: 4px; overflow-x: auto; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #555; padding: 4px; }}
                    a {{ color: {link}; }}
                </style></head><body>{html}</body></html>
                """

                self.release_notes.setHtml(styled_html, baseUrl=QUrl("https://github.com"))
                self.write_version_json(tag)
            else:
                self.label.setText(f"Error fetching releases: {resp.status_code}")
                self.release_notes.setHtml("")
        except Exception as e:
            self.label.setText("Network error")
            self.release_notes.setHtml(f"<pre>{e}</pre>")


    def write_version_json(self, version):
        try:
            with open(self.version_path, "w", encoding="utf-8") as f:
                json.dump({"version": version}, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error writing version.json: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
