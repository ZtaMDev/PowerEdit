name = "Hello World"
enabled = False

def setup(api):
    def saludar():
        api.show_message("¡Hola desde la extensión!", "Hello")

    api.add_menu_action("Extensiones/Hello World", saludar)
