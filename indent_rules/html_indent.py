import os, json, re
from PyQt5.QtGui import QTextCursor
#INFIERNO DE IMPLEMENTAR HECHO ARCHIVO...
def load_html_tag_sets():
    path = os.path.join("completions", "html.compl")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            return (
                set(tag.lower() for tag in data.get("selfClosing", [])),
                set(tag.lower() for tag in data.get("nonClosing", []))
            )
    return set(), set()

SELF_CLOSING_TAGS, NON_CLOSING_TAGS = load_html_tag_sets()

# Reconoce apertura, cierre y slash final
TAG_RE = re.compile(r"<(/?)([a-zA-Z0-9\-]+)([^>]*)?(/?)>")

def compute_indent_level(text):
    stack = []
    for m in TAG_RE.finditer(text):
        closing, tag, extra, self_slash = m.groups()
        tag = tag.lower()
        is_self = (self_slash == "/") or (tag in SELF_CLOSING_TAGS)
        if is_self or (tag not in NON_CLOSING_TAGS):
            continue
        if closing:
            if stack and stack[-1] == tag:
                stack.pop()
        else:
            stack.append(tag)
    return len(stack)

def handle_indent(text_edit):
    cursor = text_edit.textCursor()
    doc   = text_edit.document()
    pos   = cursor.position()

    full   = doc.toPlainText()
    before = full[:pos]
    after  = full[pos:pos+100]

    level        = compute_indent_level(before)
    inner_indent = "    " * level
    outer_indent = "    " * max(0, level - 1)

    # 1) CIERRE inmediat o </tag> justo tras el cursor (sin salto de línea delante)
    if not after.startswith("\n"):
        m = re.match(r"\s*</([a-zA-Z0-9\-]+)>", after)
        if m:
            tag = m.group(1).lower()
            if tag in NON_CLOSING_TAGS:
                cursor.beginEditBlock()
                cursor.insertText("\n" + inner_indent)   # línea interior
                cursor.insertText("\n" + outer_indent)   # línea del cierre
                cursor.movePosition(QTextCursor.PreviousBlock)
                cursor.movePosition(QTextCursor.EndOfLine)
                cursor.endEditBlock()
                text_edit.setTextCursor(cursor)
                return True

    # 2) SELF-CLOSING (p.ej. <br/> o tags en SELF_CLOSING_TAGS)
    line = cursor.block().text().strip()
    m_self = TAG_RE.fullmatch(line)
    if m_self:
        _, tag, extra, self_slash = m_self.groups()
        tag = tag.lower()
        is_self = (self_slash == "/") or (tag in SELF_CLOSING_TAGS)
        if is_self:
            cursor.insertText("\n" + inner_indent)
            return True

    # 3) APERTURA nonClosing (<div>, <p>, etc.)
    m_open = re.fullmatch(r"<([a-zA-Z0-9\-]+)(\s[^>]*)?>", line)
    if m_open and m_open.group(1).lower() in NON_CLOSING_TAGS:
        cursor.insertText("\n" + inner_indent)
        return True

    # 4) Si la línea actual es un cierre </tag>, mantenemos el mismo nivel (inner_indent)
    m_close_line = re.fullmatch(r"</([a-zA-Z0-9\-]+)>", line)
    if m_close_line:
        tag = m_close_line.group(1).lower()
        if tag in NON_CLOSING_TAGS:
            cursor.insertText("\n" + inner_indent)
            return True

    # 5) Fallback: indentación estándar según nesting
    cursor.insertText("\n" + inner_indent)
    return True
