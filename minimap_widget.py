from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtCore import Qt, QPoint
#DEPRECATED NO USAR LAGUEA MUCHO INNUSABLE POR AHORA...
class MinimapWidget(QPlainTextEdit):
    def __init__(self, editor, max_lines=500):
        super().__init__()
        self.setReadOnly(True)
        self.editor = editor
        self.max_lines = max_lines
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #2e2e2e;
                color: #888888;
                font-size: 4px;
                font-family: Consolas, monospace;
                border: none;
                padding: 0px;
            }
        """)

        self.setFixedWidth(80)

        # Conectar scroll del editor al minimap
        self.editor.verticalScrollBar().valueChanged.connect(self.update_minimap)
        self.editor.textChanged.connect(self.update_minimap)

    def update_minimap(self):
        # Línea superior visible en el editor
        top_line = self.editor.cursorForPosition(QPoint(0, 0)).blockNumber()
        total_lines = self.editor.blockCount()
        half_window = self.max_lines // 2

        start_line = max(0, top_line - half_window)
        end_line = min(total_lines, start_line + self.max_lines)

        # Extraer texto visible
        text = []
        block = self.editor.document().findBlockByNumber(start_line)
        for _ in range(start_line, end_line):
            if not block.isValid():
                break
            text.append(block.text())
            block = block.next()

        self.setPlainText('\n'.join(text))
