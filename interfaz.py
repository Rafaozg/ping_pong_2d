import io
import math
import random
import struct
import time
import wave
from collections import deque

import pygame

import config
import datos

# --- COLORES DE UI (tema oscuro estilo cyborg) ---
COLOR_PANEL = "#1a1a1a"
COLOR_BORDE = "#3c3c3c"
COLOR_VERDE = "#28a745"
COLOR_AMARILLO = "#ffc107"
COLOR_AZUL = "#17a2b8"
COLOR_ROJO = "#dc3545"
COLOR_GRIS = "#6c757d"

# --- PODERES (nombre corto y color de cada habilidad) ---
PODERES = {
    "congelar": ("CONG", "#22d3ee"),
    "lentitud": ("LENT", "#a855f7"),
    "rapidez": ("RAP", "#22c55e"),
    "reduccion": ("REC", "#f97316"),
    "muro": ("MURO", "#ffd93b"),
    "invertir": ("INV", "#ff4d6d"),
}


# Genera un beep simple (16-bit mono) sin usar numpy ni archivos externos.
def _generar_sonido(frecuencia, duracion_ms, volumen=0.35):
    rate = 22050
    muestras = int(rate * duracion_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        marcas = bytearray()
        for i in range(muestras):
            env = 1.0 - i / muestras  # Decaimiento para evitar clics.
            valor = int(volumen * env * 32767 * math.sin(2 * math.pi * frecuencia * i / rate))
            marcas += struct.pack("<h", valor)
        w.writeframes(bytes(marcas))
    buf.seek(0)
    return pygame.mixer.Sound(file=buf)


class Boton:
    def __init__(self, cx, cy, ancho, alto, texto, color, fuente):
        self.rect = pygame.Rect(0, 0, ancho, alto)
        self.rect.center = (cx, cy)
        self.texto = texto
        self.color = pygame.Color(color)
        self.fuente = fuente

    def dibujar(self, surface, raton):
        color = self.color
        if self.rect.collidepoint(raton):
            color = self.color.lerp((255, 255, 255), 0.25)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        img = self.fuente.render(self.texto, True, "white")
        surface.blit(img, img.get_rect(center=self.rect.center))

    def clic(self, pos):
        return self.rect.collidepoint(pos)


class EntradaTexto:
    def __init__(self, cx, cy, ancho, alto, texto_inicial, fuente):
        self.rect = pygame.Rect(0, 0, ancho, alto)
        self.rect.center = (cx, cy)
        self.texto = texto_inicial
        self.fuente = fuente
        self.activo = False
        self.cursor_tick = 0

    def manejar(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.activo = self.rect.collidepoint(event.pos)
        if not self.activo:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.texto = self.texto[:-1]
            elif event.key == pygame.K_RETURN:
                self.activo = False
            elif event.unicode and event.unicode.isprintable() and len(self.texto) < 18:
                self.texto += event.unicode

    def dibujar(self, surface):
        pygame.draw.rect(surface, COLOR_PANEL, self.rect, border_radius=6)
        borde = "white" if self.activo else COLOR_BORDE
        pygame.draw.rect(surface, borde, self.rect, 2, border_radius=6)
        img = self.fuente.render(self.texto, True, "white")
        surface.blit(img, img.get_rect(midleft=(self.rect.x + 10, self.rect.centery)))
        self.cursor_tick += 1
        if self.activo and (self.cursor_tick // 30) % 2 == 0:
            cx = self.rect.x + 12 + img.get_width()
            pygame.draw.line(surface, "white", (cx, self.rect.y + 7), (cx, self.rect.bottom - 7), 2)


class Juego:
    def __init__(self):
        pygame.init()

        # Audio: si el dispositivo falla (WSL sin PulseAudio), seguimos en silencio.
        self.audio_ok = False
        try:
            pygame.mixer.pre_init(22050, -16, 1, 512)
            pygame.mixer.init()
            self.snd_pala = _generar_sonido(440, 70)
            self.snd_pared = _generar_sonido(220, 60, 0.25)
            self.snd_punto = _generar_sonido(660, 150)
            self.snd_cuenta = _generar_sonido(300, 80, 0.25)
            self.snd_oro = _generar_sonido(880, 250)
            self.snd_poder = _generar_sonido(600, 120, 0.3)
            self.snd_activar = _generar_sonido(760, 180, 0.3)
            self.audio_ok = True
        except pygame.error:
            pass

        pygame.display.set_caption("PING PONG 2D")
        self.pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        config.ANCHO, config.ALTO = self.pantalla.get_size()
        self.reloj = pygame.time.Clock()
        self.corriendo = True

        # Fuentes.
        self.f_titulo = pygame.font.SysFont("arial", 56, bold=True)
        self.f_sub = pygame.font.SysFont("arial", 28, bold=True)
        self.f_normal = pygame.font.SysFont("arial", 20)
        self.f_peque = pygame.font.SysFont("arial", 16)
        self.f_marcador = pygame.font.SysFont("arial", 48, bold=True)
        self.f_cuenta = pygame.font.SysFont("arial", 90, bold=True)

        self.escena = "menu"
        self.error = ("", 0)
        self.dificultad = "NORMAL"
        self._iconos = self._generar_iconos()
        self._crear_menu()

    # --- SONIDO ---

    def _sonar(self, clave):
        if not self.audio_ok:
            return
        mapa = {
            "pala": self.snd_pala,
            "pared": self.snd_pared,
            "punto": self.snd_punto,
            "cuenta": self.snd_cuenta,
            "oro": self.snd_oro,
            "poder": self.snd_poder,
            "activar": self.snd_activar,
        }
        mapa[clave].play()

    # --- BUCLE PRINCIPAL ---

    def run(self):
        while self.corriendo:
            dt = self.reloj.tick(config.FPS)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.corriendo = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.corriendo = False
                else:
                    self._evento(e)
            self._actualizar(dt)
            self._dibujar()
        pygame.quit()

    def _evento(self, e):
        if self.escena == "menu":
            self._ev_menu(e)
        elif self.escena == "amistoso":
            self._ev_amistoso(e)
        elif self.escena == "torneo":
            self._ev_torneo(e)
        elif self.escena == "versus":
            self._ev_versus(e)
        elif self.escena == "juego":
            self._ev_juego(e)
        elif self.escena == "resultados":
            self._ev_resultados(e)

    def _actualizar(self, dt):
        if self.error[1] > 0:
            self.error = (self.error[0], self.error[1] - 1)
        if self.escena == "juego":
            self._upd_juego(dt)

    def _dibujar(self):
        self.pantalla.fill(config.COLOR_FONDO)
        raton = pygame.mouse.get_pos()
        if self.escena == "menu":
            self._drw_menu(raton)
        elif self.escena == "amistoso":
            self._drw_amistoso(raton)
        elif self.escena == "torneo":
            self._drw_torneo(raton)
        elif self.escena == "versus":
            self._drw_versus(raton)
        elif self.escena == "juego":
            self._drw_juego(raton)
        elif self.escena == "resultados":
            self._drw_resultados(raton)
        if self.error[1] > 0:
            img = self.f_normal.render(self.error[0], True, COLOR_ROJO)
            self.pantalla.blit(img, img.get_rect(center=(config.ANCHO // 2, config.ALTO - 60)))
        pygame.display.flip()

    def _generar_iconos(self):
        iconos = {}
        try:
            import os
            base = os.path.join(config.DIRECTORIO_BASE, "ico")
            mapa = {
                "congelar": os.path.join(base, "congelar.png"),
                "lentitud": os.path.join(base, "lentitud.png"),
                "rapidez": os.path.join(base, "rapidez.png"),
                "reduccion": os.path.join(base, "reduccion.png"),
                "muro": os.path.join(base, "muro.png"),
                "invertir": os.path.join(base, "invertir.png"),
            }
            for tipo, ruta in mapa.items():
                if not os.path.exists(ruta):
                    continue
                try:
                    img = pygame.image.load(ruta).convert_alpha()
                    img = pygame.transform.smoothscale(img, (66, 66))
                    iconos[tipo] = img
                except Exception:
                    continue
        except Exception:
            return {}
        return iconos

    def _texto(self, s, fuente, color, pos, centro=True):
        img = fuente.render(s, True, color)
        rect = img.get_rect()
        if centro:
            rect.center = pos
        else:
            rect.topleft = pos
        self.pantalla.blit(img, rect)
        return rect

    def _fallo(self, mensaje):
        self.error = (mensaje, 180)

    # --- MENU ---

    def _crear_menu(self):
        cx = config.ANCHO // 2
        cy = config.ALTO // 2
        w, h = 320, 52
        self.btn_amistoso = Boton(cx, cy - 60, w, h, "JUGAR AMISTOSO", COLOR_VERDE, self.f_normal)
        self.btn_torneo = Boton(cx, cy, w, h, "MODO TORNEO", COLOR_AMARILLO, self.f_normal)
        self.btn_resultados = Boton(cx, cy + 60, w, h, "VER RESULTADOS", COLOR_AZUL, self.f_normal)
        self.btn_salir = Boton(cx, cy + 120, w, h, "CERRAR JUEGO", COLOR_ROJO, self.f_normal)

    def _ev_menu(self, e):
        if e.type != pygame.MOUSEBUTTONDOWN or e.button != 1:
            return
        if self.btn_amistoso.clic(e.pos):
            self._crear_amistoso()
        elif self.btn_torneo.clic(e.pos):
            self._crear_torneo()
        elif self.btn_resultados.clic(e.pos):
            self._crear_resultados()
        elif self.btn_salir.clic(e.pos):
            self.corriendo = False

    def _drw_menu(self, raton):
        self._texto("PING PONG 2D", self.f_titulo, "white", (config.ANCHO // 2, config.ALTO // 4))
        for b in (self.btn_amistoso, self.btn_torneo, self.btn_resultados, self.btn_salir):
            b.dibujar(self.pantalla, raton)

    # --- PARTIDO AMISTOSO ---

    def _crear_amistoso(self):
        self.escena = "amistoso"
        cx, cy = config.ANCHO // 2, config.ALTO // 2
        self.inp1 = EntradaTexto(cx, cy - 60, 320, 44, "JUGADOR 1", self.f_normal)
        self.inp2 = EntradaTexto(cx, cy, 320, 44, "JUGADOR 2", self.f_normal)
        self.dif_btns = []
        w_b = 90
        h_b = 40
        for i, d in enumerate(config.DIFICULTADES):
            x = cx - (w_b * 1.5) + i * (w_b + 10)
            b = Boton(x, cy + 60, w_b, h_b, d, COLOR_PANEL, self.f_peque)
            self.dif_btns.append((b, d))
        self.btn_comenzar = Boton(cx, cy + 120, 260, 48, "COMENZAR", COLOR_VERDE, self.f_normal)
        self.btn_atras = Boton(cx, cy + 180, 260, 44, "ATRAS", COLOR_GRIS, self.f_normal)

    def _ev_amistoso(self, e):
        self.inp1.manejar(e)
        self.inp2.manejar(e)
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self._configurar_amistoso()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for b, d in getattr(self, "dif_btns", []):
                if b.clic(e.pos):
                    self.dificultad = d
                    return
            if self.btn_comenzar.clic(e.pos):
                self._configurar_amistoso()
            elif self.btn_atras.clic(e.pos):
                self.escena = "menu"

    def _configurar_amistoso(self):
        n1, n2 = self.inp1.texto.strip(), self.inp2.texto.strip()
        if n1 == "" or n2 == "":
            self._fallo("Los nombres no pueden estar vacios.")
            return
        if n1.lower() == n2.lower():
            self._fallo("Nombres iguales no permitidos.")
            return
        numero = datos.obtener_siguiente_numero("Amistoso")
        self.nombre_evento = f"Amistoso {numero}"
        self.modo = "amistoso"
        self.nombre1, self.nombre2 = n1, n2
        self._preparar_partido()

    def _drw_amistoso(self, raton):
        cx = config.ANCHO // 2
        cy = config.ALTO // 2
        self._texto("PARTIDO AMISTOSO", self.f_titulo, "white", (cx, cy - 180))
        self._texto("NOMBRES DE JUGADORES", self.f_sub, COLOR_AMARILLO, (cx, cy - 110))
        self._texto("DIFICULTAD", self.f_peque, COLOR_AMARILLO, (cx, cy + 30))
        self.inp1.dibujar(self.pantalla)
        self.inp2.dibujar(self.pantalla)
        for b, d in getattr(self, "dif_btns", []):
            b.dibujar(self.pantalla, raton)
            if d == self.dificultad:
                pygame.draw.rect(self.pantalla, "white", b.rect, 2, border_radius=8)
        self.btn_comenzar.dibujar(self.pantalla, raton)
        self.btn_atras.dibujar(self.pantalla, raton)

    # --- TORNEO ---

    def _crear_torneo(self):
        self.escena = "torneo"
        cx, cy = config.ANCHO // 2, config.ALTO // 2
        self.cajas = []
        for i in range(4):
            self.cajas.append(EntradaTexto(cx, cy - 100 + i * 52, 320, 40, f"Equipo {i + 1}", self.f_normal))
        self.dif_btns_t = []
        w_b = 90
        h_b = 40
        for i, d in enumerate(config.DIFICULTADES):
            x = cx - (w_b * 1.5) + i * (w_b + 10)
            b = Boton(x, cy + 120, w_b, h_b, d, COLOR_PANEL, self.f_peque)
            self.dif_btns_t.append((b, d))
        self.btn_iniciar = Boton(cx, cy + 180, 260, 48, "INICIAR COPA", COLOR_AMARILLO, self.f_normal)
        self.btn_atras = Boton(cx, cy + 240, 260, 44, "ATRAS", COLOR_GRIS, self.f_normal)

    def _ev_torneo(self, e):
        for c in self.cajas:
            c.manejar(e)
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self._configurar_torneo()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for b, d in getattr(self, "dif_btns_t", []):
                if b.clic(e.pos):
                    self.dificultad = d
                    return
            if self.btn_iniciar.clic(e.pos):
                self._configurar_torneo()
            elif self.btn_atras.clic(e.pos):
                self.escena = "menu"

    def _configurar_torneo(self):
        nombres = [c.texto.strip() for c in self.cajas]
        if any(n == "" for n in nombres):
            self._fallo("Nombres vacios no permitidos.")
            return
        if len(set(n.lower() for n in nombres)) != 4:
            self._fallo("Nombres repetidos no permitidos.")
            return
        numero = datos.obtener_siguiente_numero("Torneo")
        self.modo = "torneo"
        self.nombre_evento = f"Torneo {numero}"
        self.equipos = nombres
        self.fase = 1
        self.ganadores = []
        self._crear_versus()

    def _drw_torneo(self, raton):
        cx = config.ANCHO // 2
        cy = config.ALTO // 2
        self._texto("TORNEO", self.f_titulo, "white", (cx, cy - 200))
        self._texto("COPA (4 EQUIPOS)", self.f_sub, COLOR_AMARILLO, (cx, cy - 140))
        self._texto("DIFICULTAD", self.f_peque, COLOR_AMARILLO, (cx, cy + 90))
        for c in self.cajas:
            c.dibujar(self.pantalla)
        for b, d in getattr(self, "dif_btns_t", []):
            b.dibujar(self.pantalla, raton)
            if d == self.dificultad:
                pygame.draw.rect(self.pantalla, "white", b.rect, 2, border_radius=8)
        self.btn_iniciar.dibujar(self.pantalla, raton)
        self.btn_atras.dibujar(self.pantalla, raton)

    # --- VERSUS (entre partidos de torneo) ---

    def _crear_versus(self):
        self.escena = "versus"
        if self.fase == 1:
            self.nombre1, self.nombre2 = self.equipos[0], self.equipos[1]
            self.titulo_fase = "SEMIFINAL 1"
        elif self.fase == 2:
            self.nombre1, self.nombre2 = self.equipos[2], self.equipos[3]
            self.titulo_fase = "SEMIFINAL 2"
        else:
            self.nombre1, self.nombre2 = self.ganadores[0], self.ganadores[1]
            self.titulo_fase = "GRAN FINAL"
        cx, cy = config.ANCHO // 2, config.ALTO // 2
        self.btn_mesa = Boton(cx, cy + 80, 280, 52, "IR A LA MESA", COLOR_VERDE, self.f_normal)

    def _ev_versus(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self._preparar_partido()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.btn_mesa.clic(e.pos):
            self._preparar_partido()

    def _drw_versus(self, raton):
        cx, cy = config.ANCHO // 2, config.ALTO // 2
        self._texto(self.nombre_evento, self.f_normal, "white", (cx, cy - 140))
        self._texto(self.titulo_fase, self.f_titulo, COLOR_AMARILLO, (cx, cy - 70))
        self._texto(f"{self.nombre1} VS {self.nombre2}", self.f_sub, "white", (cx, cy + 20))
        self.btn_mesa.dibujar(self.pantalla, raton)

    # --- PARTIDO (MESA) ---

    def _preparar_partido(self):
        self.escena = "juego"
        self.teclas = {}
        self.puntos1, self.puntos2 = 0, 0
        self.punto_oro = False
        self.fin_partida = False
        self.ganador = ""
        self.jugando = False

        dif = getattr(self, "dificultad", "NORMAL")
        self._dif = dif
        self.tiempo_limite = 120
        self._v_pe = config.VELOCIDAD_PELOTA * config.DIF_VEL_PELOTA.get(dif, 1.0)
        self._v_or = config.VELOCIDAD_ORO * config.DIF_VEL_ORO.get(dif, 1.0)
        self._v_jg = config.VELOCIDAD_JUGADOR * config.DIF_VEL_JUGADOR.get(dif, 1.0)
        self._v_mx = config.VELOCIDAD_MAX * config.DIF_VEL_MAX.get(dif, 1.0)
        self._acl = config.ACELERACION * config.DIF_ACELERACION.get(dif, 1.0)
        self._spm = config.DIF_SPAWN_PODER.get(dif, 1.0)
        self._d_p = config.DIF_DUR_PODER.get(dif, 1.0)
        self._f_l = config.DIF_FACT_LENT.get(dif, config.FACTOR_LENTITUD)
        self._f_r = config.DIF_FACT_RAP.get(dif, config.FACTOR_RAPIDEZ)
        self._f_red = config.DIF_FACT_RED.get(dif, config.FACTOR_REDUCCION)
        self._alto_p = config.ALTO_PALA * config.DIF_ALTO_PALA.get(dif, 1.0)

        mitad = config.ALTO // 2
        self.j1 = pygame.Rect(30, mitad - self._alto_p // 2, config.ANCHO_PALA, self._alto_p)
        self.j2 = pygame.Rect(config.ANCHO - 50, mitad - self._alto_p // 2, config.ANCHO_PALA, self._alto_p)

        self.dx = self._v_pe
        self.dy = self._v_pe
        self.estela = deque(maxlen=10)
        self.shake_amp, self.shake_ticks = 0.0, 0

        # Poderes por jugador (0=J1, 1=J2): en el campo, en la mano y activo.
        self.campo_poder = [None, None]
        self.poder_mano = [None, None]
        self.poder_activo = [None, None]
        self.poder_ms = [0.0, 0.0]
        s1 = random.uniform(config.SPAWN_PODER_MIN, config.SPAWN_PODER_MAX) * 1000 * self._spm
        s2 = random.uniform(config.SPAWN_PODER_MIN, config.SPAWN_PODER_MAX) * 1000 * self._spm
        self.poder_spawn_ms = [s1, s2]

        # Efectos
        self.invertir_por_j = None
        self.invertir_ms = 0.0

        self._centrar_pelota()
        self._iniciar_cuenta()

    def _centrar_pelota(self):
        self.bx = config.ANCHO / 2 - 10
        self.by = config.ALTO / 2 - 10
        vel = self._v_or if getattr(self, "punto_oro", False) else getattr(self, "_v_pe", config.VELOCIDAD_PELOTA)
        self.dx = vel * random.choice([1, -1])
        self.dy = vel * random.choice([1, -1])
        self.estela.clear()

    def _iniciar_cuenta(self):
        self.jugando = False
        self.contador = 3
        self.cuenta_ms = 0
        self.mostrar_jueguen = False

    def _sacudir(self, amp):
        self.shake_amp = amp
        self.shake_ticks = 5

    def _offset_shake(self):
        if self.shake_ticks > 0:
            s = max(1, int(self.shake_amp * self.shake_ticks / 5))
            self.shake_ticks -= 1
            return (random.randint(-s, s), random.randint(-s, s))
        return (0, 0)

    def _ev_juego(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_w:
                self.teclas["w"] = True
            elif e.key == pygame.K_s:
                self.teclas["s"] = True
            elif e.key == pygame.K_UP:
                self.teclas["up"] = True
            elif e.key == pygame.K_DOWN:
                self.teclas["down"] = True
            elif e.key == pygame.K_q:
                self._activar_poder(0)
            elif e.key == pygame.K_RETURN:
                if self.fin_partida:
                    self._siguiente()
                else:
                    self._activar_poder(1)
        elif e.type == pygame.KEYUP:
            if e.key == pygame.K_w:
                self.teclas["w"] = False
            elif e.key == pygame.K_s:
                self.teclas["s"] = False
            elif e.key == pygame.K_UP:
                self.teclas["up"] = False
            elif e.key == pygame.K_DOWN:
                self.teclas["down"] = False
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.fin_partida:
            if self.rect_continuar and self.rect_continuar.collidepoint(e.pos):
                self._siguiente()

    def _upd_juego(self, dt):
        # Palas con movimiento continuo (se mueven tambien durante la cuenta).
        # Velocidades con habilidades: rapidez propia y lentitud del rival.
        vel1 = getattr(self, "_v_jg", config.VELOCIDAD_JUGADOR)
        vel2 = getattr(self, "_v_jg", config.VELOCIDAD_JUGADOR)
        f_r = getattr(self, "_f_r", config.FACTOR_RAPIDEZ)
        f_l = getattr(self, "_f_l", config.FACTOR_LENTITUD)
        f_red = getattr(self, "_f_red", config.FACTOR_REDUCCION)
        if self.poder_activo[0] == "rapidez":
            vel1 *= f_r
        if self.poder_activo[1] == "rapidez":
            vel2 *= f_r
        if self.poder_activo[1] == "lentitud":
            vel1 *= f_l
        if self.poder_activo[0] == "lentitud":
            vel2 *= f_l
        s1 = int(self.teclas.get("s", False))
        w1 = int(self.teclas.get("w", False))
        up2 = int(self.teclas.get("up", False))
        dn2 = int(self.teclas.get("down", False))
        if getattr(self, "invertir_ms", 0) > 0 and self.invertir_por_j == 0:
            s1, w1 = -s1, -w1
        if getattr(self, "invertir_ms", 0) > 0 and self.invertir_por_j == 1:
            up2, dn2 = -up2, -dn2
        vy1 = int((s1 - w1) * vel1)
        vy2 = int((dn2 - up2) * vel2)
        self.vy_pala1, self.vy_pala2 = vy1, vy2
        # Reduccion: achica la pala del rival de quien la activo (conserva el centro).
        alto_base = getattr(self, "_alto_p", config.ALTO_PALA)
        if self.poder_activo[0] == "muro":
            alto1 = int(alto_base * config.FACTOR_MURO)
        elif self.poder_activo[1] == "reduccion":
            alto1 = int(alto_base * f_red)
        else:
            alto1 = int(alto_base)
        if self.poder_activo[1] == "muro":
            alto2 = int(alto_base * config.FACTOR_MURO)
        elif self.poder_activo[0] == "reduccion":
            alto2 = int(alto_base * f_red)
        else:
            alto2 = int(alto_base)
        for pala, alto in ((self.j1, alto1), (self.j2, alto2)):
            if pala.h != alto:
                centro = pala.centery
                pala.h = alto
                pala.centery = centro
        self.j1.y += vy1
        self.j2.y += vy2
        self.j1.y = max(config.GROSOR_PARED, min(config.ALTO - config.GROSOR_PARED - self.j1.h, self.j1.y))
        self.j2.y = max(config.GROSOR_PARED, min(config.ALTO - config.GROSOR_PARED - self.j2.h, self.j2.y))

        if self.fin_partida:
            return

        # Cuenta regresiva (3-2-1-JUEGUEN o la del Punto de Oro).
        if not self.jugando:
            self.cuenta_ms += dt
            if self.mostrar_jueguen:
                if self.cuenta_ms >= 700:
                    self.jugando = True
                    self.tiempo_inicio = time.time()
            else:
                if self.cuenta_ms >= 1000:
                    self.contador -= 1
                    self.cuenta_ms = 0
                    if self.contador <= 0:
                        self.mostrar_jueguen = True
                        self._sonar("cuenta")
                    else:
                        self._sonar("cuenta")
            return

        # Reloj de la partida (no se muestra en Punto de Oro).
        if not self.punto_oro:
            restante = self.tiempo_limite - (time.time() - self.tiempo_inicio)
            if restante <= 0:
                if self.puntos1 == self.puntos2:
                    self._activar_oro()
                else:
                    self._terminar()
                return

        # Poderes: efectos activos, agarres y apariciones en el arco.
        self._upd_poderes(dt)

        # Congelar: la pelota permanece inmovil hasta agotar el efecto.
        if "congelar" not in (self.poder_activo[0], self.poder_activo[1]):
            self.bx += self.dx
            self.by += self.dy
            self._colisiones()
            self._actualizar_estela()

    def _actualizar_estela(self):
        self.estela.append((self.bx + 10, self.by + 10))

    # --- PODERES ---

    def _duracion_poder(self, tipo):
        d = getattr(self, "_d_p", 1.0)
        return {
            "congelar": config.DUR_CONGELAR * 1000 * d,
            "lentitud": config.DUR_LENTITUD * 1000 * d,
            "rapidez": config.DUR_RAPIDEZ * 1000 * d,
            "reduccion": config.DUR_REDUCCION * 1000 * d,
            "muro": config.DUR_MURO * 1000 * d,
            "invertir": config.DUR_INVERTIR * 1000 * d,
        }[tipo]

    def _upd_poderes(self, dt):
        # Efectos con temporizador
        if self.invertir_ms > 0:
            self.invertir_ms -= dt
            if self.invertir_ms <= 0:
                self.invertir_ms = 0.0
                self.invertir_por_j = None

        for i in (0, 1):
            # Enfriamiento del efecto activo (al agotarse queda libre la mano).
            if self.poder_activo[i] is not None:
                self.poder_ms[i] -= dt
                if self.poder_ms[i] <= 0:
                    # Limpiar efectos especiales al expirar
                    if self.poder_activo[i] == "muro":
                        alto_base = getattr(self, "_alto_p", config.ALTO_PALA)
                        pala = self.j1 if i == 0 else self.j2
                        centro = pala.centery
                        pala.h = int(alto_base)
                        pala.centery = centro
                        if pala.top < config.GROSOR_PARED:
                            pala.top = config.GROSOR_PARED
                        if pala.bottom > config.ALTO - config.GROSOR_PARED:
                            pala.bottom = config.ALTO - config.GROSOR_PARED
                    if self.poder_activo[i] == "invertir":
                        self.invertir_por_j = None
                        self.invertir_ms = 0.0
                    self.poder_activo[i] = None
                    self.poder_ms[i] = 0.0
                continue

            # Agarre: la pala que pase por encima se queda el poder.
            if self.campo_poder[i] is not None:
                pala = self.j1 if i == 0 else self.j2
                if pala.colliderect(self.campo_poder[i]["rect"]):
                    tipo = self.campo_poder[i]["tipo"]
                    self.campo_poder[i] = None
                    self.poder_mano[i] = tipo
                    self._sonar("poder")
                    self._sacudir(3)
                continue

            # Con un poder en la mano sin activar no aparece otro.
            if self.poder_mano[i] is not None:
                continue

            # Sin habilidad: cuenta para la siguiente aparicion aleatoria.
            self.poder_spawn_ms[i] -= dt
            if self.poder_spawn_ms[i] <= 0:
                self._spawn_poder(i)
                spm = getattr(self, "_spm", 1.0)
                self.poder_spawn_ms[i] = random.uniform(config.SPAWN_PODER_MIN,
                                                        config.SPAWN_PODER_MAX) * 1000 * spm

    def _spawn_poder(self, i):
        # En la columna de la pala, altura aleatoria dentro del arco.
        pala = self.j1 if i == 0 else self.j2
        lado = 46
        radio = lado // 2
        y = random.randint(config.GROSOR_PARED + radio,
                           config.ALTO - config.GROSOR_PARED - radio)
        rect = pygame.Rect(0, 0, lado, lado)
        rect.center = (pala.centerx, y)
        self.campo_poder[i] = {"rect": rect, "tipo": random.choice(list(PODERES))}

    def _activar_poder(self, i):
        if self.fin_partida or self.poder_mano[i] is None or self.poder_activo[i] is not None:
            return
        tipo = self.poder_mano[i]
        if tipo == "muro":
            pala = self.j1 if i == 0 else self.j2
            centro = pala.centery
            base = getattr(self, "_alto_p", config.ALTO_PALA)
            pala.h = int(base * config.FACTOR_MURO)
            pala.centery = centro
            if pala.top < config.GROSOR_PARED:
                pala.top = config.GROSOR_PARED
            if pala.bottom > config.ALTO - config.GROSOR_PARED:
                pala.bottom = config.ALTO - config.GROSOR_PARED
            self.poder_activo[i] = tipo
            self.poder_mano[i] = None
            self.poder_ms[i] = self._duracion_poder(tipo)
            self._sonar("activar")
            self._sacudir(4)
            return
        if tipo == "invertir":
            self.invertir_por_j = 1 - i  # Invierte controles del rival
            self.invertir_ms = self._duracion_poder(tipo)
            self.poder_activo[i] = tipo
            self.poder_mano[i] = None
            self.poder_ms[i] = self._duracion_poder(tipo)
            self._sonar("activar")
            self._sacudir(4)
            return

        self.poder_activo[i] = tipo
        self.poder_mano[i] = None
        self.poder_ms[i] = self._duracion_poder(tipo)
        self._sonar("activar")
        self._sacudir(4)

    def _colisiones(self):
        # Rebotes arriba/abajo.
        if self.by <= config.GROSOR_PARED:
            self.by = config.GROSOR_PARED
            self.dy = abs(self.dy)
            self._sonar("pared")
            self._sacudir(2)
        elif self.by + 20 >= config.ALTO - config.GROSOR_PARED:
            self.by = config.ALTO - config.GROSOR_PARED - 20
            self.dy = -abs(self.dy)
            self._sonar("pared")
            self._sacudir(2)

        pelota = pygame.Rect(int(self.bx), int(self.by), 20, 20)

        # Puntos (la pelota sale por izquierda o derecha).
        if self.bx > config.ANCHO:
            self.puntos1 += 1
            self._tras_punto()
            return
        if self.bx + 20 < 0:
            self.puntos2 += 1
            self._tras_punto()
            return

        # Rebote en palas con angulo segun el punto de impacto + spin.
        if pelota.colliderect(self.j1) and self.dx < 0:
            self._rebote_pala(self.j1, +1, self.vy_pala1)
        elif pelota.colliderect(self.j2) and self.dx > 0:
            self._rebote_pala(self.j2, -1, self.vy_pala2)

    def _rebote_pala(self, pala, direccion, vy_pala):
        # Centros flotantes para un calculo estable del angulo.
        centro_pelota = self.by + 10
        # Mitad de la pala REAL (puede estar reducida por el poder REC).
        mitad_pala = max(1.0, pala.h / 2)
        offset = (centro_pelota - pala.centery) / mitad_pala
        offset = max(-1.0, min(1.0, offset))
        angulo = offset * config.MAX_ANGULO

        acl = getattr(self, "_acl", config.ACELERACION)
        v_mx = getattr(self, "_v_mx", config.VELOCIDAD_MAX)
        vel = math.hypot(self.dx, self.dy) * acl
        vel = min(vel, v_mx)
        dx = vel * math.cos(angulo) * direccion
        dy = vel * math.sin(angulo) + vy_pala * 0.4  # Spin segun movimiento de la pala.

        # Renormalizamos a 'vel': el spin solo cambia la DIRECCION y nunca
        # resta velocidad. Cada golpe mantiene o acelera, jamas frena.
        magnitud = math.hypot(dx, dy)
        if magnitud > 0:
            self.dx = dx * vel / magnitud
            self.dy = dy * vel / magnitud
        else:
            self.dx = vel * direccion
            self.dy = 0.0

        # Sacamos la pelota del interior de la pala para evitar rebotes dobles.
        if direccion > 0:
            self.bx = pala.right
        else:
            self.bx = pala.left - 20
        self._sonar("pala")
        self._sacudir(4)

    def _tras_punto(self):
        self._sonar("punto")
        self._sacudir(8)
        if self.punto_oro:
            self._terminar()
            return
        self._centrar_pelota()

    def _activar_oro(self):
        self.punto_oro = True
        self._centrar_pelota()
        self._sacudir(10)
        self._sonar("oro")
        self._iniciar_cuenta()

    def _terminar(self):
        self.jugando = False
        self.fin_partida = True
        if self.puntos1 > self.puntos2:
            self.ganador = self.nombre1
        else:
            self.ganador = self.nombre2
        datos.guardar_partida(self.nombre_evento, self.nombre1, self.puntos1,
                              self.nombre2, self.puntos2, self.ganador)
        if self.modo == "torneo":
            self.ganadores.append(self.ganador)
        cx, cy = config.ANCHO // 2, config.ALTO // 2
        self.rect_continuar = pygame.Rect(0, 0, 260, 50)
        self.rect_continuar.center = (cx, cy + 90)

    def _siguiente(self):
        self.teclas = {}
        self.rect_continuar = None
        if self.modo == "amistoso":
            self.escena = "menu"
        else:
            if self.fase < 3:
                self.fase += 1
                self._crear_versus()
            else:
                self.escena = "menu"

    def _drw_juego(self, raton):
        ox, oy = self._offset_shake()

        # --- MUNDO (con shake) ---
        fondo = pygame.Surface((config.ANCHO, config.ALTO))
        fondo.fill(config.COLOR_FONDO)
        pygame.draw.rect(fondo, config.COLOR_LINEAS,
                         (ox, oy, config.ANCHO, config.GROSOR_PARED))
        pygame.draw.rect(fondo, config.COLOR_LINEAS,
                         (ox, config.ALTO - config.GROSOR_PARED + oy, config.ANCHO, config.GROSOR_PARED))
        for y in range(0, config.ALTO, 30):
            pygame.draw.line(fondo, config.COLOR_LINEAS,
                             (config.ANCHO // 2 + ox, oy + y),
                             (config.ANCHO // 2 + ox, oy + y + 15), 2)
        pygame.draw.rect(fondo, config.COLOR_J1, (self.j1.x + ox, self.j1.y + oy, self.j1.w, self.j1.h))
        pygame.draw.rect(fondo, config.COLOR_J2, (self.j2.x + ox, self.j2.y + oy, self.j2.w, self.j2.h))

        # Poderes esperando en el arco de cada jugador (pulso luminoso).
        for i in (0, 1):
            if self.campo_poder[i] is None:
                continue
            r = self.campo_poder[i]["rect"]
            nombre, color = PODERES[self.campo_poder[i]["tipo"]]
            pulso = 0.5 + 0.5 * math.sin(time.time() * 5)
            radio = r.w // 2
            pygame.draw.circle(fondo, color, (r.centerx + ox, r.centery + oy), radio + int(8 * pulso), 8)
            pygame.draw.circle(fondo, "#0c0c0c", (r.centerx + ox, r.centery + oy), radio - 12)
            try:
                icono = getattr(self, "_iconos", {}).get(self.campo_poder[i]["tipo"])
                if icono:
                    ir = icono.get_rect()
                    ir.center = (r.centerx + ox, r.centery + oy)
                    try:
                        fondo.blit(icono, ir)
                    except Exception:
                        fondo.blit(icono, ir)
                else:
                    img = self.f_peque.render(nombre, True, color)
                    fondo.blit(img, img.get_rect(center=(r.centerx + ox, r.centery + oy)))
            except Exception:
                try:
                    img = self.f_peque.render(nombre, True, color)
                    fondo.blit(img, img.get_rect(center=(r.centerx + ox, r.centery + oy)))
                except Exception:
                    pass

        # Estela con alfa real (surface SRCALPHA).
        capa = pygame.Surface((config.ANCHO, config.ALTO), pygame.SRCALPHA)
        color_base = (255, 0, 0) if self.punto_oro else (255, 255, 255)
        n = len(self.estela)
        for i, (x, y) in enumerate(self.estela):
            a = int(150 * (i + 1) / max(n, 1))
            pygame.draw.circle(capa, (*color_base, a), (int(x) + ox, int(y) + oy), 10)
        fondo.blit(capa, (0, 0))

        # Pelota congelada (poder CONG): tinte y halo de hielo.
        congelada = "congelar" in (self.poder_activo[0], self.poder_activo[1])
        if congelada:
            color_pelota = PODERES["congelar"][1]
        else:
            color_pelota = config.COLOR_PUNTO_ORO if self.punto_oro else config.COLOR_BLANCO
        if congelada:
            pygame.draw.circle(fondo, PODERES["congelar"][1], (int(self.bx) + 10 + ox, int(self.by) + 10 + oy), 17, 2)
        pygame.draw.ellipse(fondo, color_pelota,
                            (int(self.bx) + ox, int(self.by) + oy, 20, 20))
        self.pantalla.blit(fondo, (0, 0))

        # Tinte rojo pulsante durante el Punto de Oro.
        if self.punto_oro:
            tinte = pygame.Surface((config.ANCHO, config.ALTO), pygame.SRCALPHA)
            alfa = int(40 + 30 * math.sin(time.time() * 6))
            tinte.fill((180, 0, 0, alfa))
            self.pantalla.blit(tinte, (0, 0))

        # --- HUD (estable, sin shake) ---
        self._texto(f"{self.puntos1} - {self.puntos2}", self.f_marcador, "white",
                    (config.ANCHO // 2, 55))
        self._drw_hud_poder(0, 30)    # J1: tecla Q.
        self._drw_hud_poder(1, config.ANCHO - 30)  # J2: tecla ENTER.
        dif = getattr(self, "_dif", getattr(self, "dificultad", "NORMAL"))
        self._texto(f"DIFICULTAD: {dif}", self.f_peque, COLOR_AMARILLO, (config.ANCHO // 2, 85))
        dif = getattr(self, "_dif", getattr(self, "dificultad", "NORMAL"))
        self._texto(f"DIFICULTAD: {dif}", self.f_peque, COLOR_AMARILLO, (config.ANCHO // 2, 85))
        if self.punto_oro:
            self._texto("PUNTO DE ORO!", self.f_sub, COLOR_ROJO, (config.ANCHO // 2, 115))
        elif self.jugando:
            restante = max(0, self.tiempo_limite - (time.time() - self.tiempo_inicio))
            self._texto(f"{int(restante // 60)}:{int(restante % 60):02d}", self.f_sub, COLOR_AMARILLO,
                        (config.ANCHO // 2, config.ALTO - 40))

        # Cuenta regresiva / JUEGUEN.
        if not self.jugando and not self.fin_partida:
            if self.mostrar_jueguen:
                self._texto("JUEGUEN!", self.f_sub, "yellow", (config.ANCHO // 2, config.ALTO // 2))
            else:
                self._texto(str(self.contador), self.f_cuenta, "white", (config.ANCHO // 2, config.ALTO // 2))

        # Pantalla de ganador.
        if self.fin_partida:
            self._texto(f"GANADOR: {self.ganador}", self.f_titulo, COLOR_AMARILLO,
                        (config.ANCHO // 2, config.ALTO // 2 - 30))
            pygame.draw.rect(self.pantalla, COLOR_VERDE, self.rect_continuar, border_radius=8)
            img = self.f_normal.render("CONTINUAR", True, "white")
            self.pantalla.blit(img, img.get_rect(center=self.rect_continuar.center))

    def _drw_hud_poder(self, i, x_anc):
        # Muestra el poder en mano (con su tecla) o el activo con barra de tiempo.
        tecla = "Q" if i == 0 else "ENTER"
        if self.poder_activo[i] is not None:
            nombre, color = PODERES[self.poder_activo[i]]
            restante = max(0.0, self.poder_ms[i] / 1000)
            img = self.f_peque.render(f"{nombre} {restante:.1f}s", True, color)
            rect = img.get_rect()
            if i == 0:
                rect.midleft = (x_anc, 95)
            else:
                rect.midright = (x_anc, 95)
            self.pantalla.blit(img, rect)
            try:
                icono = getattr(self, "_iconos", {}).get(self.poder_activo[i])
                if icono:
                    ir = icono.get_rect()
                    if i == 0:
                        ir.midleft = (rect.right + 30, rect.centery)
                    else:
                        ir.midright = (rect.left - 30, rect.centery)
                    self.pantalla.blit(icono, ir)
            except Exception:
                pass
            # Barra proporcional del tiempo restante.
            total = self._duracion_poder(self.poder_activo[i])
            ancho = 110
            barra = pygame.Rect(0, 0, ancho, 5)
            if i == 0:
                barra.midleft = (x_anc, rect.bottom + 5)
            else:
                barra.midright = (x_anc, rect.bottom + 5)
            pygame.draw.rect(self.pantalla, "#333333", barra, border_radius=3)
            lleno = pygame.Rect(barra.x, barra.y, int(ancho * self.poder_ms[i] / total), 5)
            pygame.draw.rect(self.pantalla, color, lleno, border_radius=3)
        elif self.poder_mano[i] is not None:
            nombre, color = PODERES[self.poder_mano[i]]
            parpadeo = (int(time.time() * 3) % 2 == 0)
            if parpadeo:
                img = self.f_peque.render(f"[{tecla}] {nombre}", True, color)
                rect = img.get_rect()
                if i == 0:
                    rect.midleft = (x_anc, 95)
                else:
                    rect.midright = (x_anc, 95)
                self.pantalla.blit(img, rect)
            try:
                icono = getattr(self, "_iconos", {}).get(self.poder_mano[i])
                if icono:
                    ir = icono.get_rect()
                    if i == 0:
                        ir.midleft = (rect.right + 30, rect.centery)
                    else:
                        ir.midright = (rect.left - 30, rect.centery)
                    self.pantalla.blit(icono, ir)
            except Exception:
                pass

    # --- RESULTADOS ---

    def _crear_resultados(self):
        self.escena = "resultados"
        self.tab_res = "Amistoso"
        self.lista_res = datos.leer_historial(self.tab_res)
        cx = config.ANCHO // 2
        self.btn_tab_am = Boton(cx - 140, 50, 180, 40, "Amistosos", COLOR_AZUL, self.f_normal)
        self.btn_tab_to = Boton(cx + 140, 50, 180, 40, "Torneos", COLOR_AZUL, self.f_normal)
        self.btn_borrar = Boton(cx - 100, config.ALTO - 40, 180, 40, "BORRAR", COLOR_ROJO, self.f_normal)
        self.btn_atras = Boton(cx + 100, config.ALTO - 40, 180, 40, "ATRAS", COLOR_GRIS, self.f_normal)

    def _ev_resultados(self, e):
        if e.type != pygame.MOUSEBUTTONDOWN or e.button != 1:
            return
        if self.btn_tab_am.clic(e.pos):
            self.tab_res = "Amistoso"
            self.lista_res = datos.leer_historial(self.tab_res)
        elif self.btn_tab_to.clic(e.pos):
            self.tab_res = "Torneo"
            self.lista_res = datos.leer_historial(self.tab_res)
        elif self.btn_borrar.clic(e.pos):
            datos.borrar_todo()
            self.lista_res = []
        elif self.btn_atras.clic(e.pos):
            self.escena = "menu"

    def _drw_resultados(self, raton):
        cx = config.ANCHO // 2
        self._texto("RESULTADOS", self.f_titulo, "white", (cx, 120))
        self.btn_tab_am.dibujar(self.pantalla, raton)
        self.btn_tab_to.dibujar(self.pantalla, raton)

        # Pestaña activa resaltada.
        activo = self.btn_tab_am if self.tab_res == "Amistoso" else self.btn_tab_to
        pygame.draw.rect(self.pantalla, "white", activo.rect, 2, border_radius=8)

        # Tabla dibujada a mano.
        cols = ["EVENTO", "J1", "PUNTOS", "J2", "GANADOR"]
        anchos = [140, 180, 90, 180, 180]
        x0 = cx - sum(anchos) // 2
        y = 170
        x = x0
        for titulo, w in zip(cols, anchos):
            self._texto(titulo, self.f_peque, COLOR_AMARILLO, (x + w // 2, y), centro=True)
            x += w
        y += 12
        pygame.draw.line(self.pantalla, COLOR_BORDE, (x0, y), (x0 + sum(anchos), y))
        y += 18

        for p in self.lista_res:
            if y > config.ALTO - 90:
                self._texto("...", self.f_peque, "white", (cx, y))
                break
            valores = [p["evento"], p["jugador1"], f"{p['puntos1']}-{p['puntos2']}",
                       p["jugador2"], p["ganador"]]
            x = x0
            for valor, w in zip(valores, anchos):
                self._texto(valor, self.f_peque, "white", (x + w // 2, y), centro=True)
                x += w
            y += 28

        u = datos.contar_jugadores_unicos()
        self._texto(f"Jugadores distintos: {u}", self.f_normal, "white", (cx, config.ALTO - 100))
        self.btn_borrar.dibujar(self.pantalla, raton)
        self.btn_atras.dibujar(self.pantalla, raton)
