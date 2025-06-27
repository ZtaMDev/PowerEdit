# json_indent.py
import re
from PyQt5.QtGui import QTextCursor

def handle_indent(text_edit):
    cursor = text_edit.textCursor()
    doc = text_edit.document()
    pos = cursor.position()
    text = doc.toPlainText()

    # Línea actual e indentación existente
    block = cursor.block()
    current_line = block.text()
    indent = current_line[:len(current_line) - len(current_line.lstrip(" "))]

    # Caracter antes y después del cursor
    before = text[pos-1] if pos > 0 else ""
    after  = text[pos]   if pos < len(text) else ""

    pairs = {"{": "}", "[": "]"}

    # 1) Caso: cursor ENTRE {} o [] → expandir bloque vacío
    if before in pairs and after == pairs[before]:
        closing = after

        cursor.beginEditBlock()
        # Eliminar la llave/corchete de cierre original
        cursor.deleteChar()
        # Inserta línea intermedia indentada
        cursor.insertText("\n" + indent + "    ")
        # Inserta línea de cierre con indent base
        cursor.insertText("\n" + indent + closing)
        cursor.endEditBlock()

        # Coloca el cursor al final de la línea intermedia
        cursor.movePosition(QTextCursor.PreviousBlock)
        cursor.movePosition(QTextCursor.EndOfLine)
        text_edit.setTextCursor(cursor)
        return True

    # 2) Caso: línea termina con { o [ → abrir nuevo nivel
    if re.search(r"[\{\[]\s*(,)?\s*$", current_line):
        cursor.insertText("\n" + indent + "    ")
        return True

    # 3) Caso: justo antes de } o ] → outdent un nivel
    if re.match(r"\s*[\}\]]", after):
        # reducir indent (4 espacios)
        new_indent = indent[:-4] if len(indent) >= 4 else ""
        cursor.insertText("\n" + new_indent)
        return True

    # 4) Fallback: misma indentación
    cursor.insertText("\n" + indent)
    return True
