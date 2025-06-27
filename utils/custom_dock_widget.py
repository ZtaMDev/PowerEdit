from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QHBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class CustomDockWidget(QDockWidget):
    def __init__(self, title, parent=None):
        super().__init__("", parent)
        self.setObjectName(f"Dock_{title.replace(' ', '_')}")
        self.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.setTitleBarWidget(self._create_title_bar(title))

    def _create_title_bar(self, title):
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(4, 2, 4, 2)   # márgenes pequeños
        layout.setSpacing(4)

        label = QLabel(title)
        font = QFont("Consolas", 8)  # fuente pequeña
        font.setBold(True)
        label.setFont(font)
        label.setStyleSheet("color: white;")

        btn_min = QPushButton("–")
        btn_min.setFixedSize(16, 16)
        btn_min.setStyleSheet("""
            QPushButton {
                background: none;
                color: white;
                border: none;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        btn_min.clicked.connect(self.hide)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(16, 16)
        btn_close.setStyleSheet(btn_min.styleSheet())
        btn_close.clicked.connect(self.close)

        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(btn_min)
        layout.addWidget(btn_close)

        bar.setStyleSheet("""
            background-color: #282a36;
            border-top: 1px solid #444;
            border-bottom: 1px solid #222;
        """)
        return bar
