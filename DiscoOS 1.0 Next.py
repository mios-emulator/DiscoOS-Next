# ============================================================
#  DiscoOS 1.0 Next
#  Mini sistema operativo de texto hecho en Python
# ============================================================

import os
import sys
import json
import time
import math
import random
import platform
from datetime import datetime

try:
    import readline  # Linux / macOS -> historial con flechas
except ImportError:
    readline = None

# ------------------------------------------------------------
# CONFIGURACIÓN GLOBAL
# ------------------------------------------------------------
NOMBRE = "DiscoOS"
VERSION = "1.0 Next"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FS_FILE = os.path.join(BASE_DIR, "discofs.json")
USER_FILE = os.path.join(BASE_DIR, "usuarios.json")
TAREAS_FILE = os.path.join(BASE_DIR, "tareas.json")
NOTAS_FILE = os.path.join(BASE_DIR, "notas.txt")
LOG_FILE = os.path.join(BASE_DIR, "discoos.log")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

USUARIO_ACTUAL = None
CWD = "/home"

# ------------------------------------------------------------
# COLORES ANSI
# ------------------------------------------------------------
if os.name == "nt":
    os.system("")  # activa secuencias ANSI en Windows

class C:
    R     = "\033[0m"
    B     = "\033[1m"
    ROJO  = "\033[91m"
    VERDE = "\033[92m"
    AMAR  = "\033[93m"
    AZUL  = "\033[94m"
    MAG   = "\033[95m"
    CIAN  = "\033[96m"
    GRIS  = "\033[90m"

def col(texto, color):
    return f"{color}{texto}{C.R}"

# ------------------------------------------------------------
# UTILIDADES
# ------------------------------------------------------------
def limpiar():
    os.system("cls" if os.name == "nt" else "clear")

def pausa(msg="Presiona ENTER para continuar..."):
    input(f"\n{col(msg, C.GRIS)}")

def log(evento):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {evento}\n")
    except Exception:
        pass

def cargar_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def guardar_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(col(f"Error guardando {path}: {e}", C.ROJO))

# ------------------------------------------------------------
# USUARIOS
# ------------------------------------------------------------
def cargar_usuarios():
    usuarios = cargar_json(USER_FILE, None)
    if not usuarios:
        usuarios = {"admin": {"pass": "1234", "rol": "admin"},
                    "invitado": {"pass": "", "rol": "user"}}
        guardar_json(USER_FILE, usuarios)
    return usuarios

def login():
    usuarios = cargar_usuarios()
    limpiar()
    print(col("╔════════════════════════════════╗", C.CIAN))
    print(col("║      INICIO DE SESIÓN          ║", C.CIAN))
    print(col("╚════════════════════════════════╝", C.CIAN))
    print(col("Usuarios: " + ", ".join(usuarios.keys()), C.GRIS))
    print()
    for _ in range(3):
        u = input("Usuario: ").strip()
        c = input("Contraseña: ").strip()
        if u in usuarios and usuarios[u]["pass"] == c:
            print(col(f"\n✔ Bienvenido, {u}.", C.VERDE))
            log(f"Login OK: {u}")
            time.sleep(1)
            return u
        print(col("✘ Credenciales incorrectas.", C.ROJO))
    print(col("Demasiados intentos.", C.ROJO))
    log("Login FALLIDO x3")
    return None

# ------------------------------------------------------------
# SISTEMA DE ARCHIVOS VIRTUAL
# ------------------------------------------------------------
def fs_inicial():
    fs = cargar_json(FS_FILE, None)
    if not fs:
        fs = {
            "/":               {"tipo": "dir"},
            "/home":           {"tipo": "dir"},
            "/home/readme.txt": {"tipo": "archivo",
                                 "contenido": "Bienvenido a DiscoOS 2.0"},
            "/bin":            {"tipo": "dir"},
            "/etc":            {"tipo": "dir"},
        }
        guardar_json(FS_FILE, fs)
    return fs

FS = fs_inicial()

def ruta_abs(p):
    if p.startswith("/"):
        return "/" + p.strip("/") or "/"
    base = CWD.rstrip("/")
    return (base + "/" + p).replace("//", "/")

