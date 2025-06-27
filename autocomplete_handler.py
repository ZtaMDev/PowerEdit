import os
import json
import re

class AutoCompleteHandler:
    def __init__(self, language="plain"):
        self.language = language
        # Pairs de cierre automático para paréntesis, comillas, etc.
        self.pairs = {
            "(": ")",
            "[": "]",
            "{": "}",
            "'": "'",
            '"': '"',
            "`": "`"
        }
        # Carga las etiquetas de HTML si corresponde
        self.self_closing = set()
        self.non_closing = set()
        self.load_html_tags()

    def set_language(self, language):
        self.language = language
        self.load_html_tags()

    def load_html_tags(self):
        """Carga selfClosing y nonClosing desde completions/html.compl si es HTML."""
        self.self_closing.clear()
        self.non_closing.clear()
        if self.language != "html":
            return
        path = os.path.join("completions", "html.compl")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.self_closing = {tag.lower() for tag in data.get("selfClosing", [])}
            self.non_closing = {tag.lower() for tag in data.get("nonClosing", [])}
        except Exception as e:
            print(f"❌ Error cargando {path}: {e}")

    def handle_key_press(self, text_edit, event):
        cursor = text_edit.textCursor()
        key = event.text()

        # 1) Autocierre normal para (), [], {}, "", '', ``
        if key in self.pairs:
            close_char = self.pairs[key]
            cursor.insertText(key + close_char)
            cursor.movePosition(cursor.Left)
            text_edit.setTextCursor(cursor)
            return True

        # 2) Al escribir '>' en HTML, insertar </tag> si corresponde
        if self.language == "html" and key == ">":
            # Primero, inserta el '>' normalmente
            cursor.insertText(">")
            cursor_pos = cursor.position()
            full = text_edit.toPlainText()
            prev = full[max(0, cursor_pos - 100):cursor_pos]  # hasta 100 chars antes

            # Detecta un tag abierto al final: <tag ...>
            m = re.search(r"<([a-zA-Z0-9\-]+)(\s[^>]*)?>$", prev)
            if m:
                tag = m.group(1).lower()
                # Solo para etiquetas que están en non_closing y no en self_closing
                if tag in self.non_closing and tag not in self.self_closing:
                    closing = f"</{tag}>"
                    cursor.insertText(closing)
                    # Mover el cursor antes del cierre recién insertado
                    cursor.movePosition(cursor.Left, cursor.MoveAnchor, len(closing))
                    text_edit.setTextCursor(cursor)
            return True

        # 3) No lo manejamos 
        return False
