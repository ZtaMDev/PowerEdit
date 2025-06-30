from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QLabel, QStackedLayout, QMenu, QAction,
    QApplication, QHBoxLayout, QPushButton
)
from PyQt5.QtGui import QMovie, QCursor
from PyQt5.QtCore import Qt, QSize, QUrl, QPoint, QTimer
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtCore import QUrl
import os
from PyQt5.QtWebEngineWidgets import QWebEnginePage
import socket
import threading
import functools
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from PyQt5.QtWebEngineWidgets import QWebEngineView
import time
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
import re
from urllib.parse import urljoin

class LivePreviewDock(QDockWidget):
    def __init__(self, parent=None):
        # Initialize all attributes first to avoid AttributeError in showEvent
        self.user_minimized = False
        self.external_url = None
        self.auto_refresh = True
        self._first_show = True
        self._first_load = True
        self._initial_size = None
        self.server_started = False
        self.server_port = None
        self.server_root = None
        self.httpd = None
        self.server_thread = None
        self.last_loaded_path = None

        super().__init__("", parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.setFloating(False)

        # Crear barra de título personalizada
        self.setTitleBarWidget(self._create_custom_titlebar())

        # UI
        container = QWidget()
        self.setWidget(container)
        self.layout = QStackedLayout(container)

        self.spinner = QLabel(alignment=Qt.AlignCenter)
        movie = QMovie("icons/spinner.gif")
        movie.setScaledSize(QSize(32, 32))
        self.spinner.setMovie(movie)
        movie.start()
        self.layout.addWidget(self.spinner)
        self.spinner.hide()

        self.webview = QWebEngineView()
        self.layout.addWidget(self.webview)
        self.webview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.webview.customContextMenuRequested.connect(self._show_custom_menu)
        self.webview.loadFinished.connect(self._on_load_finished)

        self.hide()

    def _create_custom_titlebar(self):
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(4, 0, 4, 0)

        title = QLabel("Live Preview")
        title.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(title)
        layout.addStretch()

        btn_min = QPushButton("-")
        btn_min.setToolTip("Minimizar")
        btn_min.setFixedSize(20, 20)
        btn_min.clicked.connect(self._user_hide)
        btn_min.setStyleSheet("QPushButton { background: #444; color: white; border: none; }"
                              "QPushButton:hover { background: #666; }")
        layout.addWidget(btn_min)

        btn_close = QPushButton("✕")
        btn_close.setToolTip("Cerrar vista previa")
        btn_close.setFixedSize(20, 20)
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("QPushButton { background: #444; color: white; border: none; }"
                                "QPushButton:hover { background: #c00; }")
        layout.addWidget(btn_close)

        return bar
    def _user_hide(self):
        self.user_minimized = True
        self.hide()
    
    def show(self):
        self.user_minimized = False
        super().show()


    def showEvent(self, ev):
        super().showEvent(ev)
        if self._first_show:
            self._first_show = False
            #Causa problemas ayuda
            #self.resize(600, self.parent().height())
            self._initial_size = QSize(600, 600)


    def _show_spinner_once(self):
        if not self._first_load:
            return
        self._first_load = False
        if self._initial_size:
            self.setFixedSize(self._initial_size)
        self.spinner.show()
        self.layout.setCurrentWidget(self.spinner)
    
    def _show_spinner_for_refresh(self):
        if self._initial_size:
            self.setFixedSize(self._initial_size)
        self.spinner.show()
        self.layout.setCurrentWidget(self.spinner)

    def _on_load_finished(self, ok):
        # Se oculta spinner y se muestra el webview
        self.spinner.hide()
        self.layout.setCurrentWidget(self.webview)
        # Restaurar tamaños mínimos/máximos para permitir resize
        self.setMaximumSize(QSize(16777215, 16777215))
        self.setMinimumSize(QSize(0, 0))

    def start_server(self, root_dir):
        self._start_server_if_needed(root_dir)

    def _show_custom_menu(self, pos: QPoint):
        menu = QMenu(self)
        main = self.parent()
        if hasattr(main, "style_menu"):
            main.style_menu(menu)

        load_ext = QAction("Load external URL…", self)
        load_ext.triggered.connect(self._prompt_and_load_url)
        menu.addAction(load_ext)
        menu.addSeparator()
        # 1) Abrir en navegador
        open_action = QAction("Open in browser", self)
        open_action.triggered.connect(self._open_in_browser)
        menu.addAction(open_action)

        # 2) Recargar vista previa
        reload_action = QAction("Reaload live preview", self)
        reload_action.triggered.connect(self.refresh)
        menu.addAction(reload_action)

        menu.addSeparator()


        # 3) Copiar URL adecuada
        if self.external_url:
            # copiar la URL externa
            copy_action = QAction("Copiar URL externa", self)
            copy_action.triggered.connect(lambda: QApplication.clipboard().setText(self.external_url))
            menu.addAction(copy_action)

        elif self.last_loaded_path:
            # copiar URL local del servidor
            rel = os.path.relpath(self.last_loaded_path, self.server_root).replace(os.sep, "/")
            url = f"http://localhost:{self.server_port}/{rel}"
            copy_action = QAction("Copiar URL local", self)
            copy_action.triggered.connect(lambda: QApplication.clipboard().setText(url))
            menu.addAction(copy_action)

        # 5) Aplicar estilos al menú
        if hasattr(main, "menu_background") and hasattr(main, "menu_text_color"):
            bg = main.menu_background
            fg = main.menu_text_color
            menu.setStyleSheet(f"""
                QMenu {{ background-color: {bg}; color: {fg}; border: 1px solid {fg}; }}
                QMenu::item:selected {{ background-color: {fg}; color: {bg}; }}
            """)

        # 6) Mostrar menú UNA SOLA vez
        menu.exec_(self.webview.mapToGlobal(pos))

    def load_external_url(self, raw: str):
        """Carga directamente una URL (http://…) sin pasar por archivo local."""
        from PyQt5.QtCore import QUrl

        url = QUrl(raw)
        if not url.scheme():
            url.setScheme("http")

        self.external_url = url
        self.last_loaded_path = None

        self._show_spinner_for_refresh()
        self.webview.load(url)

        if self.isHidden() or self.user_minimized:
            self.user_minimized = False
            self.show()
        self.raise_()
        print(f"[LivePreview] Cargando URL externa: {url.toString()}")

    def _prompt_and_load_url(self):
        from PyQt5.QtWidgets import QInputDialog
        from PyQt5.QtCore import QUrl

        text, ok = QInputDialog.getText(
            self, "Load external URL",
            "Write URL to open with Live Preview:"
        )
        if not ok or not text.strip():
            return

        raw = text.strip()
        url = QUrl(raw)
        if not url.scheme():
            url.setScheme("http")

        # Guardar esta URL
        self.external_url = url
        # Deshabilitamos el servidor local
        self.last_loaded_path = None

        self._show_spinner_for_refresh()
        self.webview.load(url)
        print(f"[LivePreview] Loading URL externa: {url.toString()}")

    def _open_in_browser(self):
        import webbrowser

        # si había una URL externa, la abre
        if self.external_url:
            webbrowser.open(self.external_url.toString())
            return

        if self.server_started and self.last_loaded_path:
            rel_path = os.path.relpath(self.last_loaded_path, self.server_root).replace(os.sep, "/")
            url = f"http://localhost:{self.server_port}/{rel_path}"
            webbrowser.open(url)

    def _start_server_if_needed(self, root_dir):
        if self.server_started:
            return
        if not os.path.isdir(root_dir):
            root_dir = os.path.expanduser("~")

        for p in range(3000, 3100):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', p)) != 0:
                    self.server_port = p
                    break
        else:
            print("No se encontró puerto libre.")
            return

        handler = functools.partial(SimpleHTTPRequestHandler, directory=root_dir)

        def serve():
            self.httpd = ThreadingHTTPServer(('localhost', self.server_port), handler)
            self.httpd.serve_forever()

        self.server_root = root_dir
        self.server_thread = threading.Thread(target=serve, daemon=True)
        self.server_thread.start()
        self.server_started = True

    def _load_url(self, file_path):
        rel = os.path.relpath(file_path, self.server_root).replace(os.sep, "/")
        timestamp = int(time.time() * 1000)
        url = QUrl(f"http://localhost:{self.server_port}/{rel}?t={timestamp}")
        self.webview.load(url)
        print(f"[LivePreview] Cargando URL: {url.toString()}")

    def load_html_from_file(self, file_path):
        if not os.path.isfile(file_path):
            return
        self.last_loaded_path = file_path
        self.external_url = None
        base_dir = os.path.dirname(file_path) or os.getcwd()
        self._start_server_if_needed(base_dir)

        # primera carga:
        self._show_spinner_once()
        QTimer.singleShot(300, self.refresh)
        self.show()

    def _load_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
        except Exception as e:
            print(f"[LivePreview] Error al leer HTML: {e}")
            return

        timestamp = int(time.time() * 1000)
        base_url = f"http://localhost:{self.server_port}/"

        def replace_css(match):
            href = match.group(1)
            # rutas absolutas (/...)
            if href.startswith("/"):
                new_href = f"{base_url.rstrip('/')}{href}?t={timestamp}"
            else:
                new_href = f"{href}?t={timestamp}"
            return f'href="{new_href}"'

        # añade ?t= al href de todas las hojas .css
        html = re.sub(r'href="([^"]+\.css)"', replace_css, html)

        # carga el HTML otorgándole baseUrl para que funcione el href absoluto
        self.webview.setHtml(html, QUrl(base_url))
        print("[LivePreview] HTML cargado sin caché para CSS.")

    def toggle_auto_refresh(self, enable: bool):
        """ Permite activar/desactivar el auto-refresh en caliente. """
        self.auto_refresh = enable
        print(f"[LivePreview] auto_refresh = {self.auto_refresh}")

    def _load_buffer(self, html: str, base_path: str):
        timestamp = int(time.time() * 1000)
        base_url = QUrl(f"file:///{base_path}/")
        # Cache-bust de los CSS embebidos
        def repl_css(m):
            href = m.group(1)
            if href.startswith("/"):
                new_href = f"{base_url.toString().rstrip('/')}{href}?t={timestamp}"
            else:
                new_href = f"{href}?t={timestamp}"
            return f'href="{new_href}"'
        html = re.sub(r'href="([^"]+\.css)"', repl_css, html)
        self.webview.setHtml(html, base_url)
        print("[LivePreview] _load_buffer() injectado sin guardar")

    def refresh(self):
        if getattr(self, "external_url", None):
            # recarga la URL externa
            QTimer.singleShot(50, lambda: self.webview.load(QUrl(self.external_url)))
            return
        if not (self.server_started and self.last_loaded_path):
            return

        if self.auto_refresh:
            # Tomar el editor actual de MainWindow
            mw = self.parent()
            editor = getattr(mw, "_current_preview_editor", None)
            if editor:
                html = editor.toPlainText()
                # base_path es la carpeta donde está el HTML (para resolver rutas relativas)
                base_path = os.path.dirname(self.last_loaded_path)
                self._load_buffer(html, base_path)
                return

        # comportamiento normal cache-busting
        rel = os.path.relpath(self.last_loaded_path, self.server_root).replace(os.sep, "/")
        ts = int(time.time() * 1000)
        url = QUrl(f"http://localhost:{self.server_port}/{rel}?t={ts}")
        self.webview.load(url)
        print(f"[LivePreview] reload from disk: {url.toString()}")


    def _perform_refresh(self):
        # 1) limpiar caché
        profile = self.webview.page().profile()
        profile.clearHttpCache()
        profile.clearAllVisitedLinks()
        print("[LivePreview] Caché limpiado.")

        # 2) mostrar spinner rápido
        self.spinner.show()
        self.layout.setCurrentWidget(self.spinner)

        # 3) disparar carga real pocos ms después
        QTimer.singleShot(50, lambda: self._load_url(self.last_loaded_path))


    def closeEvent(self, event):
        self.user_minimized = True
        self.stop_server()
        if hasattr(self, "external_url"):
            del self.external_url
        super().closeEvent(event)



    def stop_server(self):
        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
                print("[LivePreview] Servidor detenido.")
            except Exception as e:
                print(f"Error al detener servidor: {e}")
            self.httpd = None
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1)
            self.server_thread = None
        self.server_started = False
        self.last_loaded_path = None


    def clear_cache(self):
        profile = self.webview.page().profile()
        profile.clearHttpCache()
        profile.clearAllVisitedLinks()
        print("[LivePreview] Caché limpiado.")
    def load_url_from_backend(self, url: str):
        self.external_url = url
        self.server_started = False
        self.last_loaded_path = None
        self._first_show = True
        self._first_load = True

        # Muetra el spinner la primera vez
        self._show_spinner_once()
        # Carga la página
        self.webview.load(QUrl(url))
        self.show()
    def _on_manual_close(self):
        # 1) Ocultamos la vista
        self.user_minimized = True
        super().hide()
        # 2) Si hay un servidor local, se detiene
        self.stop_server()
        if hasattr(self, "external_url"):
            del self.external_url