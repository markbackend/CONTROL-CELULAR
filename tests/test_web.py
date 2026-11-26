"""Las páginas del control (Android e iPhone) en un Chrome invisible.

La conexión con la PC se reemplaza por una falsa que anota cada mensaje que el celular manda. Cada prueba corre
un pedacito de JavaScript dentro de la página y deja el resultado en el título, que se lee de vuelta.
Si no está Google Chrome (o Edge), estas pruebas se saltean.
"""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
WEB = RAIZ / "web"
NAVEGADORES = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
               r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
               r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
NAVEGADOR = next((n for n in NAVEGADORES if os.path.exists(n)), None)
pytestmark = pytest.mark.skipif(NAVEGADOR is None, reason="no encontré Chrome ni Edge")

PAGINAS = ["index.html", "iphone.html"]
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 Version/18.1 Mobile Safari"

# Se inyecta antes que todo: conexión falsa, cuadros sin pantalla, permiso de giroscopio de iPhone y errores.
PREPARACION = r"""<script>
window.ERRORES = []; window.MSG = [];
addEventListener("error", (e) => ERRORES.push(String(e.message)));
window.requestAnimationFrame = (f) => setTimeout(f, 0);
window.DeviceMotionEvent = window.DeviceMotionEvent || function () {};
DeviceMotionEvent.requestPermission = () => Promise.resolve("granted");
window.WebSocket = class { constructor() { this.readyState = 1; window.WS = this;
    setTimeout(() => { this.onopen && this.onopen(); this.onmessage && this.onmessage({ data: "ok x" }); }, 0); }
  send(m) { MSG.push(m); } close() {} };
window.alert = () => {}; window.confirm = () => true;
const espera = (ms = 20) => new Promise((ok) => setTimeout(ok, ms));
const tocar = (el, tipo, x, y, id = 7) => el.dispatchEvent(new PointerEvent(tipo, { bubbles: true, pointerId: id,
  clientX: x, clientY: y }));
const centro = (el) => { const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
const apretar = async (el, ms = 30, id = 7) => { const [x, y] = centro(el); tocar(el, "pointerdown", x, y, id);
  await espera(ms); tocar(el, "pointerup", x, y, id); await espera(); };
window.RESULTADO = (r) => { document.title = "RES:" + JSON.stringify({ r, errores: ERRORES }); };
</script>"""


def ejecutar(pagina: str, prueba_js: str, ajustes: dict | None = None, idioma="es-AR", ua=None, ancho=800, alto=360,
             antes: str = ""):
    """Abre la página con los ajustes dados (localStorage), corre prueba_js (async) y devuelve su resultado."""
    html = (WEB / pagina).read_text("utf-8")
    for js in ["i18n.js", "plantillas.js"]:
        html = html.replace(f'<script src="/{js}"></script>', "<script>" + (WEB / js).read_text("utf-8") + "</script>")
    html = html.replace('const seguro = location.protocol === "https:";', "const seguro = true;")
    datos = {"token": "x", "tutorialVisto": "1", **(ajustes or {})}
    guardar = "localStorage.clear();" + "".join(f"localStorage.setItem({json.dumps(k)},{json.dumps(v)});"
                                                 for k, v in datos.items())
    html = html.replace("<title>", PREPARACION + f"<script>{guardar}{antes}</script><title>", 1)
    html = html.replace("</body>", "<script>setTimeout(async () => { try { RESULTADO(await (async () => {"
                        + prueba_js + "})()); } catch (e) { ERRORES.push('PRUEBA: ' + e); RESULTADO(null); } }, 150);"
                        "</script></body>")
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
    cmd = [NAVEGADOR, "--headless=new", "--disable-gpu", f"--lang={idioma}", f"--window-size={ancho},{alto}",
           "--virtual-time-budget=8000", "--dump-dom", Path(f.name).as_uri()]
    if ua:
        cmd.insert(1, f"--user-agent={ua}")
    salida = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=90).stdout
    os.unlink(f.name)
    m = re.search(r"<title>RES:(.*?)</title>", salida, re.S)
    assert m, "la página no terminó la prueba"
    datos = json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">"))
    assert datos["errores"] == [], datos["errores"]
    return datos["r"]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_carga_sin_errores_y_con_el_control(pagina):
    r = ejecutar(pagina, "return document.querySelectorAll('#pad3 .el').length;")
    assert r > 10


