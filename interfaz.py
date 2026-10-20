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
        self.inp1 = EntradaTexto(cx, cy - 40, 320, 44, "JUGADOR 1", self.f_normal)
        self.inp2 = EntradaTexto(cx, cy + 20, 320, 44, "JUGADOR 2", self.f_normal)
        self.btn_comenzar = Boton(cx, cy + 100, 260, 48, "COMENZAR", COLOR_VERDE, self.f_normal)
        self.btn_atras = Boton(cx, cy + 160, 260, 44, "ATRAS", COLOR_GRIS, self.f_normal)

    def _ev_amistoso(self, e):
        self.inp1.manejar(e)
        self.inp2.manejar(e)
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self._configurar_amistoso()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
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
        self._texto("PARTIDO AMISTOSO", self.f_titulo, "white", (cx, cy - 160))
        self._texto("NOMBRES DE JUGADORES", self.f_sub, COLOR_AMARILLO, (cx, cy - 90))
        self.inp1.dibujar(self.pantalla)
        self.inp2.dibujar(self.pantalla)
        self.btn_comenzar.dibujar(self.pantalla, raton)
        self.btn_atras.dibujar(self.pantalla, raton)

    # --- TORNEO ---

    def _crear_torneo(self):
        self.escena = "torneo"
        cx, cy = config.ANCHO // 2, config.ALTO // 2
        self.cajas = []
        for i in range(4):
            self.cajas.append(EntradaTexto(cx, cy - 80 + i * 52, 320, 40, f"Equipo {i + 1}", self.f_normal))
        self.btn_iniciar = Boton(cx, cy + 160, 260, 48, "INICIAR COPA", COLOR_AMARILLO, self.f_normal)
        self.btn_atras = Boton(cx, cy + 220, 260, 44, "ATRAS", COLOR_GRIS, self.f_normal)

    def _ev_torneo(self, e):
        for c in self.cajas:
            c.manejar(e)
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self._configurar_torneo()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
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
        self._texto("TORNEO", self.f_titulo, "white", (cx, cy - 180))
        self._texto("COPA (4 EQUIPOS)", self.f_sub, COLOR_AMARILLO, (cx, cy - 120))
        for c in self.cajas:
            c.dibujar(self.pantalla)
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
        self.tiempo_limite = 60
        self.jugando = False

        mitad = config.ALTO // 2
        self.j1 = pygame.Rect(30, mitad - config.ALTO_PALA // 2, config.ANCHO_PALA, config.ALTO_PALA)
        self.j2 = pygame.Rect(config.ANCHO - 50, mitad - config.ALTO_PALA // 2, config.ANCHO_PALA, config.ALTO_PALA)

        self.dx = config.VELOCIDAD_PELOTA
        self.dy = config.VELOCIDAD_PELOTA
        self.estela = deque(maxlen=10)
        self.shake_amp, self.shake_ticks = 0.0, 0
        self._centrar_pelota()
        self._iniciar_cuenta()

    def _centrar_pelota(self):
        self.bx = config.ANCHO / 2 - 10
        self.by = config.ALTO / 2 - 10
        vel = config.VELOCIDAD_ORO if self.punto_oro else config.VELOCIDAD_PELOTA
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
            elif e.key == pygame.K_RETURN and self.fin_partida:
                self._siguiente()
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
        vy1 = (int(self.teclas.get("s", False)) - int(self.teclas.get("w", False))) * config.VELOCIDAD_JUGADOR
        vy2 = (int(self.teclas.get("down", False)) - int(self.teclas.get("up", False))) * config.VELOCIDAD_JUGADOR
        self.vy_pala1, self.vy_pala2 = vy1, vy2
        self.j1.y += vy1
        self.j2.y += vy2
        limite_inf = config.ALTO - config.GROSOR_PARED - config.ALTO_PALA
        self.j1.y = max(config.GROSOR_PARED, min(limite_inf, self.j1.y))
        self.j2.y = max(config.GROSOR_PARED, min(limite_inf, self.j2.y))

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

        self.bx += self.dx
        self.by += self.dy
        self._colisiones()
        self._actualizar_estela()

    def _actualizar_estela(self):
        self.estela.append((self.bx + 10, self.by + 10))

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
        offset = (centro_pelota - pala.centery) / (config.ALTO_PALA / 2)
        offset = max(-1.0, min(1.0, offset))
        angulo = offset * config.MAX_ANGULO

        vel = math.hypot(self.dx, self.dy) * config.ACELERACION
        vel = min(vel, config.VELOCIDAD_MAX)
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

        # Estela con alfa real (surface SRCALPHA).
        capa = pygame.Surface((config.ANCHO, config.ALTO), pygame.SRCALPHA)
        color_base = (255, 0, 0) if self.punto_oro else (255, 255, 255)
        n = len(self.estela)
        for i, (x, y) in enumerate(self.estela):
            a = int(150 * (i + 1) / max(n, 1))
            pygame.draw.circle(capa, (*color_base, a), (int(x) + ox, int(y) + oy), 10)
        fondo.blit(capa, (0, 0))

        pygame.draw.ellipse(fondo, config.COLOR_PUNTO_ORO if self.punto_oro else config.COLOR_BLANCO,
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
        if self.punto_oro:
            self._texto("PUNTO DE ORO!", self.f_sub, COLOR_ROJO, (config.ANCHO // 2, 105))
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
