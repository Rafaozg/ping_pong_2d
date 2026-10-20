import ttkbootstrap as ttk # Importamos la libreria visual.
import interfaz            # Importamos nuestro archivo de interfaz.

# Verificamos que este archivo sea el principal.
if __name__ == "__main__":
    # Creamos la ventana principal con el tema 'cyborg'.
    app = ttk.Window(themename="cyborg")
    
    # Iniciamos la clase del juego.
    juego = interfaz.VentanaJuego(app)
    
    # Mantenemos la ventana abierta.
    app.mainloop()