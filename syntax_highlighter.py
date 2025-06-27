import os
import json
import re
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt5.QtCore import QRegularExpression

def safe_regex(pattern):
    if isinstance(pattern, str) and pattern.strip():
        regex = QRegularExpression(pattern)
        if regex.isValid():
            return regex
    return None

class GenericHighlighter(QSyntaxHighlighter):
    def __init__(self, document, rules):
        super().__init__(document)
        self.rules = rules
        colors = rules.get("colors", {})
        self.in_multiline_import = False
        self.multiline_import_text = ""
        self.multiline_import_start_pos = 0
        self.multiline_import_regions = []

        def fmt(hex_color):
            f = QTextCharFormat()
            f.setForeground(QColor(hex_color))
            return f

        self.highlighting_rules = []

        is_css = "css" in rules.get("extensions", [])
        is_html = "html" in rules.get("extensions", [])

        # Keywords
        kw_fmt = fmt(colors.get("keyword", "#569CD6"))
        
        self.html_keyword_patterns = []
        if is_html:
            for kw in rules.get("keywords", []):
                pat = safe_regex(rf'\b{kw}\b')
                if pat:
                    self.html_keyword_patterns.append((pat, kw_fmt))
        else:
            for kw in rules.get("keywords", []):
                pat = safe_regex(rf'\b{kw}\b')
                if pat:
                    self.highlighting_rules.append((pat, kw_fmt))
        self.keyword_fmt = kw_fmt
        # Builtins
        bi_fmt = fmt(colors.get("builtin", "#BD93F9"))
        for bi in rules.get("builtins", []):
            pat = safe_regex(rf'\b{bi}\b')
            if pat:
                self.highlighting_rules.append((pat, bi_fmt))

        # Types
        type_fmt = fmt(colors.get("type", "#8BE9FD"))
        for t in rules.get("types", []):
            pat = safe_regex(rf'\b{t}\b')
            if pat:
                self.highlighting_rules.append((pat, type_fmt))

        # Constants
        const_fmt = fmt(colors.get("constant", "#1E6FB8"))
        for c in rules.get("constants", []):
            pat = safe_regex(rf'\b{c}\b')
            if pat:
                self.highlighting_rules.append((pat, const_fmt))

        # Functions
        fn_fmt = fmt(colors.get("function", "#50FA7B"))
        if rules.get("function_pattern"):
            pat = safe_regex(rules["function_pattern"])
            if pat:
                self.highlighting_rules.append((pat, fn_fmt))

        # Comentarios
        self.comment_fmt = fmt(colors.get("comment", "#6A9955"))
        self.comment_pattern = safe_regex(rules.get("comment_pattern", "#.*")) or QRegularExpression("#.*")

        # Strings
        self.string_patterns = []
        str_fmt = fmt(colors.get("string", "#CE9178"))
        for sp in rules.get("string_patterns", []):
            pat = safe_regex(sp)
            if pat:
                self.string_patterns.append((pat, str_fmt))

        self.multi_line_patterns = []
        for mpat in rules.get("multi_line_strings", []):
            start = safe_regex(mpat.get("start"))
            end = safe_regex(mpat.get("end"))
            if start and end:
                self.multi_line_patterns.append((start, end, fmt(colors.get("string", "#CE9178"))))

        # Valores
        self.values = rules.get("value", [])
        self.value_fmt = fmt(colors.get("value", "#3CB371"))
        self.value_patterns = [
            safe_regex(rf'\b\d+{re.escape(v)}\b|\b{re.escape(v)}\b') for v in self.values
        ]
        self.value_patterns = [p for p in self.value_patterns if p]

        # self y atributos (solo si no es HTML)
        self.self_format = fmt(colors.get("self", "#00BFFF"))
        if not is_html:
            for pattern in [
                r'\bself\b',
                r'\bself\.[a-zA-Z_]\w*\b',
                r'(?<=\.)[A-Za-z_]\w*\b',
                r'\b[A-Za-z_]\w*(?=\.)'
            ]:
                pat = safe_regex(pattern)
                if pat:
                    self.highlighting_rules.append((pat, self.self_format))

        # Métodos
        self.method_regex = safe_regex(r"\b[a-zA-Z_][a-zA-Z0-9_]*(?=\s*\()") or QRegularExpression()
        self.method_fmt = fn_fmt

        # Módulos
        self.modules = rules.get("modules", [])
        self.module_fmt = fmt(colors.get("module", "#2AA198")) if self.modules else None
        self.module_patterns = [
            safe_regex(rf'\b{re.escape(m)}\b') for m in self.modules
        ]
        self.module_patterns = [p for p in self.module_patterns if p]

        # Tags HTML
        self.tag_fmt = fmt(colors.get("tag", "#FF79C6")) if "tag" in colors else None
        self.tag_patterns = []
        if (is_css or is_html) and self.tag_fmt:
            html_path = os.path.join("extend", "html.extend")
            if os.path.exists(html_path):
                with open(html_path, encoding="utf-8") as f:
                    html_data = json.load(f)
                for tag in html_data.get("keywords", []):
                    regex = rf'\b{tag}\b' if is_css else rf'(?<=<)\s*{tag}(?=\s|>|/)'
                    pat = safe_regex(regex)
                    if pat:
                        self.tag_patterns.append(pat)
        
        # Atributos HTML
        self.attr_fmt = fmt(colors.get("attr", "#FF79C6"))
        self.attr_patterns = []

        if is_html:
            extend_attrs = rules.get("attributes", None)
            if extend_attrs:
                for attr in extend_attrs:
                    pat = safe_regex(rf'\b{attr}(?=\s*=)')
                    if pat:
                        self.attr_patterns.append(pat)
            else:
                self.attr_patterns = []

    def highlightBlock(self, text):
        if not text:
            return

        self.setCurrentBlockState(0)
        string_regions = []
        comment_regions = []

        def inside(pos, regions):
            return any(s <= pos < e for s, e in regions)

        # 1) Cadenas normales
        for pat, fmt in self.string_patterns:
            it = pat.globalMatch(text)
            while it.hasNext():
                m = it.next()
                s, l = m.capturedStart(), m.capturedLength()
                self.setFormat(s, l, fmt)
                string_regions.append((s, s + l))

        # 2) Cadenas multilínea
        for i, (start_e, end_e, fmt) in enumerate(self.multi_line_patterns):
            if self.previousBlockState() != i + 1:
                sm = start_e.match(text)
                si = sm.capturedStart() if sm.hasMatch() else -1
            else:
                si = 0
            while si >= 0:
                em = end_e.match(text, si + 1)
                if em.hasMatch():
                    ei = em.capturedStart() + em.capturedLength()
                    self.setFormat(si, ei - si, fmt)
                    string_regions.append((si, ei))
                    sm = start_e.match(text, ei)
                    si = sm.capturedStart() if sm.hasMatch() else -1
                else:
                    self.setCurrentBlockState(i + 1)
                    self.setFormat(si, len(text) - si, fmt)
                    string_regions.append((si, len(text)))
                    break

        # 3) Comentarios
        it = self.comment_pattern.globalMatch(text)
        while it.hasNext():
            m = it.next()
            s, l = m.capturedStart(), m.capturedLength()
            self.setFormat(s, l, self.comment_fmt)
            comment_regions.append((s, s + l))

        # 4) Resto de reglas (keywords, builtins, tipos…)
        for pat, fmt in self.highlighting_rules:
            it = pat.globalMatch(text)
            while it.hasNext():
                m = it.next()
                s, l = m.capturedStart(), m.capturedLength()
                if not inside(s, string_regions) and not inside(s, comment_regions):
                    self.setFormat(s, l, fmt)

        # 5) Tags HTML
        if self.tag_fmt and self.tag_patterns:
            for pat in self.tag_patterns:
                it = pat.globalMatch(text)
                while it.hasNext():
                    m = it.next()
                    s, l = m.capturedStart(), m.capturedLength()
                    if not inside(s, string_regions) and not inside(s, comment_regions):
                        self.setFormat(s, l, self.tag_fmt)

        # 6) Atributos HTML
        if self.attr_patterns:
            tag_regions = []
            tag_re = safe_regex(r"<[^!][^>]*?>")
            if tag_re:
                it = tag_re.globalMatch(text)
                while it.hasNext():
                    m = it.next()
                    tag_regions.append((m.capturedStart(), m.capturedEnd()))
            def inside_tag(pos):
                return any(s <= pos < e for s, e in tag_regions)
            for pat in self.attr_patterns:
                it = pat.globalMatch(text)
                while it.hasNext():
                    m = it.next()
                    s, l = m.capturedStart(), m.capturedLength()
                    if (not inside(s, string_regions)
                        and not inside(s, comment_regions)
                        and inside_tag(s)):
                        self.setFormat(s, l, self.attr_fmt)

        # 7) Métodos
        python_keywords = set(self.rules.get("keywords", []))

        # 7.1) Métodos
        it = self.method_regex.globalMatch(text)
        while it.hasNext():
            m = it.next()
            s, l = m.capturedStart(), m.capturedLength()
            word = text[s:s + l]
            if (not inside(s, string_regions)
                    and not inside(s, comment_regions)
                    and word not in python_keywords):
                self.setFormat(s, l, self.method_fmt)


        # No sirve ni idea de porque...
        is_multiline_start = bool(re.match(
            r'^\s*from\s+[A-Za-z_][\w\.]*\s+import\s*\($', text
        ))

        # Resaltar el módulo después de 'from ... import', incluso si es multilínea
        if self.module_fmt and ("import" in text or "from" in text):
            fm = re.search(r"\bfrom\s+([A-Za-z_][\w\.]*)\s+import", text)
            if fm:
                s0, e0 = fm.start(1), fm.end(1)
                if not inside(s0, string_regions) and not inside(s0, comment_regions):
                    self.setFormat(s0, e0 - s0, self.module_fmt)

        # Resaltar solo los módulos a la derecha del 'import' si NO es apertura multilínea
        if self.module_fmt and not is_multiline_start and ("import" in text or "from" in text):
            im = re.search(r"\bimport\s+(.+)", text)
            if im:
                base = im.start(1)
                for part in im.group(1).split(","):
                    name = part.strip().split(" as ")[0]
                    off = im.group(1).find(name)
                    s = base + off
                    l = len(name)
                    if not inside(s, string_regions) and not inside(s, comment_regions):
                        self.setFormat(s, l, self.module_fmt)

        # Resaltar módulos sueltos (en cualquier otro contexto)
        if self.module_fmt:
            for pat in self.module_patterns:
                it = pat.globalMatch(text)
                while it.hasNext():
                    m = it.next()
                    s, l = m.capturedStart(), m.capturedLength()
                    if not inside(s, string_regions) and not inside(s, comment_regions):
                        self.setFormat(s, l, self.module_fmt)

        # 10) Valores
        for pat in self.value_patterns:
            it = pat.globalMatch(text)
            while it.hasNext():
                m = it.next()
                s, l = m.capturedStart(), m.capturedLength()
                if not inside(s, string_regions) and not inside(s, comment_regions):
                    self.setFormat(s, l, self.value_fmt)

        # 11) Keywords HTML en tags
        if self.html_keyword_patterns:
            tag_regions = []
            tag_re = safe_regex(r"<[^!][^>]*?>")
            if tag_re:
                it = tag_re.globalMatch(text)
                while it.hasNext():
                    m = it.next()
                    tag_regions.append((m.capturedStart(), m.capturedEnd()))
            def inside_tag2(pos):
                return any(s <= pos < e for s, e in tag_regions)
            for pat, fmt in self.html_keyword_patterns:
                it = pat.globalMatch(text)
                while it.hasNext():
                    m = it.next()
                    s, l = m.capturedStart(), m.capturedLength()
                    if (not inside(s, string_regions)
                        and not inside(s, comment_regions)
                        and inside_tag2(s)):
                        self.setFormat(s, l, fmt)



def load_highlighter(language, document):
    path = os.path.join("extend", f"{language}.extend")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            rules = json.load(f)
        return GenericHighlighter(document, rules)
    return None
