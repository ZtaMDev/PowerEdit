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

    # Caracter antes y después del cursor
    before = text[pos-1] if pos > 0 else ""
    after = text[pos] if pos < len(text) else ""

    pairs = {"{": "}", "[": "]", "(": ")"}

    # 1) Caso: cursor ENTRE {}, [] o () → expandir bloque vacío con línea indentada en medio
    if before in pairs and after == pairs[before]:
        closing = after

        cursor.beginEditBlock()
        cursor.deleteChar()  # eliminar el caracter de cierre original
        cursor.insertText("\n" + indent + "    ")
        cursor.insertText("\n" + indent + closing)
        cursor.endEditBlock()

        cursor.movePosition(QTextCursor.PreviousBlock)
        cursor.movePosition(QTextCursor.EndOfLine)
        text_edit.setTextCursor(cursor)
        return True

    # 2) Caso: línea termina con apertura de bloque {, [, o ( → aumentar indentación
    if re.search(r"[\{\[\(]\s*(//.*)?$", current_line):
        cursor.insertText("\n" + indent + "    ")
        return True

    # 3) Caso: justo antes de cierre de bloque } ] o ) → reducir indentación
    if re.match(r"\s*[\}\]\)]", after):
        new_indent = indent[:-4] if len(indent) >= 4 else ""
        cursor.insertText("\n" + new_indent)
        return True

    # 4) Caso por defecto: mantener indentación actual
    cursor.insertText("\n" + indent)
    return True