def cmd_ls(args=""):
    prefijo = CWD.rstrip("/") + "/"
    hijos = {}
    for ruta, info in FS.items():
        if ruta.startswith(prefijo) and ruta != CWD:
            resto = ruta[len(prefijo):]
            if resto and "/" not in resto.strip("/"):
                hijos[resto] = info.get("tipo", "dir")
    if not hijos:
        print(col("(vacío)", C.GRIS))
    for nombre in sorted(hijos):
        icono = "📁" if hijos[nombre] == "dir" else "📄"
        color = C.AZUL if hijos[nombre] == "dir" else C.R
        print(f"  {icono} {col(nombre, color)}")

def cmd_cd(args):
    global CWD
    if not args or args == "~":
        CWD = f"/home"
        return
    if args == "..":
        if CWD != "/":
            CWD = "/" + "/".join(CWD.strip("/").split("/")[:-1])
            CWD = CWD.rstrip("/") or "/"
        return
    ruta = ruta_abs(args)
    if FS.get(ruta, {}).get("tipo") == "dir":
        CWD = ruta
    else:
        print(col(f"cd: '{args}' no existe.", C.ROJO))

def cmd_mkdir(args):
    if not args:
        print(col("Uso: mkdir <nombre>", C.AMAR)); return
    ruta = ruta_abs(args)
    if ruta in FS:
        print(col("Ya existe.", C.ROJO)); return
    FS[ruta] = {"tipo": "dir"}
    guardar_json(FS_FILE, FS)

def cmd_write(args):
    nombre, _, texto = args.partition(" ")
    if not nombre:
        print(col("Uso: write <archivo> <texto>", C.AMAR)); return
    ruta = ruta_abs(nombre)
    FS[ruta] = {"tipo": "archivo", "contenido": texto}
    guardar_json(FS_FILE, FS)

def cmd_cat(args):
    ruta = ruta_abs(args)
    info = FS.get(ruta)
    if not info:
        print(col("No encontrado.", C.ROJO))
    elif info["tipo"] != "archivo":
        print(col("Es un directorio.", C.ROJO))
    else:
        print(info.get("contenido", ""))

def cmd_rm(args):
    ruta = ruta_abs(args)
    if ruta not in FS:
        print(col("No existe.", C.ROJO)); return
    if FS[ruta]["tipo"] == "dir":
        # borra también hijos
        for k in [k for k in FS if k == ruta or k.startswith(ruta + "/")]:
            del FS[k]
    else:
        del FS[ruta]
    guardar_json(FS_FILE, FS)

def cmd_tree(args=""):
    prefijo = ruta_abs(args) if args else CWD
    base_len = 0 if prefijo == "/" else len(prefijo)
    print(col(prefijo, C.AZUL))
    for ruta in sorted(FS):
        if ruta == prefijo: continue
        if prefijo == "/" or ruta.startswith(prefijo + "/"):
            rel = ruta[base_len:].strip("/")
            nivel = rel.count("/")
            nombre = rel.split("/")[-1]
            icono = "📁" if FS[ruta]["tipo"] == "dir" else "📄"
            print("  " * (nivel + 1) + f"{icono} {nombre}")

# ------------------------------------------------------------
# TAREAS
# ------------------------------------------------------------
def cargar_tareas():
    return cargar_json(TAREAS_FILE, [])

def guardar_tareas(t):
    guardar_json(TAREAS_FILE, t)

def app_tareas():
    while True:
        limpiar()
        print(col("===== TAREAS =====", C.MAG))
        tareas = cargar_tareas()
        if not tareas:
            print(col("(sin tareas)", C.GRIS))
        for i, t in enumerate(tareas, 1):
            estado = col("✔", C.VERDE) if t["hecha"] else col("○", C.AMAR)
            print(f" {i}. [{estado}] {t['texto']}")
        print()
        print(" a) Añadir   b) Marcar   c) Borrar   d) Volver")
        op = input("DiscoOS> ").strip().lower()

        if op == "d" or op == "":
            break
        elif op == "a":
            texto = input("Nueva tarea: ").strip()
            if texto:
                tareas.append({"texto": texto, "hecha": False})
                guardar_tareas(tareas)
        elif op == "b":
            try:
                i = int(input("Número: ")) - 1
                tareas[i]["hecha"] = not tareas[i]["hecha"]
                guardar_tareas(tareas)
            except (ValueError, IndexError):
                print(col("Inválido.", C.ROJO)); time.sleep(1)
        elif op == "c":
            try:
                i = int(input("Número: ")) - 1
                tareas.pop(i)
                guardar_tareas(tareas)
            except (ValueError, IndexError):
                print(col("Inválido.", C.ROJO)); time.sleep(1)

