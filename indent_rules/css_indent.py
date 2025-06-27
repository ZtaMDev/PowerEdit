# css_indent.py
import re
from PyQt5.QtGui import QTextCursor

def handle_indent(text_edit):
    cursor = text_edit.textCursor()
    doc = text_edit.document()
    pos = cursor.position()
    text = doc.toPlainText()

    block = cursor.block()
    current_line = block.text()
    indent = current_line[:len(current_line) - len(current_line.lstrip(" "))]

    before = text[pos-1] if pos > 0 else ""
    after  = text[pos]   if pos < len(text) else ""

    pairs = {"{": "}"}

    # 1) Cursor ENTRE {} → expandir bloque vacío con salto de línea e indentación
    if before in pairs and after == pairs[before]:
        closing = after

        cursor.beginEditBlock()
        cursor.deleteChar()
        cursor.insertText("\n" + indent + "    ")
        cursor.insertText("\n" + indent + closing)
        cursor.endEditBlock()

        cursor.movePosition(QTextCursor.PreviousBlock)
        cursor.movePosition(QTextCursor.EndOfLine)
        text_edit.setTextCursor(cursor)
        return True

    # 2) Línea termina con { → abrir nuevo nivel indentado
    if re.search(r"\{\s*(,)?\s*$", current_line):
        cursor.insertText("\n" + indent + "    ")
        return True

    # 3) Justo antes de } → outdent un nivel (4 espacios)
    if re.match(r"\s*\}", after):
        new_indent = indent[:-4] if len(indent) >= 4 else ""
        cursor.insertText("\n" + new_indent)
        return True

    # 4) Fallback: mantener misma indentación
    cursor.insertText("\n" + indent)
    return True
