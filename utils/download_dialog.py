import os
import requests
import zipfile
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QLineEdit, QHBoxLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

GITHUB_ZIP_URL = "https://github.com/ZtaMDev/PowerEdit/archive/refs/heads/main.zip"

def get_documents_folder():
    return os.path.join(os.path.expanduser("~"), "Documents")

class DownloaderThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, extract_path):
        super().__init__()
        self.extract_path = extract_path

    def run(self):
        try:
            self.log.emit("Downloading source code...")
            response = requests.get(GITHUB_ZIP_URL, stream=True)

            if response.status_code != 200:
                self.log.emit(f"❌ Error downloading code: {response.status_code}")
                self.finished.emit("")
                return

            os.makedirs(self.extract_path, exist_ok=True)
            zip_path = os.path.join(self.extract_path, "poweredit_download.zip")

            total = response.headers.get('content-length')
            total = int(total) if total else None

            with open(zip_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            percent = int((downloaded / total) * 100)
                            self.progress.emit(percent)
                        else:
                            self.progress.emit(0)

            self.log.emit("Extracting file...")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_path)

            os.remove(zip_path)
            self.finished.emit(self.extract_path)

        except Exception as e:
            self.log.emit(f"❌ Error: {str(e)}")
            self.finished.emit("")


class DownloadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Source Code")
        self.setMinimumSize(500, 400)

        
        self.setStyleSheet("""
        QDialog {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QLabel, QLineEdit, QTextEdit, QPushButton {
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #444;
        }
        QLineEdit, QTextEdit {
            selection-background-color: #444;
            selection-color: #fff;
        }
        QPushButton:hover {
            background-color: #3a3a3a;
        }

        QProgressBar {
            border: 1px solid #444;
            border-radius: 4px;
            background-color: #2a2a2a;
            color: white;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #0078d7;
            width: 10px;
            margin: 0.5px;
        }
    """)


        layout = QVBoxLayout(self)

        # Campo de ruta y botón de examinar
        ruta_layout = QHBoxLayout()
        self.path_input = QLineEdit(get_documents_folder())
        ruta_layout.addWidget(self.path_input)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.select_folder)
        ruta_layout.addWidget(self.browse_button)
        layout.addLayout(ruta_layout)

        # Progress bar (without custom styles)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Log console
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        # Download button
        self.download_button = QPushButton("Download from GitHub")
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

    def log(self, message):
        self.log_output.append(message)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", get_documents_folder())
        if folder:
            self.path_input.setText(folder)

    def start_download(self):
        self.download_button.setEnabled(False)
        extract_path = self.path_input.text().strip()

        self.thread = DownloaderThread(extract_path)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.log.connect(self.log)
        self.thread.finished.connect(self.download_finished)
        self.thread.start()

    def download_finished(self, path):
        if path:
            self.log(f"✅ Source code extracted to:\n{path}")
        else:
            self.log("❌ An error occurred.")
        self.download_button.setEnabled(True)
