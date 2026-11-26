"""El servidor de verdad, arrancado en otros puertos con una carpeta temporal y controles de mentira.

Le habla como si fueran celulares: emparejar, varios jugadores, ajustes, DualShock 4, páginas y QR.
"""

import asyncio
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from websockets.asyncio.client import connect

RAIZ = Path(__file__).resolve().parent.parent
PUERTO, PUERTO_SEGURO = 18765, 18443
ANDROID = "Mozilla/5.0 (Linux; Android 14; SM-A065M) Chrome/130 Mobile"
IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) Safari/604.1"


@pytest.fixture(scope="module")
def servidor():
    datos = Path(tempfile.mkdtemp(prefix="control-celular-servidor-"))
    entorno = dict(os.environ, CONTROL_DATOS=str(datos), CONTROL_PUERTO=str(PUERTO),
                   CONTROL_PUERTO_SEGURO=str(PUERTO_SEGURO), CONTROL_MANDO_FALSO="1", CONTROL_SIN_BANDEJA="1",
                   CONTROL_SIN_FIREWALL="1", CONTROL_SIN_STEAM="1", PYTHONIOENCODING="utf-8")
    proc = subprocess.Popen([sys.executable, "-u", str(RAIZ / "server.py")], cwd=RAIZ, env=entorno,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    lineas, codigo = [], None
    fin = time.time() + 30
    while time.time() < fin and codigo is None:
        linea = proc.stdout.readline()
        if not linea:
            break
        lineas.append(linea)
        m = re.search(r"(?:código|code)\s+(\d{4})", linea)
        if m:
            codigo = m.group(1)
    if codigo is None:
        proc.kill()
        pytest.fail("El servidor no arrancó:\n" + "".join(lineas))
    threading.Thread(target=lambda: [None for _ in proc.stdout], daemon=True).start()  # vaciar la salida
    ctx = ssl.create_default_context(cafile=str(datos / "certs" / "ca.crt"))
    yield {"codigo": codigo, "ssl": ctx, "datos": datos}
    proc.kill()
    proc.wait(10)
    shutil.rmtree(datos, ignore_errors=True)


def correr(corrutina):
    return asyncio.run(corrutina)


async def entrar(srv, clave):
    """Conecta un "celular" y devuelve (ws, {tipo: mensaje}) con lo que la PC manda al conectarse."""
    ws = await connect(f"wss://127.0.0.1:{PUERTO_SEGURO}/ws", ssl=srv["ssl"])
    await ws.send("a " + clave)
    primero = await ws.recv()
    recibidos = {primero.split(" ")[0]: primero}
    if primero.startswith("ok"):
        while "j" not in recibidos:
            m = await ws.recv()
            recibidos[m.split(" ")[0]] = m
    return ws, recibidos


async def esperar(ws, prefijo):
    while True:
        m = await ws.recv()
        if m.startswith(prefijo):
            return m


def get(url, ua=ANDROID, ctx=None):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ua}), context=ctx, timeout=10)
        return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""


def test_emparejar_reconectar_y_codigo_equivocado(servidor):
    async def prueba():
        ws, m = await entrar(servidor, servidor["codigo"])
        token = m["ok"].split()[1]
        assert m["n"] == "n 1" and m["m"] == "m xbox" and m["c"] == "c {}"
        assert m["app"] == "app " + __import__("version").VERSION  # para que la app avise si está vieja
        await ws.close()
        ws, m = await entrar(servidor, token)  # vuelve con el token, sin código
        assert m["n"] == "n 1"
        await ws.close()
        malo = "0000" if servidor["codigo"] != "0000" else "1111"
        ws, m = await entrar(servidor, malo)
        assert "no" in m
        await ws.close()
    correr(prueba())


def test_varios_jugadores_ping_ajustes_y_ds4(servidor):
    async def prueba():
        a, ma = await entrar(servidor, servidor["codigo"])
        b, mb = await entrar(servidor, servidor["codigo"])
        assert {ma["n"], mb["n"]} == {"n 1", "n 2"}
        await a.send("p 123")
        assert await esperar(a, "p ") == "p 123"
        await a.send("d PruebaA")
        await a.send("k sens 7")
        await a.send("m ds4")
        assert await esperar(a, "m ") == "m ds4"
        await b.send("l")
        lista = json.loads((await esperar(b, "lc "))[3:])
        assert [c["nombre"] for c in lista] == ["PruebaA"]
        await b.send("cp " + lista[0]["id"])
        assert json.loads((await esperar(b, "cc "))[3:]) == {"sens": "7"}
        token_a = ma["ok"].split()[1]
        await a.close()
        await b.close()
        await asyncio.sleep(0.3)
        a, ma = await entrar(servidor, token_a)  # recuerda sus ajustes y que es DualShock 4
        assert ma["c"] == 'c {"sens": "7"}' and ma["m"] == "m ds4"
        for m in ["b A 1", "b UP 1", "b RIGHT 1", "t L 255", "s L 500 -500", "g 1 2 3 4 5 6", "r"]:
            await a.send(m)
        await a.send("p 1")
        assert await esperar(a, "p ") == "p 1"  # siguió vivo después de todos esos mensajes
        await a.close()
    correr(prueba())


