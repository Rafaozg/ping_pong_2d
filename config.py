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

# --- PODERES (habilidades recogidas con la pala) ---
DUR_CONGELAR = 2.0       # Segundos que la pelota queda quieta.
DUR_LENTITUD = 5.0       # Segundos de pala rival lenta.
DUR_RAPIDEZ = 5.0        # Segundos de pala propia rapida.
DUR_REDUCCION = 5.0      # Segundos de pala rival reducida.
FACTOR_LENTITUD = 0.5    # Multiplicador de velocidad con Lentitud.
FACTOR_RAPIDEZ = 1.5     # Multiplicador de velocidad con Rapidez.
FACTOR_REDUCCION = 0.5   # Multiplicador de alto de pala con Reduccion.
SPAWN_PODER_MIN = 5.0    # Segundos minimos entre apariciones por arco.
SPAWN_PODER_MAX = 9.0    # Segundos maximos entre apariciones por arco.
