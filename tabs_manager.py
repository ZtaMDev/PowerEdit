import os, json
from PyQt5.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QLabel
)
from PyQt5.QtCore import Qt
from editor_widget import EditorWidget
from PyQt5.QtWidgets import QTabBar
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMessageBox, QPushButton
from PyQt5.QtGui import QIcon

class CustomTabBar(QTabBar):
    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        text = self.tabText(index)
        fm = self.fontMetrics()
        width = fm.horizontalAdvance(text) + 100  # 100px padding
        return QSize(width, size.height())

class TabsManager(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setTabBar(CustomTabBar())
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self._welcome_tab = self._create_welcome_tab()
        self.addTab(self._welcome_tab, "Welcome")
        self._file_paths = {}
        self.saved_texts = {}
        self.tabBar().setTabEnabled(self.indexOf(self._welcome_tab), False)  # No clickeable ni cerrable
        self.currentChanged.connect(self.on_tab_changed)
        self.ext_map = {}
        self.load_extensions()
        self.currentChanged.connect(self.on_tab_changed)
        self.minimap_visible = True  # Estado global del minimapa
        self._load_minimap_state()

    def _load_minimap_state(self):
        try:
            complements_path = os.path.join(os.getcwd(), "complements.json")
            if os.path.exists(complements_path):
                with open(complements_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.minimap_visible = bool(data.get("minimap_visible", True))
        except Exception as e:
            print(f"⚠️ Error leyendo estado del minimapa: {e}")

    def _save_minimap_state(self):
        try:
            data = {}
            complements_path = os.path.join(os.getcwd(), "complements.json")
            if os.path.exists(complements_path):
                with open(complements_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["minimap_visible"] = self.minimap_visible
            with open(complements_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error guardando estado del minimapa: {e}")

    def on_minimap_toggled(self, visible):
        self.minimap_visible = visible
        self._save_minimap_state()
        # Sincronizar todos los editores abiertos
        for i in range(self.count()):
            editor = self.widget(i)
            if hasattr(editor, 'minimap'):
                if visible:
                    editor.minimap.show()
                    editor.minimap_toggle_btn.setIcon(QIcon("icons/arrow-left.svg"))
                    editor.setViewportMargins(editor.line_number_area_width(), 0, editor._minimap_width, 0)
                else:
                    editor.minimap.hide()
                    editor.minimap_toggle_btn.setIcon(QIcon("icons/arrow-right.svg"))
                    editor.setViewportMargins(editor.line_number_area_width(), 0, 12, 0)
                editor.update()

    def show_welcome_tab(self):
        if self.indexOf(self._welcome_tab) == -1:
            self.addTab(self._welcome_tab, "Welcome")
            self.tabBar().setTabEnabled(self.indexOf(self._welcome_tab), False)
        self.setCurrentIndex(self.indexOf(self._welcome_tab))
    def on_tab_changed(self, index):
        editor = self.widget(index)
        if editor and hasattr(editor, "sync_minimap_state"):
            editor.sync_minimap_state()
        if editor and hasattr(editor, "set_language"):
            lang = None
            main = self.parent()
            if main and hasattr(main, "current_files"):
                path = main.current_files.get(editor)
                if path:
                    ext = os.path.splitext(path)[1].lstrip(".").lower()
                    lang = self.ext_map.get(ext, None)
            if not lang and hasattr(editor, "language"):
                lang = editor.language
            if not lang:
                lang = "plain"
            editor.set_language(lang)

        if hasattr(self.parent(), "update_run_button"):
            self.parent().update_run_button(editor)

    def _create_welcome_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel("Select File → New to start coding")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: gray; font-size: 16px;")
        layout.addWidget(label)
        return widget

    def load_extensions(self):
        extend_folder = "extend"
        if not os.path.isdir(extend_folder):
            return
        for fname in os.listdir(extend_folder):
            if not fname.endswith(".extend"):
                continue
            lang = fname.replace(".extend", "")
            path = os.path.join(extend_folder, fname)
            try:
                rules = json.load(open(path, encoding="utf-8"))
                for ext in rules.get("extensions", [lang]):
                    self.ext_map[ext.lower()] = lang
            except Exception as e:
                print(f"⚠️ Error leyendo {path}: {e}")

    def new_tab(self, file_path=None, content="", language=None):
        welcome_index = self.indexOf(self._welcome_tab)

        if welcome_index != -1:
            self.removeTab(welcome_index)

        editor = EditorWidget(minimap_visible=self.minimap_visible)
        editor.language = language
        if file_path:
            self._file_paths[editor] = file_path

        if content:
            editor.setUpdatesEnabled(False)
            editor.setUndoRedoEnabled(False)
            
            # Medición precisa
            import time
            start = time.perf_counter()
            editor.setPlainText(content)
            end = time.perf_counter()
            print(f"[DEBUG] setPlainText() tomó {end - start:.4f} segundos")

            editor.setUndoRedoEnabled(True)
            editor.setUpdatesEnabled(True)

            self.saved_texts[editor] = content

        else:
            self.saved_texts[editor] = ""

        if language:
            editor.set_language(language)
        elif file_path:
            ext = os.path.splitext(file_path)[1].lstrip(".").lower()
            lang = self.ext_map.get(ext, "plain")
            editor.set_language(lang)
        else:
            editor.set_language("plain")

        index = self.addTab(editor, "")
        self.setCurrentIndex(index)

        # Conectar señal para detectar modificaciones
        editor.textChanged.connect(lambda e=editor: self.on_editor_modified(e))
        if hasattr(editor, "setStyleSheet"):
            editor.setStyleSheet(self.styleSheet())  # Aplica el tema actual

        self.update_tab_text(index, file_path=file_path, language=language)
        editor.textChanged.connect(lambda e=editor: self.on_editor_modified(e))

        editor.textChanged.connect(lambda e=editor: self.parent().update_live_preview(e))

        return editor

    def on_tab_changed(self, index):
        if hasattr(self.parent(), "save_settings"):
            self.parent().save_settings()

        main = self.parent()
        editor = self.widget(index)
        path = getattr(main, "current_files", {}).get(editor)
        is_html = bool(path and path.lower().endswith(".html"))
        if getattr(main.live_preview, "external_url", None) and not main.live_preview.user_minimized:
            main.live_preview.show()
            return
        if not is_html:
            main.live_preview.hide()
        else:
            # Solo mostrar si ya fue previsualizado Y no fue ocultado manualmente
            if (
                editor in getattr(main, "_html_previewed_editors", ())
                and not main.live_preview.user_minimized
            ):
                main.live_preview.show()

        
    def on_editor_modified(self, editor):
        if getattr(editor, "_ignore_change_signal", False):
            return  # Ignora el cambio porque fue intencional(carga de archivos grandes 'OPTIMIZADO' que se noten la comillas)
        
        current_text = editor.toPlainText()
        saved_text = self.saved_texts.get(editor, "")
        if current_text != saved_text:
            index = self.indexOf(editor)
            self.update_tab_text(index, modified=True)
            main = self.parent()
            if hasattr(main, "live_preview") and main.live_preview.refresh:
                main._reload_live_preview()

    def close_tab(self, index):
        widget = self.widget(index)
        if hasattr(widget, "suggestions") and widget.suggestions.isVisible():
            widget.suggestions.hide()
        # No cerrar el welcome si es el único
        if widget == self._welcome_tab and self.count() == 1:
            return
        main = self.parent()
        current_path = getattr(main, "current_files", {}).get(widget)
        live_path = getattr(main.live_preview, "last_loaded_path", None)
        is_external = getattr(main.live_preview, "external_url", None)

        if (
            live_path and current_path and
            os.path.normpath(live_path) == os.path.normpath(current_path) and
            not is_external
        ):
            main.live_preview.user_minimized = True
            main.live_preview.stop_server()
            main.live_preview.hide()


        if isinstance(widget, EditorWidget):
            current_text = widget.toPlainText()
            saved_text = self.saved_texts.get(widget, "")
            if current_text != saved_text:
                msgbox = QMessageBox(self)
                msgbox.setWindowTitle("File modified")
                msgbox.setText("This file has unsaved changes\n¿You want to save it before?")
                msgbox.setIcon(QMessageBox.Warning)

                guardar_btn = msgbox.addButton("Guardar", QMessageBox.AcceptRole)
                descartar_btn = msgbox.addButton("Descartar cambios", QMessageBox.DestructiveRole)
                cancelar_btn = msgbox.addButton("Cancelar", QMessageBox.RejectRole)

                msgbox.setStyleSheet("""
                    QMessageBox {
                        background-color: #1e1e1e;
                        color: white;
                        font-family: Consolas, monospace;
                        font-size: 14px;
                    }
                    QPushButton {
                        background-color: #44475A;
                        color: white;
                        border-radius: 4px;
                        padding: 6px 12px;
                    }
                    QPushButton:hover {
                        background-color: #6272A4;
                    }
                """)

                msgbox.exec_()

                if msgbox.clickedButton() == guardar_btn:
                    if hasattr(self.parent(), "save_file"):
                        self.parent().save_file()
                        self.saved_texts[widget] = widget.toPlainText()  # Actualiza contenido guardado
                    else:
                        print("⚠️ No se encontró método save_file en el padre.")
                elif msgbox.clickedButton() == cancelar_btn:
                    return  # No cerrar
                # Si descarta cambios, simplemente continúa
        
        self.removeTab(index)
        if hasattr(self.parent(), "save_settings"):
            self.parent().save_settings()

        if self.count() == 0:
            self.addTab(self._welcome_tab, "Welcome")
            self.tabBar().setTabEnabled(self.indexOf(self._welcome_tab), False)
            self.setCurrentIndex(0)
        
    def current_editor(self):
        widget = self.currentWidget()
        if widget and hasattr(widget, "set_language"):
            return widget
        return None
    def update_tab_text(self, index, file_path=None, language=None, modified=False):
        widget = self.widget(index)
        
        if language is None and hasattr(widget, 'language'):
            language = getattr(widget, 'language', None)
        
        if file_path is None and widget in getattr(self, '_file_paths', {}):
            file_path = self._file_paths.get(widget)

        if file_path:
            base_name = os.path.basename(file_path)
            display_text = base_name
            tooltip = file_path
        else:
            display_text = "Untitled"
            tooltip = ""

        if not language or language.lower() == "plain":
            display_text += "(Plain Text)"

        if modified:
            display_text += " ●"  # indicador de modificado

        self.setTabText(index, display_text)
        self.setTabToolTip(index, tooltip or display_text)