# ------------------------------------------------------------
# NOTAS
# ------------------------------------------------------------
def app_notas():
    while True:
        limpiar()
        print(col("===== NOTAS =====", C.MAG))
        contenido = ""
        if os.path.exists(NOTAS_FILE):
            with open(NOTAS_FILE, "r", encoding="utf-8") as f:
                contenido = f.read()
        print(contenido if contenido else col("(vacío)", C.GRIS))
        print()
        print(" a) Añadir línea   b) Reemplazar   c) Borrar todo   d) Volver")
        op = input("DiscoOS> ").strip().lower()
        if op == "d" or op == "":
            break
        elif op == "a":
            linea = input("Línea: ")
            with open(NOTAS_FILE, "a", encoding="utf-8") as f:
                f.write(linea + "\n")
        elif op == "b":
            texto = input("Nuevo contenido:\n")
            with open(NOTAS_FILE, "w", encoding="utf-8") as f:
                f.write(texto + "\n")
        elif op == "c":
            with open(NOTAS_FILE, "w", encoding="utf-8") as f:
                f.write("")

# ------------------------------------------------------------
# JUEGOS
# ------------------------------------------------------------
def juego_adivina():
    secreto = random.randint(1, 100)
    intentos = 0
    limpiar()
    print(col("===== ADIVINA EL NÚMERO =====", C.MAG))
    print("Piensa un número del 1 al 100.")
    while True:
        try:
            n = int(input("Tu número: "))
        except ValueError:
            print(col("Número inválido.", C.ROJO)); continue
        intentos += 1
        if n < secreto:
            print(col("Muy bajo ↑", C.AMAR))
        elif n > secreto:
            print(col("Muy alto ↓", C.AMAR))
        else:
            print(col(f"¡Correcto en {intentos} intentos!", C.VERDE))
            break
    pausa()

def juego_ppt():
    opciones = ["piedra", "papel", "tijera"]
    limpiar()
    print(col("===== PIEDRA PAPEL TIJERA =====", C.MAG))
    while True:
        jug = input("piedra/papel/tijera (o 'salir'): ").strip().lower()
        if jug == "salir":
            break
        if jug not in opciones:
            print(col("Opción inválida.", C.ROJO)); continue
        pc = random.choice(opciones)
        print(f"PC eligió: {col(pc, C.CIAN)}")
        if jug == pc:
            print(col("Empate.", C.AMAR))
        elif (jug == "piedra" and pc == "tijera") or \
             (jug == "papel" and pc == "piedra") or \
             (jug == "tijera" and pc == "papel"):
            print(col("¡Ganaste!", C.VERDE))
        else:
            print(col("Perdiste.", C.ROJO))

def menu_juegos():
    while True:
        limpiar()
        print(col("===== JUEGOS =====", C.MAG))
        print(" 1. Adivina el número")
        print(" 2. Piedra, papel o tijera")
        print(" 3. Volver")
        op = input("DiscoOS> ").strip()
        if op == "1":
            juego_adivina()
        elif op == "2":
            juego_ppt()
        elif op == "3" or op == "":
            break

# ------------------------------------------------------------
# TERMINAL
# ------------------------------------------------------------
def cmd_help(args=""):
    print(f"""
{col('COMANDOS DISPONIBLES', C.B)}
  {col('help', C.CIAN)}          - Mostrar esta ayuda
  {col('clear', C.CIAN)}         - Limpiar pantalla
  {col('time', C.CIAN)}          - Hora actual
  {col('date', C.CIAN)}          - Fecha actual
  {col('whoami', C.CIAN)}        - Usuario actual
  {col('system', C.CIAN)}        - Info del sistema
  {col('about', C.CIAN)}         - Sobre DiscoOS
  {col('echo <txt>', C.CIAN)}    - Repetir texto
  {col('calc', C.CIAN)}          - Abrir calculadora

{col('ARCHIVOS', C.B)}
  {col('ls', C.CIAN)}            - Listar directorio
  {col('cd <dir>', C.CIAN)}      - Cambiar directorio
  {col('mkdir <dir>', C.CIAN)}   - Crear directorio
  {col('write <f> <txt>', C.CIAN)} - Crear/escribir archivo
  {col('cat <f>', C.CIAN)}       - Ver archivo
  {col('rm <f>', C.CIAN)}        - Borrar
  {col('tree', C.CIAN)}          - Árbol de archivos

{col('SISTEMA', C.B)}
  {col('exit', C.CIAN)}          - Cerrar sesión
""")
    pausa()

