enabled = True
name = "EjemploExtensión"

def setup(api):
    
    #abrir_archivo_python(api)
    #insertar_y_verificar(api)
    #verificar_modificacion(api)
    #cerrar_actual_si_no_es_welcome(api)
    #dock_de_prueba(api)
    #registrar_callback(api)
    #mostrar_ruta_archivo_actual(api)
    forzar_lenguaje_python(api)

def al_cambiar_pestana(index):
    print(f"[Extensión] Cambiaste a la pestaña con índice {index}")

def registrar_callback(api):
    api.on_tab_changed(al_cambiar_pestana)

def abrir_archivo_python(api):
    ruta = "prueba.py"
    contenido = "# Código de ejemplo\nprint('Hola Mundo')"
    api.open_new_tab(content=contenido, file_path=ruta, language="python")

def insertar_y_verificar(api):
    texto = "# Comentario insertado desde la extensión"
    api.insert_text_on_editor(texto)
    contenido = api.get_editor_text()
    api.log(f"Contenido actual del editor:\n{contenido}")
def verificar_modificacion(api):
    index = api.main_window.tabs.currentIndex()
    if api.is_tab_modified(index):
        api.show_message("Esta pestaña tiene cambios no guardados.")
    else:
        api.show_message("Esta pestaña está guardada.")
def cerrar_actual_si_no_es_welcome(api):
    if not api.is_current_tab_welcome():
        api.close_current_tab()
    else:
        api.show_message("No puedes cerrar la pestaña Welcome.")
def dock_de_prueba(api):
    def al_pulsar():
        api.show_message("¡Botón del dock pulsado!")

    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
    widget = QWidget()
    layout = QVBoxLayout(widget)
    boton = QPushButton("Púlsame", widget)
    boton.clicked.connect(al_pulsar)
    layout.addWidget(boton)

    dock = api.create_dock_widget("Dock de prueba", widget)
def mostrar_ruta_archivo_actual(api):
    ruta = api.get_current_tab_file_path()
    if ruta:
        api.show_message(f"Ruta actual: {ruta}")
    else:
        api.show_message("No hay archivo abierto.")
def forzar_lenguaje_python(api):
    api.set_language_on_editor("python")
    api.show_message("Lenguaje cambiado a Python.")
