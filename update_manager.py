import os
import sys
import requests
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QProgressBar,
    QPushButton, QTextEdit, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal

GITHUB_REPO    = "ZtaMDev/PowerEdit"
CURRENT_VERSION= "1.0.3"
APP_EXECUTABLE = os.path.join(os.path.dirname(sys.argv[0]), "app.exe")
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)
def get_download_dir():
    # Usa la carpeta temporal del usuario
    return os.getenv('TEMP') or os.path.expanduser("~\\AppData\\Local\\Temp")


UPDATE_BASENAME = "PowerEdit-Setup"
# Hilo para buscar actualizacione
class UpdaterThread(QThread):
    log         = pyqtSignal(str)
    new_version= pyqtSignal(str)
    finished   = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.download_url   = None
        self.latest_version = ""

    def run(self):
        try:
            self.log.emit("Checking for updates...")
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            r = requests.get(url, timeout=2)
            if r.status_code != 200:
                self.log.emit("⚠️ Cannot reach GitHub.")
                self.finished.emit(False)
                return

            data = r.json()
            ver = data.get("tag_name", "")
            assets = data.get("assets", [])

            if not ver or ver <= CURRENT_VERSION:
                self.finished.emit(True)
                return

            self.latest_version = ver
            self.log.emit(f"📦 New version available: {ver}")
            self.new_version.emit(ver)

            for a in assets:
                if a.get("name", "").startswith(UPDATE_BASENAME):
                    self.download_url = a.get("browser_download_url")
                    break

            if not self.download_url:
                self.log.emit("❌ Installer asset not found.")
                self.finished.emit(False)

        except Exception as e:
            self.log.emit(f"❌ Error checking updates: {e}")
            self.finished.emit(False)


# Hilo para descargar el instalador sin bloquear la UI
class InstallerThread(QThread):
    progress = pyqtSignal(int)
    log      = pyqtSignal(str)
    finished = pyqtSignal(str)  # emite ruta absoluta del installer o "" en error

    def __init__(self, url, version):
        super().__init__()
        self.url     = url
        self.version = version

    def run(self):
        base = get_download_dir()
        fname = f"{UPDATE_BASENAME}-v{self.version}.exe"
        path  = os.path.join(base, fname)
        try:
            if os.path.exists(path):
                os.remove(path)

            self.log.emit(f"⬇️ Downloading to {base}: {fname}…")
            r = requests.get(self.url, stream=True, timeout=30)
            total = int(r.headers.get("content-length", 0))
            if total <= 0:
                raise Exception("Invalid content length")

            with open(path, "wb") as f:
                dl = 0
                for chunk in r.iter_content(8192):
                    if not chunk: continue
                    f.write(chunk)
                    dl += len(chunk)
                    pct = int(dl * 100 / total)
                    self.progress.emit(pct)

            self.log.emit("✅ Download complete.")
            self.finished.emit(path)

        except Exception as e:
            self.log.emit(f"❌ Download error: {e}")
            self.finished.emit("")


class UpdateManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PowerEdit Updater")
        self.setFixedSize(460, 320)
        self._setup_ui()
        self.hide()

        self.updater = UpdaterThread()
        self.updater.log.connect(self.log_box.append)
        self.updater.new_version.connect(self._on_new_version)
        self.updater.finished.connect(self._on_search_finished)
        self.updater.start()

    def _setup_ui(self):
        self.setStyleSheet("""
            QWidget { background: #1e1e1e; color: #fff; font: 12px Consolas; }
            QTextEdit { background: #2b2b2b; border: 1px solid #444; color: #ccc; }
            QPushButton { background: #0078d7; color: #fff; padding: 6px; border-radius:4px; }
            QPushButton:hover { background: #1890ff; }
            QProgressBar { border:1px solid #444; background:#2a2a2a; border-radius:4px; text-align:center; }
            QProgressBar::chunk { background:#00bcf2; }
        """)
        layout = QVBoxLayout(self)

        self.label       = QLabel("Verifying updates...")
        self.progress    = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate while checking
        self.log_box     = QTextEdit(); self.log_box.setReadOnly(True)
        self.btn_download= QPushButton("Download & Install")
        self.btn_download.clicked.connect(self._start_download)
        self.btn_download.setVisible(False)
        self.btn_launch  = QPushButton("Start PowerEdit")
        self.btn_launch.clicked.connect(self._launch_app)
        self.btn_launch.setEnabled(False)

        for w in (self.label, self.progress, self.log_box,
                  self.btn_download, self.btn_launch):
            layout.addWidget(w)

    def _on_new_version(self, ver):
        resp = QMessageBox.question(
            self, "Update Available",
            f"A new version ({ver}) is available.\nDo you want to update now?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            self.show()
            self.progress.setRange(0, 100)
            self.btn_download.setVisible(True)
            self.label.setText(f"Ready to download v{ver}")
        else:
            self._launch_app()

    def _on_search_finished(self, ok):
        # restore determinate or launch silently
        self.progress.setRange(0, 100)
        if ok and not self.updater.download_url:
            self.label.setText("✅ PowerEdit is up to date.")
            self._launch_app()
        elif not ok and not self.isVisible():
            self.show()
            self.label.setText("❌ Error checking updates.")
            self.btn_launch.setEnabled(True)

    def _start_download(self):
        self.btn_download.setEnabled(False)
        ver = self.updater.latest_version
        self.installer = InstallerThread(self.updater.download_url, ver)
        self.installer.log.connect(self.log_box.append)
        self.installer.progress.connect(self.progress.setValue)
        self.installer.finished.connect(self._on_download_finished)
        self.installer.start()

    def _on_download_finished(self, installer_path):
        if installer_path:
            try:
                subprocess.Popen([installer_path], shell=True)
            except Exception as e:
                self.log_box.append(f"❌ Could not launch installer: {e}")
            finally:
                self.close()
        else:
            self.log_box.append("❌ Failed to download installer.")
            self.btn_download.setEnabled(True)
            self.btn_launch.setEnabled(True)
            self.label.setText("Installer download failed.")


    def _launch_app(self):
        try:
            subprocess.Popen([APP_EXECUTABLE], shell=True)
        except Exception as e:
            self.log_box.append(f"❌ Cannot start PowerEdit: {e}")
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    manager = UpdateManager()
    sys.exit(app.exec_())
