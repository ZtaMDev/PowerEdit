from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLineEdit, QDockWidget
)
from PyQt5.QtCore import QProcess, Qt
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QDockWidget
from PyQt5.QtCore import QProcess, Qt
from PyQt5.QtGui import QTextCursor

import pyte,os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPlainTextEdit, QLineEdit
)
from PyQt5.QtCore import QProcess, Qt

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPlainTextEdit, QLineEdit, QPushButton
)
from PyQt5.QtCore import QProcess, Qt
from PyQt5.QtGui import QTextCursor
import os
import ctypes
import signal
# console_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QLineEdit, QPushButton
from PyQt5.QtCore import QProcess, Qt
from PyQt5.QtGui import QTextCursor
import os
import os
import signal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QLineEdit, QPushButton
from PyQt5.QtCore import QProcess, Qt, QObject, QEvent,pyqtSignal
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPlainTextEdit, QLineEdit, QPushButton,
    QMenu, QAction
)

class ConsoleWidget(QWidget):
    live_server_requested = pyqtSignal(str)
    def __init__(self, shell="cmd.exe", work_dir=None, parent=None):
        super().__init__(parent)

        self.shell = shell
        self.work_dir = work_dir or os.path.expanduser("~/Documents")
        self._restart_requested = False
        self._new_work_dir = None

        self.output_area = QPlainTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setContextMenuPolicy(Qt.CustomContextMenu)
        self.output_area.customContextMenuRequested.connect(self._on_output_context_menu)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Write a command and press Enter...")
        self.input_line.returnPressed.connect(self.send_command)

        self.restart_button = QPushButton("⟳ Restart Console")
        self.restart_button.clicked.connect(lambda: self.restart_shell(self.work_dir))
        self.exit_button = QPushButton("✕ Exit Process")
        self.exit_button.clicked.connect(self.send_sigint)

        # Instala el eventFilter en la línea de entrada
        self.input_line.installEventFilter(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self.output_area)
        layout.addWidget(self.input_line)
        #Se ve feo mejor no
        #layout.addWidget(self.exit_button)
        # layout.addWidget(self.restart_button)
        self.setLayout(layout)

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.on_ready_read)
        self.process.finished.connect(self.on_process_finished)

        self.start_process()

    def start_process(self):
        self.process.setWorkingDirectory(self.work_dir)
        self.process.start(self.shell)

    def restart_shell(self, new_work_dir=None):
        self._restart_requested = True
        self._new_work_dir = new_work_dir or self.work_dir
        self.process.kill()

    def on_process_finished(self, code, status):
        self.append_text(f"\n⚠️ Console closed with code {code}\n")
        if self._restart_requested:
            self._restart_requested = False
            self.work_dir = self._new_work_dir
            self.output_area.clear()
            self.start_process()

    def send_sigint(self):
        if self.process.state() == QProcess.Running:
            self.process.kill()
            self.append_text("\n^C Process canceled.\n")
            self.restart_shell()  # Reiniciar sin limpiar la consola

    def _on_output_context_menu(self, pos):
        menu = QMenu(self.output_area)
        # Accion copiar
        copy_act = QAction("Copy", menu)
        copy_act.setShortcut("Ctrl+C")
        copy_act.triggered.connect(self.output_area.copy)
        menu.addAction(copy_act)

        # Accion Live Server
        live_act = QAction("Open with Live Server", menu)
        live_act.triggered.connect(self._open_in_live_preview)
        menu.addAction(live_act)

        menu.exec_(self.output_area.mapToGlobal(pos))

    def _open_in_live_preview(self):
        text = self.output_area.textCursor().selectedText().strip()
        if not text:
            return
        # llamar al MainWindow
        mw = self.window()
        if hasattr(mw, "_on_live_server_request"):
            mw._on_live_server_request(text)

    def send_command(self):
        cmd = self.input_line.text().strip()
        if not cmd:
            return
        self.process.write((cmd + "\n").encode())
        self.input_line.clear()

    def on_ready_read(self):
        text = self.process.readAllStandardOutput().data().decode(errors="ignore")
        self.append_text(text)

    def append_text(self, text):
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.output_area.setTextCursor(cursor)
        self.output_area.insertPlainText(text)
        self.output_area.verticalScrollBar().setValue(self.output_area.verticalScrollBar().maximum())

    #Por que esto existe?
    def apply_theme(self, css):
        # Aplica el mismo estilo a los tres widgets si se desea
        self.output_area.setStyleSheet(css)
        self.input_line.setStyleSheet(css)
        self.restart_button.setStyleSheet(css)

    def execute_command(self, cmd):
        if not cmd.strip():
            return
        self.input_line.setText(cmd)
        self.send_command()
        
    def eventFilter(self, obj, event):
        # Si es la línea de entrada y presionan Ctrl+C
        if obj is self.input_line and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
                self.send_sigint()
                return True
        return super().eventFilter(obj, event)

from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtCore import Qt
from console_widget import ConsoleWidget

class ConsoleDock(QDockWidget):
    def __init__(self, parent=None, shell_cmd="cmd.exe"):
        super().__init__("Consola", parent)
        self.console = ConsoleWidget(shell_cmd, self)
        self.setWidget(self.console)
        self.setFeatures(
            QDockWidget.DockWidgetClosable |
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable
        )
        self.setAllowedAreas(
            Qt.BottomDockWidgetArea |
            Qt.TopDockWidgetArea |
            Qt.LeftDockWidgetArea |
            Qt.RightDockWidgetArea
        )

    def restart_in_directory(self, path):
        self.console.restart_shell(path)