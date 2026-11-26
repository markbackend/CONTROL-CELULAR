"""CONTROL CELULAR - servidor de la PC.

Sirve la página del control y recibe por WebSocket lo que se toca en cada celular.
Cada celular es un jugador (hasta 4) con su propio control virtual (Xbox 360 o DualShock 4).

Partes:  mandos.py (controles virtuales)  ·  celulares.py (emparejamiento, ajustes, intentos)
         paginas.py (páginas web y QR)    ·  steam.py · certs.py · red.py · bandeja.py · idioma.py

Protocolo (texto, mensajes cortos):
  celular -> PC:  "a <codigo|token>"     emparejar / reconectar
                  "b <BOTON> <0|1>"      botón apretado / suelto
                  "t <L|R> <0-255>"      gatillo
                  "s <L|R> <x> <y>"      stick, x/y en -1000..1000 (y positivo = arriba)
                  "r"                    soltar todo
                  "p <n>"                ping (la PC contesta lo mismo, para medir la demora)
                  "k <clave> <valor>"    guardar un ajuste de ESTE celular en la PC (valor vacío = borrarlo)
                  "d <nombre>"           nombre del celular (su modelo), para reconocerlo en las listas
                  "l"                    pedir la lista de otros celulares con ajustes guardados
                  "cp <id>"              copiar los ajustes de otro celular a este
                  "m <xbox|ds4>"         qué control ve la PC (Xbox 360 o DualShock 4)
                  "g gx gy gz ax ay az"  giroscopio y acelerómetro (solo DualShock 4, unidades del DS4)
  PC -> celular:  "ok <token>" | "no" | "lleno"   resultado del emparejamiento
                  "espera <segundos>"    demasiados códigos equivocados: esperar antes de reintentar
                  "lc <json>"            lista de otros celulares [{id, nombre, visto}]
                  "cc <json>"            ajustes recién copiados (aplicarlos y recargar)
                  "n <jugador>"          qué número de jugador es (1-4)
                  "m <xbox|ds4>"         qué control es
                  "c <json>"             los ajustes de este celular guardados en la PC (al conectarse)
                  "v <grande> <chico>"   vibración (0-255 cada motor)
                  "j <appid> <tipo> <nombre>" | "j 0"   juego de Steam abierto en la PC (o ninguno)
                  "p <n>"                respuesta al ping
                  "app <versión>"        versión del programa de la PC (la app de Android avisa si es más vieja)
  HTTP(S):        /juegos?t=<token>      biblioteca de Steam (JSON)   /portada/<appid>?t=<token>  portada
                  /qr                    QR para conectarse (solo desde esta misma PC)

Variables de entorno (para las pruebas): CONTROL_PUERTO, CONTROL_PUERTO_SEGURO, CONTROL_DATOS (rutas.py),
CONTROL_MANDO_FALSO=1 (mandos.py), CONTROL_SIN_BANDEJA=1, CONTROL_SIN_FIREWALL=1, CONTROL_SIN_STEAM=1.
"""

import asyncio
import json
import os
import socket
import ssl
import sys
import time

from websockets.asyncio.server import serve

import celulares
import certs
import dialogos
import enlaces
import paginas
import panel
import red
import rutas
import steam
import version
from celulares import Registro
from idioma import T
from mandos import TIPOS_MANDO, Jugador

PUERTO = int(os.environ.get("CONTROL_PUERTO", "8765"))                 # HTTP: instalar el certificado
PUERTO_SEGURO = int(os.environ.get("CONTROL_PUERTO_SEGURO", "8443"))   # HTTPS: el control
MAX_JUGADORES = 4
WEB = rutas.RECURSOS / "web"
DESCARGA_VIGEMBUS = "https://github.com/nefarius/ViGEmBus/releases"
MINIMIZADO = "--minimizado" in sys.argv  # al arrancar con Windows: ventana oculta, sin preguntas
SIN_STEAM = os.environ.get("CONTROL_SIN_STEAM") == "1"

registro = Registro(rutas.DATOS)
bluetooth = enlaces.Bluetooth()  # celulares con la app de Android por Bluetooth
jugadores: dict[int, Jugador] = {}
loop: asyncio.AbstractEventLoop | None = None
direccion = {"qr": "", "ip": ""}
al_cambiar_conexiones = None  # lo usa el ícono de la barra para mostrar quiénes están conectados


def salir(codigo_salida: int = 0) -> None:
    """Con consola, que no se cierre antes de leer el mensaje (sin consola, el cartel ya esperó)."""
    if rutas.EMPAQUETADO and not MINIMIZADO:
        dialogos.esperar_enter(T("  Presioná Enter para cerrar...", "  Press Enter to close..."))
    raise SystemExit(codigo_salida)


