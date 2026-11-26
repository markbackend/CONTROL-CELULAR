// Idiomas de la página del control: español (el texto original) e inglés.
// El idioma se elige solo según el celular, o a mano en ⚙ Opciones → Idioma ("idioma": auto | es | en).
// Cómo funciona: los textos quedan escritos en español; si el idioma es inglés, al cargar se reemplazan
// usando este diccionario (traducirDOM) y el código usa tr("texto") para lo que arma mientras funciona.
(() => {
  const EN = {
    // ---- Conexión y emparejamiento
    "Escribí el código que aparece en la PC": "Type the code shown on the PC",
    "Conectar": "Connect",
    "Código incorrecto": "Wrong code",
    "Demasiados códigos equivocados. Esperá {n} segundos y probá de nuevo.": "Too many wrong codes. Wait {n} seconds and try again.",
    "Ya hay 4 celulares conectados a esta PC.": "There are already 4 phones connected to this PC.",
    "Girá el celular (acostado) ↻": "Turn your phone sideways ↻",
    // ---- App de Android: elegir la PC
    "Conectá con tu PC": "Connect to your PC",
    "Buscando Control Celular…": "Looking for Control Celular…",
    "Buscando Control Celular… ¿Está abierto en la PC?": "Looking for Control Celular… Is it open on the PC?",
    "Tocá tu PC:": "Tap your PC:",
    "El celular y la PC en la misma red. Tu PC aparece arriba sola.": "Phone and PC on the same network. Your PC shows up above by itself.",
    "🔌 Cable USB": "🔌 USB cable",
    "Enchufá el celular a la PC con el cable y activá «Anclaje USB». Tu PC aparece arriba sola.": "Plug your phone into the PC with its cable and turn on “USB tethering”. Your PC shows up above by itself.",
    "Abrir «Anclaje USB»": "Open “USB tethering”",
    "Si la PC tiene Bluetooth. Dejá Control Celular abierto en la PC: se conecta solo.": "If the PC has Bluetooth. Keep Control Celular open on the PC: it connects by itself.",
    "Conectar por Bluetooth": "Connect via Bluetooth",
    "Escribir la dirección de la PC a mano": "Type the PC's address",
    "Cambiar de PC o de conexión": "Change PC or connection",
    "Hay una versión nueva de la app": "There's a new version of the app",
    "Tenés la {n}": "You have {n}", "y la PC tiene la {n}.": "and the PC has {n}.",
    "Más tarde": "Later", "Bajarla": "Download it",
    "Se instala encima de esta: no perdés tus controles ni tus ajustes.": "It installs over this one: you keep your controllers and settings.",
    "Por Bluetooth no se puede ver la lista de juegos: elegí el tipo de control en «Control para».": "The game list isn't available over Bluetooth: pick the controller type in “Controller for”.",
    // ---- Menú ☰
    "Elegí el control": "Choose your controller",
    "Completo (Xbox)": "Full (Xbox)",
    "Alargado (1, 2, A, B)": "Sideways remote (1, 2, A, B)",
    "Por juego (Steam)": "Per game (Steam)", "PS4 (DualShock 4)": "PS4 (DualShock 4)",
    "Control para": "Controller for",
    "(sugerido)": "(suggested)",
    "Más": "More",
    "⚙ Opciones": "⚙ Settings",
    "✏️ Editor de control": "✏️ Controller editor",
    "Copiar ajustes de otro celular": "Copy settings from another phone",
    "Ver tutorial": "Show tutorial",
    "Pantalla completa": "Full screen",
    "Instalar app": "Install app",
    "Activar app y giroscopio": "Enable app and gyro",
    "Volver al control": "Back to the controller",
    "Agregar a inicio (iPhone)": "Add to Home Screen (iPhone)",
    // ---- ⚙ Opciones
    "Opciones": "Settings", "Menú": "Menu", "⚙ Opciones": "⚙ Settings", "General": "General", "Giroscopio": "Gyro", "Sticks": "Sticks", "Listo": "Done",
    "Vibrar al tocar": "Vibrate on tap", "Un toquecito cada vez que apretás un botón.": "A short buzz every time you press a button.",
    "Vibración del juego": "Game rumble", "El celular vibra cuando el juego hace vibrar el control.": "Your phone vibrates when the game rumbles the controller.",
    "Modo noche": "Night mode", "Colores oscuros, para jugar con poca luz.": "Dark colors, for playing in low light.",
    "Modo zurdo": "Left-handed mode", "Da vuelta el control como un espejo.": "Flips the controller like a mirror.",
    "La PC lo ve como": "The PC sees it as", "DualShock 4 sirve para juegos y emuladores de PlayStation.": "DualShock 4 is for PlayStation games and emulators.",
    "Idioma": "Language", "Automático": "Automatic", "El idioma de la página del control.": "The language of the controller page.",
    "En iPhone, Safari no deja que una página web vibre.": "On iPhone, Safari doesn't let web pages vibrate.",
    "Modo": "Mode", "Mover el celular para controlar el juego.": "Move your phone to control the game.",
    "Apagado": "Off", "Volante (stick izq.)": "Steering wheel (left stick)", "Apuntar (stick der.)": "Aim (right stick)",
    "Movimiento real (DualShock 4)": "Real motion (DualShock 4)",
    "Sensibilidad": "Sensitivity", "Cuánto responde a cada movimiento.": "How much it reacts to each movement.",
    "Invertir horizontal": "Invert horizontal", "Si gira para el lado contrario.": "If it turns the wrong way.",
    "Invertir vertical": "Invert vertical", "Si sube cuando querés bajar.": "If it goes up when you want it to go down.",
    "Centrar volante": "Center the wheel", "Sostené el celular derecho y tocá.": "Hold your phone straight and tap.", "Centrar": "Center",
    "Permitir el giroscopio (iPhone)": "Allow the gyro (iPhone)", "El iPhone pide permiso para usar el movimiento.": "iPhone asks for permission to use motion.",
    "Permitir": "Allow", "Vibración": "Vibration",
    "Para instalarla: en Safari tocá Compartir (el cuadrado con la flecha) → «Agregar a inicio». Después abrila desde el ícono.":
      "To install it: in Safari tap Share (the square with the arrow) → “Add to Home Screen”. Then open it from the icon.",
    "Stick izquierdo": "Left stick", "Stick derecho": "Right stick",
    "Zona muerta": "Dead zone", "Respuesta": "Response", "Recorrido": "Travel",
    "Suave": "Smooth", "Normal": "Normal", "Rápida": "Fast",
    "Zona muerta:": "Dead zone:", "Respuesta:": "Response:", "Recorrido:": "Travel:",
    "cuánto mover antes de que responda (más = no se mueve solo).": "how far to move before it reacts (more = it won't drift).",
    "suave es más precisa en movimientos chicos (ideal para apuntar).": "smooth is more precise for small movements (great for aiming).",
    "cuánto mover el dedo para llegar al máximo.": "how far to move your finger to reach the maximum.",
    // ---- Lista de juegos y copiar ajustes
    "Tus juegos de Steam": "Your Steam games", "Cambiar solo al juego que abro en la PC": "Switch automatically to the game I open on the PC",
    "Volver": "Back", "Cargando tus juegos…": "Loading your games…", "Abierto ahora": "Open now",
    "No encontré juegos de Steam instalados en la PC.": "I couldn't find any Steam games installed on the PC.",
    "No pude traer la lista. ¿Está conectado el control (puntito verde)?": "I couldn't get the list. Is the controller connected (green dot)?",
    "Buscando…": "Searching…", "Primero conectate a la PC (puntito verde).": "Connect to the PC first (green dot).",
    "Elegí de qué celular copiar:": "Choose which phone to copy from:",
    "No hay otros celulares con ajustes guardados en esta PC.": "There are no other phones with saved settings on this PC.",
    " · usado hoy": " · used today", " · hace {n} días": " · {n} days ago",
    "¿Copiar los ajustes de «{n}»? Se reemplazan los de este celular (controles editados y opciones).":
      "Copy the settings from “{n}”? This phone's settings (edited controllers and options) will be replaced.",
    // ---- Editor
    "Editor de control": "Controller editor", "+ Botón": "+ Button", "+ Stick": "+ Stick", "+ Cruceta": "+ D-pad",
    "↶ Deshacer": "↶ Undo", "▦ Cuadrícula": "▦ Grid", "⇅ Barras": "⇅ Bars", "Restaurar original": "Restore original",
    "Cancelar": "Cancel", "Guardar": "Save",
    "Tocá un botón para cambiarlo, o arrastralo para moverlo.": "Tap a button to change it, or drag it to move it.",
    "Tamaño": "Size", "Redondo / píldora": "Round / pill", "Manda": "Sends", "Es el": "It's the",
    "stick izquierdo": "left stick", "stick derecho": "right stick",
    "Normal ": "Normal", "⚡ Turbo (se repite solo)": "⚡ Turbo (repeats by itself)", "📌 Fijo (un toque aprieta, otro suelta)": "📌 Toggle (tap to press, tap again to release)",
    "Texto": "Text", "Texto chico": "Small text", "Duplicar": "Duplicate", "Borrar": "Delete",
    "Gris": "Gray", "Blanco (oscuro en modo noche)": "White (dark in night mode)", "Verde": "Green", "Rojo": "Red", "Azul": "Blue",
    "Amarillo": "Yellow", "Violeta": "Purple", "Naranja": "Orange", "Negro": "Black",
    "RT + A (derrape)": "RT + A (drift)", "Guide ●": "Guide ●", "L3 (apretar stick izq.)": "L3 (press left stick)",
    "R3 (apretar stick der.)": "R3 (press right stick)", "Touchpad (solo DualShock 4)": "Touchpad (DualShock 4 only)",
    "Cruceta ▲": "D-pad ▲", "Cruceta ▼": "D-pad ▼", "Cruceta ◀": "D-pad ◀", "Cruceta ▶": "D-pad ▶",
    // ---- Tutorial
    "Saltar": "Skip", "Siguiente": "Next", "¡A jugar!": "Let's play!",
    "¡Listo, estás conectado!": "Done, you're connected!",
    "El puntito verde de arriba indica que el control está conectado a la PC. Al lado ves tu número de jugador y la demora (ms).":
      "The green dot at the top means the controller is connected to the PC. Next to it you'll see your player number and the delay (ms).",
    "Elegí tu control": "Choose your controller",
    "En el menú ☰ elegís entre Completo, Alargado o Por juego: muestra tus juegos de Steam y arma un control cómodo para cada uno.":
      "In the ☰ menu you choose Full, Sideways remote or Per game: it shows your Steam games and builds a comfortable controller for each one.",
    "Hacelo a tu gusto": "Make it yours",
    "En ☰ → Editor de control movés, agrandás, pintás y cambiás cualquier botón. Tus cambios se guardan en la PC.":
      "In ☰ → Controller editor you can move, resize, recolor and change any button. Your changes are saved on the PC.",
    "En ⚙ ajustás todo: vibración, modo noche, modo zurdo, el giroscopio (volante o apuntar) y la respuesta de los sticks.":
      "In ⚙ you set everything up: vibration, night mode, left-handed mode, the gyro (steering or aiming) and stick response.",
    // ---- Nombres de los controles y de los botones (plantillas.js)
    "Carreras": "Racing", "Disparos": "Shooter", "Plataformas": "Platformer", "Deportes": "Sports", "Pelea": "Fighting",
    "Completo (acción, aventura, estrategia)": "Full (action, adventure, strategy)", "Propio de Sonic Racing": "Sonic Racing's own",
    "Alargado": "Sideways remote",
    "Acelerar": "Accelerate", "Frenar": "Brake", "Derrape": "Drift", "+ acelera": "+ accelerates", "RT + acelera": "RT + accelerates",
    "Ítem": "Item", "Atrás": "Look back", "poder": "power", "Apuntar": "Aim", "Disparar": "Shoot", "Agachar": "Crouch",
    "Recargar": "Reload", "Arma": "Weapon", "Correr": "Sprint", "Golpe": "Melee",
  };

  const elegido = (() => { try { return localStorage.getItem("idioma") || "auto"; } catch (e) { return "auto"; } })();
  const idioma = elegido === "es" || elegido === "en" ? elegido
    : ((navigator.language || "es").toLowerCase().startsWith("es") ? "es" : "en");
  document.documentElement.lang = idioma;

  window.IDIOMA = idioma;
  window.tr = (s, n) => {
    let t = idioma === "en" && EN[s] !== undefined ? EN[s] : s;
    if (n !== undefined) t = t.replace("{n}", n);
    return t;
  };
  // Traduce todos los textos de una parte de la página (y los title / placeholder).
  window.traducirDOM = (raiz) => {
    if (idioma !== "en" || !raiz) return;
    const recorrer = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT);
    const nodos = [];
    while (recorrer.nextNode()) nodos.push(recorrer.currentNode);
    for (const n of nodos) {
      const p = n.parentNode && n.parentNode.nodeName;
      if (p === "SCRIPT" || p === "STYLE") continue;
      const limpio = n.nodeValue.replace(/\s+/g, " ").trim();
      if (limpio && EN[limpio] !== undefined) {
        const antes = n.nodeValue.match(/^\s*/)[0], despues = n.nodeValue.match(/\s*$/)[0];
        n.nodeValue = antes + EN[limpio] + despues;
      }
    }
    raiz.querySelectorAll && raiz.querySelectorAll("[title],[placeholder]").forEach((el) => {
      for (const a of ["title", "placeholder"]) {
        const v = el.getAttribute(a);
        if (v && EN[v] !== undefined) el.setAttribute(a, EN[v]);
      }
    });
  };
})();
