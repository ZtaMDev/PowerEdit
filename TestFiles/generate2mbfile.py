# Crear un archivo de texto de ~2MB llenándolo con texto repetido

def crear_archivo_2mb(nombre_archivo="archivo_10MB.txt"):
    texto = "Esta es una línea de prueba para llenar el archivo.Esta es una línea de prueba para llenar el archivo.Esta es una línea de prueba para llenar el archivo.Esta es una línea de prueba para llenar el archivo.Esta es una línea de prueba para llenar el archivo.Esta es una línea de prueba para llenar el archivo.Esta es una línea de prueba para llenar el archivo.\n"
    tamaño_objetivo = 10 * 1024 * 1024  # 2 MB en bytes
    repeticiones = tamaño_objetivo // len(texto)

    with open(nombre_archivo, "w", encoding="utf-8") as f:
        for _ in range(repeticiones):
            f.write(texto)

    print(f"Archivo '{nombre_archivo}' creado con tamaño aproximado de 10 MB.")

if __name__ == "__main__":
    crear_archivo_2mb()
 