@pytest.mark.parametrize("pagina", PAGINAS)
def test_boton_a_y_cruceta_diagonal(pagina):
    r = ejecutar(pagina, """
      await apretar(document.querySelector('#pad3 [data-b=A]'));
      const dp = document.querySelector('#pad3 [data-dpad]'), b = dp.getBoundingClientRect();
      tocar(dp, 'pointerdown', b.right - 3, b.top + 3); await espera(); tocar(dp, 'pointerup', 0, 0); await espera();
      return MSG.filter((m) => /^[bt] /.test(m));""")
    assert r[:2] == ["b A 1", "b A 0"]
    assert set(r[2:4]) == {"b RIGHT 1", "b UP 1"} and set(r[4:6]) == {"b RIGHT 0", "b UP 0"}


@pytest.mark.parametrize("pagina", PAGINAS)
def test_turbo_y_fijo(pagina):
    control = {"el": [{"k": "btn", "x": 30, "y": 50, "d": 20, "b": "A", "txt": "A", "modo": "turbo"},
                      {"k": "btn", "x": 70, "y": 50, "d": 20, "b": "B", "txt": "B", "modo": "fijo"}]}
    r = ejecutar(pagina, """
      const A = document.querySelector('#pad3 [data-b=A]'), B = document.querySelector('#pad3 [data-b=B]');
      MSG.length = 0; await apretar(A, 260); const turbo = MSG.filter((m) => m[0] === 'b'); MSG.length = 0;
      await apretar(B); const fijo1 = MSG.slice(), quedo = B.classList.contains('on'); MSG.length = 0;
      await apretar(B); return { turbo, fijo1, quedo, fijo2: MSG.slice() };""",
                 {"modelo": "completo", "control_completo": json.dumps(control)})
    assert r["turbo"].count("b A 1") >= 2 and r["turbo"][-1] == "b A 0"
    assert r["fijo1"] == ["b B 1"] and r["quedo"] and r["fijo2"] == ["b B 0"]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_zona_muerta_y_recorrido_del_stick(pagina):
    r = ejecutar(pagina, """
      const el = document.querySelector('#pad3 .stick[data-s=L]'), [cx, cy] = centro(el);
      const rad = el.offsetWidth / 2 - el.firstElementChild.offsetWidth / 4, res = [];
      tocar(el, 'pointerdown', cx, cy); await espera();
      for (const f of [0.05, 0.5, 1]) { MSG.length = 0; tocar(el, 'pointermove', cx + rad * f, cy); await espera();
        const s = MSG.filter((m) => m.startsWith('s L')); res.push(s.length ? +s[s.length - 1].split(' ')[2] : null); }
      return res;""", {"dzL": "20", "alcL": "50"})
    assert r[0] in (None, 0)     # dentro de la zona muerta (20 %) no se mueve (queda en 0: no manda nada)
    assert r[1] == 1000          # con recorrido 50 %, a la mitad ya está al máximo
    assert r[2] in (None, 1000)  # más allá sigue al máximo (y no manda nada nuevo)


def _superpuestos_js():
    """JavaScript que busca elementos del control encimados (círculos como círculos, el resto como rectángulos)."""
    return r"""
      const els = [...document.querySelectorAll('#pad3 .el')].filter((e) => !e.matches('.barra3, .nombreJuego'));
      els.push(document.querySelector('#pad3 .barra3'));
      const forma = (e) => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
        const redondo = Math.abs(r.width - r.height) < 2 && (cs.borderRadius.includes('50%') || e.matches('.stick'));
        return { r, redondo, n: e.dataset.b || e.dataset.t || e.dataset.s || (e.matches('[data-dpad]') ? 'cruceta' : e.className) }; };
      const f = els.map(forma), malos = [];
      const chocan = (a, b) => {
        if (a.redondo && b.redondo) {
          const dx = (a.r.left + a.r.width / 2) - (b.r.left + b.r.width / 2), dy = (a.r.top + a.r.height / 2) - (b.r.top + b.r.height / 2);
          return Math.hypot(dx, dy) < (a.r.width + b.r.width) / 2 - 2; }
        const enc = (q) => q.redondo ? { l: q.r.left + q.r.width * .15, r: q.r.right - q.r.width * .15,
          t: q.r.top + q.r.height * .15, b: q.r.bottom - q.r.height * .15 } : { l: q.r.left, r: q.r.right, t: q.r.top, b: q.r.bottom };
        const p = enc(a), q = enc(b);
        return Math.min(p.r, q.r) - Math.max(p.l, q.l) > 2 && Math.min(p.b, q.b) - Math.max(p.t, q.t) > 2; };
      for (let i = 0; i < f.length; i++) for (let j = i + 1; j < f.length; j++) if (chocan(f[i], f[j])) malos.push(f[i].n + ' / ' + f[j].n);
      const fuera = f.filter((x) => x.r.left < -2 || x.r.top < -2 || x.r.right > innerWidth + 2 || x.r.bottom > innerHeight + 2).map((x) => x.n);
      return { malos, fuera };"""