def cmd_clear(args=""):
    limpiar()

def cmd_time(args=""):
    print("Hora:", col(datetime.now().strftime("%H:%M:%S"), C.CIAN))
    pausa()

def cmd_date(args=""):
    print("Fecha:", col(datetime.now().strftime("%A %d/%m/%Y"), C.CIAN))
    pausa()

def cmd_whoami(args=""):
    print("Usuario:", col(USUARIO_ACTUAL, C.VERDE))
    pausa()

def cmd_system(args=""):
    print(f"Sistema:      {col(platform.system(), C.CIAN)}")
    print(f"Arquitectura: {col(platform.machine(), C.CIAN)}")
    print(f"Python:       {col(platform.python_version(), C.CIAN)}")
    print(f"Procesador:   {col(platform.processor() or 'desconocido', C.CIAN)}")
    pausa()

def cmd_about(args=""):
    print(col(f"{NOMBRE} {VERSION}", C.B))
    print("Mini sistema operativo de texto en Python.")
    print("Creado con cariño por un dev curioso.")
    pausa()

def cmd_echo(args=""):
    print(args)

def cmd_calc(args=""):
    calculadora()

def terminal():
    global CWD
    limpiar()
    print(col(f"Terminal de {NOMBRE} — escribe 'help' para ver comandos.", C.GRIS))
    pausa()

    while True:
        try:
            prompt = f"{col(NOMBRE, C.VERDE)}:{col(CWD, C.AZUL)}> "
            entrada = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not entrada:
            continue
        cmd, _, args = entrada.partition(" ")
        log(f"{USUARIO_ACTUAL}: {entrada}")

        if cmd == "exit":
            break
        elif cmd == "help":
            cmd_help(args)
        elif cmd == "clear":
            limpiar()
        elif cmd == "time":
            cmd_time()
        elif cmd == "date":
            cmd_date()
        elif cmd == "whoami":
            cmd_whoami()
        elif cmd == "system":
            cmd_system()
        elif cmd == "about":
            cmd_about()
        elif cmd == "echo":
            cmd_echo(args)
        elif cmd == "calc":
            cmd_calc()
        elif cmd == "ls":
            cmd_ls(args)
        elif cmd == "cd":
            cmd_cd(args)
        elif cmd == "mkdir":
            cmd_mkdir(args)
        elif cmd == "write":
            cmd_write(args)
        elif cmd == "cat":
            cmd_cat(args)
        elif cmd == "rm":
            cmd_rm(args)
        elif cmd == "tree":
            cmd_tree(args)
        else:
            print(col(f"Comando no encontrado: {cmd}", C.ROJO))

# ------------------------------------------------------------
# CALCULADORA
# ------------------------------------------------------------
def calculadora():
    while True:
        limpiar()
        print(col("===== CALCULADORA =====", C.MAG))
        print(" 1. Sumar        5. Raíz cuadrada")
        print(" 2. Restar       6. Potencia")
        print(" 3. Multiplicar  7. Seno / Coseno")
        print(" 4. Dividir      8. Volver")
        print()
        op = input("DiscoOS> ").strip()
        if op == "8" or op == "":
            break
        try:
            if op in "1234":
                a = float(input("Número 1: "))
                b = float(input("Número 2: "))
                if   op == "1": r = a + b
                elif op == "2": r = a - b
                elif op == "3": r = a * b
                elif op == "4":
                    if b == 0:
                        print(col("Error: división entre cero.", C.ROJO))
                        pausa(); continue
                    r = a / b
                print(col(f"\nResultado: {r}", C.VERDE)); pausa()
            elif op == "5":
                a = float(input("Número: "))
                print(col(f"\n√{a} = {math.sqrt(a)}", C.VERDE)); pausa()
            elif op == "6":
                a = float(input("Base: "))
                b = float(input("Exponente: "))
                print(col(f"\n{a}^{b} = {a**b}", C.VERDE)); pausa()
            elif op == "7":
                a = float(input("Ángulo (grados): "))
                rad = math.radians(a)
                print(col(f"sin = {math.sin(rad):.4f}   cos = {math.cos(rad):.4f}", C.VERDE))
                pausa()
            else:
                print(col("Opción inválida.", C.ROJO)); time.sleep(1)
        except ValueError:
            print(col("Introduce números válidos.", C.ROJO)); pausa()

