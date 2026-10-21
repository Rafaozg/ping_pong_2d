# --- MANDOS (gamepads PS3 y compatibles, USB y Bluetooth) ---
# Detecta mandos por orden de conexion (slot 0 = Jugador 1, slot 1 = Jugador 2),
# normaliza su estado (stick, D-pad, Cruce/Circulo) y convierte los bordes de
# los botones en acciones de UI. Primero se usa la API GameController de SDL
# (mapa canonico del propio SDL para PS3); si no hay mapa se cae al joystick
# crudo (ejes y botones por indice, configurable en config.py).

import pygame

try:
    from pygame._sdl2 import controller as _ctrl
except Exception:  # pygame sin soporte SDL2: solo joystick crudo.
    _ctrl = None

import config


class Mando:
    """Estado normalizado de un mando conectado."""

    def __init__(self, nombre, iid, joy=None, ctrl=None, eje_y_offset=0.0):
        self.nombre = nombre
        self.iid = iid
        self.joy = joy
        self.ctrl = ctrl
        self.jugador = None
        self.eje_y = 0.0
        self.eje_y_offset = eje_y_offset  # Centro calibrado al conectar
        self.up = False
        self.dn = False
        self.acciones = []
        self.nav_prev = 0
        self.nav_ms = 0.0
        self.nav_espera = 0.0

    @property
    def dpad(self):
        # -1 arriba, 0 quieto, +1 abajo.
        if self.up and not self.dn:
            return -1
        if self.dn and not self.up:
            return 1
        return 0


