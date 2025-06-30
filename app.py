# app.py
import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("poweredit.ico"))

    window = MainWindow()
    window.setAttribute(Qt.WA_DontShowOnScreen, True)
    window.show()
    start = time.perf_counter()
    app.processEvents()

    end = time.perf_counter()

    print(f"[DEBUG] Inicio de la app tomó {end - start:.4f} segundos")

    window.setAttribute(Qt.WA_DontShowOnScreen, False)
    window.hide()
    QTimer.singleShot(0, window.show)

    QTimer.singleShot(0, window.load_extensions_manager)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