def ip_local() -> str:
    """IP de la PC en la red de casa (no manda nada a internet)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def url_qr() -> str:
    return f"http://{direccion['ip']}:{PUERTO}/?c={registro.codigo}"


def _avisar_bloqueo(ip, segundos):
    n = celulares.INTENTOS
    print(T(f"  {n} códigos equivocados desde {ip}: bloqueado {segundos} segundos.",
            f"  {n} wrong codes from {ip}: blocked for {segundos} seconds."))


def _avisar_codigo_nuevo(codigo):
    print(T(f"  Demasiados intentos fallidos: cambié el código de emparejamiento. Nuevo código: {codigo}",
            f"  Too many failed attempts: I changed the pairing code. New code: {codigo}"))
    print(T("  (el QR del ícono ya tiene el código nuevo)", "  (the QR in the tray icon already has the new code)"))


registro.al_bloquear = _avisar_bloqueo
registro.al_cambiar_codigo = _avisar_codigo_nuevo


# ---------- Jugadores ----------

def _al_vibrar(jugador: Jugador, grande: int, chico: int) -> None:
    """Lo llama el driver (desde otro hilo) cuando un juego hace vibrar el control de este jugador."""
    if jugador.ws is not None and loop is not None:
        loop.call_soon_threadsafe(asyncio.ensure_future, enviar(jugador.ws, f"v {grande} {chico}"))


def crear_primer_control() -> None:
    """El jugador 1 se crea al arrancar: así, si falta ViGEmBus, se avisa enseguida."""
    try:
        jugadores[1] = Jugador(1, al_vibrar=_al_vibrar)
    except Exception as e:  # casi siempre: falta el driver ViGEmBus
        try:
            import webbrowser
            webbrowser.open(DESCARGA_VIGEMBUS)
        except Exception:
            pass
        dialogos.avisar(
            T(f"\n  No pude crear el control virtual de Xbox: {e}\n"
              f"  Falta el driver ViGEmBus (es gratis y oficial). Te abro la página para descargarlo:\n"
              f"    {DESCARGA_VIGEMBUS}\n"
              f"  Bajá el archivo ViGEmBus_..._x64_x86_arm64.exe, instalalo y volvé a abrir Control Celular.\n",
              f"\n  I couldn't create the virtual Xbox controller: {e}\n"
              f"  The ViGEmBus driver is missing (it's free and official). Opening its download page:\n"
              f"    {DESCARGA_VIGEMBUS}\n"
              f"  Download ViGEmBus_..._x64_x86_arm64.exe, install it and open Control Celular again.\n"), error=True)
        salir(1)


def lugar_para(token: str) -> Jugador | None:
    """El mismo celular vuelve siempre a su número de jugador; uno nuevo toma el primer lugar libre."""
    for j in jugadores.values():
        if j.token == token:
            return j
    for n in range(1, MAX_JUGADORES + 1):
        j = jugadores.get(n)
        if j is None:
            jugadores[n] = Jugador(n, al_vibrar=_al_vibrar)
            return jugadores[n]
        if j.ws is None:
            return j
    return None


def conectados() -> list[Jugador]:
    return [j for j in jugadores.values() if j.ws is not None]


def avisar_conexiones() -> None:
    if al_cambiar_conexiones:
        try:
            al_cambiar_conexiones([j.numero for j in conectados()])
        except Exception:
            pass


async def enviar(ws, texto: str) -> None:
    try:
        await ws.send(texto)
    except Exception:
        pass


async def a_todos(texto: str) -> None:
    for j in conectados():
        await enviar(j.ws, texto)


# ---------- Conexión de cada celular ----------

async def atender(ws):
    ip = ws.remote_address[0]
    # Emparejamiento: primer mensaje = código (primera vez) o token guardado.
    try:
        primero = await asyncio.wait_for(ws.recv(), timeout=30)
    except Exception:
        return
    partes = primero.split()
    if len(partes) != 2 or partes[0] != "a":
        await ws.send("no")
        return
    resultado, dato = registro.emparejar(partes[1], ip)
    if resultado == "espera":
        await ws.send(f"espera {dato}")
        return
    if resultado == "no":
        await ws.send("no")
        print(T("  Intento con código incorrecto desde", "  Wrong code attempt from"), ip)
        return
    token = dato

    j = lugar_para(token)
    if j is None:
        await ws.send("lleno")
        print(T(f"  Ya hay {MAX_JUGADORES} celulares conectados; no entra otro.",
                f"  {MAX_JUGADORES} phones are already connected; no room for another."))
        return
    if j.ws is not None:  # el mismo celular se reconectó: cerrar la conexión vieja
        viejo, j.ws = j.ws, None
        await viejo.close()
    j.ws, j.token = ws, token
    celular = registro.celulares[token]
    await ws.send(f"ok {token}")
    j.cambiar_tipo(celular.get("mando", "xbox"))  # cada celular recuerda si es Xbox o DualShock 4
    await ws.send(f"n {j.numero}")
    await ws.send(f"m {j.tipo}")
    await ws.send("c " + json.dumps(registro.ajustes_de(token), ensure_ascii=False))
    await ws.send(f"app {version.VERSION}")  # la app de Android avisa si ella es más vieja (hay que bajar la nueva)
    await ws.send(mensaje_abierto())  # el último del saludo
    print(T(f"  Jugador {j.numero} conectado ({celular['nombre']}):",
            f"  Player {j.numero} connected ({celular['nombre']}):"), ip)
    avisar_conexiones()
    try:
        async for msg in ws:
            if token not in registro.celulares:  # lo olvidaron desde el ícono mientras estaba conectado
                break
            try:
                await mensaje(j, token, ws, msg)
            except (ValueError, IndexError):
                pass
    except Exception:
        pass
    finally:
        if j.ws is ws:
            j.ws = None
            j.soltar()
            print(T(f"  Jugador {j.numero} desconectado (se soltaron todos sus botones)",
                    f"  Player {j.numero} disconnected (all its buttons were released)"))
            avisar_conexiones()


async def mensaje(j: Jugador, token: str, ws, msg: str) -> None:
    if msg.startswith("p "):
        await ws.send(msg)
    elif msg.startswith("k "):
        registro.guardar_ajuste(token, msg[2:])
    elif msg.startswith("d "):  # el celular dice su modelo, para reconocerlo en las listas
        nombre = " ".join(msg[2:].split())[:40]
        if nombre and registro.poner(token, "nombre", nombre):
            avisar_conexiones()
    elif msg.startswith("m "):  # qué control ve la PC: Xbox 360 o DualShock 4
        nuevo = msg[2:].strip()
        if nuevo in TIPOS_MANDO and nuevo != j.tipo:
            j.cambiar_tipo(nuevo)
            registro.poner(token, "mando", nuevo)
            nombre_mando = "DualShock 4" if nuevo == "ds4" else "Xbox 360"
            print(T(f"  Jugador {j.numero} ahora es un control {nombre_mando}",
                    f"  Player {j.numero} is now a {nombre_mando} controller"))
        await ws.send(f"m {j.tipo}")
    elif msg == "l":
        await ws.send("lc " + json.dumps(registro.otros(token), ensure_ascii=False))
    elif msg.startswith("cp "):
        if registro.copiar(token, msg[3:].strip()):
            await ws.send("cc " + json.dumps(registro.ajustes_de(token), ensure_ascii=False))
    else:
        j.aplicar(msg)


# ---------- Olvidar celulares (desde el ícono de la barra) ----------

def lista_para_bandeja() -> list[dict]:
    return registro.lista({j.token for j in conectados()})


async def _olvidar(ids: set[str] | None) -> None:
    olvidados = registro.olvidar(ids)
    for t in olvidados:
        for j in jugadores.values():
            if j.token == t:
                j.token = None
                if j.ws is not None:
                    await j.ws.close()
    print(T(f"  Olvidé {len(olvidados)} celular(es). Para volver a usarlos hay que emparejarlos de nuevo (QR).",
            f"  Forgot {len(olvidados)} phone(s). To use them again, pair them again (QR)."))
    avisar_conexiones()


def olvidar_desde_bandeja(ids: set[str] | None) -> None:
    """Lo llama el ícono (otro hilo): hace el trabajo dentro del servidor."""
    if loop is not None:
        loop.call_soon_threadsafe(asyncio.ensure_future, _olvidar(ids))


# ---------- Biblioteca de Steam ----------
_biblio = {"hora": 0.0, "lista": []}
abierto = {"id": None}


def biblioteca() -> list[dict]:
    """Lista de juegos instalados (se relee cada 5 minutos, leerla cuesta un poco)."""
    if SIN_STEAM:
        return []
    if time.time() - _biblio["hora"] > 300:
        try:
            _biblio["lista"] = steam.juegos()
        except Exception as e:  # nunca tirar abajo el servidor por esto
            print(T("  No pude leer la biblioteca de Steam:", "  I couldn't read the Steam library:"), e)
        _biblio["hora"] = time.time()
    return _biblio["lista"]


def mensaje_abierto() -> str:
    j = next((j for j in biblioteca() if j["id"] == abierto["id"]), None)
    return f"j {j['id']} {j['tipo']} {j['nombre']}" if j else "j 0"


async def vigilar_juego():
    """Cada 4 segundos se fija qué juego está abierto y, si cambió, les avisa a los celulares."""
    while True:
        try:
            actual = None if SIN_STEAM else await asyncio.to_thread(lambda: steam.juego_abierto(biblioteca()))
        except Exception:
            actual = None
        if actual != abierto["id"]:
            abierto["id"] = actual
            await a_todos(mensaje_abierto())
        await asyncio.sleep(4)


# ---------- Arranque ----------

# ---------- La ventana de la PC (panel.py + web/panel.html) ----------

def _bandeja():
    try:
        import bandeja
        return bandeja
    except Exception:  # sin Windows o sin pystray: la ventana anda igual, sin esas opciones
        return None


def estado_panel() -> dict:
    import version
    ip = direccion["ip"]
    lugares = []
    for n in range(1, MAX_JUGADORES + 1):
        j = jugadores.get(n)
        if j is not None and j.ws is not None:
            c = registro.celulares.get(j.token, {})
            lugares.append({"numero": n, "nombre": c.get("nombre") or "Celular", "mando": j.tipo,
                            "conexion": getattr(j.ws, "tipo", "red")})
        else:
            lugares.append({"numero": n})
    juego = next((x for x in _biblio["lista"] if x["id"] == abierto["id"]), None)
    b = _bandeja()
    return {
        "version": version.VERSION, "idioma": T("es", "en"),
        "ip": ip, "direccion": f"http://{ip}:{PUERTO}", "codigo": registro.codigo,
        "sinRed": ip.startswith("127."),
        "jugadores": lugares, "celulares": registro.lista({j.token for j in conectados()}),
        "juego": juego["nombre"] if juego else None, "juegosSteam": len(_biblio["lista"]),
        "inicio": b.inicio_activado() if b else False,
        "buscarVersiones": b.buscar_versiones_activado() if b else False,
        "versionNueva": b.VERSION_NUEVA["v"] if b else None,
        "actividad": list(panel.actividad)[-30:],
        "bluetooth": bluetooth.estado,
    }


def accion_panel(que: str, datos: dict) -> dict:
    """Lo que se toca en la ventana. Corre dentro del servidor (no hace falta pasar de hilo)."""
    import version
    import webbrowser
    b = _bandeja()
    activar = datos.get("v") == "1"
    if que == "olvidar" and datos.get("id"):
        asyncio.ensure_future(_olvidar({datos["id"]}))
    elif que == "olvidarTodos":
        asyncio.ensure_future(_olvidar(None))
    elif que == "inicio" and b:
        b.cambiar_inicio(activar)
    elif que == "versiones" and b:
        b.guardar_config("buscarVersiones", activar)
    elif que == "descargar":
        webbrowser.open(version.PAGINA_RELEASES)
    elif que == "salir":
        loop.call_later(.4, soltar_todo_y_salir)  # que la respuesta llegue antes de cerrar
    else:
        return {"ok": False}
    return {"ok": True}


def abrir_panel() -> None:
    """Desde el ícono: trae la ventana (o la abre). Si no se puede, muestra la consola de siempre."""
    if not panel.abrir(PUERTO):
        if b := _bandeja():
            b.mostrar_ventana(True)


async def _abrir_panel_al_arrancar() -> None:
    """Al abrir el programa: cuando termina la animación aparece la ventana, y la consola se esconde."""
    import animacion
    animacion.listo.set()
    await asyncio.to_thread(animacion.terminada.wait, 8)
    b = _bandeja()
    if panel.abrir(PUERTO):
        if b:
            b.mostrar_ventana(False)
    elif b:
        b.mostrar_ventana(True)


def contexto_paginas() -> paginas.Contexto:
    return paginas.Contexto(web=WEB, es_celular_emparejado=lambda t: t in registro.celulares,
                            biblioteca=biblioteca, juego_abierto=lambda: abierto["id"],
                            url_qr=url_qr, codigo=lambda: registro.codigo,
                            panel_clave=lambda: panel.clave, panel_estado=estado_panel, panel_accion=accion_panel)


async def main():
    global loop, al_cambiar_conexiones
    loop = asyncio.get_running_loop()
    ip = ip_local()
    direccion["ip"] = ip
    crt, key = certs.preparar(ip)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(crt, key)
    opciones = dict(compression=None, ping_interval=5, ping_timeout=10)
    ctx = contexto_paginas()
    async with serve(atender, "0.0.0.0", PUERTO, process_request=paginas.servir_archivos(False, ctx), **opciones), \
            serve(atender, "0.0.0.0", PUERTO_SEGURO, process_request=paginas.servir_archivos(True, ctx), ssl=tls,
                  **opciones) as seguro:
        print()
        print(T("  CONTROL CELULAR listo. Escaneá este QR con la cámara del celular:",
                "  CONTROL CELULAR is ready. Scan this QR code with your phone's camera:"))
        print()
        paginas.mostrar_qr_en_consola(url_qr())
        print()
        print(T(f"  O abrí en Chrome:  http://{ip}:{PUERTO}   y poné el código  {registro.codigo}",
                f"  Or open in your browser:  http://{ip}:{PUERTO}   and enter the code  {registro.codigo}"))
        print(T(f"  (con el certificado ya instalado, la app es:  https://{ip}:{PUERTO_SEGURO})",
                f"  (with the certificate installed, the app is at:  https://{ip}:{PUERTO_SEGURO})"))
        print(T("  El celular tiene que estar en la misma red WiFi que esta PC. Hasta 4 celulares a la vez.",
                "  Your phone must be on the same WiFi network as this PC. Up to 4 phones at once."))
        print(T("  ¿No conecta? Cerrá y volvé a abrir: te ofrezco abrir el firewall (solo para tu red de casa).",
                "  Can't connect? Close and reopen it: I'll offer to open the firewall (only for your home network)."))
        print(T("  El ícono del control, al lado del reloj, tiene el QR y más opciones.",
                "  The controller icon next to the clock has the QR code and more options."))
        print()
        panel.capturar_actividad()  # desde acá, lo que se avisa también se ve en la ventana
        panel.guardar_clave(PUERTO)
        if os.environ.get("CONTROL_SIN_BANDEJA") != "1":
            try:
                import bandeja
                al_cambiar_conexiones = bandeja.iniciar(f"http://127.0.0.1:{PUERTO}/qr", soltar_todo_y_salir,
                                                         MINIMIZADO, lista_para_bandeja, olvidar_desde_bandeja,
                                                         abrir_panel=abrir_panel)
            except Exception as e:
                print(T("  (No pude poner el ícono en la barra de tareas:", "  (I couldn't add the tray icon:"), e, ")")
        if panel.debe_abrirse():
            asyncio.ensure_future(_abrir_panel_al_arrancar())
        await asyncio.to_thread(biblioteca)
        print(T(f"  Biblioteca de Steam: {len(biblioteca())} juegos", f"  Steam library: {len(biblioteca())} games"))
        asyncio.ensure_future(vigilar_juego())
        if enlaces.faro_activado():  # la app de Android encuentra la PC sola (WiFi y cable USB)
            asyncio.ensure_future(enlaces.faro(PUERTO))
        if enlaces.bluetooth_activado():  # y por Bluetooth, si la PC tiene
            asyncio.ensure_future(bluetooth.correr(atender))
        await seguro.serve_forever()


def soltar_todo_y_salir() -> None:
    panel.cerrar()
    for j in jugadores.values():
        try:
            j.soltar()
        except Exception:
            pass
    os._exit(0)


def correr() -> None:
    """Arranca el programa. Lo llama arranque.py, que muestra cualquier error en vez de cerrarse."""
    try:
        # Que los mensajes salgan al instante. Si la salida no es una ventana (va a un archivo), en UTF-8:
        # así se ven los acentos y el QR (en la ventana de Windows ya se ven siempre).
        if sys.stdout.isatty():
            sys.stdout.reconfigure(line_buffering=True)
        else:
            sys.stdout.reconfigure(line_buffering=True, encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    import version
    print()
    print(f"  === CONTROL CELULAR {version.VERSION} ===")
    print()
    if os.environ.get("CONTROL_SIN_FIREWALL") != "1":
        red.revisar(preguntar=not MINIMIZADO)  # firewall: solo pregunta si falta (o es la regla vieja)
    crear_primer_control()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except OSError as e:
        texto = T(f"\n  No pude arrancar: {e}", f"\n  I couldn't start: {e}")
        if getattr(e, "winerror", None) == 10048:
            texto += T("\n  Parece que Control Celular ya está abierto (mirá el ícono al lado del reloj).",
                       "\n  It looks like Control Celular is already open (check the icon next to the clock).")
        dialogos.avisar(texto, error=True)
        salir(1)
    except Exception as e:
        dialogos.avisar(T(f"\n  Error inesperado: {e!r}", f"\n  Unexpected error: {e!r}"), error=True)
        salir(1)


if __name__ == "__main__":
    correr()
