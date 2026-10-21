# AGENTS.md

## Qué es

Juego de Ping Pong 2D en Python con `pygame`. Sin tests, sin linter, sin CI.

## Cómo ejecutar

```bash
source .venv/bin/activate && python main.py
```

- El entorno virtual `.venv` ya existe. Si falta: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- `pygame` se instala solo con pip (sin paquetes apt). `datos.py` no cambió respecto a la versión ttkbootstrap.
- La app es GUI y bloquea el mainloop. Para probar sin bloquear la terminal: `timeout 10 python main.py` (exit 124 = arrancó bien). En WSL con ALSA sin dispositivo aparecen avisos `snd_pcm_dmix_open` en stderr; el juego los tolera y corre en silencio.

## Estructura

- `main.py` — punto de entrada (instancia `interfaz.Juego` y llama `run()`).
- `interfaz.py` — toda la UI (menús, entradas de texto, tabla de resultados) y la lógica del juego en una máquina de escenas (`menu`, `amistoso`, `torneo`, `versus`, `juego`, `resultados`). La navegación de menús con mando vive en `_mando_accion`/`_foco_activar`/`_elementos_foco`.
- `mandos.py` — gestión de mandos (clase `Mandos`): detección/hotplug, asignación por orden de conexión (slot 0 = J1, slot 1 = J2), estado normalizado (stick con zona muerta, D-pad, Cruce/Circulo) y acciones de UI con repetición de navegación.
- `config.py` — constantes (dimensiones, colores, velocidades a 60 FPS, ajustes de mando en `MANDO_*`). `ANCHO`/`ALTO` se sobreescriben en runtime al tamaño del monitor real.
- `datos.py` — persistencia CSV en `partidos_resultados.csv` (sin cambios, independiente de la librería gráfica).

## Convenciones y gotchas

- Comentarios y UI en español; mantener ese idioma.
- `partidos_resultados.csv` está en `.gitignore` (historial local). Se crea/vacía en runtime; no commitear.
- La ventana es fullscreen; `Escape` la cierra (enlazado en el bucle de eventos de `Juego.run`).
- El fondo es `#060606` explícito (evita cancha blanca en WSL).
- El bucle corre a `config.FPS = 60` con `clock.tick`; las velocidades en `config.py` son px/frame.
- Sonido: beeps generados en runtime con la stdlib `wave` (sin numpy ni assets). Si `mixer.init()` falla (WSL sin audio), el juego sigue en silencio (`audio_ok = False`).
- La lógica de física (`_colisiones`, `_rebote_pala`) aplica aceleración por golpe y ángulo según impacto; el "Punto de Oro" es el desempate por empate al terminar el tiempo.

## Mandos (PS3 y compatibles)

- Controles: stick/D-pad mueven la pala y navegan menús, **Cruce (A)** = aceptar/activar poder, **Círculo (B)** = volver. En partida el teclado sigue funcionando a la vez (W/S + flechas + Q/Enter).
- Se usa la API GameController de SDL (`pygame._sdl2.controller`, con mapa PS3 incluido en la gamecontrollerdb de SDL, USB y Bluetooth); si no hay mapa se cae al joystick crudo (`MANDO_EJE_Y`, `MANDO_BTN_ACEPTAR`, `MANDO_BTN_VOLVER` en `config.py`).
- USB y Bluetooth funcionan igual para SDL; para Bluetooth hay que emparejar el mando antes con `bluetoothctl` (o el menú de KDE). El mando PS3 por Bluetooth necesita los módulos del kernel `hid-sony` o `hid-playstation`.
- **Permisos**: el usuario debe estar en el grupo `input` para leer `/dev/input` (`sudo usermod -aG input $USER` y volver a entrar). Sin eso SDL no ve los mandos y el juego sigue solo con teclado.
- Verificación sin hardware: baterías ad-hoc con eventos sintéticos SDL (`CONTROLLERBUTTONDOWN`, `JOYAXISMOTION`, `JOYDEVICEADDED/REMOVED`...) bajo `SDL_VIDEODRIVER=dummy` con `config.ARCHIVO` apuntado a un temporal (nunca al CSV real). Ej.: `PYTHONPYCACHEPREFIX=/tmp/pycache python -B /tmp/opencode/test_mandos.py` (44 aserciones) y `test_regresion.py` (48 aserciones).
