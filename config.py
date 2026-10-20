import os
# --- CONFIGURACION ---
# Este archivo guarda valores fijos (Constantes) para el Ping Pong.

# Obtiene la carpeta exacta donde está guardado config.py
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(DIRECTORIO_BASE, "partidos_resultados.csv")

# Frames por segundo del bucle (pygame). El juego ttkbootstrap corria a ~33 FPS.
FPS = 60

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

# Velocidades (Pixeles que se mueve el objeto POR CUADRO a 60 FPS).
VELOCIDAD_JUGADOR = 9      # Movimiento continuo de las palas por cuadro.
VELOCIDAD_PELOTA = 6      # Velocidad normal de la pelota.
VELOCIDAD_ORO = 11        # Velocidad rapida para el desempate.
VELOCIDAD_MAX = 16        # Tope de la pelota acelerada.
ACELERACION = 1.03        # Factor de aceleracion por golpe de pala.
MAX_ANGULO = 1.047        # Angulo maximo de rebote en radianes (60 grados).
