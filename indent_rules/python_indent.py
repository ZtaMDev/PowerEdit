from PyQt5.QtGui import QTextCursor

def handle_indent(text_edit):
    cursor = text_edit.textCursor()
    doc = text_edit.document()
    block = cursor.block()
    current_line = block.text()
    # Use 4 spaces or a tab if the current line starts with a tab
    if current_line.startswith("\t"):
        indent_str = "\t"
    else:
        indent_str = "    "
    # Count leading indents
    leading = 0
    i = 0
    while i < len(current_line):
        if current_line[i:i+len(indent_str)] == indent_str:
            leading += 1
            i += len(indent_str)
        else:
            break
    # If current line ends with ':', increase indent level
    if current_line.strip().endswith(":"):
        leading += 1
    cursor.insertText("\n" + (indent_str * leading))
    return True