def test_maximo_4_celulares(servidor):
    async def prueba():
        conexiones = [await entrar(servidor, servidor["codigo"]) for _ in range(4)]
        quinto, m = await entrar(servidor, servidor["codigo"])
        assert "lleno" in m
        for ws, _ in conexiones + [(quinto, None)]:
            await ws.close()
    correr(prueba())


def test_cada_celular_recibe_su_pagina(servidor):
    ctx = servidor["ssl"]
    for ua, titulo in [(ANDROID, "<title>Control Celular</title>"), (IPHONE, "<title>Control Celular (iPhone)</title>")]:
        status, html = get(f"https://127.0.0.1:{PUERTO_SEGURO}/", ua, ctx)
        assert status == 200 and titulo in html
    for ua, titulo in [(ANDROID, "<title>Configurar Control Celular</title>"),
                       (IPHONE, "<title>Configurar Control Celular (iPhone)</title>")]:
        status, html = get(f"http://127.0.0.1:{PUERTO}/", ua)
        assert status == 200 and titulo in html
    for archivo in ["i18n.js", "plantillas.js", "sw.js", "manifest.webmanifest"]:
        assert get(f"https://127.0.0.1:{PUERTO_SEGURO}/{archivo}", ctx=ctx)[0] == 200, archivo
    assert get(f"http://127.0.0.1:{PUERTO}/../server.py")[0] == 404  # no se puede salir de la carpeta web


def test_biblioteca_qr_y_certificado(servidor):
    ctx = servidor["ssl"]
    assert get(f"https://127.0.0.1:{PUERTO_SEGURO}/juegos", ctx=ctx)[0] == 403  # sin token, no
    token = json.loads((servidor["datos"] / "tokens.json").read_text("utf-8"))
    status, cuerpo = get(f"https://127.0.0.1:{PUERTO_SEGURO}/juegos?t={next(iter(token))}", ctx=ctx)
    assert status == 200 and json.loads(cuerpo)["juegos"] == []
    status, html = get(f"http://127.0.0.1:{PUERTO}/qr")  # desde la misma PC, sí
    assert status == 200 and servidor["codigo"] in html
    assert get(f"http://127.0.0.1:{PUERTO}/ca.crt")[0] == 200


def test_ventana_de_la_pc(servidor):
    """La ventana (panel): solo desde esta PC, por HTTP y con la clave; muestra los jugadores conectados."""
    clave = json.loads((servidor["datos"] / "panel.clave").read_text("utf-8"))["clave"]
    base = f"http://127.0.0.1:{PUERTO}/panel"
    status, html = get(base)
    assert status == 200 and "Control Celular" in html
    assert get(f"{base}/estado")[0] == 403                      # sin clave, no
    assert get(f"{base}/estado?k=otra-clave")[0] == 403         # con otra clave, tampoco
    assert get(f"https://127.0.0.1:{PUERTO_SEGURO}/panel/estado?k={clave}", ctx=servidor["ssl"])[0] == 403
    status, cuerpo = get(f"{base}/estado?k={clave}")
    e = json.loads(cuerpo)
    assert status == 200 and e["codigo"] == servidor["codigo"] and len(e["jugadores"]) == 4

    async def con_un_celular():
        ws, _ = await entrar(servidor, servidor["codigo"])
        await ws.send("d Celular de prueba")
        await asyncio.sleep(.3)
        estado = json.loads(get(f"{base}/estado?k={clave}")[1])
        await ws.close()
        return estado

    e = correr(con_un_celular())
    assert any(j.get("nombre") == "Celular de prueba" for j in e["jugadores"])
    assert any("conectado" in a["texto"] or "connected" in a["texto"] for a in e["actividad"])
    assert json.loads(get(f"{base}/accion?k={clave}&que=no-existe")[1]) == {"ok": False}


def test_la_app_de_android_se_puede_bajar():
    status, svg = get(f"http://127.0.0.1:{PUERTO}/qr-app.svg")
    assert status == 200 and "<svg" in svg
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:{PUERTO}/app.apk", timeout=10)
        datos = r.read()
        assert datos[:2] == b"PK" and r.headers["Content-Type"] == "application/vnd.android.package-archive"
    except urllib.error.HTTPError as e:  # sin las herramientas de Android no se arma la app: avisa con un 404
        assert e.code == 404
