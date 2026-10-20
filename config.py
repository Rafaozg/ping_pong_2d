import os
# --- CONFIGURACION ---
# Este archivo guarda valores fijos (Constantes) para el Ping Pong.

# Obtiene la carpeta exacta donde está guardado config.py
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(DIRECTORIO_BASE, "partidos_resultados.csv")

# Dimensiones iniciales de la ventana (luego se ajustan a tu pantalla).
ANCHO = 900  # Ancho en pixeles.
ALTO = 600   # Alto en pixeles.

# Grosor de la linea blanca de arriba y abajo para que la pelota rebote.
GROSOR_PARED = 10 

# Colores del juego (Tematica Ping Pong).
COLOR_FONDO = "#060606"    # Negro del tema Cyborg para evitar cancha blanca en WSL.
COLOR_LINEAS = "white"     # Blanco para la red y bordes.
COLOR_J1 = "orange"        # Color para la pala del Jugador 1.
COLOR_J2 = "blue"          # Color para la pala del Jugador 2.
COLOR_BLANCO = "white"     # Color normal de la pelota.
COLOR_PUNTO_ORO = "red"    # Color rojo para la pelota en el Punto Decisivo.

# Tamaños de los objetos en pixeles.
ANCHO_PALA = 20   # Ancho de la raqueta/pala.
ALTO_PALA = 100   # Alto de la raqueta/pala.

# Velocidades (Pixeles que se mueve el objeto por cuadro).
VELOCIDAD_JUGADOR = 25  # Velocidad de las palas.
VELOCIDAD_PELOTA = 7    # Velocidad normal de la pelota.
VELOCIDAD_ORO = 12      # Velocidad rapida para el desempate.