# ------------------------------------------------------------
# INFORMACIÓN DEL SISTEMA
# ------------------------------------------------------------
def informacion():
    limpiar()
    print(col("╔══════════════════════════════╗", C.CIAN))
    print(col("║       INFORMACIÓN            ║", C.CIAN))
    print(col("╚══════════════════════════════╝", C.CIAN))
    print()
    print(f"Nombre:       {col(NOMBRE, C.VERDE)}")
    print(f"Versión:      {col(VERSION, C.VERDE)}")
    print(f"Usuario:      {col(USUARIO_ACTUAL or 'n/a', C.VERDE)}")
    print(f"Python:       {platform.python_version()}")
    print(f"Sistema:      {platform.system()} {platform.release()}")
    print(f"Arquitectura: {platform.machine()}")
    print(f"Directorio:   {CWD}")
    print(f"Archivos FS:  {len(FS)}")
    pausa()

# ------------------------------------------------------------
# ARRANQUE / APAGADO
# ------------------------------------------------------------
def boot():
    limpiar()
    print(col("=" * 42, C.CIAN))
    print(col("         DiscoOS BIOS v1.0".center(42), C.B))
    print(col("=" * 42, C.CIAN))
    print()
    time.sleep(0.4)
    for i in range(101):
        llenos = i // 5
        barra = "█" * llenos + "░" * (20 - llenos)
        print(f"\rCargando sistema... [{barra}] {i:3d}%", end="")
        time.sleep(0.008)
    print()
    time.sleep(0.3)
    print(col("✔ Sistema listo.", C.VERDE))
    time.sleep(0.6)

def apagar():
    limpiar()
    print(col("DiscoOS está apagándose...", C.AMAR))
    time.sleep(1)
    for i in range(3, 0, -1):
        print(f"\rCerrando sesión en {i}...", end="")
        time.sleep(0.6)
    print()
    print(col("\n✔ DiscoOS apagado. ¡Hasta pronto!", C.VERDE))
    log("Apagado")

# ------------------------------------------------------------
# MENÚ PRINCIPAL
# ------------------------------------------------------------
def menu_principal():
    while True:
        limpiar()
        print(col("╔════════════════════════════════╗", C.CIAN))
        print(col("║", C.CIAN) + col(f"   {NOMBRE} {VERSION}  —  {USUARIO_ACTUAL}   ".center(28), C.B) + col("║", C.CIAN))
        print(col("╠════════════════════════════════╣", C.CIAN))
        print(col("║", C.CIAN) + "  1. Terminal                    " + col("║", C.CIAN))
        print(col("║", C.CIAN) + "  2. Calculadora                 " + col("║", C.CIAN))
        print(col("║", C.CIAN) + "  3. Tareas                      " + col("║", C.CIAN))
        print(col("║", C.CIAN) + "  4. Notas                       " + col("║", C.CIAN))
        print(col("║", C.CIAN) + "  5. Juegos                      " + col("║", C.CIAN))
        print(col("║", C.CIAN) + "  6. Información del sistema     " + col("║", C.CIAN))
        print(col("║", C.CIAN) + "  7. Apagar                      " + col("║", C.CIAN))
        print(col("╚════════════════════════════════╝", C.CIAN))
        print()
        op = input(f"{col(NOMBRE, C.VERDE)}> ").strip()

        if   op == "1": terminal()
        elif op == "2": calculadora()
        elif op == "3": app_tareas()
        elif op == "4": app_notas()
        elif op == "5": menu_juegos()
        elif op == "6": informacion()
        elif op == "7":
            apagar(); break
        else:
            print(col("Opción inválida.", C.ROJO))
            time.sleep(1)

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    global USUARIO_ACTUAL
    boot()
    USUARIO_ACTUAL = login()
    if not USUARIO_ACTUAL:
        print(col("Sesión cancelada.", C.ROJO))
        return
    menu_principal()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(col("\n\n[!] Interrupción detectada. Apagando DiscoOS...", C.AMAR))
    except Exception as e:
        print(col(f"\n[!] Error fatal: {e}", C.ROJO))
        input("ENTER para salir...")

    