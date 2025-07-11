# main_window.py 
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QMessageBox
from tabs_manager import TabsManager
import os, json
from PyQt5.QtGui import QKeySequence
from file_explorer import FileExplorer
from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtCore import Qt, QUrl
from console_widget import ConsoleWidget
from console_widget import ConsoleDock
import subprocess
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QSplitter, QWidget, QVBoxLayout
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QPushButton,
    QFontComboBox, QSpinBox, QHBoxLayout, QMessageBox, QFileDialog
)
from PyQt5.QtWidgets import QProgressDialog, QMessageBox
from PyQt5.QtCore import Qt
import subprocess
import threading
import os
import sys
import sys
import os, shutil, tempfile, re, requests, importlib.util, traceback
from PyQt5.QtWidgets import QLineEdit, QTextEdit
import tempfile
from zipfile import ZipFile
from PyQt5.QtWidgets import QMenu, QAction, QToolButton
import shutil
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
import os
import importlib.util
import traceback
import importlib.util
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QProgressDialog, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
import os, time
from PyQt5.QtGui import QFont
import re, os
import time
from live_preview_dock import LivePreviewDock
from PyQt5.QtCore import QTimer
from minimap_widget import MinimapWidget
from utils.file_loading import load_large_file_to_editor
import time
from utils.file_loading import load_large_file_to_editor
from utils.custom_dock_widget import CustomDockWidget
from utils.download_dialog import DownloadDialog
from PyQt5.QtCore import QThread
import json
from editor_api import EditorAPI

