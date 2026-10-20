import interfaz            # Importamos nuestro archivo de interfaz.

# Verificamos que este archivo sea el principal.
if __name__ == "__main__":
    # Iniciamos el juego (pygame) con la clase principal.
    juego = interfaz.Juego()
    juego.run()
