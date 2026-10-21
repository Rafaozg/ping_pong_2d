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

# --- DIFICULTAD ---
DIFICULTADES = ["FACIL", "NORMAL", "DIFICIL"]

# Multiplicadores por dificultad
DIF_VEL_PELOTA = {"FACIL": 0.85, "NORMAL": 1.0, "DIFICIL": 1.4}
DIF_VEL_ORO = {"FACIL": 0.85, "NORMAL": 1.0, "DIFICIL": 1.5}
DIF_VEL_JUGADOR = {"FACIL": 1.15, "NORMAL": 1.0, "DIFICIL": 0.8}
DIF_VEL_MAX = {"FACIL": 0.85, "NORMAL": 1.0, "DIFICIL": 1.35}
DIF_ACELERACION = {"FACIL": 1.01, "NORMAL": 1.03, "DIFICIL": 1.07}
DIF_SPAWN_PODER = {"FACIL": 1.6, "NORMAL": 1.0, "DIFICIL": 0.5}  # Multiplicador de tiempo (mayor = menos frecuentes en facil)

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

# Multiplicadores de efectos por dificultad
DIF_DUR_PODER = {"FACIL": 1.3, "NORMAL": 1.0, "DIFICIL": 0.8}
DIF_FACT_LENT = {"FACIL": 0.6, "NORMAL": 0.5, "DIFICIL": 0.4}
DIF_FACT_RAP = {"FACIL": 1.3, "NORMAL": 1.5, "DIFICIL": 1.7}
DIF_FACT_RED = {"FACIL": 0.6, "NORMAL": 0.5, "DIFICIL": 0.4}
DIF_ALTO_PALA = {"FACIL": 1.15, "NORMAL": 1.0, "DIFICIL": 0.85}
DIF_TIEMPO_LIMITE = {"FACIL": 75, "NORMAL": 60, "DIFICIL": 50}

# Nuevos poderes
DUR_MURO = 5.0
DUR_INVERTIR = 5.0
DUR_FANTASMA = 1.5
FACTOR_MURO = 2.0  # Multiplicador de alto de pala (doble)

# --- MANDOS (gamepads PS3 y compatibles; USB y Bluetooth) ---
MANDO_DEADZONE = 0.25   # Zona muerta del stick para mover la pala.
MANDO_EJE_NAV = 0.55    # Inclinacion minima del stick para navegar menus.
MANDO_NAV_INICIAL = 350  # ms de espera antes de repetir el movimiento de seleccion.
MANDO_NAV_REPETIR = 140  # ms entre repeticiones manteniendo stick/D-pad.
MANDO_EJE_Y = 1         # Eje vertical del stick izquierdo (fallback sin mapa).
MANDO_BTN_ACEPTAR = 0   # Boton crudo = Cruce (si no hay mapa de gamecontroller).
MANDO_BTN_VOLVER = 1    # Boton crudo = Circulo.
