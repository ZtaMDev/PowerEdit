from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont, QFontMetrics

class MinimapWidget(QWidget):
    def __init__(self, editor, highlighter=None, max_lines=300):
        super().__init__()
        self.editor = editor
        self.highlighter = highlighter
        self.max_lines = max_lines
        self.left_margin = 3
        self.setMinimumWidth(90)
        self.setMaximumWidth(90)
        self.setMinimumHeight(40)
        self.setStyleSheet("background-color: #2e2e2e; border: none; padding: 0px;")
        self.font = QFont("Consolas", 3)
        self.line_height = 3  # px per line, small but readable
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update)
        self.editor.verticalScrollBar().valueChanged.connect(self.schedule_update)
        self.editor.textChanged.connect(self.schedule_update)
        self.setMouseTracking(True)
        self._dragging = False
        self._scrolling_from_minimap = False
        self._hover = False

    def set_highlighter(self, highlighter):
        self.highlighter = highlighter
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()
    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def schedule_update(self):
        if not self._dragging:
            self.update_timer.start(15)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self.font)
        doc = self.editor.document()
        total_lines = doc.blockCount()
        visible_lines = self.editor.get_visible_lines()
        if visible_lines:
            first_visible = visible_lines[0]
            last_visible = visible_lines[-1]
        else:
            first_visible = 0
            last_visible = 0
        # Limit to max_lines (300) centered around visible region
        half = self.max_lines // 2
        center = (first_visible + last_visible) // 2 if visible_lines else 0
        start_line = max(0, center - half)
        end_line = min(total_lines, start_line + self.max_lines)
        y = 0
        metrics = QFontMetrics(self.font)
        max_line_width = 0
        elided_lines = []
        for i in range(start_line, end_line):
            block = doc.findBlockByNumber(i)
            text = block.text()
            elided = metrics.elidedText(text, Qt.ElideRight, 10000)  # No width limit for measuring
            width = metrics.horizontalAdvance(elided)
            if width > max_line_width:
                max_line_width = width
            elided_lines.append((elided, block))
        # Set minimap width to fit the largest elided line, up to 200px
        new_width = min(max_line_width, 200)
        if self.width() != new_width:
            self.setMinimumWidth(new_width)
            self.setMaximumWidth(new_width)
        # Now draw lines using the new width
        for elided, block in elided_lines:
            layout = block.layout()
            formats = layout.additionalFormats() if layout else []
            color = QColor("#888888")
            if formats:
                color_lengths = {}
                for fmt_range in formats:
                    fg = fmt_range.format.foreground()
                    if fg.style() != 0:
                        c = fg.color().rgb()
                        color_lengths[c] = color_lengths.get(c, 0) + fmt_range.length
                if color_lengths:
                    dominant_rgb = max(color_lengths, key=color_lengths.get)
                    color = QColor.fromRgb(dominant_rgb)
            painter.setPen(color)
            painter.drawText(0, y + self.line_height, elided)
            y += self.line_height
        # Draw visible region highlight (scroll bar)
        if self._hover or self._dragging:
            highlight_color = QColor(128, 128, 128, 120)  # semi-transparent grey
        else:
            highlight_color = QColor(128, 128, 128, 0)    # fully transparent by default
        painter.setBrush(highlight_color)
        painter.setPen(Qt.NoPen)
        y1 = (first_visible - start_line) * self.line_height
        y2 = (last_visible - start_line + 1) * self.line_height
        painter.drawRect(self.left_margin, y1, self.width() - self.left_margin, y2 - y1)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self.scroll_to_position(event.pos().y())
            self.update()

    def mouseMoveEvent(self, event):
        if self._dragging:
            self.scroll_to_position(event.pos().y())
            self.update()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self.update()

    def scroll_to_position(self, y):
        if self._scrolling_from_minimap:
            return
        self._scrolling_from_minimap = True
        try:
            doc = self.editor.document()
            total_lines = doc.blockCount()
            visible_lines = self.editor.get_visible_lines()
            half = self.max_lines // 2
            center = (visible_lines[0] + visible_lines[-1]) // 2 if visible_lines else 0
            start_line = max(0, center - half)
            end_line = min(total_lines, start_line + self.max_lines)
            line = int(y / self.line_height) + start_line
            line = max(0, min(line, total_lines - 1))
            block = doc.findBlockByNumber(line)
            cursor = self.editor.textCursor()
            cursor.setPosition(block.position())
            self.editor.setTextCursor(cursor)
            self.editor.centerCursor()
        finally:
            self._scrolling_from_minimap = False

    def wheelEvent(self, event):
        # Forward wheel events to the parent editor so scrolling works
        if self.editor:
            self.editor.wheelEvent(event)
        else:
            super().wheelEvent(event)

    def setVisible(self, visible):
        super().setVisible(visible)
        # When minimap is hidden, remove its width from the editor's right margin
        if hasattr(self.editor, 'setViewportMargins'):
            if visible:
                self.editor.setViewportMargins(self.editor.line_number_area_width(), 0, self.width(), 0)
            else:
                # Only leave margin for buttons/scrollbar, not minimap
                btn_size = 24
                scrollbar_width = 12
                self.editor.setViewportMargins(self.editor.line_number_area_width(), 0, btn_size * 2 + 18 + scrollbar_width, 0)
        if hasattr(self.editor, 'update'):
            self.editor.update()
