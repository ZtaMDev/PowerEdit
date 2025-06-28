import re
from PyQt5.QtGui import QTextCursor

def detect_indent_string(doc, default="    "):
    indents = []
    for i in range(min(50, doc.blockCount())):
        line = doc.findBlockByNumber(i).text()
        m = re.match(r"^( +|\t+)", line)
        if m:
            indents.append(m.group(1))
    if not indents:
        return default
    min_indent = min((s for s in indents if s.strip()), key=len, default=default)
    if all(s.startswith("\t") for s in indents):
        return "\t"
    space_indents = [s for s in indents if s.startswith(" ")]
    if space_indents:
        from collections import Counter
        lengths = [len(s) for s in space_indents]
        most_common = Counter(lengths).most_common(1)
        if most_common:
            return " " * most_common[0][0]
    return min_indent or default

def handle_indent(text_edit):
    cursor = text_edit.textCursor()
    doc = text_edit.document()
    pos = cursor.position()
    text = doc.toPlainText()

    block = cursor.block()
    current_line = block.text()
    indent = current_line[:len(current_line) - len(current_line.lstrip(" "))]
    indent_str = detect_indent_string(doc)

    # Caracter antes y después del cursor
    before = text[pos-1] if pos > 0 else ""
    after = text[pos] if pos < len(text) else ""

    pairs = {"{": "}", "[": "]", "(": ")"}

    # 1) Caso: cursor ENTRE {}, [] o () → expandir bloque vacío con línea indentada en medio
    if before in pairs and after == pairs[before]:
        closing = after

        cursor.beginEditBlock()
        cursor.deleteChar()  # eliminar el caracter de cierre original
        cursor.insertText("\n" + indent + indent_str)
        cursor.insertText("\n" + indent + closing)
        cursor.endEditBlock()

        cursor.movePosition(QTextCursor.PreviousBlock)
        cursor.movePosition(QTextCursor.EndOfLine)
        text_edit.setTextCursor(cursor)
        return True

    # 2) Caso: línea termina con apertura de bloque {, [, o ( → aumentar indentación
    if re.search(r"[\{\[\(]\s*(//.*)?$", current_line):
        cursor.insertText("\n" + indent + indent_str)
        return True

    # 3) Caso: justo antes de cierre de bloque } ] o ) → reducir indentación
    if re.match(r"\s*[\}\]\)]", after):
        new_indent = indent[:-len(indent_str)] if len(indent) >= len(indent_str) else ""
        cursor.insertText("\n" + new_indent)
        return True

    # 4) Caso por defecto: mantener indentación actual
    cursor.insertText("\n" + indent)
    return True
