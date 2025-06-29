import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QFileSystemModel, QTreeView, QFileDialog
)
from PyQt5.QtCore import pyqtSignal, QModelIndex, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel,
    QFileSystemModel, QTreeView, QFileDialog
)
from PyQt5.QtCore import pyqtSignal, QModelIndex, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu, QAction, QInputDialog, QMessageBox
from PyQt5.QtWidgets import QApplication  # Asegura que QApplication esté importado
import time
class CustomFileSystemModel(QFileSystemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Iconos
        self.folder_icon = QIcon("icons/folder.svg")
        self.file_icon = QIcon("icons/file.svg")

    def data(self, index, role):
        if role == Qt.DecorationRole:
            if self.isDir(index):
                return self.folder_icon
            else:
                return self.file_icon
        return super().data(index, role)
    
class FileExplorer(QWidget):
    file_open_requested = pyqtSignal(str)
    project_root_changed = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)

        self.project_root = None
        
        self.model = CustomFileSystemModel(self)
        self.model.setRootPath("")

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)
        self.tree.hide()
        self.tree.setRootIsDecorated(True)  # ← permite mostrar la carpeta raíz como nodo expandible(no funciona...)
        self.tree.doubleClicked.connect(self.on_double_click)
        
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)

        self.label = QLabel("To select your project,\n first choose the root folder.")
        self.label.setStyleSheet("""
            color: white;
            font-family: Consolas, monospace;
            font-size: 12px;
            color: gray; 
        """)
        self.label.setAlignment(Qt.AlignCenter)

        self.root_folder_label = QLabel("")
        self.root_folder_label.setStyleSheet("""
            color: #6272A4;
            font-family: Consolas, monospace;
            font-size: 12px;
            padding: 4px 8px;
        """)
        self.root_folder_label.hide()  # Oculto inicialmente

        self.button = QPushButton("Select root folder")
        self.button.clicked.connect(self.select_project_root)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #44475A;
                color: white;
                padding: 4px 8px;
                border: none;
                border-radius: 2px;
                font-family: Consolas, monospace;
            }
            QPushButton:hover {
                background-color: #6272A4;
            }
        """)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        layout.addWidget(self.tree)
        layout.addWidget(self.root_folder_label)
        self.setLayout(layout)
        

    def open_context_menu(self, position):
        index = self.tree.indexAt(position)
        menu = QMenu(self)

        rename_action = QAction("Rename", self)
        delete_action = QAction("Delete", self)
        new_file_action = QAction("New File", self)
        properties_action = QAction("Properties", self)

        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.addSeparator()
        menu.addAction(new_file_action)
        new_folder_action = QAction("New Folder", self)
        menu.addAction(new_folder_action)
        menu.addSeparator()
        menu.addAction(properties_action)
        new_folder_action.triggered.connect(lambda: self.create_new_folder(index))
        # APLICAR ESTILO ACTUAL DEL TEMA DINÁMICAMENTE
        if hasattr(self.parent(), "menu_background") and hasattr(self.parent(), "menu_text_color"):
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {self.parent().menu_background};
                    color: {self.parent().menu_text_color};
                    border: 1px solid #555;
                    font-family: Consolas, monospace;
                    font-size: 11px;
                }}
                QMenu::item:selected {{
                    background-color: #444;
                    color: white;
                }}
            """)
        else:
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2c2c2c;
                    color: white;
                    border: 1px solid #444;
                    padding: 4px;
                    font-family: Consolas, monospace;
                    font-size: 12px;
                }
                QMenu::item {
                    padding: 4px 12px;
                    background-color: transparent;
                }
                QMenu::item:selected {
                    background-color: #3a3a3a;
                    color: white;
                }
                QMenu::separator {
                    height: 1px;
                    background: #555;
                    margin: 4px 0;
                }
            """)

        # Conectar acciones
        rename_action.triggered.connect(lambda: self.rename_item(index))
        delete_action.triggered.connect(lambda: self.delete_item(index))
        new_file_action.triggered.connect(lambda: self.create_new_file(index))
        properties_action.triggered.connect(lambda: self.show_properties_dialog(index))

        menu.exec_(self.tree.viewport().mapToGlobal(position))

    def show_properties_dialog(self, index):
        if not index.isValid():
            return
        path = self.model.filePath(index)
        is_dir = self.model.isDir(index)
        icon = self.model.folder_icon if is_dir else self.model.file_icon
        # Detectar tipo
        if is_dir:
            tipo = "Folder"
            ext = ""
            lang = ""
        else:
            ext = os.path.splitext(path)[1].lstrip(".").lower()
            # Buscar lenguaje usando .extend
            lang = ext
            extend_folder = "extend"
            lang_name = None
            if os.path.isdir(extend_folder):
                for fname in os.listdir(extend_folder):
                    if not fname.endswith(".extend"): continue
                    try:
                        import json
                        rules = json.load(open(os.path.join(extend_folder, fname), encoding="utf-8"))
                        exts = rules.get("extensions", [fname.replace(".extend","")])
                        if ext in [e.lower() for e in exts]:
                            lang_name = fname.replace(".extend","")
                            break
                    except Exception:
                        pass
            tipo = f".{ext} ({lang_name if lang_name else 'Unknown'})"
        # Crear popup menos invasivo, fondo sólido y opaco, estilo oscuro neutro
        dlg = QDialog(self, flags=Qt.FramelessWindowHint | Qt.Popup)
        dlg.setModal(False)
        dlg.setFixedWidth(320)
        dlg.setStyleSheet("""
            QDialog { background: #181a1b; color: #e0e0e0; border-radius: 10px; border: 2px solid #23272e; }
            QLabel { font-size: 11.5px; font-family: Consolas, monospace; color: #e0e0e0; }
            #IconLabel { margin-top: 8px; margin-bottom: 8px; }
            QPushButton { background: #23272e; color: #e0e0e0; border: none; border-radius: 4px; padding: 4px 16px; font-size: 11px; }
            QPushButton:hover { background: #444c56; }
        """)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 10, 16, 10)
        icon_label = QLabel()
        icon_label.setObjectName("IconLabel")
        icon_label.setPixmap(icon.pixmap(80,80))
        icon_label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(icon_label)
        # Propiedades organizadas
        # Adaptar tamaño de fuente y dividir en dos líneas si la ruta es muy larga
        max_chars_per_line = 55
        min_font_size = 8
        base_font_size = 11
        path_display = path
        font_size = base_font_size
        if len(path) > max_chars_per_line * 2:
            font_size = min_font_size
            first_line = path[:max_chars_per_line]
            second_line = path[max_chars_per_line:max_chars_per_line*2]
            if len(path) > max_chars_per_line*2:
                second_line += '...'
            path_html = f"<b>Path:</b> <span style='color:#8be9fd;font-size:{font_size}px'>{first_line}<br>{second_line}</span>"
        elif len(path) > max_chars_per_line:
            font_size = 9
            first_line = path[:max_chars_per_line]
            second_line = path[max_chars_per_line:]
            path_html = f"<b>Path:</b> <span style='color:#8be9fd;font-size:{font_size}px'>{first_line}<br>{second_line}</span>"
        elif len(path) > 40:
            font_size = 10
            path_html = f"<b>Path:</b> <span style='color:#8be9fd;font-size:{font_size}px'>{path}</span>"
        else:
            path_html = f"<b>Path:</b> <span style='color:#8be9fd;font-size:{font_size}px'>{path}</span>"
        path_label = QLabel(path_html)
        # Obtener fecha de modificación
        try:
            import datetime
            mtime = os.path.getmtime(path)
            mod_dt = datetime.datetime.fromtimestamp(mtime)
            mod_str = mod_dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            mod_str = 'Unknown'
        mod_label = QLabel(f"<b>Modified:</b> <span style='color:#bd93f9;font-size:11px'>{mod_str}</span>")
        # Mostrar primero 'Calculating...' y calcular el tamaño en segundo plano
        size_label = QLabel("<b>Size:</b> <span style='color:#50fa7b;font-size:11px'>Calculating...</span>")
        type_label = QLabel(f"<b>Type:</b> <span style='color:#f1fa8c;font-size:11px'>{tipo}</span>")
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        type_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        mod_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        size_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(path_label)
        layout.addWidget(type_label)
        layout.addWidget(size_label)
        layout.addWidget(mod_label)
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.accept)
        btn.setFixedWidth(70)
        btn.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(btn, alignment=Qt.AlignRight)
        # Posicionar el popup a la izquierda del archivo/carpeta, pero evitar que se salga de la pantalla
        rect = self.tree.visualRect(index)
        global_pos = self.tree.viewport().mapToGlobal(rect.topLeft())
        dlg.adjustSize()
        popup_x = global_pos.x() - dlg.width() - 8  # A la izquierda del item
        popup_y = global_pos.y() + rect.height()//2 - dlg.height()//2  # Centrado verticalmente respecto al item
        # Limitar para que no se salga de la pantalla
        screen = QApplication.primaryScreen().availableGeometry()
        if popup_x < screen.left():
            # Si no cabe a la izquierda, mostrar a la derecha
            popup_x = global_pos.x() + rect.width() + 8
            if popup_x + dlg.width() > screen.right():
                popup_x = screen.right() - dlg.width() - 8
        if popup_y < screen.top():
            popup_y = screen.top() + 8
        if popup_y + dlg.height() > screen.bottom():
            popup_y = screen.bottom() - dlg.height() - 8
        dlg.move(popup_x, popup_y)
        dlg.show()
        # Calcular tamaño en segundo plano
        from PyQt5.QtCore import QThread, pyqtSignal, QObject
        class SizeWorker(QObject):
            finished = pyqtSignal(str)
            def __init__(self, path, is_dir):
                super().__init__()
                self.path = path
                self.is_dir = is_dir
            def run(self):
                import os
                def human_size(size):
                    for unit in ['B','KB','MB','GB','TB']:
                        if size < 1024.0:
                            return f"{size:.2f} {unit}"
                        size /= 1024.0
                    return f"{size:.2f} PB"
                def get_folder_size(folder):
                    total = 0
                    for dirpath, dirnames, filenames in os.walk(folder):
                        for f in filenames:
                            fp = os.path.join(dirpath, f)
                            try:
                                total += os.path.getsize(fp)
                            except Exception:
                                pass
                    return total
                try:
                    if self.is_dir:
                        size_bytes = get_folder_size(self.path)
                        size_str = human_size(size_bytes)
                    else:
                        size_bytes = os.path.getsize(self.path)
                        size_str = human_size(size_bytes)
                except Exception:
                    size_str = 'Unknown'
                self.finished.emit(size_str)
        def update_size_label(size_str):
            size_label.setText(f"<b>Size:</b> <span style='color:#50fa7b;font-size:11px'>{size_str}</span>")
        worker = SizeWorker(path, is_dir)
        thread = QThread()
        worker.moveToThread(thread)
        worker.finished.connect(update_size_label)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        thread.start()
        # Mantener referencia al thread y worker para evitar recolección de basura
        dlg._size_thread = thread
        dlg._size_worker = worker
        # Cerrar si pierde foco
        dlg.setFocus()
        dlg.activateWindow()
        def close_on_focus_out(event):
            thread.quit()
            thread.wait()
            dlg.close()
        dlg.focusOutEvent = close_on_focus_out

    def create_new_folder(self, index: QModelIndex):
        if index.isValid() and self.model.isDir(index):
            folder_path = self.model.filePath(index)
        else:
            folder_path = self.project_root or ""
            if not folder_path:
                QMessageBox.warning(self, "Error", "No folder selected and no project root set.")
                return

        dialog = CustomInputDialog("New Folder", "Enter folder name:", self)
        folder_name, ok = dialog.getText()

        if ok and folder_name:
            new_folder_path = os.path.join(folder_path, folder_name)
            try:
                os.makedirs(new_folder_path)
                print(f"[FileExplorer] Carpeta creada: {new_folder_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo crear la carpeta:\n{e}")


    def rename_item(self, index: QModelIndex):

        if not index.isValid():
            return

        old_path = self.model.filePath(index)
        old_name = os.path.basename(old_path)

        dialog = CustomInputDialog("Rename", "New name:", self)
        dialog.input.setText(old_name)
        name, ok = dialog.getText()
        if ok and name and name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), name)
            try:
                os.rename(old_path, new_path)
                print(f"[FileExplorer] Renombrado a: {new_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not rename:\n{e}")


    def delete_item(self, index: QModelIndex):
        if not index.isValid():
            return

        path = self.model.filePath(index)
        name = os.path.basename(path)
        ret = QMessageBox.question(
            self,
            "Delete",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if ret == QMessageBox.Yes:
            try:
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                print(f"[FileExplorer] Eliminado: {path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete:\n{e}")


    def create_new_file(self, index: QModelIndex):

        if index.isValid() and self.model.isDir(index):
            folder_path = self.model.filePath(index)
        else:
            folder_path = getattr(self, "project_root", None)
            if folder_path is None:
                QMessageBox.warning(self, "Error", "No folder selected and no project root set.")
                return

        dialog = CustomInputDialog("New File", "Enter the new file name:", self)
        name, ok = dialog.getText()
        if ok and name:
            new_file_path = os.path.join(folder_path, name)
            if os.path.exists(new_file_path):
                QMessageBox.warning(self, "Error", "File already exists.")
                return
            try:
                with open(new_file_path, "w", encoding="utf-8") as f:
                    f.write("")
                print(f"[FileExplorer] Archivo creado: {new_file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create file:\n{e}")

    def on_double_click(self, index: QModelIndex):
        if self.model.isDir(index):
            return
        file_path = self.model.filePath(index)
        self.file_open_requested.emit(file_path)

    def set_root(self, path):
        if path and os.path.isdir(path):
            
            self.project_root = path
            self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.Files)
            self.model.setRootPath(path)

            start = time.perf_counter()
            index = self.model.index(path)
            self.tree.setRootIndex(index)
            self.tree.expand(index)
            self.tree.setCurrentIndex(index)

            self.tree.show()
            end = time.perf_counter()
            print(f"[DEBUG] Carga del proyecto tomó {end - start:.4f} segundos")
            self.button.hide()
            self.label.hide()
            # Mostrar el nombre o ruta de la carpeta raíz
            self.root_folder_label.setText(f"Root folder: {os.path.basename(path)}")
            self.root_folder_label.show()
            self.project_root_changed.emit(path)
        else:
            self.project_root = None
            self.tree.setRootIndex(self.model.index(""))
            self.tree.hide()
            self.button.show()
            self.label.show()
            self.project_root_changed.emit("")


    def select_project_root(self):
        folder = QFileDialog.getExistingDirectory(self, "Select root folder")
        if folder:
            self.set_root(folder)

    def reselect_project_root(self):
        folder = QFileDialog.getExistingDirectory(self, "Select root folder")
        if folder:
            self.set_root(folder)

    def update_icons_color(self, hex_color):
        def color_svg(path, color):
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            icon = QIcon(path)
            icon.paint(painter, 0, 0, 24, 24, Qt.AlignCenter, QIcon.Normal, QIcon.On)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(color))
            painter.end()
            return QIcon(pixmap)

        if hex_color is None:
            # Restaurar iconos originales
            self.model.folder_icon = QIcon("icons/folder.svg")
            self.model.file_icon = QIcon("icons/file.svg")
        else:
            self.model.folder_icon = color_svg("icons/folder.svg", hex_color)
            self.model.file_icon = color_svg("icons/file.svg", hex_color)

        # Actualizar vista para reflejar cambio
        self.tree.viewport().update()


#Class popups
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt

class CustomInputDialog(QDialog):
    def __init__(self, title, label, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setObjectName("CustomPopup")
        self.setFixedWidth(320)
        
        self.setStyleSheet("""
            #CustomPopup {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #444;
                font-family: Consolas, monospace;
                border-radius: 8px;
            }
            QLabel {
                color: #ccc;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #555;
                padding: 6px;
                font-family: Consolas, monospace;
            }
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)

        layout = QVBoxLayout(self)

        self.label = QLabel(label)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter text…")
        self.input.returnPressed.connect(self.accept)

        buttons = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        buttons.addStretch()
        buttons.addWidget(self.ok_btn)
        buttons.addWidget(self.cancel_btn)

        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addLayout(buttons)

    def getText(self):
        if self.exec_() == QDialog.Accepted:
            return self.input.text(), True
        return "", False
