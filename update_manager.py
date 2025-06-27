import os
import sys
import requests
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QProgressBar,
    QPushButton, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

GITHUB_REPO = "ZondaxDeveloper/MiCodeEditorPowerEditor"
CURRENT_VERSION = "1.0.0"
# Ejecutable principal (editor)
APP_EXECUTABLE = os.path.join(os.path.dirname(sys.argv[0]), "app.exe")
# Nombre del instalador descargable desde Releases
UPDATE_FILENAME = "PowerEdit-Setup.exe"

class UpdaterThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    new_version = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.download_url = None

    def run(self):
        try:
            self.log.emit("🔍 Buscando actualizaciones...")
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(url)
            if response.status_code != 200:
                self.log.emit("⚠️ No se pudo acceder a GitHub.")
                self.finished.emit(False)
                return

            data = response.json()
            latest_version = data.get("tag_name", "")
            assets = data.get("assets", [])

            if not latest_version or latest_version <= CURRENT_VERSION:
                # Sin actualizaciones
                self.finished.emit(True)
                return

            # Hay versión nueva
            self.log.emit(f"🚀 Nueva versión disponible: {latest_version}")
            self.new_version.emit(latest_version)

            # Buscar URL del instalador
            for asset in assets:
                if asset.get("name") == UPDATE_FILENAME:
                    self.download_url = asset.get("browser_download_url")
                    break

            if not self.download_url:
                self.log.emit("❌ No se encontró el instalador en la release.")
                self.finished.emit(False)
                return

            # Usuario debe confirmar antes de descargar
            # La descarga se realizará tras confirmación en la UI

        except Exception as e:
            self.log.emit(f"❌ Error al buscar actualizaciones: {e}")
            self.finished.emit(False)

class UpdateManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PowerEdit Updater")
        self.setFixedSize(460, 320)
        self.setup_ui()
        self.hide()

        # Iniciar hilo de búsqueda
        self.thread = UpdaterThread()
        self.thread.log.connect(self.log_box.append)
        self.thread.new_version.connect(self.on_new_version)
        self.thread.finished.connect(self.on_search_finished)
        self.thread.start()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: white; font-family: Consolas; }
            QTextEdit { background-color: #2b2b2b; border: 1px solid #444; color: #ccc; }
            QPushButton { background-color: #0078d7; color: white; padding: 6px; border-radius: 4px; }
            QPushButton:hover { background-color: #1890ff; }
            QProgressBar { border: 1px solid #444; background-color: #2a2a2a; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background-color: #00bcf2; }
        """)

        layout = QVBoxLayout(self)
        self.label = QLabel("Verificando actualizaciones...")
        self.progress = QProgressBar()
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.button_update = QPushButton("Descargar e instalar")
        self.button_update.clicked.connect(self.start_download)
        self.button_update.setVisible(False)
        self.button_launch = QPushButton("Iniciar PowerEdit")
        self.button_launch.clicked.connect(self.launch_app)
        self.button_launch.setEnabled(False)

        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        layout.addWidget(self.log_box)
        layout.addWidget(self.button_update)
        layout.addWidget(self.button_launch)

    def on_new_version(self, version):
        # Mostrar diálogo de confirmación
        reply = QMessageBox.question(
            self, "Actualización Disponible",
            f"Hay una nueva versión ({version}).\n¿Deseas descargar e instalar?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Mostrar UI y botón de descarga
            self.show()
            self.button_update.setVisible(True)
            self.label.setText(f"Preparado para descargar v{version}")
        else:
            # Saltar actualización y lanzar app
            self.launch_app()

    def on_search_finished(self, ok):
        if ok and not self.thread.download_url:
            # Sin actualización: lanzar app silent
            self.launch_app()
        elif not ok and not self.isVisible():
            # Error y UI no visible
            self.show()
            self.label.setText("Error al buscar actualizaciones.")
            self.button_launch.setEnabled(True)

    def start_download(self):
        # Desactivar botón para evitar reintentos
        self.button_update.setEnabled(False)
        self.log_box.append("⬇️ Iniciando descarga...")
        try:
            r = requests.get(self.thread.download_url, stream=True)
            total = int(r.headers.get("content-length", 0))
            if total <= 0:
                raise Exception("Tamaño inválido")
            with open(UPDATE_FILENAME, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = int(downloaded*100/total)
                        self.progress.setValue(percent)
            self.log_box.append("✅ Descarga completa.")
            # Ejecutar instalador y luego cerrar updater
            subprocess.Popen([UPDATE_FILENAME], shell=True)
        except Exception as e:
            self.log_box.append(f"❌ Error al descargar: {e}")
            self.button_update.setEnabled(True)
        finally:
            self.button_launch.setEnabled(True)
            self.label.setText("Instalador descargado.")

    def launch_app(self):
        try:
            subprocess.Popen([APP_EXECUTABLE], shell=True)
        except Exception as e:
            self.log_box.append(f"❌ No se pudo iniciar PowerEdit: {e}")
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    manager = UpdateManager()
    sys.exit(app.exec_())
