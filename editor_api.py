import sys
import os

# Inyectar site-packages del Python embebido si estamos usando PyInstaller
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.abspath(os.path.dirname(__file__))

embedded_site_packages = os.path.join(base_dir, "python_embedded", "Lib", "site-packages")

if os.path.exists(embedded_site_packages) and embedded_site_packages not in sys.path:
    sys.path.insert(0, embedded_site_packages)
    print("[EditorAPI] ✔ site-packages del Python embebido inyectado.")

from PyQt5.QtWidgets import (
    QApplication,
    QMessageBox,
    QAction,
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QMenu,
    QTabWidget,
    QProgressBar,
    QInputDialog,
    QLineEdit,
    QFileDialog,
    QLabel,
    QMainWindow,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QIcon, QPixmap, QTextCursor
import subprocess

class EditorAPI:
    def __init__(self, main_window, extension_name="UnknownExtension"):
        self.main_window = main_window
        self.extension_name = extension_name

    def log(self, message):
        print(f"[Extension: {self.extension_name}] {message}")

    def get_app(self):
        return QApplication.instance()
    
    def get_current_editor(self):
        if not self.main_window or not hasattr(self.main_window, 'tabs'):
            self.log("Main window or tabs not found.")
            return None
        return self.main_window.tabs.current_editor()
    
    def insert_text_on_editor(self, text):
        editor = self.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            cursor.insertText(text)
            editor.setTextCursor(cursor)
        else:
            self.log("No active editor found to insert text.")

    def get_editor_text(self):
        editor = self.get_current_editor()
        if editor:
            return editor.toPlainText()
        self.log("No active editor found to get text.")
        return ""
    
    def set_editor_text(self, text):
        editor = self.get_current_editor()
        if editor:
            editor.setPlainText(text)
        else:
            self.log("No active editor found to set text.")

    def when_editor_loaded(self, callback, check_interval=100):
        def check():
            editor = self.get_current_editor()
            if editor and editor.isVisible():
                callback(editor)
            else:
                QTimer.singleShot(check_interval, check)
        check()

    def wait_for_seconds(self, seconds, callback=None):
        if callback:
            QTimer.singleShot(int(seconds * 1000), callback)
        else:
            QTimer.singleShot(int(seconds * 1000), lambda: self.log(f"Waited {seconds} seconds."))

    def pause(self, condition_fn, on_resume=None, check_interval=100):
        def check():
            if condition_fn():
                if on_resume:
                    on_resume()
            else:
                QTimer.singleShot(check_interval, check)
        check()

    def show_message(self, text, title="Extension Message"):
        QMessageBox.information(self.main_window, title, text)

    def add_menu_action(self, path, callback):
        parts = path.split("/")
        parent_menu = self.main_window.menuBar()
        for part in parts[:-1]:
            menu = None
            for action in parent_menu.actions():
                if action.text() == part:
                    menu = action.menu()
                    break
            if not menu:
                menu = parent_menu.addMenu(part)
            parent_menu = menu

        action = QAction(parts[-1], self.main_window)
        action.triggered.connect(callback)
        parent_menu.addAction(action)
        return action

    def add_menu_action_with_shortcut(self, path, callback, shortcut=None):
        action = QAction(path.split("/")[-1], self.main_window)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(callback)
        menu = self.add_menu("/".join(path.split("/")[:-1]))
        menu.addAction(action)
        return action

    def add_menu(self, path):
        parts = path.split("/")
        parent_menu = self.main_window.menuBar()
        for part in parts:
            menu = None
            for action in parent_menu.actions():
                if action.text() == part:
                    menu = action.menu()
                    break
            if not menu:
                menu = parent_menu.addMenu(part)
            parent_menu = menu
        return parent_menu

    def pause_until_valid_tab(self):
        def condition():
            count = self.get_tab_count()
            for i in range(count):
                name = self.get_tab_name(i)
                if name.lower() != "welcome":
                    return True
            return False

        def on_resume():
            self.log("Se detectó una pestaña válida distinta de Welcome.")

        self.pause(condition, on_resume)

    def get_tab_count(self):
        if not self.main_window or not hasattr(self.main_window, 'tabs'):
            return 0
        return self.main_window.tabs.count()

    def get_tab_name(self, index):
        if not self.main_window or not hasattr(self.main_window, 'tabs'):
            return ""
        if 0 <= index < self.main_window.tabs.count():
            return self.main_window.tabs.tabText(index)
        return ""
    def close_current_tab(self):
        if not self.main_window or not hasattr(self.main_window, 'tabs'):
            self.log("No se pudo cerrar pestaña actual: tabs manager no encontrado.")
            return
        index = self.main_window.tabs.currentIndex()
        if index >= 0:
            self.main_window.tabs.close_tab(index)
    
    def get_current_tab_file_path(self):
        if not self.main_window or not hasattr(self.main_window, 'tabs'):
            return None
        tabs = self.main_window.tabs
        editor = tabs.currentWidget()
        if editor in tabs._file_paths:
            return tabs._file_paths[editor]
        return None

    def is_current_tab_welcome(self):
        if not self.main_window or not hasattr(self.main_window, 'tabs'):
            return False
        tabs = self.main_window.tabs
        index = tabs.currentIndex()
        if index < 0:
            return False
        widget = tabs.widget(index)
        return widget == tabs._welcome_tab

    def get_current_tab_name(self):
        if not self.main_window or not hasattr(self.main_window, 'tabs'):
            return ""
        idx = self.main_window.tabs.currentIndex()
        if idx < 0:
            return ""
        return self.main_window.tabs.tabText(idx)
    
    def open_new_tab(self, file_path=None, content="", language=None):
        if not hasattr(self.main_window, 'tabs') or not hasattr(self.main_window.tabs, 'new_tab'):
            self.log("Tabs manager o método new_tab no encontrado.")
            return None
        return self.main_window.tabs.new_tab(file_path=file_path, content=content, language=language)


    def close_tab(self, index):
        self.main_window.tabs.removeTab(index)

    def is_tab_modified(self, index):
        if not self.main_window or not hasattr(self.main_window, 'tabs'):
            return False
        tabs = self.main_window.tabs
        if 0 <= index < tabs.count():
            widget = tabs.widget(index)
            if hasattr(widget, 'toPlainText'):
                current_text = widget.toPlainText()
                saved_text = tabs.saved_texts.get(widget, "")
                return current_text != saved_text
        return False


    def on_tab_changed(self, callback):
        if not self.main_window or not hasattr(self.main_window, 'tabs'):
            self.log("Tabs manager no encontrado para conectar on_tab_changed.")
            return
        self.main_window.tabs.currentChanged.connect(callback)


    def _get_or_create_view_menu(self):
        """Obtiene o crea el menú 'View' en el menuBar."""
        menu_bar = self.main_window.menuBar()
        for action in menu_bar.actions():
            if action.text() == "View":
                return action.menu()
        # No existe, crear menú
        return menu_bar.addMenu("View")

    def create_dock_widget(self, title, widget=None, area=Qt.RightDockWidgetArea, checkable=True, checked=False, shortcut=None):
        dock = CustomDockWidget(title, self.main_window)
        if widget is None:
            widget = QWidget()
            widget.setLayout(QVBoxLayout())
        dock.setWidget(widget)
        self.main_window.addDockWidget(area, dock)

        # Añadir acción al menú View para mostrar/ocultar este dock
        view_menu = self._get_or_create_view_menu()
        action = view_menu.addAction(title)
        action.setCheckable(checkable)
        action.setChecked(checked)
        if shortcut:
            action.setShortcut(shortcut)

        def toggle_visibility(checked):
            dock.setVisible(checked)

        # Sincronizar acción con visibilidad del dock
        action.toggled.connect(toggle_visibility)
        dock.visibilityChanged.connect(action.setChecked)

        return dock

    def create_floating_window(self, title, widget=None):
        """
        Crear una ventana flotante con un widget dentro, y añadir al menú View.
        """
        from PyQt5.QtWidgets import QMainWindow
        window = QMainWindow()
        window.setWindowTitle(title)
        if widget is None:
            widget = QWidget()
            widget.setLayout(QVBoxLayout())
        window.setCentralWidget(widget)
        window.show()

        view_menu = self._get_or_create_view_menu()
        action = view_menu.addAction(title)
        action.setCheckable(True)
        action.setChecked(True)

        def toggle_visibility(checked):
            window.setVisible(checked)

        action.toggled.connect(toggle_visibility)
        window.visibilityChanged = lambda visible: action.setChecked(visible)  # No tiene señal visibilityChanged nativa
        # Como workaround para sincronizar (no hay señal visibilityChanged en QMainWindow):
        # Se puede conectar a eventos show/hide si quieres más precisión.

        return window
    def set_language_on_editor(self, language):
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'set_language'):
            editor.set_language(language)
        else:
            self.log("No se pudo cambiar el lenguaje: editor no válido o no soporta set_language.")

    def create_button(self, parent, text, callback):
        btn = QPushButton(text, parent)
        btn.clicked.connect(callback)
        return btn

    def create_progress_bar(self, parent=None):
        bar = QProgressBar(parent if parent else self.main_window)
        return bar

    def open_file_dialog(self, caption="Open File", directory="", filter="All Files (*)"):
        return QFileDialog.getOpenFileName(self.main_window, caption, directory, filter)

    def save_file_dialog(self, caption="Save File", directory="", filter="All Files (*)"):
        return QFileDialog.getSaveFileName(self.main_window, caption, directory, filter)

    def input_dialog(self, title, label, text=""):
        return QInputDialog.getText(self.main_window, title, label, QLineEdit.Normal, text)

    def get_icon(self, path):
        return QIcon(path)

    def get_pixmap(self, path):
        return QPixmap(path)
    def add_tool_window(self, title, widget):
        return self.create_dock_widget(title, widget)
    
    def require(self, module_name, auto_install=False, callback=None):
        import subprocess

        # Determinar ruta del Python embebido
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.abspath(os.path.dirname(__file__))
        python_path = os.path.join(base_dir, "python_embedded", "python.exe")

        if not os.path.exists(python_path):
            self.show_message(f"Embedded Python not found at:\n{python_path}", "Error")
            if callback:
                callback(False)
            return False

        # Configurar flags para no mostrar consola (solo en Windows)
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        # Verificar si el módulo ya está instalado
        try:
            result = subprocess.run(
                [python_path, "-c", f"import {module_name}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
            if result.returncode == 0:
                if callback:
                    callback(True)
                return True
        except Exception as e:
            self.log(f"Error checking module '{module_name}': {e}")

        self.log(f"❌ Módulo '{module_name}' no encontrado.")

        if not auto_install:
            if callback:
                callback(False)
            return False

        # Mostrar progress bar solo si se va a instalar
        from PyQt5.QtWidgets import QProgressDialog
        progress = QProgressDialog(f"Installing '{module_name}'...", None, 0, 0, self.main_window)
        progress.setWindowTitle("Installing Module")
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.show()

        # Crear hilo de instalación
        self._installer_thread = ModuleInstaller(python_path, module_name)
        self._installer_thread.finished.connect(lambda success, error: self._on_install_finished(
            module_name, success, error, callback, progress
        ))
        self._installer_thread.start()
        return None



    def _on_install_finished(self, module_name, success, error_msg, callback, progress):
        progress.close()
        if success:
            self.log(f"✅ MModule '{module_name}' installed successfully.")
        else:
            self.show_message(f"Failed to install '{module_name}':\n{error_msg}", "Error")
        if callback:
            callback(success)
    

from PyQt5.QtWidgets import QDockWidget, QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

class CustomDockWidget(QDockWidget):
    def __init__(self, title, parent=None):
        super().__init__("", parent)  # Dejamos el título vacío
        self.setObjectName("CustomDock")
        self.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self._custom_title = self._create_title_bar(title)
        self.setTitleBarWidget(self._custom_title)

    def _create_title_bar(self, title):
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 2, 8, 2)

        label = QLabel(title)
        label.setStyleSheet("""
            color: white;
            font-family: Consolas, monospace;
            font-size: 12px;
        """)

        minimize_btn = QPushButton("—")
        minimize_btn.setFixedSize(20, 20)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #FF5555;
            }
        """)
        minimize_btn.clicked.connect(self.hide)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(minimize_btn.styleSheet())
        close_btn.clicked.connect(self.close)

        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(minimize_btn)
        layout.addWidget(close_btn)

        return bar


from PyQt5.QtCore import QThread, pyqtSignal

class ModuleInstaller(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, python_path, module_name):
        super().__init__()
        self.python_path = python_path
        self.module_name = module_name

    def run(self):
        import subprocess
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            result = subprocess.run(
                [self.python_path, "-m", "pip", "install", self.module_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )
            success = result.returncode == 0
            error_msg = result.stderr.decode() if not success else ""
            self.finished.emit(success, error_msg)
        except Exception as e:
            self.finished.emit(False, str(e))
