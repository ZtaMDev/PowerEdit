import os, json
from PyQt5.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QLabel, QScrollArea,
    QShortcut
)
from PyQt5.QtCore import Qt, pyqtSignal
from editor_widget import EditorWidget
from PyQt5.QtWidgets import QTabBar
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMessageBox, QPushButton
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence

class CustomTabBar(QTabBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setUsesScrollButtons(True)  # Scroll real
        self.setElideMode(Qt.ElideRight)
        self.setMovable(True)
        self.setExpanding(False)
        self.setTabsClosable(True)
        self.setFocusPolicy(Qt.StrongFocus)
        # Ocultar flechas/botones de movimiento
        self.setStyleSheet("""
            QTabBar::scroller, QToolButton {
                width: 0px; height: 0px; border: none; background: transparent;
            }
        """)
    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        text = self.tabText(index)
        fm = self.fontMetrics()
        width = fm.horizontalAdvance(text) + 100  # padding
        width = max(120, min(width, 300))  # mínimo 120px, máximo 300px
        return QSize(width, size.height())

class TabsManager(QTabWidget):
    close_live_preview_requested = pyqtSignal(str)
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

        # Atajos de teclado para zoom de fuente en el editor activo
        QShortcut(QKeySequence("Ctrl++"), self, activated=self.zoom_in_editor_font)
        QShortcut(QKeySequence("Ctrl+="), self, activated=self.zoom_in_editor_font)  # Para algunos teclados
        QShortcut(QKeySequence("Ctrl+-"), self, activated=self.zoom_out_editor_font)
        QShortcut(QKeySequence("Ctrl+0"), self, activated=self.reset_editor_font)

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
        # Cambia el estado global y sincroniza todos los editores
        self.minimap_visible = visible
        self._save_minimap_state()
        # Forzar el estado en todos los editores usando setVisible
        for i in range(self.count()):
            editor = self.widget(i)
            if hasattr(editor, 'minimap'):
                editor.minimap.setVisible(visible)
                # Cambiar icono del botón
                if visible:
                    editor.minimap_toggle_btn.setIcon(QIcon("icons/arrow-left.svg"))
                    editor.setViewportMargins(editor.line_number_area_width(), 0, editor._minimap_width, 0)
                else:
                    editor.minimap_toggle_btn.setIcon(QIcon("icons/arrow-right.svg"))
                    editor.setViewportMargins(editor.line_number_area_width(), 0, 12, 0)
                editor.update()

    def show_welcome_tab(self):
        if self.indexOf(self._welcome_tab) == -1:
            self.addTab(self._welcome_tab, "Welcome")
            self.tabBar().setTabEnabled(self.indexOf(self._welcome_tab), False)
        self.setCurrentIndex(self.indexOf(self._welcome_tab))
    def on_tab_changed(self, index):
        # Sincronizar el estado del minimapa en TODOS los editores abiertos
        for i in range(self.count()):
            editor = self.widget(i)
            if hasattr(editor, "sync_minimap_state"):
                editor.sync_minimap_state()
        editor = self.widget(index)
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
        # --- Guardar el estado del minimapa tras cada cambio de tab ---
        self._save_minimap_state()

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

        # Soporte para imágenes
        image_exts = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "ico"}
        ext = os.path.splitext(file_path or "")[1].lstrip(".").lower() if file_path else ""
        if ext in image_exts and file_path and os.path.isfile(file_path):
            widget = ImageTab(file_path)
            index = self.addTab(widget, os.path.basename(file_path))
            self.setCurrentIndex(index)
            self.setTabToolTip(index, file_path)
            return widget

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
            return  # Ignora el cambio porque fue intencional (carga de archivos grandes)
        current_text = editor.toPlainText()
        saved_text = self.saved_texts.get(editor, "")
        if current_text != saved_text:
            index = self.indexOf(editor)
            self.update_tab_text(index, modified=True)
            main = self.parent()
            if hasattr(main, "live_preview") and getattr(main.live_preview, "refresh", False):
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

        # Si corresponde, emite la señal para cerrar el live preview en segundo plano
        if (
            live_path and current_path and
            os.path.normpath(live_path) == os.path.normpath(current_path) and
            not is_external
        ):
            self.close_live_preview_requested.emit(current_path)

        if isinstance(widget, EditorWidget):
            current_text = widget.toPlainText()
            saved_text = self.saved_texts.get(widget, "")
            if current_text != saved_text:
                msgbox = QMessageBox(self)
                msgbox.setWindowTitle("File modified")
                msgbox.setText("This file has unsaved changes\n¿You want to save it before?")
                msgbox.setIcon(QMessageBox.Warning)

                guardar_btn = msgbox.addButton("Save", QMessageBox.AcceptRole)
                descartar_btn = msgbox.addButton("Discard changes", QMessageBox.DestructiveRole)
                cancelar_btn = msgbox.addButton("Cancel", QMessageBox.RejectRole)

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
        # Si es una pestaña de imagen, no tiene set_language ni document
        if widget and hasattr(widget, "set_language"):
            return widget
        return None

    def update_tab_text(self, index, file_path=None, language=None, modified=False):
        widget = self.widget(index)
        # Si es una pestaña de imagen, solo mostrar el nombre
        if hasattr(widget, "label") and hasattr(widget, "scroll"):
            if file_path:
                display_text = os.path.basename(file_path)
                tooltip = file_path
            else:
                display_text = "Image"
                tooltip = ""
            self.setTabText(index, display_text)
            self.setTabToolTip(index, tooltip or display_text)
            return

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

    def zoom_in_editor_font(self):
        editor = self.current_editor()
        if editor:
            font = editor.font()
            size = font.pointSize()
            if size <= 0:
                size = 12  # fallback seguro
            size = min(size + 1, 120)  # Zoom de 1 en 1
            font.setPointSize(size)
            editor.setFont(font)
            editor.setTabStopDistance(4 * editor.fontMetrics().horizontalAdvance(' '))
            if hasattr(editor, 'update_line_number_area_width'):
                editor.update_line_number_area_width(0)
            editor.update()
            # Modifica el QSS global
            main = self.parent()
            while main and not hasattr(main, 'set_editor_font_size'):
                main = getattr(main, 'parent', lambda: None)()
            if main and hasattr(main, 'set_editor_font_size'):
                main.set_editor_font_size(size)
                if hasattr(main, 'update_theme_font_size'):
                    main.update_theme_font_size(size)

    def zoom_out_editor_font(self):
        editor = self.current_editor()
        if editor:
            font = editor.font()
            size = font.pointSize()
            if size <= 0:
                size = 12  # fallback seguro
            size = max(size - 1, 4)  # Zoom de 1 en 1
            font.setPointSize(size)
            editor.setFont(font)
            editor.setTabStopDistance(4 * editor.fontMetrics().horizontalAdvance(' '))
            if hasattr(editor, 'update_line_number_area_width'):
                editor.update_line_number_area_width(0)
            editor.update()
            # Modifica el QSS global
            main = self.parent()
            while main and not hasattr(main, 'set_editor_font_size'):
                main = getattr(main, 'parent', lambda: None)()
            if main and hasattr(main, 'set_editor_font_size'):
                main.set_editor_font_size(size)
                if hasattr(main, 'update_theme_font_size'):
                    main.update_theme_font_size(size)

    def reset_editor_font(self):
        editor = self.current_editor()
        if editor:
            font = editor.font()
            font.setPointSize(12)
            editor.setFont(font)
            editor.setTabStopDistance(4 * editor.fontMetrics().horizontalAdvance(' '))
            if hasattr(editor, 'update_line_number_area_width'):
                editor.update_line_number_area_width(0)
            editor.update()
            # Modifica el QSS global
            main = self.parent()
            while main and not hasattr(main, 'set_editor_font_size'):
                main = getattr(main, 'parent', lambda: None)()
            if main and hasattr(main, 'set_editor_font_size'):
                main.set_editor_font_size(12)
                if hasattr(main, 'update_theme_font_size'):
                    main.update_theme_font_size(12)

    def wheelEvent(self, event):
        # Desactivar zoom con Ctrl+scroll (solo scroll normal)
        super().wheelEvent(event)

