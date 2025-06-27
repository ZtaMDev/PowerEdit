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

        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.addSeparator()
        menu.addAction(new_file_action)
        new_folder_action = QAction("New Folder", self)
        menu.addAction(new_folder_action)
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

        menu.exec_(self.tree.viewport().mapToGlobal(position))


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