class Mandos:
    """Gestiona hasta 2 mandos; los mensajes de conexion salen por drenar_mensajes."""

    def __init__(self):
        self.ctrl_ok = False
        if _ctrl is not None:
            try:
                _ctrl.init()
                self.ctrl_ok = bool(_ctrl.get_init())
                _ctrl.set_eventstate(True)
            except Exception:
                self.ctrl_ok = False
        try:
            if not pygame.joystick.get_init():
                pygame.joystick.init()
        except Exception:
            pass
        self.slots = [None, None]
        self._por_iid = {}
        self._mensajes = []
        self.abrir_todos()

    # --- CONEXION / DESCONEXION ---

    def abrir_todos(self):
        # Al arrancar abrimos lo que ya este enchufado (ademas de JOYDEVICEADDED).
        try:
            n = pygame.joystick.get_count()
        except Exception:
            n = 0
        for i in range(n):
            self._abrir(i)

    def _abrir(self, device_index):
        try:
            joy = pygame.joystick.Joystick(device_index)
            joy.init()
        except pygame.error:
            return
        iid = joy.get_instance_id()
        if iid in self._por_iid:
            return
        ctrl = None
        eje_y_inicial = 0.0
        if self.ctrl_ok and _ctrl is not None:
            try:
                ctrl = _ctrl.Controller.from_joystick(joy)
            except Exception:
                ctrl = None
        # Leer estado inicial del eje Y para calibrar el centro (evita drift al conectar).
        # Los mandos PS3 suelen reportar ±1.0 al conectar; solo usamos el valor
        # si está cerca del centro real (|v| < 0.2), si no, offset = 0.
        try:
            if ctrl is not None:
                eje_y_inicial = ctrl.get_axis(pygame.CONTROLLER_AXIS_LEFTY)
            else:
                eje_y_inicial = joy.get_axis(config.MANDO_EJE_Y)
        except Exception:
            eje_y_inicial = 0.0
        if abs(eje_y_inicial) >= 0.2:
            eje_y_inicial = 0.0
        self._alta(joy.get_name(), iid, joy, ctrl, eje_y_inicial)

    def _alta(self, nombre, iid, joy=None, ctrl=None, eje_y_offset=0.0):
        slot = next((i for i, m in enumerate(self.slots) if m is None), None)
        if slot is None:
            return None
        m = Mando(nombre, iid, joy, ctrl, eje_y_offset)
        m.jugador = slot
        self.slots[slot] = m
        self._por_iid[iid] = m
        self._mensajes.append(f"MANDO {slot + 1} CONECTADO: {nombre}")
        return m

    def _baja(self, iid):
        m = self._por_iid.pop(iid, None)
        if m is None:
            return
        if m.jugador is not None:
            self.slots[m.jugador] = None
        if m.ctrl is not None:
            try:
                m.ctrl.quit()
            except Exception:
                pass
        self._mensajes.append(f"MANDO {m.jugador + 1} DESCONECTADO")

    # --- EVENTOS ---

    @staticmethod
    def _iid(e):
        # JOY/CONTROLLER usan instance_id (joy/which son alias antiguos).
        for k in ("instance_id", "joy", "which"):
            v = getattr(e, k, None)
            if v is not None:
                return v
        return None

    def procesar(self, e):
        t = e.type
        if t == pygame.JOYDEVICEADDED:
            self._abrir(getattr(e, "device_index", 0))
            return
        if t in (pygame.JOYDEVICEREMOVED, pygame.CONTROLLERDEVICEREMOVED):
            self._baja(self._iid(e))
            return
        iid = self._iid(e)
        if iid is None:
            return
        m = self._por_iid.get(iid)
        if m is None:
            return
        if t in (pygame.CONTROLLERAXISMOTION, pygame.CONTROLLERBUTTONDOWN,
                 pygame.CONTROLLERBUTTONUP):
            if m.ctrl is None:
                return
            self._ctrl_evento(m, e)
        elif t in (pygame.JOYAXISMOTION, pygame.JOYBUTTONDOWN,
                   pygame.JOYBUTTONUP, pygame.JOYHATMOTION):
            if m.ctrl is not None:
                return  # Con mapa canonico solo se atiende el flujo CONTROLLER.
            self._joy_evento(m, e)

    def _ctrl_evento(self, m, e):
        t = e.type
        if t == pygame.CONTROLLERAXISMOTION:
            if e.axis == pygame.CONTROLLER_AXIS_LEFTY:
                m.eje_y = max(-1.0, min(1.0, float(e.value)))
        elif t == pygame.CONTROLLERBUTTONDOWN:
            b = e.button
            if b == pygame.CONTROLLER_BUTTON_A:          # Cruce
                m.acciones.append("aceptar")
            elif b == pygame.CONTROLLER_BUTTON_B:        # Circulo
                m.acciones.append("volver")
            elif b == pygame.CONTROLLER_BUTTON_DPAD_UP:
                m.up = True
            elif b == pygame.CONTROLLER_BUTTON_DPAD_DOWN:
                m.dn = True
        elif t == pygame.CONTROLLERBUTTONUP:
            b = e.button
            if b == pygame.CONTROLLER_BUTTON_DPAD_UP:
                m.up = False
            elif b == pygame.CONTROLLER_BUTTON_DPAD_DOWN:
                m.dn = False

    def _joy_evento(self, m, e):
        t = e.type
        if t == pygame.JOYAXISMOTION:
            if e.axis == config.MANDO_EJE_Y:
                m.eje_y = max(-1.0, min(1.0, float(e.value)))
        elif t == pygame.JOYHATMOTION:
            if getattr(e, "hat", 0) == 0:
                y = e.value[1]
                m.up = y > 0
                m.dn = y < 0
        elif t == pygame.JOYBUTTONDOWN:
            if e.button == config.MANDO_BTN_ACEPTAR:
                m.acciones.append("aceptar")
            elif e.button == config.MANDO_BTN_VOLVER:
                m.acciones.append("volver")

    # --- ESTADO CONTINUO Y ACCIONES ---

    @staticmethod
    def _nav_dir(m):
        # Direccion de navegacion de menus (D-pad primero, si no stick con umbral).
        if m.dpad != 0:
            return m.dpad
        if m.eje_y <= -config.MANDO_EJE_NAV:
            return -1
        if m.eje_y >= config.MANDO_EJE_NAV:
            return 1
        return 0

    def actualizar(self, dt):
        # Repeticion de la seleccion al mantener stick/D-pad en los menus.
        for m in self.slots:
            if m is None:
                continue
            d = self._nav_dir(m)
            if d != 0 and d != m.nav_prev:
                m.nav_ms = 0.0
                m.nav_espera = config.MANDO_NAV_INICIAL
                self._encolar_nav(m, d)
            elif d != 0:
                m.nav_ms += dt
                if m.nav_ms >= m.nav_espera:
                    m.nav_ms = 0.0
                    m.nav_espera = config.MANDO_NAV_REPETIR
                    self._encolar_nav(m, d)
            else:
                m.nav_ms = 0.0
                m.nav_espera = config.MANDO_NAV_INICIAL
            m.nav_prev = d

    @staticmethod
    def _encolar_nav(m, d):
        m.acciones.append("nav_up" if d < 0 else "nav_down")

    def direccion(self, i):
        if not (0 <= i < 2) or self.slots[i] is None:
            return 0.0
        m = self.slots[i]
        if m.dpad != 0:
            return float(m.dpad)
        v = m.eje_y - m.eje_y_offset
        a = abs(v)
        dz = config.MANDO_DEADZONE
        if a < dz:
            return 0.0
        return (1.0 if v > 0 else -1.0) * (a - dz) / (1.0 - dz)

    def drenar(self):
        # Acciones acumuladas: lista de (jugador, accion) ya consumidas.
        out = []
        for m in self.slots:
            if m is None or not m.acciones:
                continue
            for acc in m.acciones:
                out.append((m.jugador, acc))
            m.acciones.clear()
        return out

    def drenar_mensajes(self):
        msgs = self._mensajes[:]
        self._mensajes.clear()
        return msgs

    def tiene(self, i):
        return 0 <= i < 2 and self.slots[i] is not None

    def conectados(self):
        return sum(1 for m in self.slots if m is not None)