GITHUB_API = "https://api.github.com/repos/ZtaMDev/poweredit-extensions/contents"
class SettingsWriter(QThread):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = settings

    def run(self):
        try:
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"⚠️ Error writing settings in thread: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        # Crear settings.json por defecto si no existe
        settings_path = "settings.json"
        if not os.path.exists(settings_path):
            default_settings = {
                "theme": "Default-Ideal",
                "project_root": None,
                "open_tabs": [],
                "active_tab": 0
            }
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(default_settings, f, indent=4)
        super().__init__()
        self.extensions = []
        self.setWindowIcon(QIcon("poweredit.ico"))
        self.setWindowTitle("PowerEdit")
        self.setGeometry(100, 100, 1000, 700)
        self._html_previewed_editors = set()
        self.tabs = TabsManager()
        self.tabs.close_live_preview_requested.connect(self.close_live_preview_background)
        self.tabs.current_editor()
        self.auto_refresh = False
        self.setCentralWidget(self.tabs)
        self.current_files = {}
        self.ext_map = { "py": "python" }
        self.file_explorer = FileExplorer()
        self.file_explorer.file_open_requested.connect(self.open_file_from_explorer)


        self.dock = CustomDockWidget("Explorer", self)
        self.dock.setWidget(self.file_explorer)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        self.dock.visibilityChanged.connect(self.on_dock_visibility_changed)


        self.console = ConsoleWidget()
        self.console_dock = CustomDockWidget("Console", self)
        self.console_dock.setWidget(self.console)
        self.console_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.console.live_server_requested.connect(self._on_live_server_request)

        self.live_preview = LivePreviewDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.live_preview)
        self.live_preview.hide()
        self.live_preview_timer = QTimer()
        self.live_preview_timer.setSingleShot(True)
        self.live_preview_timer.timeout.connect(self._reload_live_preview)
        self._current_preview_editor = None
        self.live_preview = LivePreviewDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.live_preview)
       

        try:
            self.file_explorer.project_root_changed.disconnect(self.console.restart_shell)
            
        except TypeError:
            pass

        self.file_explorer.project_root_changed.connect(self.console.restart_shell)
        self.file_explorer.project_root_changed.connect(self.save_settings)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.console_dock)
        self.console_dock.hide()

        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)

                # ─── Cargar tema ────────────────────
                theme_name = settings.get("theme")
                if theme_name:
                    self.load_theme(theme_name)

                # ─── Cargar carpeta raíz ─────────────
                project_root = settings.get("project_root")
                if project_root and os.path.isdir(project_root):
                    self.file_explorer.set_root(project_root)

                # ─── Abrir pestañas anteriores ────────
                open_tabs = settings.get("open_tabs", [])
                for entry in open_tabs:
                    if isinstance(entry, dict):
                        path = entry.get("path")
                        lang = entry.get("language", "plain")
                    else:
                        # compatibilidad con formatos antiguos
                        path = entry
                        ext = os.path.splitext(path)[1].lstrip(".").lower()
                        lang = self.ext_map.get(ext, "plain")

                    if os.path.isfile(path):
                        self.open_file_from_path(path, lang=lang)

                # Si no se abrió ninguna pestaña, mostramos la bienvenida
                if self.tabs.count() == 0:
                    self.tabs.show_welcome_tab()

                # ─── Restaurar pestaña activa ────────
                active_tab = settings.get("active_tab", 0)
                if 0 <= active_tab < self.tabs.count():
                    self.tabs.setCurrentIndex(active_tab)

        except Exception as e:
            print(f"Can't load configuration: {e}")

        self.init_menu()
        # Cargar tema desde settings.json si existe
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
                theme_name = settings.get("theme")
                if theme_name:
                    self.load_theme(theme_name)
        except Exception as e:
            print(f"Can't load theme: {e}")
        self.tabs.currentChanged.connect(self.update_run_button_for_current_tab)
        
        self.update_run_button_for_current_tab()  # inicial

    def show_extension_details(self, item):
        ext = item.data(Qt.UserRole)
        details = f"<h2>{ext.get('name', 'Sin nombre')}</h2>"

        if ext.get("icon_path") and os.path.exists(ext["icon_path"]):
            details = f'<img src="{ext["icon_path"]}" width="64" height="64"><br>' + details

        readme_path = ext.get("readme_path")
        if readme_path and os.path.exists(readme_path):
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    markdown = f.read()
                    import markdown as md
                    html = md.markdown(markdown)
                    details += html
            except Exception as e:
                details += f"<p><i>Error leyendo README.md: {e}</i></p>"
        else:
            details += "<p><i>README.md no encontrado.</i></p>"

        self.extensions_detail.setTextFormat(Qt.RichText)
        self.extensions_detail.setText(details)

    def toggle_extensions_manager_dock(self):
        if hasattr(self, "extensions_dock") and self.extensions_dock:
            self.extensions_dock.show()
            self.extensions_dock.raise_()
            return

        self.extensions_dock = CustomDockWidget("Extensions Manager", self)
        self.extensions_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.extensions_dock.setObjectName("extensions_manager_dock")

        container = QWidget()
        self.extensions_layout = QVBoxLayout(container)
        self.extensions_list = QListWidget()
        self.extensions_detail = QLabel("Click on an extension to see more information")
        self.extensions_detail.setWordWrap(True)
        self.extensions_detail.setAlignment(Qt.AlignTop)

        self.extensions_layout.addWidget(self.extensions_detail)
        self.extensions_layout.addWidget(QLabel("Installed extensions:"))
        self.extensions_layout.addWidget(self.extensions_list)

        container.setLayout(self.extensions_layout)
        self.extensions_dock.setWidget(container)
        self.addDockWidget(Qt.RightDockWidgetArea, self.extensions_dock)

        # === Botón desinstalar ===
        uninstall_btn = QPushButton("🗑️ Uninstall Extension")
        uninstall_btn.hide()
        uninstall_btn.setEnabled(False)
        self.uninstall_button = uninstall_btn
        uninstall_btn.clicked.connect(self.uninstall_selected_extension)

        # === Cuando se hace clic en un item ===
        def on_item_selected(item):
            if item:
                uninstall_btn.show()
                uninstall_btn.setEnabled(True)
                self.show_extension_details(item)
                self.selected_extension_item = item

        self.extensions_list.itemClicked.connect(on_item_selected)

        # === Cuando se cambia la selección (para detectar deselección) ===
        def on_selection_changed():
            current = self.extensions_list.currentItem()
            if current is None:
                self.uninstall_button.hide()
                self.uninstall_button.setEnabled(False)
                self.selected_extension_item = None
                self.extensions_detail.setText("Double click on an extension to see more information")

        self.extensions_list.itemSelectionChanged.connect(on_selection_changed)


        # === Llenar lista ===
        for ext in self.extensions:
            item = QListWidgetItem()
            icon_path = ext.get("icon_path") or "icons/plugin.svg"
            icon = QIcon(icon_path)
            item.setIcon(icon)
            item.setText(ext.get("name", "Unknown"))
            item.setData(Qt.UserRole, ext)
            self.extensions_list.addItem(item)

        # === Botones adicionales ===
        install_btn = QPushButton("Install Extension (.ext)")
        install_btn.clicked.connect(self.install_ext_file)

        refresh_btn = QPushButton("Refresh Extensions")
        refresh_btn.clicked.connect(self.refresh_extensions_list)

        # === Añadir a layout ===
        self.extensions_layout.addWidget(install_btn)
        self.extensions_layout.addWidget(refresh_btn)
        self.extensions_layout.addWidget(uninstall_btn)

        self.extensions_layout.addWidget(QLabel("Available from GitHub:"))
        self.github_list = QListWidget()
        self.extensions_layout.addWidget(self.github_list)

        self.github_list.itemClicked.connect(self.on_github_item_selected)
        self.github_list.itemSelectionChanged.connect(self.on_github_selection_cleared)

        # Botón para descargar de GitHub
        self.github_install_btn = QPushButton("Download && Install from GitHub")
        self.github_install_btn.setEnabled(False)
        self.github_install_btn.clicked.connect(self.install_from_github)
        self.extensions_layout.addWidget(self.github_install_btn)
        self.extensions_list.itemClicked.connect(lambda item: self.github_list.clearSelection())
        self.github_list.itemClicked.connect(lambda item: self.extensions_list.clearSelection())

        self.extensions_dock.show()
        self.load_github_list()

    def load_github_list(self):
        installed = {e["name"] for e in self.extensions}
        try:
            resp = requests.get(GITHUB_API + "/bundles")
            resp.raise_for_status()
            entries = resp.json()
        except Exception as e:
            QMessageBox.warning(self, "GitHub Error", f"Failed to fetch list: {e}")
            return

        self.github_list.clear()
        for entry in entries:
            name = entry["name"]
            if not name.lower().endswith(".ext"):
                continue
            extname = name[:-4]
            if extname in installed:
                continue
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, entry["download_url"])
            self.github_list.addItem(item)

    def on_github_item_selected(self, item):
        self.github_install_btn.setEnabled(bool(item))
        # Se puede mostrar más info aquí

    def on_github_selection_cleared(self):
        if not self.github_list.currentItem():
            self.github_install_btn.setEnabled(False)

    def install_from_github(self):
        item = self.github_list.currentItem()
        if not item:
            return
        dl_url = item.data(Qt.UserRole)
        name = item.text()[:-4]
        confirm = QMessageBox.question(
            self, "Install Extension",
            f"Download and install '{name}' from GitHub?\n\nYou will need to restart PowerEdit manually.",
            QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return

        try:
            resp = requests.get(dl_url)
            resp.raise_for_status()
            tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".ext")
            tmpfile.write(resp.content)
            tmpfile.close()

            # Usa tu método ya existente:
            self.install_ext_file_from_path(tmpfile.name)

            # Refrescar:
            QMessageBox.information(
                self, "Installed",
                f"'{name}' installed. Restart PowerEdit manually to activate."
            )
            self.refresh_extensions_list()
            self.load_github_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Download/install failed:\n{e}")
    
    def install_ext_file_from_path(self, file_path):
        def get_executable_dir():
                if getattr(sys, 'frozen', False):
                    # Estamos en un ejecutable PyInstaller
                    return os.path.dirname(sys.executable)
                else:
                    # Estamos en un script .py normal
                    return os.path.dirname(os.path.abspath(__file__))
        def run_command_silently(args):
            # Ejecuta el comando sin mostrar ventana de consola en Windows
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW
            result = subprocess.run(args, creationflags=creationflags)
            return result.returncode
        def install_requirements_with_embedded_python(requirements_file, parent_widget):
            base_dir = get_executable_dir()
            embedded_python = os.path.join(base_dir, "python_embedded", "python.exe")

            if not os.path.exists(embedded_python):
                QMessageBox.warning(parent_widget, "Missing Python",
                                    "Embedded Python not found. Cannot install requirements.")
                return False

            progress = QProgressDialog("Installing dependencies...", None, 0, 0, parent_widget)
            progress.setWindowModality(Qt.ApplicationModal)
            progress.setWindowTitle("Installing")
            progress.setCancelButton(None)
            progress.setMinimumDuration(0)
            progress.show()

            result_holder = {"success": False}  # mutable holder to get result from thread

            def run_install():
                try:
                    run_command_silently([embedded_python, "-m", "pip", "install", "--upgrade", "pip"])
                    ret = run_command_silently([embedded_python, "-m", "pip", "install", "-r", requirements_file])
                    result_holder["success"] = (ret == 0)
                except Exception as e:
                    print("Error installing requirements:", e)
                    result_holder["success"] = False
                finally:
                    progress.close()

            thread = threading.Thread(target=run_install)
            thread.start()

        with tempfile.TemporaryDirectory() as tmp:
            with ZipFile(file_path, 'r') as z:
                z.extractall(tmp)
            ext_folder = None
            for root, dirs, files in os.walk(tmp):
                if ".pext" in files and "main.py" in files:
                    ext_folder = root
                    break
            if not ext_folder:
                raise Exception("Invalid extension bundle")
            main_py = os.path.join(ext_folder, "main.py")
            ext_name = None
            for ln in open(main_py, encoding="utf-8"):
                m = re.match(r'^\s*name\s*=\s*["\'](.+?)["\']', ln)
                if m:
                    ext_name = m.group(1)
                    break
            if not ext_name:
                raise Exception("Couldn't determine extension name")
            dest = os.path.join("extensions", ext_name)
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(ext_folder, dest)

            # Instalar dependencias si existe requirements.txt
            requirements_path = os.path.join(dest, "requirements.txt")
            if os.path.exists(requirements_path):
                base_dir = get_executable_dir()
                embedded_python = os.path.join(base_dir, "python_embedded", "python.exe")

                if not os.path.exists(embedded_python):
                    QMessageBox.warning(self, "Missing Python", "Embedded Python not found.")
                else:
                    progress = QProgressDialog("Installing dependencies...", None, 0, 0, self)
                    progress.setWindowTitle("Installing")
                    progress.setCancelButton(None)
                    progress.setWindowModality(Qt.ApplicationModal)
                    progress.setMinimumDuration(0)
                    progress.show()

                    def on_finished(success):
                        progress.close()
                        if not success:
                            QMessageBox.warning(self, "Dependency Installation",
                                                f"Failed to install dependencies for {ext_name}")
                        # Aquí puedes seguir con el resto de la instalación si lo necesitas

                    thread = InstallThread(embedded_python, requirements_path)
                    thread.finished_signal.connect(on_finished)
                    thread.start()


            # carga solo esa extensión
            spec = importlib.util.spec_from_file_location(f"ext_{ext_name}",
                                                        os.path.join(dest, "main.py"))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            enabled = getattr(module, "enabled", True)
            api = EditorAPI(self, extension_name=ext_name)
            if enabled and hasattr(module, "setup"):
                module.setup(api)
            # añade a memoria
            icon_path = None
            for fn in ("plugin.svg", "plugin.png"):
                p = os.path.join(dest, "icons", fn)
                if os.path.exists(p):
                    icon_path = p
                    break
            self.extensions.append({
                "name": ext_name,
                "enabled": enabled,
                "description": getattr(module, "description", ""),
                "module": module,
                "path": dest,
                "readme_path": os.path.join(dest, "README.md") if os.path.exists(os.path.join(dest, "README.md")) else None,
                "icon_path": icon_path
            })

    def uninstall_selected_extension(self):
        item = getattr(self, "selected_extension_item", None)
        if not item:
            return

        ext = item.data(Qt.UserRole)
        name = ext.get("name", "")
        path = ext.get("path", "")

        confirm = QMessageBox.question(
            self, "Uninstall Extension",
            f"Are you sure you want to uninstall the extension '{name}'?\n\nYou will need to restart PowerEdit manually.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            import shutil
            shutil.rmtree(path)
            print(f"[Extensions] ❌ Extension '{name}' removed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove extension:\n\n{e}")
            return

        # Eliminar de la UI y restaurar estado
        self.extensions_list.takeItem(self.extensions_list.row(item))
        self.extensions_detail.setText("Click on an extension to see more information")
        self.uninstall_button.hide()
        self.uninstall_button.setEnabled(False)
        self.selected_extension_item = None

        deconfirm = QMessageBox.information(
            self,
            "Extension Uninstalled",
            f"The extension '{name}' was uninstalled.\n\nPlease restart PowerEdit manually to fully unload it.",
            QMessageBox.Yes | QMessageBox.No
        )
        if deconfirm == QMessageBox.Yes:
            app = QApplication.instance()
            app.quit()


    def refresh_extensions_list(self):
        """
        Solo repuebla la lista visual, manteniendo self.extensions ya cargadas.
        """
        extensions_dir = "extensions"
        os.makedirs(extensions_dir, exist_ok=True)

        # Quitar las que borraron del disco
        self.extensions = [e for e in self.extensions if os.path.isdir(e["path"])]

        # UI
        if hasattr(self, "extensions_list"):
            self.extensions_list.clear()
            for ext in self.extensions:
                item = QListWidgetItem(ext["name"])
                icon = QIcon(ext.get("icon_path") or "icons/plugin.svg")
                item.setIcon(icon)
                item.setData(Qt.UserRole, ext)
                self.extensions_list.addItem(item)

    
    
    def install_ext_file(self):
        def get_executable_dir():
                if getattr(sys, 'frozen', False):
                    # Estamos en un ejecutable PyInstaller
                    return os.path.dirname(sys.executable)
                else:
                    # Estamos en un script .py normal
                    return os.path.dirname(os.path.abspath(__file__))
        def run_command_silently(args):
            # Ejecuta el comando sin mostrar ventana de consola en Windows
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW
            result = subprocess.run(args, creationflags=creationflags)
            return result.returncode
        def install_requirements_with_embedded_python(requirements_file, parent_widget):

            base_dir = get_executable_dir()
            embedded_python = os.path.join(base_dir, "python_embedded", "python.exe")

            if not os.path.exists(embedded_python):
                QMessageBox.warning(parent_widget, "Missing Python",
                                    "Embedded Python not found. Cannot install requirements.")
                return False

            progress = QProgressDialog("Installing dependencies...", None, 0, 0, parent_widget)
            progress.setWindowModality(Qt.ApplicationModal)
            progress.setWindowTitle("Installing")
            progress.setCancelButton(None)
            progress.setMinimumDuration(0)
            progress.show()

            result_holder = {"success": False}  # mutable holder to get result from thread

            def run_install():
                try:
                    run_command_silently([embedded_python, "-m", "pip", "install", "--upgrade", "pip"])
                    ret = run_command_silently([embedded_python, "-m", "pip", "install", "-r", requirements_file])
                    result_holder["success"] = (ret == 0)
                except Exception as e:
                    print("Error installing requirements:", e)
                    result_holder["success"] = False
                finally:
                    progress.close()

            thread = threading.Thread(target=run_install)
            thread.start()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Extension Bundle (.ext)", "", "Extension Bundles (*.ext)"
        )
        if not file_path:
            return

        try:
            with tempfile.TemporaryDirectory() as tmp:
                with ZipFile(file_path, 'r') as z:
                    z.extractall(tmp)

                ext_folder = None
                for root, dirs, files in os.walk(tmp):
                    if ".pext" in files and "main.py" in files:
                        ext_folder = root
                        break

                if not ext_folder:
                    QMessageBox.warning(self, "Invalid Extension",
                                        "The selected .ext is not a valid extension.")
                    return

                # Leer nombre de main.py
                main_py = os.path.join(ext_folder, "main.py")
                ext_name = None
                with open(main_py, "r", encoding="utf-8") as f:
                    for ln in f:
                        m = re.match(r'^\s*name\s*=\s*["\'](.+?)["\']', ln)
                        if m:
                            ext_name = m.group(1)
                            break

                if not ext_name:
                    QMessageBox.warning(self, "Invalid Extension",
                                        "Could not determine extension name.")
                    return

                dest = os.path.join("extensions", ext_name)
                if os.path.exists(dest):
                    shutil.rmtree(dest)
                shutil.copytree(ext_folder, dest)

                # ✅ Instalar dependencias si hay requirements.txt
                requirements_path = os.path.join(dest, "requirements.txt")
                if os.path.exists(requirements_path):
                    install_requirements_with_embedded_python(requirements_path,self)


                # Cargar y ejecutar extensión
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"ext_{ext_name}", os.path.join(dest, "main.py"))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                enabled = getattr(module, "enabled", True)
                api = EditorAPI(self, extension_name=ext_name)
                if enabled and hasattr(module, "setup"):
                    module.setup(api)

                # Añadir a memoria
                icon_path = None
                for fn in ("plugin.svg", "plugin.png"):
                    p = os.path.join(dest, "icons", fn)
                    if os.path.exists(p):
                        icon_path = p
                        break

                self.extensions.append({
                    "name": ext_name,
                    "enabled": enabled,
                    "description": getattr(module, "description", ""),
                    "module": module,
                    "path": dest,
                    "readme_path": os.path.join(dest, "README.md") if os.path.exists(os.path.join(dest, "README.md")) else None,
                    "icon_path": icon_path
                })

                QMessageBox.information(self, "Extension Installed",
                                        f"'{ext_name}' installed successfully.")

                self.refresh_extensions_list()


        except Exception:
            QMessageBox.critical(self, "Error Installing", traceback.format_exc())



    def load_extensions_manager(self):
        import os
        import traceback
        import importlib.util

        extensions_dir = "extensions"
        if not os.path.exists(extensions_dir):
            os.makedirs(extensions_dir)
            print("[Extensions] Created extensions directory.")

        # Limpiar estado interno ANTES de cargar extensiones para evitar acumulación
        if hasattr(self, "_extension_actions"):
            # Eliminar acciones de menú previas
            for ext_name, actions in self._extension_actions.items():
                for act in actions:
                    self.menuBar().removeAction(act)
            self._extension_actions.clear()
        else:
            self._extension_actions = {}

        self.extensions = []

        for folder in os.listdir(extensions_dir):
            folder_path = os.path.join(extensions_dir, folder)
            main_file = os.path.join(folder_path, "main.py")
            readme_file = os.path.join(folder_path, "README.md")
            icon_path = None
            for icon_name in ("plugin.svg", "plugin.png"):
                possible_icon = os.path.join(folder_path, "icons", icon_name)
                if os.path.exists(possible_icon):
                    icon_path = possible_icon
                    break

            if not os.path.isdir(folder_path) or not os.path.exists(main_file):
                continue

            try:
                spec = importlib.util.spec_from_file_location(f"ext_{folder}", main_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                ext_name = getattr(module, "name", folder)
                enabled = getattr(module, "enabled", True)
                description = getattr(module, "description", "")

                self._extension_actions[ext_name] = []

                api = EditorAPI(self, extension_name=ext_name)

                if enabled and hasattr(module, "setup"):
                    original_add_menu_action = api.add_menu_action

                    def tracked_add_menu_action(path, callback):
                        action = original_add_menu_action(path, callback)
                        self._extension_actions[ext_name].append(action)
                        return action

                    api.add_menu_action = tracked_add_menu_action
                    module.setup(api)
                    print(f"[Extensions] ✅ Extensión '{ext_name}' cargada.")
                elif not enabled:
                    print(f"[Extensions] 🚫 Extensión '{ext_name}' deshabilitada.")
                else:
                    print(f"[Extensions] ⚠️ Extensión '{ext_name}' sin setup(api).")

                # Leer README
                readme = ""
                if os.path.exists(readme_file):
                    try:
                        with open(readme_file, "r", encoding="utf-8") as f:
                            readme = f.read()
                    except:
                        print(f"[Extensions] ⚠️ No se pudo leer README.md de '{ext_name}'.")

                self.extensions.append({
                    "name": ext_name,
                    "enabled": enabled,
                    "description": description,
                    "module": module,
                    "path": folder_path,
                    "readme_path": readme_file if os.path.exists(readme_file) else None,
                    "icon_path": icon_path if icon_path else None
                })

            except Exception as e:
                print(f"[Extensions] ❌ Error al cargar extensión '{folder}':\n{traceback.format_exc()}")

        # Limpiar UI visual ANTES de actualizar lista
        if hasattr(self, "extensions_list"):
            self.extensions_list.clear()
            for ext in self.extensions:
                item = QListWidgetItem()
                icon_path = ext.get("icon_path") or "icons/plugin.svg"
                icon = QIcon(icon_path)
                item.setIcon(icon)
                item.setText(ext.get("name", "Unknown"))
                item.setData(Qt.UserRole, ext)
                self.extensions_list.addItem(item)




    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, '_version_popup_shown', False):
            self._version_popup_shown = True
            from PyQt5.QtCore import QTimer
            def show_version_popup():
                try:
                    from versionpopup import VersionPopup
                    version_path = os.path.join(os.getcwd(), "version.json")
                    repo = "ZtaMDev/PowerEdit"  # Cambia si tu repo es otro
                    # Leer versión local
                    local_version = None
                    if os.path.exists(version_path):
                        with open(version_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            local_version = data.get("version")
                    # Consultar versión de GitHub
                    import requests
                    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
                    resp = requests.get(api_url, timeout=10)
                    if resp.status_code == 200:
                        latest = resp.json()
                        github_version = latest.get("tag_name")
                        if github_version and github_version != local_version:
                            popup = VersionPopup(repo, github_version, self, version_path=version_path, theme_css=self.current_theme_css)
                            popup.exec_()
                except Exception as e:
                    print(f"[VersionPopup] Error: {e}")
            QTimer.singleShot(350, show_version_popup)

    def update_run_button_for_current_tab(self):
        editor = self.tabs.current_editor()
        if editor is None:
            return

        path = self.current_files.get(editor)
        if path and path.endswith(".py"):
            editor.set_run_button_visible(True)
            try:
                editor.runRequested.disconnect()
            except TypeError:
                pass
            editor.runRequested.connect(lambda: self.run_current_file(editor))

        elif path and path.endswith(".html"):
            QTimer.singleShot(3000, lambda: editor.set_run_button_visible(True))
            try:
                editor.runRequested.disconnect()
            except TypeError:
                pass
            editor.runRequested.connect(lambda: self.run_html_preview(editor))
        else:
            editor.set_run_button_visible(False)

    def load_theme(self, theme_name):
        import os
        import json
        import re

        path = os.path.join("themes", theme_name + ".theme")
        if not os.path.exists(path):
            print(f"Tema '{theme_name}' no encontrado.")
            return

        with open(path, "r", encoding="utf-8") as f:
            css = f.read()
        self.current_theme_path = path

        # --- ICON COLOR ---
        icon_color = "#FFFFFF"
        match_icon = re.search(r"@icon-color:\s*(#[0-9A-Fa-f]{6}|default)", css)
        if match_icon:
            value = match_icon.group(1).strip().lower()
            if value != "default":
                icon_color = value
                if hasattr(self.file_explorer, "update_icons_color"):
                    self.file_explorer.update_icons_color(icon_color)
            else:
                if hasattr(self.file_explorer, "update_icons_color"):
                    self.file_explorer.update_icons_color(None)

        # --- FONT FAMILY ---
        font_family = None
        match_font = re.search(r"@font-family:\s*([^;\n]+);", css)
        if match_font:
            font_family = match_font.group(1).strip().strip('"').strip("'")

        # --- FONT SIZE ---
        font_size = None
        match_size = re.search(r"@font-size:\s*([0-9]+)px?;", css)
        if match_size:
            font_size = match_size.group(1).strip()

        # --- MENU COLORS ---
        menu_bg = "#2c2c2c"
        menu_fg = "#ffffff"

        match_menu_bg = re.search(r"@menu-background:\s*(#[0-9A-Fa-f]{6});", css)
        match_menu_fg = re.search(r"@menu-text-color:\s*(#[0-9A-Fa-f]{6});", css)

        if match_menu_bg:
            menu_bg = match_menu_bg.group(1).strip()
        if match_menu_fg:
            menu_fg = match_menu_fg.group(1).strip()

        self.menu_background = menu_bg
        self.menu_text_color = menu_fg

        # --- APLICAR FONT SIZE Y FONT FAMILY ---
        selectors = [
            "QMainWindow", "QMenuBar", "QMenu", "QTabBar::tab",
            "QDockWidget::title", "QTreeView", "QLabel",
            "QPushButton", "QPlainTextEdit", "QLineEdit", "QListWidget"
        ]

        def replace_or_add_property(css_text, selector, prop_name, prop_value):
            pattern = rf"({re.escape(selector)}\s*{{[^}}]*)(?:{prop_name}:\s*[^;]+;)?"
            def repl(m):
                start = m.group(1)
                if re.search(rf"{prop_name}:\s*[^;]+;", m.group(0)):
                    return re.sub(rf"{prop_name}:\s*[^;]+;", f"{prop_name}: {prop_value};", m.group(0))
                else:
                    return start + f"{prop_name}: {prop_value};"
            return re.sub(pattern, repl, css_text, flags=re.MULTILINE)

        if font_family:
            for sel in selectors:
                css = replace_or_add_property(css, sel, "font-family", f"\"{font_family}\", monospace")

        if font_size:
            for sel in selectors:
                css = replace_or_add_property(css, sel, "font-size", f"{font_size}px")

        # Eliminar variables antes de aplicar CSS final
        css_clean = re.sub(r"@font-family:[^;]+;\s*", "", css)
        css_clean = re.sub(r"@font-size:[^;]+;\s*", "", css_clean)
        css_clean = re.sub(r"@icon-color:[^;]+;\s*", "", css_clean)
        css_clean = re.sub(r"@menu-background:[^;]+;\s*", "", css_clean)
        css_clean = re.sub(r"@menu-text-color:[^;]+;\s*", "", css_clean)

        self.current_theme_css = css_clean

        self.setStyleSheet(css_clean)
        self.tabs.setStyleSheet(css_clean)
        self.file_explorer.setStyleSheet(css_clean)
        if hasattr(self.console_dock, "apply_theme"):
            self.console_dock.apply_theme(css_clean)
        self.dock.setStyleSheet(css_clean)

        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if hasattr(editor, "setStyleSheet"):
                editor.setStyleSheet(css_clean)

        # Guardar selección
        settings = {}
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
        except:
            pass
        settings["theme"] = theme_name
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    
    def style_menu(self, menu):
        if hasattr(self, "menu_background") and hasattr(self, "menu_text_color"):
            bg = self.menu_background
            fg = self.menu_text_color
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {bg};
                    color: {fg};
                    border: 1px solid {fg};
                }}
                QMenu::item:selected {{
                    background-color: {fg};
                    color: {bg};
                }}
            """)

    def schedule_save_settings(self):
        try:
            project_root = getattr(self.file_explorer, 'project_root', None)
            open_tabs = []
            for i in range(self.tabs.count()):
                editor = self.tabs.widget(i)
                path = self.current_files.get(editor)
                if path:
                    lang = getattr(editor, "language", "plain")
                    open_tabs.append({"path": path, "language": lang})

            active_tab = self.tabs.currentIndex()

            # Obtener tema existente (si existe)
            theme_name = None
            try:
                with open("settings.json", "r", encoding="utf-8") as f:
                    old_settings = json.load(f)
                theme_name = old_settings.get("theme")
            except:
                pass

            settings = {
                "theme": theme_name,
                "project_root": project_root,
                "open_tabs": open_tabs,
                "active_tab": active_tab
            }

            # 🧵 Guardar en segundo plano con un hilo
            self.save_thread = SettingsWriter(settings)
            self.save_thread.start()

        except Exception as e:
            print(f"⚠️ Can't prepare configuration to save: {e}")

    def save_settings(self):
        if hasattr(self, "_save_timer") and self._save_timer.isActive():
            self._save_timer.stop()

        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self.schedule_save_settings)
        self._save_timer.start(300)  # espera 300ms antes de ejecutar


    def run_current_file(self, editor=None):
        if editor is None:
            editor = self.tabs.current_editor()

        path = self.current_files.get(editor)
        if path and path.endswith(".py"):
            self.console_dock.show()
            cmd = f'python "{path}"'
            self.console.execute_command(cmd)

    def _on_live_server_request(self, ruta: str):

        url = QUrl(ruta)
        # si no tiene esquema, asumimos http
        if not url.scheme():
            url.setScheme("http")
        # comprueba que es sintácticamente válida y tenga host o sea local
        if not url.isValid() or (not url.host() and not url.isLocalFile()):
            QMessageBox.warning(self, "URL inválida",
                f"“{ruta}” no valid URL,\n"
                "Live Server can't start.")
            return
        if ruta.startswith(("http://", "https://")):
            # 1) Cargar URL externa
            self.live_preview.load_external_url(ruta)
        else:
            # 1') Cargar fichero local
            self.live_preview.load_html_from_file(ruta)

        # 2) Hacer visible el dock (por si estaba oculto o minimizado)
        if self.live_preview.isHidden() or self.live_preview.user_minimized:
            self.live_preview.user_minimized = False
            self.live_preview.show()

        # 3) Asegurar que el dock queda al frente
        self.live_preview.raise_()

    def run_html_preview(self, editor=None):
        # Obtener el editor actual si no se pasa ninguno
        if editor is None:
            editor = self.tabs.current_editor()
        if editor is None:
            return

        path = self.current_files.get(editor)

        # 1) Si el archivo no está guardado (sin ruta), preguntar
        if not path:
            ret = QMessageBox.question(
                self,
                "Save File",
                "The file must be saved to show the preview. Do you want to save it now?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if ret == QMessageBox.Yes:
                if not self.save_file_as():
                    return
                path = self.current_files.get(editor)
            else:
                return  # Canceló, no se puede previsualizar

        # 2) Comprobar cambios reales frente al contenido "guardado"
        current_text = editor.toPlainText()
        saved_text = self.tabs.saved_texts.get(editor, "")
        has_unsaved = (current_text != saved_text)

        if has_unsaved:
            ret = QMessageBox.question(
                self,
                "Save Changes",
                "This file has unsaved changes. Do you want to save them to update the preview?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if ret == QMessageBox.Yes:
                if not self.save_file():
                    return  # Falló el guardado
                # Actualizamos el registro de "guardado"
                self.tabs.saved_texts[editor] = editor.toPlainText()
                editor.document().setModified(False)
                path = self.current_files.get(editor)
            else:
                # Si decide no guardar, usar la versión en disco (si existe)
                if not os.path.isfile(path):
                    return 
        # 3) Lanzar la vista previa con la versión en disco
        if path and os.path.isfile(path):
            # Mostrar cursor de espera antes de cargar el live preview
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QTimer.singleShot(0, lambda: self.live_preview.load_html_from_file(path))
            self.live_preview.show()
            self._html_previewed_editors.add(editor)
            # Restaurar cursor tras un pequeño delay
            QTimer.singleShot(150, QApplication.restoreOverrideCursor)
        self.update_live_preview(editor)

    def show_live_preview(self, editor):
        if editor is None:
            return

        file_path = self.current_files.get(editor)

        # Asegura el registro si aún no está
        if file_path is None and hasattr(self.tabs, "_file_paths"):
            file_path = self.tabs._file_paths.get(editor)
            if file_path:
                self.current_files[editor] = file_path

        if file_path and os.path.isfile(file_path):
            self.live_preview.load_html_from_file(file_path)
            self.save_settings()

    def hide_live_preview(self):
        self.live_preview.hide()
        
    def update_live_preview(self, editor):
        path = self.current_files.get(editor)
        if path and path.endswith(".html"):
            self._current_preview_editor = editor
            # Cada vez que se llama, reinicia el timer
            self.live_preview_timer.start(500)  # 500 ms de espera

    def _reload_live_preview(self):
        if self._current_preview_editor:
            # Solo recarga, sin abrir o hacer cosas extrañas(CREO)
            self.live_preview.refresh()

    def toggle_file_explorer(self, checked):
        if checked:
            self.dock.show()
        else:
            self.dock.hide()
    
    def on_dock_visibility_changed(self, visible):
        self.toggle_explorer_act.setChecked(visible)
    
    def init_menu(self):
        menubar = self.menuBar()
        
        # ─── Menú Archivo ────────────────────────────────
        file_menu = menubar.addMenu("File")

        new_act = QAction("New Text File", self)
        new_act.setShortcut(QKeySequence.New)
        new_act.triggered.connect(lambda: self.tabs.new_tab())
        file_menu.addAction(new_act)

        new_named_act = QAction("New File...", self)
        new_named_act.setShortcut(QKeySequence("Ctrl+Alt+N"))
        new_named_act.triggered.connect(self.create_new_file)
        file_menu.addAction(new_named_act)

        new_window_act = QAction("New Window", self)
        new_window_act.setShortcut(QKeySequence("Ctrl+Shift+W"))
        new_window_act.triggered.connect(self.new_window)
        file_menu.addAction(new_window_act)

        open_act = QAction("Open File", self)
        open_act.setShortcut(QKeySequence.Open)
        open_act.triggered.connect(self.open_file)
        file_menu.addAction(open_act)

        open_act = QAction("Open Folder", self)
        open_act.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_act.triggered.connect(self.file_explorer.reselect_project_root)
        file_menu.addAction(open_act)

        save_act = QAction("Save", self)
        save_act.setShortcut(QKeySequence.Save)
        save_act.triggered.connect(self.save_file)
        file_menu.addAction(save_act)

        save_as_act = QAction("Save as...", self)
        save_as_act.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_act.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_act)

        file_menu.addSeparator()
        close_tab_act = QAction("Close actual tab", self)
        close_tab_act.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_act.triggered.connect(lambda: self.tabs.close_tab(self.tabs.currentIndex()))
        file_menu.addAction(close_tab_act)

        exit_act = QAction("Exit", self)
        exit_act.setShortcut(QKeySequence.Quit)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # ─── Menú Editar ───────────────────────────────
        edit_menu = menubar.addMenu("Edit")

        undo_act = QAction("Undo", self)
        undo_act.setShortcut(QKeySequence.Undo)
        undo_act.triggered.connect(lambda: self._editor_action("undo"))
        edit_menu.addAction(undo_act)

        redo_act = QAction("Redo", self)
        redo_act.setShortcut(QKeySequence.Redo)
        redo_act.triggered.connect(lambda: self._editor_action("redo"))
        edit_menu.addAction(redo_act)

        edit_menu.addSeparator()

        cut_act = QAction("Cut", self)
        cut_act.setShortcut(QKeySequence.Cut)
        cut_act.triggered.connect(lambda: self._editor_action("cut"))
        edit_menu.addAction(cut_act)

        copy_act = QAction("Copy", self)
        copy_act.setShortcut(QKeySequence.Copy)
        copy_act.triggered.connect(lambda: self._editor_action("copy"))
        edit_menu.addAction(copy_act)

        paste_act = QAction("Paste", self)
        paste_act.setShortcut(QKeySequence.Paste)
        paste_act.triggered.connect(lambda: self._editor_action("paste"))
        edit_menu.addAction(paste_act)

        select_all_act = QAction("Select all", self)
        select_all_act.setShortcut(QKeySequence.SelectAll)
        select_all_act.triggered.connect(lambda: self._editor_action("selectAll"))
        edit_menu.addAction(select_all_act)
        
        # ─── Menú Ventanas ───────────────────────────────
        windows_menu = menubar.addMenu("View")

        self.toggle_explorer_act = QAction("File Explorer", self, checkable=True)
        self.toggle_explorer_act.setChecked(True)
        self.toggle_explorer_act.setShortcut("Ctrl+Shift+E")
        self.toggle_explorer_act.triggered.connect(self.toggle_file_explorer)
        windows_menu.addAction(self.toggle_explorer_act)
        self.toggle_console_act = QAction("Toggle Console", self, checkable=True)
        self.toggle_console_act.setShortcut("Ctrl+Shift+C")
        self.toggle_console_act.setChecked(False)
        self.toggle_console_act.triggered.connect(
            lambda checked: self.console_dock.setVisible(checked)
        )
        windows_menu.addAction(self.toggle_console_act)
        self.console_dock.visibilityChanged.connect(
            lambda visible: self.toggle_console_act.setChecked(visible)
        )
        self.toggle_extensions_menu = QAction("Extensions Manager", self)
        self.toggle_extensions_menu.setShortcut("Ctrl+Alt+E")
        self.toggle_extensions_menu.setChecked(False)
        windows_menu.addAction(self.toggle_extensions_menu)
        self.toggle_extensions_menu.triggered.connect(self.toggle_extensions_manager_dock)

        #──────Menu Terminal──────────────
        terminal_menu = menubar.addMenu("Terminal")
        self.reiniciar_consola_action = QAction("Restart Console", self)
        self.reiniciar_consola_action.triggered.connect(lambda: self.console.restart_shell(self.console.work_dir))
        terminal_menu.addAction(self.reiniciar_consola_action)
        
        # ─── Menú Proyecto ───────────────────────────────
        project_menu = menubar.addMenu("Project")

        reselect_root_act = QAction("Select root folder", self)
        reselect_root_act.setShortcut(QKeySequence("Ctrl+Shift+R"))
        reselect_root_act.triggered.connect(self.file_explorer.reselect_project_root)
        project_menu.addAction(reselect_root_act)

        # ─── Menú Lenguaje ───────────────────────────────
        lang_menu = edit_menu.addMenu("Highlight")

        extend_folder = "extend"
        if os.path.isdir(extend_folder):
            for fname in os.listdir(extend_folder):
                if not fname.endswith(".extend"):
                    continue
                lang = fname.replace(".extend", "")
                path = os.path.join(extend_folder, fname)
                try:
                    rules = json.load(open(path, encoding="utf-8"))
                except Exception as e:
                    print(f"⚠️ Error leyendo {path}: {e}")
                    continue

                exts = rules.get("extensions", [lang])
                for ext in exts:
                    self.ext_map[ext.lower()] = lang

                act = QAction(lang.capitalize(), self)
                act.triggered.connect(lambda _, l=lang: self.change_language(l))
                lang_menu.addAction(act)
        
        # Menú Temas
        theme_menu = menubar.addMenu("Themes")
        theme_folder = "themes"

        if os.path.isdir(theme_folder):
            for fname in os.listdir(theme_folder):
                if not fname.endswith(".theme"):
                    continue
                theme_name = fname.replace(".theme", "")
                act = QAction(theme_name, self)
                act.triggered.connect(lambda _, name=theme_name: self.load_theme(name))
                theme_menu.addAction(act)

        reload_theme_act = QAction("Reload Actual Theme", self)
        reload_theme_act.triggered.connect(self.reload_current_theme)
        theme_menu.addSeparator()
        theme_menu.addAction(reload_theme_act)
        theme_menu.addSeparator()
        extend_menu = theme_menu.addMenu("Syntaxis Config .extend")
        extend_folder = "extend"
        if os.path.isdir(extend_folder):
            for fname in os.listdir(extend_folder):
                if fname.endswith(".extend"):
                    act = QAction(fname, self)
                    act.triggered.connect(lambda checked, f=fname: self.open_extend_file(os.path.join(extend_folder, f)))
                    extend_menu.addAction(act)

        # --- Submenú para archivos .theme ---
        theme_menu = theme_menu.addMenu("Theme Config .theme")
        theme_folder = "themes"
        if os.path.isdir(theme_folder):
            for fname in os.listdir(theme_folder):
                if fname.endswith(".theme"):
                    act = QAction(fname, self)
                    act.triggered.connect(lambda checked, f=fname: self.open_theme_file(os.path.join(theme_folder, f)))
                    theme_menu.addAction(act)

        # ─── Menú Ayuda ───────────────────────────────
        help_menu = menubar.addMenu("Help")
        about_act = QAction("About PowerEdit", self)
        about_act.triggered.connect(self.show_about)
        download_act = QAction("Download source code", self)
        download_act.triggered.connect(lambda: DownloadDialog(self).exec_())
        help_menu.addAction(download_act)
        help_menu.addAction(about_act)


    def create_new_file(self):
        filename, ok = QInputDialog.getText(self, "New File", "File Name (.py .js .html .css .json)")
        if not ok or not filename.strip():
            return

        filename = filename.strip()
        extension = os.path.splitext(filename)[1].lstrip(".").lower()

        # Detectar lenguaje basado en la extensión
        language = self.ext_map.get(extension, "plain") if hasattr(self, "ext_map") else "plain"

        # Crear nueva pestaña vacía con ese nombre y lenguaje
        editor = self.tabs.new_tab(file_path=filename, content="", language=language)

        # Registrar el archivo en current_files
        if hasattr(self, "current_files"):
            self.current_files[editor] = filename

        self.save_settings()
        self.update_run_button_for_current_tab()

    def new_window(self):
        # Verificar si hay cambios sin guardar (igual que closeEvent)
        unsaved = []
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            # Saltar pestaña de bienvenida
            if hasattr(self.tabs, '_welcome_tab') and editor == self.tabs._welcome_tab:
                continue
            if hasattr(editor, 'toPlainText'):
                current = editor.toPlainText()
                saved = self.tabs.saved_texts.get(editor, "")
                if current != saved:
                    unsaved.append(self.tabs.tabText(i))

        if unsaved:
            msg = (
                "There are unsaved changes in the following tabs: \n\n" +
                "\n".join(unsaved) +
                "\n\nIf you create a new window now, all unsaved changes will be lost.\n\nDo you want to continue?"
            )
            reply = QMessageBox.warning(
                self,
                "Unsaved Changes",
                msg,
                QMessageBox.Yes | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            if reply != QMessageBox.Yes:
                return  # Cancelado por el usuario

        # Continuar con nueva ventana limpia
        default_settings = {
            "theme": "Default-Ideal",
            "project_root": None,
            "open_tabs": []
        }
        try:
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(default_settings, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Can't create new project:\n{e}")
            return

        self.tabs.clear()
        self.current_files.clear()
        self.tabs.show_welcome_tab()
        self.file_explorer.set_root(None)
        self.file_explorer.root_folder_label.hide()
        self.load_theme("Default-Ideal")


    def reload_current_theme(self):
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
            theme_name = settings.get("theme")
            if theme_name:
                self.load_theme(theme_name)
                #Innesesario pero OK para debug
                #QMessageBox.information(self, "Tema", f"El tema '{theme_name}' ha sido recargado.")
            else:
                QMessageBox.warning(self, "Theme", "No selected theme on configuration")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Can't restart theme:\n{str(e)}")

    def open_extend_file(self, filepath):
        if self.focus_tab_with_path(filepath):
            return  # Ya está abierto
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        
        # Abrir en una pestaña nueva con extensión ".extend"
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Can't open it {filepath}:\n{str(e)}")

        ext = os.path.splitext(filepath)[1].lstrip(".").lower()
        lang = self.ext_map.get(ext, "plain")

        # Forzar CSS si es .theme
        if ext == "extend":
            lang = "css"

        editor = self.tabs.new_tab(file_path=filepath, content=content, language=lang)
        self.current_files[editor] = filepath
        self.save_settings()
        self.update_run_button_for_current_tab()
    def open_theme_file(self, filepath):
        if self.focus_tab_with_path(filepath):
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Can't open it {filepath}:\n{str(e)}")
            return

        ext = os.path.splitext(filepath)[1].lstrip(".").lower()
        lang = self.ext_map.get(ext, "plain")

        # Forzar CSS si es .theme
        if ext == "theme":
            lang = "css"

        editor = self.tabs.new_tab(file_path=filepath, content=content, language=lang)
        self.current_files[editor] = filepath
        self.save_settings()
        self.update_run_button_for_current_tab()

    def toggle_console(self, checked):
        if checked:
            self.console_dock.show()
        else:
            self.console_dock.hide()

    def change_language(self, lang):
        current_widget = self.tabs.currentWidget()
        # Solo llamar si el widget actual es un editor con set_language
        if hasattr(current_widget, "set_language"):
            current_widget.set_language(lang)

    def open_file_from_path(self, path, lang=None):
        if self.focus_tab_with_path(path):
            # Si ya existe, asegúrate de fondo oscuro si es imagen
            idx = self.tabs.currentIndex()
            widget = self.tabs.widget(idx)
            image_exts = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "ico"}
            ext = os.path.splitext(path)[1].lstrip(".").lower()
            if ext in image_exts and hasattr(widget, "label") and hasattr(widget, "scroll"):
                widget.setStyleSheet("background-color: #181818;")
            return 

        try:
            image_exts = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "ico"}
            ext = os.path.splitext(path)[1].lstrip(".").lower()
            if ext in image_exts:
                widget = self.tabs.new_tab(file_path=path)
                widget.setStyleSheet("background-color: #181818;")
                self.current_files[widget] = path
                self.save_settings()
                return

            # Determinar lenguaje
            if lang is None:
                lang = self.ext_map.get(ext, "plain")

            # Crear la pestaña vacía
            editor = self.tabs.new_tab(file_path=path, content="", language=lang)

            # Carga eficiente (con ProgressDialog si procede)
            load_large_file_to_editor(editor, path, show_progress=True)

            # Marca el contenido como guardado: no disparará on_editor_modified
            self.tabs.saved_texts[editor] = editor.toPlainText()

            # Posicionar al inicio
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            editor.setTextCursor(cursor)

            # Reaplica tema
            if hasattr(editor, "setStyleSheet"):
                editor.setStyleSheet(self.styleSheet())

            # Registra en current_files y refresca UI
            self.current_files[editor] = path
            self.save_settings()
            self.update_run_button_for_current_tab()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def open_file_from_explorer(self, file_path):
        if self.focus_tab_with_path(file_path):
            idx = self.tabs.currentIndex()
            widget = self.tabs.widget(idx)
            image_exts = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "ico"}
            ext = os.path.splitext(file_path)[1].lstrip(".").lower()
            if ext in image_exts and hasattr(widget, "label") and hasattr(widget, "scroll"):
                widget.setStyleSheet("background-color: #181818;")
            return

        try:
            image_exts = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "ico"}
            ext = os.path.splitext(file_path)[1].lstrip(".").lower()
            if ext in image_exts:
                widget = self.tabs.new_tab(file_path=file_path)
                widget.setStyleSheet("background-color: #181818;")
                self.current_files[widget] = file_path
                self.save_settings()
                return

            lang = self.ext_map.get(ext, "plain")

            # Crear nueva pestaña vacía
            editor = self.tabs.new_tab(file_path=file_path, content="", language=lang)

            # Carga eficiente con un solo ProgressDialog
            load_large_file_to_editor(editor, file_path, show_progress=True)

            # Marca el contenido como guardado para no disparar “modificado”
            self.tabs.saved_texts[editor] = editor.toPlainText()

            # Posicionar al inicio
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            editor.setTextCursor(cursor)

            # Aplica tema
            if hasattr(editor, "setStyleSheet"):
                editor.setStyleSheet(self.styleSheet())

            # Registro y ajustes
            self.current_files[editor] = file_path
            self.save_settings()
            self.update_run_button_for_current_tab()

        except Exception as e:
            QMessageBox.critical(self, "Error opening file ", str(e))

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if not path or self.focus_tab_with_path(path):
            if path:
                idx = self.tabs.currentIndex()
                widget = self.tabs.widget(idx)
                image_exts = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "ico"}
                ext = os.path.splitext(path)[1].lstrip(".").lower()
                if ext in image_exts and hasattr(widget, "label") and hasattr(widget, "scroll"):
                    widget.setStyleSheet("background-color: #181818;")
            return

        self.save_settings()
        try:
            image_exts = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "ico"}
            ext = os.path.splitext(path)[1].lstrip(".").lower()
            if ext in image_exts:
                widget = self.tabs.new_tab(file_path=path)
                widget.setStyleSheet("background-color: #181818;")
                self.current_files[widget] = path
                return

            lang = self.ext_map.get(ext, "plain")

            # Crear pestaña vacía
            editor = self.tabs.new_tab(file_path=path, content="", language=lang)

            # Carga eficiente (ProgressDialog si > 512 KB en file_loading)
            load_large_file_to_editor(editor, path, show_progress=True)

            # Marca como guardado para no indicar cambio
            self.tabs.saved_texts[editor] = editor.toPlainText()

            # Posicionar al inicio y resetear scroll
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            editor.setTextCursor(cursor)
            editor.verticalScrollBar().setValue(0)

            # Reaplica tema
            if hasattr(editor, "setStyleSheet"):
                editor.setStyleSheet(self.styleSheet())

            # Registra y actualiza UI
            self.current_files[editor] = path
            self.update_run_button_for_current_tab()

        except Exception as e:
            QMessageBox.critical(self, "Error opening file", str(e))

    def save_file(self):
        editor = self.tabs.current_editor()
        if editor is None:
            return False  # Nada que guardar
        path = self.current_files.get(editor)
        self._reload_live_preview()
        if not path or not os.path.isabs(path):
            self.save_file_as()
            return False  # No se guardó aún (esperando ruta nueva)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())
            self.tabs.saved_texts[editor] = editor.toPlainText()
            self.tabs.update_tab_text(
                self.tabs.indexOf(editor),
                file_path=path,
                language=editor.language,
                modified=False
            )
            self.save_settings()
            editor.document().setModified(False)  # Marca como no modificado
            return True  # Guardado exitoso
        except Exception as e:
            QMessageBox.critical(self, "Error saving", f"Can't save file:\n{str(e)}")
            return False  # Falló

    def save_file_as(self):
        editor = self.tabs.current_editor()
        if editor is None:
            return False

        suggested = self.current_files.get(editor)
        if suggested is None or not isinstance(suggested, str):
            suggested_name = "nuevo_archivo.txt"
        else:
            suggested_name = os.path.basename(suggested).replace("*", "").strip()

        if hasattr(self.file_explorer, "project_root") and self.file_explorer.project_root:
            default_dir = self.file_explorer.project_root
        else:
            default_dir = os.path.join(os.path.expanduser("~"), "Documents")

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            os.path.join(default_dir, suggested_name),
            "Todos los archivos (*)"
        )

        if not path:
            return False

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())

            # Detectar lenguaje por extensión
            ext = os.path.splitext(path)[1].lstrip(".").lower()
            lang = self.ext_map.get(ext, "plain")

            # Leer contenido guardado
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Abrir nueva pestaña con contenido y lenguaje detectado
            new_editor = self.tabs.new_tab(file_path=path, content=content, language=lang)

            # Mover cursor al inicio
            cursor = new_editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            new_editor.setTextCursor(cursor)

            # Actualizar referencias
            self.current_files[new_editor] = path
            self.tabs.saved_texts[new_editor] = content

            # Cerrar la pestaña antigua
            old_index = self.tabs.indexOf(editor)
            if old_index != -1:
                self.tabs.removeTab(old_index)

            self.save_settings()
            return True

        except Exception as e:
            QMessageBox.critical(self, "Error saving", f"Can't save file:\n{str(e)}")
            return False

    def _editor_action(self, action):
        editor = self.tabs.current_editor()
        if editor and hasattr(editor, action):
            getattr(editor, action)()

    def show_about(self):
        dialog = QDialog(self, flags=Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        dialog.setWindowTitle("About PowerEdit")
        dialog.setModal(True)
        dialog.setStyleSheet(self.styleSheet())
        label = QLabel("""
    <b>PowerEdit</b> is a lightweight code editor built with PyQt5<br><br>
    <b>For more information visit: https://github.com/ZtaMDev/PowerEdit</b>
    <b>See the release notes here: https://github.com/ZtaMDev/PowerEdit/releases</b>
    <b>Author:</b> ZtaMDev<br>
    <b>Version:</b> 1.0.4 Beta<br>
    <b>License:</b> MIT License
    """)
        label.setTextFormat(Qt.RichText)
        label.setAlignment(Qt.AlignLeft)
        label.setWordWrap(True)

        button = QPushButton("Close")
        button.clicked.connect(dialog.accept)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(button, alignment=Qt.AlignRight)
        dialog.setLayout(layout)

        dialog.exec_()

    def closeEvent(self, event):
        # Warn if there are unsaved changes in any tab (except Welcome)
        unsaved = []
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            # Skip welcome tab
            if hasattr(self.tabs, '_welcome_tab') and editor == self.tabs._welcome_tab:
                continue
            if hasattr(editor, 'toPlainText'):
                current = editor.toPlainText()
                saved = self.tabs.saved_texts.get(editor, "")
                if current != saved:
                    unsaved.append(self.tabs.tabText(i))
        if unsaved:
            msg = ("There are unsaved changes in the following tabs: \n\n" +
                   "\n".join(unsaved) +
                   " \n\nIf you close the application now, all unsaved changes will be lost.\n\nDo you want to exit anyway?")
            reply = QMessageBox.warning(
                self,
                "Unsaved Changes",
                msg,
                QMessageBox.Yes | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
        event.accept()

    def focus_tab_with_path(self, file_path):
        # Devuelve True si se encontró y enfocó
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if self.current_files.get(editor) == file_path:
                self.tabs.setCurrentIndex(i)
                return True
        return False

    def set_editor_font_size(self, size):
        # Cambia el font-size en el QSS solo para QPlainTextEdit
        css = self.current_theme_css if hasattr(self, 'current_theme_css') else ""
        # Elimina cualquier font-size previo para QPlainTextEdit
        css = re.sub(r'(QPlainTextEdit\s*\{[^}]*?)font-size:\s*[^;]+;?', r'\1', css, flags=re.MULTILINE)
        # Añade el nuevo font-size
        css = re.sub(r'(QPlainTextEdit\s*\{)', r'\1\n    font-size: %dpx;' % size, css, count=1)
        self.setStyleSheet(css)
        self.tabs.setStyleSheet(css)
        self.file_explorer.setStyleSheet(css)
        if hasattr(self.console_dock, "apply_theme"):
            self.console_dock.apply_theme(css)
        self.dock.setStyleSheet(css)
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if hasattr(editor, "setStyleSheet"):
                editor.setStyleSheet(css)
        self.current_theme_css = css

    def update_theme_font_size(self, size):
        # Actualiza solo el atributo font-size en el .theme actual
        if not hasattr(self, 'current_theme_path') or not self.current_theme_path:
            return
        try:
            with open(self.current_theme_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            found = False
            for i, line in enumerate(lines):
                if line.strip().startswith('@font-size:'):
                    lines[i] = f'@font-size: {size}px;\n'
                    found = True
                    break
            if not found:
                # Si no existe, lo agrega al final
                lines.append(f'@font-size: {size}px;\n')
            with open(self.current_theme_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        except Exception as e:
            print(f"[update_theme_font_size] Error: {e}")

    def close_live_preview_background(self, file_path):
        from PyQt5.QtCore import QTimer
        import os
        # Solo cierra si el live preview está mostrando ese archivo
        if self.live_preview.last_loaded_path and os.path.normpath(self.live_preview.last_loaded_path) == os.path.normpath(file_path):
            def do_close():
                self.live_preview.user_minimized = True
                self.live_preview.stop_server()
                self.live_preview.hide()
            QTimer.singleShot(100, do_close)

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

class InstallThread(QThread):
    finished_signal = pyqtSignal(bool)

    def __init__(self, embedded_python, requirements_path):
        super().__init__()
        self.embedded_python = embedded_python
        self.requirements_path = requirements_path

    def run(self):
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            subprocess.run([self.embedded_python, "-m", "pip", "install", "--upgrade", "pip"], creationflags=creationflags)
            result = subprocess.run([self.embedded_python, "-m", "pip", "install", "-r", self.requirements_path], creationflags=creationflags)
            self.finished_signal.emit(result.returncode == 0)
        except Exception as e:
            print("Install error:", e)
            self.finished_signal.emit(False)
