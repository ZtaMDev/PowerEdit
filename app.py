# app.py
import sys
import time

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from main_window import MainWindow
 
def main():
    # 1) Crear la aplicación
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("poweredit.ico"))
    # 2) Poner cursor de espera global mientras inicializa
    QApplication.setOverrideCursor(Qt.WaitCursor)

    # 3) Inicializar todo (tema, docks, tabs, etc.) ANTES de mostrar
    start = time.perf_counter()
    window = MainWindow()
    end = time.perf_counter()
    print(f"[DEBUG] Inicio de la app tomó {end - start:.4f} segundos")

    # 4) Restaurar cursor normal
    QApplication.restoreOverrideCursor()

    # 5) Mostrar la ventana UNA sola vez que ya esté todo cargado
    window.show()

    # 6) Entrar al loop de eventos
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()