enabled = True
name = "EjemploExtensión"
def setup(api):
    # Crear una nueva pestaña vacía
    api.open_new_tab()

    # Crear una nueva pestaña con contenido de texto
    api.open_new_tab(content="print('Hola Mundo')", language="python")

    # Crear una nueva pestaña abriendo un archivo específico
    api.open_new_tab(file_path="C:/ruta/archivo.txt")

    # Crear una nueva pestaña con contenido y lenguaje especificado
    api.open_new_tab(content="# Esto es un script JS", language="javascript")