CONTROLES = [("completo", {"modelo": "completo"}), ("alargado", {"modelo": "alargado"}),
             ("ps4", {"modelo": "ps4", "mando": "ds4"})] + [
    (t, {"modelo": "juego", "juegoElegido": json.dumps({"id": 1, "nombre": "Prueba", "tipo": t}), "tipo_1": t})
    for t in ["carreras", "disparos", "plataformas", "deportes", "pelea", "accion"]] + [
    ("perfil Sonic", {"modelo": "juego", "juegoElegido": json.dumps({"id": 2486820, "nombre": "Sonic", "tipo": "carreras"})})]


@pytest.mark.parametrize("nombre,ajustes", CONTROLES, ids=[c[0] for c in CONTROLES])
def test_ningun_control_tiene_botones_encimados(nombre, ajustes):
    r = ejecutar("index.html", _superpuestos_js(), ajustes)
    assert r["malos"] == [] and r["fuera"] == [], r


def test_modo_zurdo_mantiene_el_rombo_y_no_encima_nada():
    r = ejecutar("index.html", """
      const x = (b) => centro(document.querySelector('#pad3 [data-b=' + b + ']'))[0];
      const sL = centro(document.querySelector('#pad3 .stick[data-s=L]'))[0];
      const rombo = x('X') < x('B'), lado = sL > innerWidth / 2;
      return { rombo, lado, ...(await (async () => {""" + _superpuestos_js() + "})()) };", {"zurdo": "1"})
    assert r["rombo"] and r["lado"] and r["malos"] == []


def test_editor_guardar_y_restaurar():
    r = ejecutar("index.html", """
      document.getElementById('editor').click(); await espera();
      const y = document.querySelector('#pad3 [data-b=Y]'); await apretar(y);
      const f = document.getElementById('edFuncion'); f.value = 't:R+b:A'; f.dispatchEvent(new Event('change'));
      document.querySelector('[data-ed=guardar]').click(); await espera();
      const guardado = JSON.parse(localStorage.getItem('control_completo') || 'null');
      const enPantalla = !!document.querySelector('#pad3 [data-t=R][data-b=A]');
      const nadaMandado = !MSG.some((m) => /^[bt] /.test(m));
      document.getElementById('editor').click(); document.querySelector('[data-ed=restaurar]').click();
      document.querySelector('[data-ed=guardar]').click(); await espera();
      return { guardado: !!guardado, enPantalla, nadaMandado, despues: localStorage.getItem('control_completo') };""")
    assert r == {"guardado": True, "enPantalla": True, "nadaMandado": True, "despues": None}


@pytest.mark.parametrize("pagina", PAGINAS)
def test_ingles(pagina):
    r = ejecutar(pagina, """
      document.querySelector('#pad3 .ajBtn').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
      const visibles = (sel) => [...document.querySelectorAll(sel)].filter((e) => e.offsetParent).map((e) => e.innerText).join(' | ');
      const ajustes = visibles('#ajustes .fila b, .ajTabs button, .ajTitulo');
      document.getElementById('ajCerrar').click();
      document.querySelector('#pad3 .menuBtn').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
      return { ajustes, menu: visibles('#menu h2, #menu button:not([hidden])') };""",
                 idioma="en-US")
    for palabra in ["Night mode", "Left-handed mode", "Settings", "Language", "Choose your controller", "More"]:
        assert palabra in r["ajustes"] + r["menu"], palabra
    for palabra in ["Modo noche", "Opciones", "Elegí", "Volver", "Idioma"]:
        assert palabra not in r["ajustes"] + r["menu"], palabra


