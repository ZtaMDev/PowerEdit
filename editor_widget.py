# editor_widget.py
import re
from PyQt5.QtWidgets import QPlainTextEdit, QWidget, QTextEdit, QDockWidget
from PyQt5.QtGui import QFont, QColor, QPainter, QTextFormat, QIcon, QTextCursor
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal
from syntax_highlighter import load_highlighter
from autocomplete_handler import AutoCompleteHandler
from indent_handler import IndentHandler
from autocomplete_suggestions import AutoCompleteSuggestions
from PyQt5.QtWidgets import QPushButton, QVBoxLayout
from minimap_widget import MinimapWidget

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

class EditorWidget(QPlainTextEdit):
    runRequested = pyqtSignal()
    def __init__(self, parent=None, minimap_visible=True):
        super().__init__(parent)
        self._minimap_width = 120  # Initialize minimap width first!
        self.language = "python"
        font = QFont("Fira Code", 12)
        font.setStyleHint(QFont.Monospace)
        self._ignore_change_signal = False
        self.setFont(font)
        self.pairs = {
            '(': ')',
            '[': ']',
            '{': '}'
        }
        # Tab = 4 espacios, sin wrap
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #F8F8F2;
                selection-background-color: #44475A;
                border: none;
            }
        """)

        # Crear Complementos
        self.highlighter = load_highlighter("python", self.document())
        self.autocomplete = AutoCompleteHandler("python")
        self.indenter = IndentHandler("python")
        self.suggestions = AutoCompleteSuggestions(self)
        self.suggestions.load_language("python")
        font = QFont("Courier New", 11)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        # Línea de números
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)
        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # --- Minimap as fixed child on the right ---
        self.minimap = MinimapWidget(self, self.highlighter, max_lines=500)
        self.minimap.setParent(self)
        if minimap_visible:
            self.minimap.show()
            minimap_icon = QIcon("icons/arrow-left.svg")
        else:
            self.minimap.hide()
            minimap_icon = QIcon("icons/arrow-right.svg")
        # --- Run button (top right, left of minimap toggle) ---
        self.run_button = QPushButton(self)
        self.run_button.setFixedSize(QSize(24, 24))
        self.run_button.setIcon(QIcon("icons/play.svg"))
        self.run_button.setIconSize(QSize(18, 18))
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #3cb371;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #5fd38d;
            }
        """)
        self.run_button.hide()
        self.run_button.clicked.connect(self.emit_run)
        # --- Minimap toggle button (rightmost) ---
        self.minimap_toggle_btn = QPushButton(self)
        self.minimap_toggle_btn.setFixedSize(QSize(24, 24))
        self.minimap_toggle_btn.setIcon(minimap_icon)
        self.minimap_toggle_btn.setIconSize(QSize(18, 18))
        self.minimap_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #888;
            }
        """)
        self.minimap_toggle_btn.clicked.connect(self.toggle_minimap)
        self.minimap_toggle_btn.show()
        self.setViewportMargins(self.line_number_area_width(), 0, self._minimap_width if minimap_visible else 12, 0)
        self.verticalScrollBar().valueChanged.connect(self.minimap.update)
        self.textChanged.connect(self.minimap.update)
        self.update()

    def get_visible_lines(self):
        visible_lines = []
        block = self.firstVisibleBlock()
        viewport_rect = self.viewport().rect()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= viewport_rect.bottom():
            if block.isVisible() and bottom >= viewport_rect.top():
                visible_lines.append(block.blockNumber())
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()

        return visible_lines

    def on_cursor_position_changed(self):
        if not self.suggestions.isVisible():
            return
        cursor = self.textCursor()
        cursor.select(cursor.WordUnderCursor)
        current_word = cursor.selectedText()
        # Si la palabra actual no es válida para sugerencias, oculta el popup
        if not current_word or not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", current_word):
            self.suggestions.hide()

    def emit_run(self):
        # Emitimos señal o llamamos función, se conectará desde MainWindow
        if hasattr(self, 'runRequested'):
            self.runRequested.emit()
        else:
            print("Botón run clickeado, pero no conectado")
    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
        btn_offset = 6
        btn_size = 24
        self.run_button.setFixedSize(QSize(btn_size, btn_size))
        self.minimap_toggle_btn.setFixedSize(QSize(btn_size, btn_size))
        scrollbar_width = 12
        if self.minimap.isVisible():
            minimap_right = self.width() - self._minimap_width
            right_margin = self._minimap_width
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.setViewportMargins(self.line_number_area_width(), 0, right_margin, 0)
        else:
            minimap_right = self.width() - scrollbar_width
            right_margin = scrollbar_width
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.setViewportMargins(self.line_number_area_width(), 0, right_margin, 0)
        btn_y = btn_offset
        btn_x_minimap = minimap_right - btn_size - btn_offset
        self.minimap_toggle_btn.move(btn_x_minimap, btn_y)
        btn_x_run = btn_x_minimap - btn_size - 6
        self.run_button.move(btn_x_run, btn_y)
        self.minimap.setGeometry(self.width() - self._minimap_width, 0, self._minimap_width, self.height())

    def sync_minimap_state(self):
        # Llama esto en showEvent y cuando cambie el tab
        parent = self.parent()
        global_state = True
        if hasattr(parent, 'minimap_visible'):
            global_state = parent.minimap_visible
        if global_state:
            self.minimap.show()
            self.minimap_toggle_btn.setIcon(QIcon("icons/arrow-left.svg"))
            self.setViewportMargins(self.line_number_area_width(), 0, self._minimap_width, 0)
        else:
            self.minimap.hide()
            self.minimap_toggle_btn.setIcon(QIcon("icons/arrow-right.svg"))
            self.setViewportMargins(self.line_number_area_width(), 0, 12, 0)
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        self.sync_minimap_state()
        # Always allow unlimited horizontal scroll when minimap is hidden
        if not self.minimap.isVisible():
            self.horizontalScrollBar().setMaximum(16777215)
        else:
            doc_width = self.document().idealWidth()
            max_x = max(0, doc_width - (self.viewport().width() - self._minimap_width))
            self.horizontalScrollBar().setMaximum(int(max_x))

    def moveCursor(self, operation, mode=QTextCursor.MoveAnchor):
        super().moveCursor(operation, mode)
        # Always allow unlimited horizontal scroll when minimap is hidden
        if not self.minimap.isVisible():
            self.horizontalScrollBar().setMaximum(16777215)
        else:
            doc_width = self.document().idealWidth()
            max_x = max(0, doc_width - (self.viewport().width() - self._minimap_width))
            self.horizontalScrollBar().setMaximum(int(max_x))

    def set_run_button_visible(self, visible):
        if visible:
            self.run_button.show()
        else:
            self.run_button.hide()
    def set_language(self, lang):
        self.highlighter = load_highlighter(lang, self.document())
        self.autocomplete.set_language(lang)
        self.indenter.set_language(lang)
        self.suggestions.load_language(lang)
        if hasattr(self, 'minimap'):
            self.minimap.set_highlighter(self.highlighter)

    def load_file(self, file_path, lang=None):
        # ...existing file loading logic...
        # After loading the file, update minimap highlighter
        if lang:
            self.set_language(lang)
        if hasattr(self, 'minimap'):
            self.minimap.set_highlighter(self.highlighter)

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_number_area_width(self, _):
        if hasattr(self, '_updating_margins') and self._updating_margins:
            return
        self._updating_margins = True
        try:
            self.setViewportMargins(self.line_number_area_width(), 0, self._minimap_width, 0)
        finally:
            self._updating_margins = False

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(30, 30, 30))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(180, 180, 180))
                painter.drawText(0, int(top), self.line_number_area.width() - 4, int(self.fontMetrics().height()),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
    def keyPressEvent(self, event):
        # Evitar autocompletar con Ctrl, Alt, Meta (modificadores)
        modifiers = event.modifiers()
        if modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier):
            super().keyPressEvent(event)
            return

        # Manejo especial para borrar pares de caracteres
        if event.key() == Qt.Key_Backspace and not self.textCursor().hasSelection():
            cursor = self.textCursor()
            pos = cursor.position()
            doc = self.document()
            if pos > 0 and pos < doc.characterCount():
                prev_char = doc.characterAt(pos - 1)
                next_char = doc.characterAt(pos)
                for open_c, close_c in self.pairs.items():
                    if prev_char == open_c and next_char == close_c:
                        block = cursor.block()
                        if block.position() <= (pos - 1) < block.position() + block.length():
                            cursor.beginEditBlock()
                            cursor.setPosition(pos)
                            cursor.deleteChar()
                            cursor.deletePreviousChar()
                            cursor.endEditBlock()
                            return

        # Si se presiona TAB y el popup está visible, insertar sugerencia y no propagar
        if event.key() == Qt.Key_Tab:
            if self.suggestions.isVisible():
                self.suggestions.insert_selected()
                return

        # Si se presiona ESC y el popup está visible, ocultarlo y no propagar
        if event.key() == Qt.Key_Escape:
            if self.suggestions.isVisible():
                self.suggestions.hide()
                return

        # Delega al manejador de autocomplete para otras teclas especiales (flechas, etc)
        if self.autocomplete.handle_key_press(self, event):
            return

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.indenter.handle_indent(self):
                self.suggestions.hide()  # oculta popup
                return

        cursor = self.textCursor()
        cursor.select(cursor.WordUnderCursor)
        prefix = cursor.selectedText()

        key_char = event.text()
        key = event.key()

        if key in (Qt.Key_Up, Qt.Key_Down):
            if not prefix or not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", prefix):
                self.suggestions.hide()
            else:
                self.suggestions.show_suggestions(prefix)
        else:
            # Ni idea de por que no funciona...
            # Mostrar sugerencias si la tecla es válida (letra, número o caracter útil en HTML/CSS)
            if prefix and (key_char.isalnum() or key_char in "_-:<>\"'/="):
                self.suggestions.show_suggestions(prefix)
            # Ocultar solo si es un espacio o punto y coma o salto de línea
            elif key_char in (" ", ";", "\n"):
                self.suggestions.hide()

        super().keyPressEvent(event)


    def focusOutEvent(self, event):
        self.suggestions.hide()  # Ocultar popup
        super().focusOutEvent(event)

    def highlight_current_line(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(60, 60, 60)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    # Helper function to add minimap dock to a QMainWindow
    # Usage: EditorWidget.add_minimap_dock(main_window, editor_instance)
    @staticmethod
    def add_minimap_dock(main_window, editor_widget):
        dock = QDockWidget("Minimap", main_window)
        dock.setWidget(MinimapWidget(editor_widget, getattr(editor_widget, 'highlighter', None)))
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)  # Unmovable, unclosable
        main_window.addDockWidget(Qt.LeftDockWidgetArea, dock)
        dock.setTitleBarWidget(QWidget())  # Hide title bar
        return dock

    def toggle_minimap(self):
        # Notificar al tab manager si existe
        if hasattr(self.parent(), 'on_minimap_toggled'):
            self.parent().on_minimap_toggled(not self.minimap.isVisible())
        # ...existing code...
        if self.minimap.isVisible():
            self.minimap.hide()
            self.minimap_toggle_btn.setIcon(QIcon("icons/arrow-right.svg"))
            scrollbar_width = 12
            right_margin = scrollbar_width
            self.setViewportMargins(self.line_number_area_width(), 0, right_margin, 0)
            self.horizontalScrollBar().setMaximum(16777215)  # unlimited
        else:
            self.minimap.show()
            self.minimap_toggle_btn.setIcon(QIcon("icons/arrow-left.svg"))
            self.setViewportMargins(self.line_number_area_width(), 0, self._minimap_width, 0)
            doc_width = self.document().idealWidth()
            max_x = max(0, doc_width - (self.viewport().width() - self._minimap_width))
            self.horizontalScrollBar().setMaximum(int(max_x))
        # Reposition minimap and button, update margins
        if self.minimap.isVisible():
            btn_x_minimap = self.width() - self._minimap_width - self.minimap_toggle_btn.width() - 6
            right_margin = self._minimap_width
        else:
            btn_x_minimap = self.width() - self.minimap_toggle_btn.width() - 6 - 12  # 12px for scrollbar
            right_margin = 12
        btn_y = 6
        self.minimap_toggle_btn.move(btn_x_minimap, btn_y)
        btn_x_run = btn_x_minimap - self.run_button.width() - 6
        self.run_button.move(btn_x_run, btn_y)
        self.minimap.setGeometry(self.width() - self._minimap_width, 0, self._minimap_width, self.height())
        self.update()

    def ensureCursorVisible(self):
        # Use the default implementation, which ensures the caret is always visible
        super().ensureCursorVisible()
        # Remove any artificial limit on the horizontal scrollbar
        self.horizontalScrollBar().setMaximum(16777215)
