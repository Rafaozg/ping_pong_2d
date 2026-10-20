import csv      # Libreria para manejar archivos CSV (Hoja de calculo simple).
import config   # Importamos la configuracion.

# Funcion: Guarda el resultado de un partido de Ping Pong.
def guardar_partida(tipo, j1, puntos1, j2, puntos2, ganador):
    try:
        # Abrimos el archivo en modo 'append' (agregar al final) con soporte UTF-8.
        archivo = open(config.ARCHIVO, mode='a', newline='', encoding='utf-8')
        
        # Creamos la herramienta para escribir.
        escritor = csv.writer(archivo)
        
        # Guardamos la fila: Tipo, Jugador1, Puntos1, Jugador2, Puntos2, Ganador.
        escritor.writerow([tipo, j1, puntos1, j2, puntos2, ganador])
        
        # Cerramos el archivo para asegurar el guardado.
        archivo.close()
    except Exception as e:
        # Si falla, mostramos error en consola.
        print("Error guardando datos:", e)

# Funcion: Lee el historial filtrando por tipo (Amistoso o Torneo).
def leer_historial(tipo_base):
    lista = [] # Lista vacia para guardar los partidos encontrados.
    try:
        # Abrimos en modo lectura ('r').
        archivo = open(config.ARCHIVO, mode='r', encoding='utf-8')
        lector = csv.reader(archivo)
        
        # Leemos linea por linea.
        for fila in lector:
            if len(fila) > 0: # Si la linea no esta vacia.
                
                # fila[0] es el nombre del evento (ej: "Torneo 1").
                if fila[0].startswith(tipo_base):
                    
                    # Guardamos en un DICCIONARIO con terminos de Ping Pong.
                    dato = {
                        "evento": fila[0],
                        "jugador1": fila[1],
                        "puntos1": fila[2],
                        "jugador2": fila[3],
                        "puntos2": fila[4],
                        "ganador": fila[5]
                    }
                    lista.append(dato)
        
        archivo.close()
        return lista    
    except:
        return [] # Si hay error, devolvemos lista vacia.

# Funcion: Calcula el numero siguiente para el evento (ej. Torneo 2 -> 3).
def obtener_siguiente_numero(palabra_clave):
    try:
        archivo = open(config.ARCHIVO, mode='r', encoding='utf-8')
        lector = csv.reader(archivo)
        maximo_numero = 0 
        
        for fila in lector:
            if len(fila) > 0:
                texto_tipo = fila[0]
                if texto_tipo.startswith(palabra_clave):
                    # Separamos "Torneo 2" -> ["Torneo", "2"].
                    partes = texto_tipo.split(" ")
                    if len(partes) > 1:
                        numero = int(partes[1])
                        if numero > maximo_numero:
                            maximo_numero = numero
                            
        archivo.close()
        return maximo_numero + 1
    except:
        return 1 

# Funcion: Cuenta jugadores unicos usando un CONJUNTO (Set).
def contar_jugadores_unicos():
    try:
        archivo = open(config.ARCHIVO, mode='r', encoding='utf-8')
        lector = csv.reader(archivo)
        conjunto = set() # Set elimina duplicados automaticamente.
        
        for fila in lector:
            if len(fila) > 0:
                conjunto.add(fila[1])
                conjunto.add(fila[3])
                
        archivo.close()
        return len(conjunto)
    except:
        return 0

# Funcion: Borra todo el historial de forma segura.
def borrar_todo():
    try:
        # 'w' borra todo el contenido al abrir.
        archivo = open(config.ARCHIVO, mode='w', encoding='utf-8')
        archivo.close()
    except Exception as e:
        print("Error borrando datos:", e)