def test_iphone_lo_propio():
    r = ejecutar("iphone.html", """
      await espera(50);
      const visible = (id) => { const e = document.getElementById(id); return !!e && !e.closest('[hidden]') && !e.hidden; };
      return { vibrar: visible('optToque'), permiso: visible('filaPermiso'), inicio: visible('agregarInicio'),
               pantalla: visible('pantalla'), nombre: MSG.find((m) => m.startsWith('d ')) };""", ua=IPHONE_UA)
    assert r == {"vibrar": False, "permiso": True, "inicio": True, "pantalla": False, "nombre": "d iPhone"}


@pytest.mark.parametrize("pagina", PAGINAS)
def test_control_de_ps4(pagina):
    r = ejecutar(pagina, """
      document.querySelector('#pad3 .menuBtn').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
      document.querySelector('.modelo[data-m=ps4]').click(); await espera();
      const pideDS4 = MSG.includes('m ds4');
      await apretar(document.querySelector('#pad3 [data-b=TOUCH]'));
      await apretar(document.querySelector('#pad3 [data-b=A]'));
      const textos = [...document.querySelectorAll('#pad3 [data-b], #pad3 [data-t]')].map((e) => e.firstChild.textContent);
      return { pideDS4, guardado: localStorage.getItem('mando'), msg: MSG.filter((m) => m[0] === 'b'), textos };""")
    assert r["pideDS4"] and r["guardado"] == "ds4"
    assert r["msg"] == ["b TOUCH 1", "b TOUCH 0", "b A 1", "b A 0"]
    for t in ["✕", "○", "□", "△", "L1", "R2", "Touchpad", "Share", "Options", "PS"]:
        assert t in r["textos"], t


# ---------- La página dentro de la app de Android (el puente window.ControlCelularApp, simulado) ----------

APP_FALSA = r"""
window.APPLOG = { conectar: [], enviar: [], vibrar: [] };
window.ControlCelularApp = {
  pcs: () => JSON.stringify([{ ip: "192.168.0.244", puerto: 8765, nombre: "PC-SALA" }]),
  conectar: (d) => { APPLOG.conectar.push(JSON.parse(d));
    if (window.FALLA_BT && JSON.parse(d).tipo === "bt") { setTimeout(() => ccEvento("error", "sin bluetooth"), 0); return; }
    setTimeout(() => { ccEvento("open", ""); ccEvento("msg", "ok x"); ccEvento("msg", "n 2"); }, 0); },
  enviar: (m) => APPLOG.enviar.push(m), cerrar: () => {}, vibrar: (p) => APPLOG.vibrar.push(p),
  abrirAnclaje: () => { APPLOG.anclaje = true; }, version: () => "1.8.0",
  abrirEnlace: (u) => { APPLOG.enlace = u; },
};
"""


def test_app_elige_la_pc_y_manda_por_la_app():
    r = ejecutar("index.html", """
      const alAbrir = document.getElementById('buscarPC').classList.contains('ver');
      const lista = [...document.querySelectorAll('#pcLista button')].map((b) => b.textContent);
      document.querySelector('#pcLista button').click(); await espera(60);
      await apretar(document.querySelector('#pad3 [data-b=A]'));
      navigator.vibrate(12);
      document.getElementById('abrirAnclaje').click();
      return { alAbrir, lista, cerrado: !document.getElementById('buscarPC').classList.contains('ver'),
               destino: APPLOG.conectar[0], enviados: APPLOG.enviar, vibro: APPLOG.vibrar, anclaje: APPLOG.anclaje,
               guardado: JSON.parse(localStorage.getItem('destino')),
               sinPantallaCompleta: document.getElementById('pantalla').hidden,
               cambiarPC: !document.getElementById('cambiarPC').hidden };""", antes=APP_FALSA)
    assert r["alAbrir"] and r["lista"] == ["🖥 PC-SALA · 192.168.0.244"] and r["cerrado"]
    assert r["destino"] == {"tipo": "red", "ip": "192.168.0.244", "puerto": 8765, "nombre": "PC-SALA"}
    assert r["enviados"][0] == "a x" and "b A 1" in r["enviados"] and "b A 0" in r["enviados"]  # por la app
    assert r["vibro"] == ["12", "12"]  # el toque de «A» y el pedido a mano: los dos vibran a través de la app
    assert r["anclaje"] and r["guardado"]["ip"] == "192.168.0.244"
    assert r["sinPantallaCompleta"] and r["cambiarPC"]


