from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, QPoint
import os
import json
import re
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QPoint, QSize

class AutoCompleteSuggestions(QListWidget):
    def __init__(self, parent_editor):
        super().__init__(parent_editor)
        self.setStyleSheet("""
            QListWidget {
                background-color: #2c2c2c;
                color: white;
                border: 1px solid #555;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
            QListWidget::item {
                color: white;
                padding: 1px;
            }
            QListWidget::item:selected {
                background-color: #5555aa;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #444;
            }
        """)
        self.icon_size = 16  # tamaño icono y altura item
        self.setIconSize(QSize(self.icon_size, self.icon_size))
        self.icons = {
            "variable": QIcon("icons/variable.svg"),
            "keyword":  QIcon("icons/keyword.svg"),
            "type":     QIcon("icons/type.svg"),
            "method":   QIcon("icons/method.svg"),
            "function": QIcon("icons/function.svg"),
            "builtin":  QIcon("icons/builtin.svg"),
            "module":   QIcon("icons/module.svg"),
            "value":    QIcon("icons/value.svg"),
            "tag":      QIcon("icons/tag.svg"),
            "color":    QIcon("icons/color.svg"),
        }

        self.editor = parent_editor
        self.setWindowFlags(Qt.ToolTip)
        self.setFocusPolicy(Qt.NoFocus)
        self.hide()

        self.items = []
        self.language_data = {}

        self.itemClicked.connect(self.insert_selected)

        # Filtro global para ocultar popup cuando se hace clic fuera de él
        self.global_click_filter = GlobalClickFilter(self)
        QApplication.instance().installEventFilter(self.global_click_filter)
        self.current_prefix = ""
        self.editor.cursorPositionChanged.connect(self.check_hide_on_cursor_move)
        self.editor.installEventFilter(self)
        scrollbar = self.editor.verticalScrollBar()
        scrollbar.valueChanged.connect(self.reposition)


    def load_language(self, lang):
        if lang in ("plain", "plaintext"):
            return None
        path = os.path.join("extend", f"{lang}.extend")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.language_data = json.load(f)
        else:
            self.language_data = {}

    def show_suggestions(self, prefix):
        number_ok = bool(self.language_data.get("value"))
        pat = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
        if number_ok:
            pat = r"^[a-zA-Z_][a-zA-Z0-9_]*$|^\d+(\.\d*)?$"
        if not prefix or not re.match(pat, prefix):
            self.hide()
            return

        data = self.language_data

        comment_pat = data.get("comment_pattern")
        if comment_pat:
            full_text = self.editor.toPlainText()
            pos = self.editor.textCursor().position()
            # Buscamos todas las regiones de comentario
            for cm in re.finditer(comment_pat, full_text):
                if cm.start() <= pos <= cm.end():
                    self.hide()
                    return
        is_css = "css" in data.get("extensions", [])
        html_tags = []
        html_attrs = []
        
        if is_css:
            html_path = os.path.join("extend", "html.extend")
            if os.path.exists(html_path):
                with open(html_path, encoding="utf-8") as f:
                    html_data = json.load(f)
                    html_tags = html_data.get("keywords", [])
            # Si no hay datos útiles, no mostramos
            if not any(data.get(k) for k in (
                    "keywords", "builtins", "types", "constants",
                    "methods", "functions", "modules", "value", "color_names"
                )):
                self.hide()
                return


        suggestions = []
        seen = set()
        text = self.editor.toPlainText()
        keywords = set(data.get("keywords", []))

        # 4) Métodos detectados en el texto (name())
        for m in sorted(set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()', text))):
            if m.startswith(prefix) and m != prefix:
                if m in keywords:
                    continue
                suggestions.append((f"{m}()", "method"))
                seen.add(m)


        # 2) Sección "methods" del .extend
        for m in data.get("methods", []):
            if m.startswith(prefix) and m not in seen:
                suggestions.append((f"{m}()", "method"))
                seen.add(m)

        # 3) keywords
        for w in data.get("keywords", []):
            if w.startswith(prefix) and w not in seen:
                suggestions.append((w, "keyword"))
                seen.add(w)

        if is_css:
            for col in data.get("color_names", []):
                if col.startswith(prefix) and col not in seen:
                    suggestions.append((col, "color"))
                    seen.add(col)
        # 4) builtins
        for w in data.get("builtins", []):
            if w.startswith(prefix) and w not in seen:
                suggestions.append((w, "builtin"))
                seen.add(w)

        # 5) types
        for w in data.get("types", []):
            if w.startswith(prefix) and w not in seen:
                suggestions.append((w, "type"))
                seen.add(w)

        # 6) constants
        for w in data.get("constants", []):
            if w.startswith(prefix) and w not in seen:
                suggestions.append((w, "constant"))
                seen.add(w)


        # 7) Valores/unidades: solo si hay "value" en .extend
        if self.language_data.get("value") and re.match(r'^\d+(\.\d*)?$', prefix):
            for unit in self.language_data["value"][:5]:  # máximo 5
                token = f"{prefix}{unit}"
                if token not in seen:
                    suggestions.append((token, "value"))
                    seen.add(token)

        # 7) functions (global functions)  
        for w in data.get("functions", []):
            if w.startswith(prefix) and w not in seen:
                if w in data.get("keywords", []):
                    continue
                suggestions.append((f"{w}()", "function"))
                seen.add(w)

        # 8) modules
        for w in data.get("modules", []):
            if w.startswith(prefix) and w not in seen:
                suggestions.append((w, "module"))
                seen.add(w)
        
        for a in html_attrs:
            if a.startswith(prefix) and a not in seen:
                suggestions.append((a, "attr"))
                seen.add(a)

        # → Sugerir tags HTML en CSS
        if is_css:
            for tag in html_tags:
                if tag.startswith(prefix) and tag not in seen:
                    suggestions.append((tag, "tag"))
                    seen.add(tag)


        # 9) variables detectadas en texto (si queda espacio)
        if not suggestions:
            var_names = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text))
            for v in sorted(var_names):
                if v.startswith(prefix) and v != prefix and v not in seen:
                    suggestions.append((v, "variable"))
                    seen.add(v)

        # 10) fallback
        if not suggestions:
            suggestions = [(prefix, "variable")]

        # Mostrar
        self.clear()
        for word, kind in suggestions:
            item = QListWidgetItem(word)
            item.setData(Qt.UserRole, kind)
            icon = self.icons.get(kind)
            if icon:
                item.setIcon(icon)
            self.addItem(item)

        self.setCurrentRow(0)
        # Posicionar y mostrar popup
        cr = self.editor.cursorRect()
        gp = self.editor.mapToGlobal(QPoint(0,0))
        self.move(gp.x() + cr.left(), gp.y() + cr.bottom() + 10)
        self.resize(240, min(300, 20 + 18 * len(suggestions)))
        self.show()
        self.current_prefix = prefix


    def check_hide_on_cursor_move(self):
        if not self.isVisible():
            return

        if not self.current_prefix:
            self.hide()
            return

        cursor = self.editor.textCursor()
        pos = cursor.position()
        text = self.editor.toPlainText()[:pos]

        match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)$', text)
        current_word = match.group(1) if match else ""

        if not current_word.startswith(self.current_prefix):
            self.hide()

    def on_editor_focus_out(self, event):
        self.hide()
        super(self.editor.__class__, self.editor).focusOutEvent(event)

    def focusOutEvent(self, event):
        self.hide()
        super().focusOutEvent(event)
    
    def insert_selected(self):
        item = self.currentItem()
        if not item:
            return

        kind = item.data(Qt.UserRole)
        word = item.text()
        data = self.language_data
        exts = data.get("extensions", [])

        cursor = self.editor.textCursor()
        cursor.select(cursor.WordUnderCursor)

        is_css = "css" in exts

        # ————————————————
        # Inserciones especializadas
        # ————————————————
        if is_css and kind == "keyword":
            # propiedad CSS → añade “: ”
            insert_text = f"{word}: "

        elif is_css and kind == "value":
            # unidad CSS → añade “;”
            insert_text = f"{word};"

        elif is_css and kind == "color":
            # color CSS → añade “;”
            insert_text = f"{word};"

        elif kind == "method":
            # método → coloca cursor dentro de ()
            insert_text = word
            cursor.insertText(insert_text)
            cursor.movePosition(cursor.Left, cursor.MoveAnchor, 1)
            self.editor.setTextCursor(cursor)
            self.hide()
            return

        else:
            # resto de casos (variable, builtin, type, constant, function, module, tag)
            insert_text = word

        # Inserta y actualiza cursor
        cursor.insertText(insert_text)
        self.editor.setTextCursor(cursor)
        self.hide()


    def reposition(self):
        if not self.isVisible():
            return

        cursor_rect = self.editor.cursorRect()
        editor_pos = self.editor.mapToGlobal(QPoint(0, 0))
        popup_x = editor_pos.x() + cursor_rect.left()
        popup_y = editor_pos.y() + cursor_rect.bottom() + 10

        self.move(popup_x, popup_y)

    def handle_key(self, event):
        key = event.text()

        # 1) Flechas: navegan el popup siempre que esté visible
        if self.isVisible():
            if event.key() == Qt.Key_Up:
                self.setCurrentRow(max(0, self.currentRow() - 1))
                return True
            elif event.key() == Qt.Key_Down:
                if self.currentRow() == self.count() - 1:
                    self.hide()
                    return False
                else:
                    self.setCurrentRow(self.currentRow() + 1)
                    return True

        # 2) Dígitos: insertan el número + reabren auto-completado "value"
        if key.isdigit() and self.language_data.get("value"):
            cursor = self.editor.textCursor()
            cursor.insertText(key)
            self.editor.setTextCursor(cursor)

            cursor.select(cursor.WordUnderCursor)
            prefix = cursor.selectedText()
            self.show_suggestions(prefix)

            # darle foco al popup para que siga recibiendo flechas
            self.setFocus()
            return True

        # 3) Tab / Enter / Escape: cuando el popup está visible
        if self.isVisible():
            if event.key() == Qt.Key_Tab:
                self.insert_selected()
                return True
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.hide()
                return False
            if event.key() == Qt.Key_Escape:
                self.hide()
                return True

        # 4) Para otras teclas, dejamos que is_word_incomplete determine
        if not self.is_word_incomplete():
            return False

        return False




    def is_word_incomplete(self):
        if not self.current_prefix:
            return False

        cursor = self.editor.textCursor()
        pos = cursor.position()
        text = self.editor.toPlainText()[:pos]

        # Buscar la última "palabra" antes del cursor (permitiendo puntos)
        match = re.search(r'([a-zA-Z0-9_][a-zA-Z0-9_]*)$', text)
        current_word = match.group(1) if match else ""

        return current_word.startswith(self.current_prefix) and current_word != self.current_prefix

    

    def eventFilter(self, obj, event):
        if obj == self.editor and event.type() == QEvent.KeyPress:
            if self.handle_key(event):
                return True  # Evento consumido
        return super().eventFilter(obj, event)


from PyQt5.QtCore import QObject, QEvent

class GlobalClickFilter(QObject):
    def __init__(self, popup):
        super().__init__()
        self.popup = popup

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            pos = event.globalPos()
            # Si el clic no está dentro del popup => oculta popup
            if not self.popup.geometry().contains(pos):
                self.popup.hide()
        return False
