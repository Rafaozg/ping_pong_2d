import ttkbootstrap as ttk      # Libreria para botones modernos.
from ttkbootstrap.constants import * # Constantes de estilo.
from tkinter import Canvas, messagebox # Canvas para dibujar, Alertas para errores.
import time                     # Para el reloj.
import random                   # Para el azar.
import config                   # Nuestras constantes.
import datos                    # Nuestra base de datos.

class VentanaJuego:
    def __init__(self, ventana_principal):
        self.ventana = ventana_principal
        self.ventana.title("PING PONG 2D") # Titulo de la ventana.
        
        # --- PANTALLA COMPLETA COMPATIBLE CON WSL Y WINDOWS ---
        self.ventana.update_idletasks()
        ancho_monitor = self.ventana.winfo_screenwidth()
        alto_monitor = self.ventana.winfo_screenheight()
        
        # Ajustamos config al monitor real.
        config.ANCHO = ancho_monitor
        config.ALTO = alto_monitor
        
        self.ventana.geometry(f"{config.ANCHO}x{config.ALTO}+0+0")
        self.ventana.attributes('-fullscreen', True)
        self.ventana.bind("<Escape>", lambda event: self.ventana.destroy())
        
        # --- VARIABLES DEL JUEGO ---
        self.jugando = False       
        self.modo = "amistoso"     # Tipo de partida.
        self.nombre_evento = ""    # Nombre para guardar (ej. Torneo 1).
        self.tiempo_limite = 60    # Tiempo de la partida.
        self.puntos1 = 0           # Puntos J1.
        self.puntos2 = 0           # Puntos J2.
        self.punto_oro_activo = False # Variable para "Punto de Oro".
        
        # Variables de torneo.
        self.fase = 0
        self.equipos = []
        self.ganadores = []
        
        # Velocidad pelota.
        self.dx = config.VELOCIDAD_PELOTA
        self.dy = config.VELOCIDAD_PELOTA

        self.crear_menu()
        
        # Canvas sin bordes y con fondo oscuro explicito para evitar color blanco en WSL.
        self.canvas = Canvas(
            self.ventana,
            width=config.ANCHO,
            height=config.ALTO,
            highlightthickness=0,
            bg=config.COLOR_FONDO
        )

    # --- MENUS ---

    def crear_menu(self):
        # Limpiamos pantalla completa.
        for w in self.ventana.winfo_children():
            w.place_forget()
            w.pack_forget()

        # Marco del menu centrado.
        self.frame_menu = ttk.Frame(self.ventana)
        self.frame_menu.place(relx=0.5, rely=0.5, anchor="center")

        # Titulo Ping Pong.
        ttk.Label(self.frame_menu, text="🏓 PING PONG 2D 🏓", font=("Impact", 40)).pack(pady=30)
        
        ttk.Button(self.frame_menu, text="JUGAR AMISTOSO🏓", width=25, bootstyle=SUCCESS, command=self.vista_amistoso).pack(pady=10)
        ttk.Button(self.frame_menu, text="MODO TORNEO🏆", width=25, bootstyle=WARNING, command=self.vista_torneo).pack(pady=10)
        ttk.Button(self.frame_menu, text="VER RESULTADOS📊", width=25, bootstyle=INFO, command=self.vista_resultados).pack(pady=10)
        ttk.Button(self.frame_menu, text="CERRAR JUEGO", width=25, bootstyle=DANGER, command=self.ventana.destroy).pack(pady=10)

    def vista_amistoso(self):
        self.frame_menu.place_forget()
        self.frame_config = ttk.Frame(self.ventana)
        self.frame_config.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(self.frame_config, text="🏓PARTIDO AMISTOSO🏓", font=("Impact", 30, "bold")).pack(pady=5)
        ttk.Label(self.frame_config, text="NOMBRES DE JUGADORES", font=("Arial", 14, "bold")).pack(pady=15)
        
        self.input1 = ttk.Entry(self.frame_config, font=("Arial", 12))
        self.input1.pack(pady=5)
        self.input1.insert(0, "JUGADOR 1")
        
        self.input2 = ttk.Entry(self.frame_config, font=("Arial", 12))
        self.input2.pack(pady=5)
        self.input2.insert(0, "JUGADOR 2")
        
        self.ventana.bind('<Return>', lambda event: self.configurar_amistoso())
        
        ttk.Button(self.frame_config, text="COMENZAR", bootstyle=SUCCESS, command=self.configurar_amistoso).pack(pady=20)
        ttk.Button(self.frame_config, text="ATRAS", bootstyle=SECONDARY, command=self.volver_menu_desde_config).pack()

    def volver_menu_desde_config(self):
        self.ventana.unbind('<Return>')
        self.crear_menu()

    def configurar_amistoso(self):
        n1 = self.input1.get()
        n2 = self.input2.get()
        
        # Validaciones de nombres.
        if n1.strip() == "" or n2.strip() == "":
            messagebox.showerror("Error", "¡Los nombres no pueden estar vacios!")
            return 
        if n1.strip().lower() == n2.strip().lower():
            messagebox.showerror("Error", "¡Nombres iguales no permitidos!")
            return 
            
        self.ventana.unbind('<Return>')
        
        numero = datos.obtener_siguiente_numero("Amistoso")
        self.nombre_evento = f"Amistoso {numero}"
        
        self.modo = "amistoso"
        self.nombre1 = n1
        self.nombre2 = n2
        self.tiempo_limite = 60 
        
        self.frame_config.place_forget()
        self.preparar_partido()

    def vista_torneo(self):
        self.frame_menu.place_forget()
        self.frame_torneo = ttk.Frame(self.ventana)
        self.frame_torneo.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(self.frame_torneo, text="🏆TORNEO🏆", font=("Impact", 30, "bold")).pack(pady=5)
        ttk.Label(self.frame_torneo, text="COPA (4 EQUIPOS)", font=("Impact", 14, "bold")).pack(pady=15)
        
        self.cajas = []
        for i in range(4):
            c = ttk.Entry(self.frame_torneo)
            c.pack(pady=3)
            c.insert(0, f"Equipo {i+1}")
            self.cajas.append(c)
            
        self.ventana.bind('<Return>', lambda event: self.configurar_torneo())
            
        ttk.Button(self.frame_torneo, text="INICIAR COPA", bootstyle=WARNING, command=self.configurar_torneo).pack(pady=20)
        ttk.Button(self.frame_torneo, text="ATRAS", bootstyle=SECONDARY, command=self.volver_menu_desde_torneo).pack()

    def volver_menu_desde_torneo(self):
        self.ventana.unbind('<Return>')
        self.crear_menu()

    def configurar_torneo(self):
        self.modo = "torneo"
        lista_temporal = []
        
        for c in self.cajas:
            nombre = c.get()
            if nombre.strip() == "":
                messagebox.showerror("Error", "Nombres vacios no permitidos.")
                return
            if nombre in lista_temporal:
                messagebox.showerror("Error", f"Nombre '{nombre}' repetido.")
                return
            lista_temporal.append(nombre)
            
        self.ventana.unbind('<Return>')
        
        numero = datos.obtener_siguiente_numero("Torneo")
        self.nombre_evento = f"Torneo {numero}"
        
        self.equipos = lista_temporal
        self.fase = 1
        self.ganadores = []
        self.tiempo_limite = 60
        
        self.frame_torneo.place_forget()
        self.pantalla_versus()

    def pantalla_versus(self):
        for w in self.ventana.winfo_children():
            w.place_forget()
            
        frame_vs = ttk.Frame(self.ventana)
        frame_vs.place(relx=0.5, rely=0.5, anchor="center")
        
        if self.fase == 1:
            titulo = "SEMIFINAL 1"
            self.nombre1 = self.equipos[0]; self.nombre2 = self.equipos[1]
        elif self.fase == 2:
            titulo = "SEMIFINAL 2"
            self.nombre1 = self.equipos[2]; self.nombre2 = self.equipos[3]
        elif self.fase == 3:
            titulo = "GRAN FINAL"
            self.nombre1 = self.ganadores[0]; self.nombre2 = self.ganadores[1]
            
        ttk.Label(frame_vs, text=f"{self.nombre_evento}", font=("Arial", 12)).pack()
        ttk.Label(frame_vs, text=titulo, font=("Impact", 30)).pack(pady=10)
        ttk.Label(frame_vs, text=f"{self.nombre1} VS {self.nombre2}", font=("Arial", 20)).pack(pady=20)
        
        def ir():
            self.ventana.unbind('<Return>')
            frame_vs.place_forget()
            self.preparar_partido()
        
        self.ventana.bind('<Return>', lambda event: ir())
        ttk.Button(frame_vs, text="IR A LA MESA", command=ir).pack()

    # --- JUEGO (MESA DE PING PONG) ---

    def preparar_partido(self):
        self.canvas.configure(bg=config.COLOR_FONDO)
        self.canvas.pack(fill=BOTH, expand=True)
        self.canvas.focus_set()
        
        self.puntos1 = 0
        self.puntos2 = 0
        self.punto_oro_activo = False
        
        self.canvas.delete("all")
        
        # Fondo oscuro de la cancha (garantiza que no se vea blanco en ningún tema de Linux)
        self.canvas.create_rectangle(0, 0, config.ANCHO, config.ALTO, fill=config.COLOR_FONDO, outline="")
        
        # Paredes blancas
        self.canvas.create_rectangle(0, 0, config.ANCHO, config.GROSOR_PARED, fill=config.COLOR_LINEAS, outline="")
        self.canvas.create_rectangle(0, config.ALTO - config.GROSOR_PARED, config.ANCHO, config.ALTO, fill=config.COLOR_LINEAS, outline="")
        
        # Red central
        self.canvas.create_line(config.ANCHO/2, 0, config.ANCHO/2, config.ALTO, fill=config.COLOR_LINEAS, width=2, dash=(10,10))
        
        # Palas
        y_centro = config.ALTO/2
        self.j1 = self.canvas.create_rectangle(30, y_centro-50, 30+config.ANCHO_PALA, y_centro+50, fill=config.COLOR_J1)
        self.j2 = self.canvas.create_rectangle(config.ANCHO-50, y_centro-50, config.ANCHO-50+config.ANCHO_PALA, y_centro+50, fill=config.COLOR_J2)
        
        # Pelota
        self.pelota = self.canvas.create_oval(0, 0, 20, 20, fill=config.COLOR_BLANCO)
        self.centrar_pelota()
        
        # Marcador y Tiempo
        self.txt_puntos = self.canvas.create_text(config.ANCHO/2, 50, text="0 - 0", fill="white", font=("Arial", 40, "bold"))
        self.txt_tiempo = self.canvas.create_text(config.ANCHO/2, config.ALTO-50, text="PREPARADOS...", fill="yellow", font=("Arial", 20))
        
        # Controles
        self.ventana.bind("w", self.mover_w); self.ventana.bind("s", self.mover_s)
        self.ventana.bind("<Up>", self.mover_arriba); self.ventana.bind("<Down>", self.mover_abajo)
        
        self.contador_inicial = 3
        self.cuenta_regresiva()

    def cuenta_regresiva(self):
        if self.contador_inicial > 0:
            self.canvas.itemconfig(self.txt_tiempo, text=str(self.contador_inicial), font=("Arial", 60, "bold"))
            self.contador_inicial -= 1
            self.ventana.after(1000, self.cuenta_regresiva) 
        else:
            self.canvas.itemconfig(self.txt_tiempo, text="¡JUEGUEN!", font=("Arial", 20))
            self.tiempo_inicio = time.time()
            self.jugando = True
            self.bucle_juego()

    def bucle_juego(self):
        if self.jugando:
            pasado = time.time() - self.tiempo_inicio
            restante = self.tiempo_limite - pasado
            
            m = int(restante // 60)
            s = int(restante % 60)
            
            # Solo actualizamos el reloj si NO es punto decisivo
            if not self.punto_oro_activo:
                self.canvas.itemconfig(self.txt_tiempo, text=f"{m}:{s:02d}")
            
            # --- LOGICA EMPATE / PUNTO DE ORO ---
            if restante <= 0 and not self.punto_oro_activo:
                if self.puntos1 == self.puntos2:
                    self.activar_punto_oro() # Vamos a desempate
                    return 
                else:
                    self.terminar() # Hay ganador
                    return

            self.canvas.move(self.pelota, self.dx, self.dy)
            self.detectar_choques()
            
            self.ventana.after(30, self.bucle_juego)

    def activar_punto_oro(self):
        self.jugando = False 
        self.punto_oro_activo = True
        
        self.centrar_pelota()
        
        # Pelota roja y rapida
        self.canvas.itemconfig(self.pelota, fill=config.COLOR_PUNTO_ORO)
        self.dx = config.VELOCIDAD_ORO 
        self.dy = config.VELOCIDAD_ORO
        
        self.canvas.itemconfig(self.txt_tiempo, text="¡PUNTO DE ORO!", fill="red")
        
        self.contador_inicial = 3
        self.cuenta_regresiva()

    def detectar_choques(self):
        c = self.canvas.coords(self.pelota)
        
        # Rebotes arriba/abajo
        if c[1] <= config.GROSOR_PARED: self.dy = abs(self.dy) 
        if c[3] >= config.ALTO - config.GROSOR_PARED: self.dy = -abs(self.dy) 
        
        # Puntos (Izquierda/Derecha)
        if c[0] > config.ANCHO:
            self.puntos1 += 1; self.actualizar_marcador(); self.centrar_pelota()
        elif c[2] < 0:
            self.puntos2 += 1; self.actualizar_marcador(); self.centrar_pelota()
            
        # Palas
        col1 = self.canvas.find_overlapping(*self.canvas.coords(self.j1))
        col2 = self.canvas.find_overlapping(*self.canvas.coords(self.j2))
        
        if self.pelota in col1: self.dx = abs(self.dx)
        if self.pelota in col2: self.dx = -abs(self.dx)

    def actualizar_marcador(self):
        self.canvas.itemconfig(self.txt_puntos, text=f"{self.puntos1} - {self.puntos2}")
        # En punto de oro, el juego acaba inmediatamente
        if self.punto_oro_activo:
            self.terminar()

    def centrar_pelota(self):
        self.canvas.coords(self.pelota, config.ANCHO/2-10, config.ALTO/2-10, config.ANCHO/2+10, config.ALTO/2+10)
        vel = config.VELOCIDAD_ORO if self.punto_oro_activo else config.VELOCIDAD_PELOTA
        self.dx = vel * random.choice([1, -1])
        self.dy = vel * random.choice([1, -1])
    
    # Movimiento manual
    def mover_w(self, e): self.mover_pala(self.j1, -config.VELOCIDAD_JUGADOR)
    def mover_s(self, e): self.mover_pala(self.j1, config.VELOCIDAD_JUGADOR)
    def mover_arriba(self, e): self.mover_pala(self.j2, -config.VELOCIDAD_JUGADOR)
    def mover_abajo(self, e): self.mover_pala(self.j2, config.VELOCIDAD_JUGADOR)

    def mover_pala(self, jugador, cant):
        c = self.canvas.coords(jugador)
        if c[1] + cant >= config.GROSOR_PARED and c[3] + cant <= config.ALTO - config.GROSOR_PARED:
            self.canvas.move(jugador, 0, cant)

    def terminar(self):
        self.jugando = False
        if self.puntos1 > self.puntos2: ganador = self.nombre1
        else: ganador = self.nombre2
            
        datos.guardar_partida(self.nombre_evento, self.nombre1, self.puntos1, self.nombre2, self.puntos2, ganador)
        
        msg = f"GANADOR: {ganador}"
        self.canvas.create_text(config.ANCHO/2, config.ALTO/2, text=msg, font=("Impact", 50), fill="yellow")
        
        def ir_sig():
            self.ventana.unbind('<Return>')
            self.siguiente()

        self.ventana.bind('<Return>', lambda event: ir_sig())

        btn = ttk.Button(self.ventana, text="CONTINUAR", command=ir_sig)
        self.canvas.create_window(config.ANCHO/2, config.ALTO/2 + 80, window=btn)
        
        if self.modo == "torneo": self.ganadores.append(ganador)

    def siguiente(self):
        self.canvas.pack_forget()
        if self.modo == "amistoso": self.crear_menu()
        elif self.modo == "torneo":
            if self.fase < 3:
                self.fase += 1
                self.pantalla_versus()
            else:
                self.crear_menu()

    def vista_resultados(self):
        top = ttk.Toplevel(self.ventana)
        top.title("Resultados")
        top.geometry("600x400")
        
        pestanas = ttk.Notebook(top)
        pestanas.pack(fill='both', expand=True)
        
        f1 = ttk.Frame(pestanas); pestanas.add(f1, text="Amistosos")
        self.llenar_tabla(f1, "Amistoso")
        
        f2 = ttk.Frame(pestanas); pestanas.add(f2, text="Torneos")
        self.llenar_tabla(f2, "Torneo")
        
        u = datos.contar_jugadores_unicos()
        ttk.Label(top, text=f"Jugadores distintos: {u}").pack(pady=5)
        
        def borrar():
            datos.borrar_todo(); top.destroy()
        ttk.Button(top, text="BORRAR", command=borrar).pack()

    def llenar_tabla(self, frame, tipo):
        cols = ("EVENTO", "J1", "PUNTOS", "J2", "GANADOR")
        tabla = ttk.Treeview(frame, columns=cols, show="headings")
        
        tabla.heading("EVENTO", text="Evento"); tabla.column("EVENTO", width=80)
        tabla.heading("J1", text="J1"); tabla.column("J1", width=80)
        tabla.heading("PUNTOS", text="Puntos"); tabla.column("PUNTOS", width=50)
        tabla.heading("J2", text="J2"); tabla.column("J2", width=80)
        tabla.heading("GANADOR", text="Ganador"); tabla.column("GANADOR", width=80)
        tabla.pack(fill='both', expand=True)
        
        lista = datos.leer_historial(tipo)
        for p in lista:
            res = f"{p['puntos1']}-{p['puntos2']}"
            tabla.insert("", END, values=(p['evento'], p['jugador1'], res, p['jugador2'], p['ganador']))