# editor_widget.py
import re
from PyQt5.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt5.QtGui import QFont, QColor, QPainter, QTextFormat
from PyQt5.QtCore import Qt, QRect, QSize
from syntax_highlighter import load_highlighter
from autocomplete_handler import AutoCompleteHandler
from indent_handler import IndentHandler
from autocomplete_suggestions import AutoCompleteSuggestions
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal
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
    def __init__(self, parent=None):
        super().__init__(parent)
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

        #Crear Complementos
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


        #RUN BTN
        self.run_button = QPushButton("▶", self)
        self.run_button.setFixedSize(QSize(30, 30))
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #50fa7b;
                border-radius: 15px;
                font-weight: bold;
                color: black;
            }
            QPushButton:hover {
                background-color: #63f98c;
            }
        """)
        self.run_button.hide()
        self.run_button.clicked.connect(self.emit_run)
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
        # Actualiza el área de números de línea
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

        # Posiciona el botón en la esquina inferior derecha (con margen)
        margin = 10
        x = self.viewport().width() - self.run_button.width() - margin
        y = self.viewport().height() - self.run_button.height() - margin
        self.run_button.move(x, y)

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


    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

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