class ImageTab(QWidget):
    def __init__(self, image_path):
        super().__init__()
        # Forzar fondo oscuro en todos los niveles
        self.setStyleSheet("QWidget { background-color: #181818 !important; }")
        layout = QVBoxLayout(self)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #181818 !important;")
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background-color: #181818 !important;")
        self._image_path = image_path
        self._pixmap = QPixmap(image_path)
        self._zoom = 1.0
        if self._pixmap.isNull():
            self.label.setText("<b>Could not load image.</b>")
        else:
            self._update_pixmap()
        self.scroll.setWidget(self.label)
        layout.addWidget(self.scroll)
        self.setLayout(layout)
        self.label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.label.customContextMenuRequested.connect(self._show_context_menu)

    def _update_pixmap(self):
        if self._pixmap.isNull():
            return
        w = int(self._pixmap.width() * self._zoom)
        h = int(self._pixmap.height() * self._zoom)
        scaled = self._pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled)
        self.label.resize(scaled.size())  # Asegura que el QLabel se ajuste al tamaño de la imagen
        self.label.setMinimumSize(scaled.size())
        self.scroll.ensureVisible(self.label.width() // 2, self.label.height() // 2)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom = min(self._zoom * 1.15, 10.0)
            else:
                self._zoom = max(self._zoom / 1.15, 0.05)
            self._update_pixmap()
            event.accept()
        else:
            super().wheelEvent(event)

    def _show_context_menu(self, pos):
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        zoom_in = menu.addAction("Zoom in (+)")
        zoom_out = menu.addAction("Zoom out (-)")
        reset = menu.addAction("Reset zoom")
        act = menu.exec_(self.label.mapToGlobal(pos))
        if act == zoom_in:
            self._zoom = min(self._zoom * 1.15, 10.0)
            self._update_pixmap()
        elif act == zoom_out:
            self._zoom = max(self._zoom / 1.15, 0.05)
            self._update_pixmap()
        elif act == reset:
            self._zoom = 1.0
            self._update_pixmap()