def test_app_recuerda_la_pc_y_el_bluetooth():
    r = ejecutar("index.html", """
      const directo = !document.getElementById('buscarPC').classList.contains('ver');
      document.getElementById('cambiarPC').click(); await espera(30);
      const volvioALaLista = document.getElementById('buscarPC').classList.contains('ver');
      window.FALLA_BT = true;
      document.getElementById('usarBT').click(); await espera(60);
      return { directo, volvioALaLista, intentos: APPLOG.conectar.map((d) => d.tipo),
               listaOtraVez: document.getElementById('buscarPC').classList.contains('ver') };""",
                 ajustes={"destino": '{"tipo":"red","ip":"10.0.0.5","puerto":8765,"nombre":"PC"}'}, antes=APP_FALSA)
    assert r["directo"] and r["volvioALaLista"]
    assert r["intentos"] == ["red", "bt"] and r["listaOtraVez"]  # Bluetooth falló: avisa y vuelve a la lista


def test_app_animacion_de_apertura():
    # En la app: tapa la pantalla al abrir, se va sola (~2,2 s) y no vuelve a salir al recargar la página.
    # Chrome sin pantalla dice «animaciones reducidas»: acá se simula un celular normal. (Las imágenes del control no
    # están junto a la página de prueba: que se vea bien se comprueba con una captura, aparte.)
    normal = """const _mm = window.matchMedia.bind(window);
window.matchMedia = (q) => /reduced-motion/.test(q) ? { matches: false } : _mm(q);"""
    r = ejecutar("index.html", """
      const capa = document.getElementById('apertura');
      const alAbrir = !capa.hidden;
      await espera(4600);
      return { alAbrir, alFinal: capa.hidden, vista: sessionStorage.getItem('aperturaVista') };""",
                 antes=APP_FALSA + normal)
    assert r["alAbrir"] and r["alFinal"] and r["vista"] == "1"
    # En el navegador (sin la app) no sale
    r = ejecutar("index.html", "return { tapa: !document.getElementById('apertura').hidden };")
    assert not r["tapa"]


def test_app_avisa_si_la_pc_tiene_una_app_mas_nueva():
    r = ejecutar("index.html", """
      await espera(60);
      const capa = document.getElementById('appNueva');
      ccEvento("msg", "app 1.8.0"); await espera(10);
      const alDia = capa.classList.contains('ver');
      ccEvento("msg", "app 1.10.0"); await espera(10);
      const vieja = capa.classList.contains('ver'), texto = document.getElementById('appNuevaTexto').textContent;
      document.getElementById('appNuevaBajar').click(); await espera(10);
      ccEvento("msg", "app 1.10.0"); await espera(10);
      return { alDia, vieja, texto, enlace: APPLOG.enlace, otraVez: capa.classList.contains('ver') };""",
                 ajustes={"destino": '{"tipo":"red","ip":"192.168.0.244","puerto":8765,"nombre":"PC-SALA"}'},
                 antes=APP_FALSA)
    assert not r["alDia"] and r["vieja"] and "1.8.0" in r["texto"] and "1.10.0" in r["texto"]
    assert r["enlace"] == "http://192.168.0.244:8765/app.apk"
    assert not r["otraVez"]  # una vez por apertura de la app


def test_app_sigue_a_la_pc_si_cambia_de_direccion():
    # Con el cable USB la dirección de la PC cambia cada vez que se activa el anclaje: la app usa la que avisa ahora.
    r = ejecutar("index.html", """
      await espera(60);
      return { destino: APPLOG.conectar[0], guardado: JSON.parse(localStorage.getItem('destino')) };""",
                 ajustes={"destino": '{"tipo":"red","ip":"192.168.42.10","puerto":8765,"nombre":"PC-SALA"}'},
                 antes=APP_FALSA)
    assert r["destino"]["ip"] == "192.168.0.244" and r["guardado"]["ip"] == "192.168.0.244"
