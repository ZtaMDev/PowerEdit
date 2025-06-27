import os
import importlib.util
from PyQt5.QtGui import QTextCursor

class IndentHandler:
    def __init__(self, language="plain"):
        self.language = language
        self.custom_logic = self._load_language_handler(language)

    def set_language(self, lang):
        self.language = lang
        self.custom_logic = self._load_language_handler(lang)

    def _load_language_handler(self, lang):
        path = os.path.join("indent_rules", f"{lang}_indent.py")
        if not os.path.exists(path):
            return None
        spec = importlib.util.spec_from_file_location(f"{lang}_indent", path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            return getattr(module, "handle_indent", None)
        except Exception as e:
            print(f"❌ Error cargando lógica de indentación para {lang}: {e}")
            return None

    def handle_indent(self, text_edit):
        if self.custom_logic:
            handled = self.custom_logic(text_edit)
            if handled:
                return True

        # fallback genérico
        cursor = text_edit.textCursor()
        doc = text_edit.document()
        pos = cursor.position()
        block = cursor.block()
        current_line = block.text()
        indent = self._get_indent_prefix(current_line)

        # Detección: cursor entre delimitadores de apertura y cierre
        #justo entre {…}, […], (…) 
        text_before = doc.toPlainText()[pos-1:pos]
        text_after  = doc.toPlainText()[pos:pos+1]
        pairs = { "{": "}", "[": "]", "(": ")" }
        
        if text_before in pairs and text_after == pairs[text_before]:
            closing = text_after

            cursor.beginEditBlock()
            # 1) Eliminar el carácter de cierre original
            cursor.deleteChar()
            # 2) Insertar newline + indent + 4 espacios
            cursor.insertText("\n" + indent + "    ")
            # 3) Insertar newline + indent + la llave de cierre
            cursor.insertText("\n" + indent + closing)
            # 4) Mover cursor a la línea intermedia (entre llaves) al final
            cursor.movePosition(QTextCursor.PreviousBlock)
            cursor.movePosition(QTextCursor.EndOfLine)
            cursor.endEditBlock()

            text_edit.setTextCursor(cursor)
            return True


        # Fallbacks según lenguaje
        extra_indent = ""
        if self.language == "python":
            if current_line.strip().endswith(":"):
                extra_indent = "    "
        elif self.language in ("javascript", "java", "c", "cpp"):
            if current_line.strip().endswith("{"):
                extra_indent = "    "

        cursor.insertText("\n" + indent + extra_indent)
        return True


    def _get_indent_prefix(self, line):
        return line[:len(line) - len(line.lstrip(" "))]
