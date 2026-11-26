# Novedades

## 1.9.0

- **Animación de apertura en la app de Android:** al abrirla, el control aparece, el neón celeste → verde se enciende
  y sale el nombre (2,2 s; un toque la saltea). Mientras tanto la app ya busca la PC.
- **La app avisa cuando hay una versión nueva:** al conectarse, si el programa de la PC es más nuevo que la app, aparece
  «Hay una versión nueva de la app» con un botón para bajarla desde la misma PC (por Bluetooth, desde GitHub). Se
  instala encima, sin perder controles ni ajustes. (Anda desde esta versión en adelante: la 1.8.0 no sabe avisar.)
- **Arreglos de la app:** los carteles de la página ahora se ven (por ejemplo, ya se puede confirmar «Copiar ajustes de
  otro celular»); con el cable USB, si la PC cambia de dirección al activar el anclaje, la app la sigue sola; el
  buscador de PCs ya no se traba al salir y volver rápido a la app.
- **Pantalla completa de verdad:** las barras de Android ya no tapan la app al girar el celular, y la app usa también
  el costado de la cámara (antes quedaba una franja negra).
- **App 4 veces más liviana:** pasó de 1,8 MB a 0,4 MB (abre más rápido y ocupa menos memoria).
- Probada en un Galaxy A06 con Android 16: animación, búsqueda de la PC por WiFi, emparejamiento y botones (15 ms).

## 1.8.0

- **App de Android (`ControlCelular.apk`):** se instala en el celular y se conecta con la PC de tres formas, para que
  ande en cualquier casa:
  - **WiFi:** la app encuentra la PC sola (no hay que escribir direcciones ni escanear nada);
  - **cable USB:** enchufás el celular a la PC y activás «Anclaje USB»; la conexión va por el cable, sin pasar por
    el router (anda aunque el router no deje que los equipos se vean);
  - **Bluetooth:** si la PC tiene Bluetooth, se conectan directo, sin router.
  Es el mismo control de siempre (todos los modelos, el editor, el giroscopio), pero sin certificado, sin navegador
  y con la vibración andando siempre. El navegador sigue funcionando como antes, y en iPhone sigue siendo la página.
- **La ventana de la PC** tiene la pestaña «App de Android», con un QR para bajar la app (también se puede bajar
  desde la misma PC, sin internet en el celular), y muestra si cada jugador está por WiFi/cable o por Bluetooth.

## 1.7.1

- **Conecta aunque Windows tenga tu red como «Pública»:** Windows marca así casi toda red nueva, y entonces el
  celular no podía entrar (`ERR_CONNECTION_TIMED_OUT`). Ahora el firewall se abre para Control Celular sea la red
  privada o pública, siempre **solo para tu red de casa** (nadie de internet puede llegar, y para usar el control
  hace falta el código de emparejamiento). Ya no hace falta marcar la red como privada: el instalador dejó de
  preguntarlo. Al actualizar, la regla vieja se reemplaza sola.
- Ayuda nueva en «Problemas comunes» para el `ERR_CONNECTION_TIMED_OUT` (antivirus con firewall propio) y para el
  bloqueo del «Control inteligente de aplicaciones» de Windows 11 (código 4551).

## 1.7.0

- **Animación de arranque nueva: «tu celular ahora es tu control».** Sobre un fondo negro aparece un celular
  parado, gira hasta quedar acostado, se le prende la pantalla y aparece el control de neón. Se ve nítida
  también en pantallas escaladas (125 %, 150 %…).
- **El control del ícono parece más un control:** hombros redondeados con sus gatillos y agarres que se abren hacia
  abajo, como uno de verdad. Mismos colores y mismo neón (escritorio, menú Inicio, ícono del reloj, app del celular
  y animación).

## 1.6.0

- **Ventana nueva en la PC:** en lugar de la ventana negra de texto, una ventana propia con el QR, el código, los
  4 lugares de jugador (qué celular está en cada uno y si es Xbox o DualShock 4), el juego de Steam abierto, los
  celulares emparejados (con «Olvidar»), la actividad y ⚙ Opciones (abrir al prender la PC, avisos de versión nueva
  y Apagar). Si la cerrás, Control Celular sigue en el ícono al lado del reloj; si lo abrís otra vez, trae la misma
  ventana en vez de avisar «ya está abierto». Las preguntas (firewall, driver) ahora son carteles con Sí / No.
- **Animación de arranque:** al abrir Control Celular, el control de neón se enciende en el centro de la pantalla
  (unos 2 segundos, mientras el programa arranca) y después aparece la ventana con el QR. No sale al arrancar oculto
  con Windows ni al volver de minimizado.
- **Limpieza más completa:** al actualizar, el instalador también borra los restos temporales que dejaban las versiones
  portátiles anteriores a la 1.4.1.

## 1.5.0

- **Instalador:** `ControlCelular-Instalar-1.5.0.exe`. Con un solo permiso de Windows deja todo listo:
  - instala **ViGEmBus**, si falta, sin ventanas extra;
  - abre el firewall para el programa y **saca los bloqueos** que Windows le haya puesto (por ejemplo, si se cerró
    con «Cancelar» el cartel del firewall, el celular no podía conectarse);
  - si la red está como «Pública», ofrece marcarla como privada;
  - crea los íconos (escritorio y menú Inicio) y se desinstala desde «Agregar o quitar programas».
- **Actualizar sin ocupar lugar:** el instalador reemplaza la versión anterior y, con una casilla marcada de entrada,
  borra los instaladores y versiones portátiles viejas de Descargas y Escritorio y los restos temporales. Tus
  ajustes, controles editados y celulares emparejados no se tocan.
- **Escanear y jugar:** al escanear el QR, el celular entra **directo al control**. El certificado (para instalar la
  app y usar el giroscopio) pasa a ser opcional: menú ☰ → «Activar app y giroscopio».
- **Ícono nuevo:** un control con bordes de neón (celeste y verde) sobre fondo oscuro, en el escritorio, el menú
  Inicio, el ícono al lado del reloj y la app del celular.
- El programa instalado arranca más rápido (ya no se descomprime cada vez).
- Sigue estando la versión portátil `ControlCelular.exe`, que no se instala.

## 1.4.1

- **ViGEmBus viene incluido:** ya no hay que bajarlo aparte. Si la PC no tiene el driver, Control Celular pregunta
  «¿Lo instalo ahora?» y abre el instalador oficial (firmado por su autor), que viaja dentro del programa. Al
  terminar, Control Celular se vuelve a abrir solo.
- **Arreglo importante:** en una PC sin ViGEmBus, el programa se cerraba al instante sin mostrar nada. Ya no pasa.
- Si el programa no puede arrancar por cualquier otro motivo, muestra el error, lo guarda en `error.txt` (en
  `%LOCALAPPDATA%\ControlCelular`) y no se cierra solo.

## 1.4.0

- **Control de PS4:** un control nuevo con la forma de uno de PS4: L1/L2/R1/R2, un touchpad grande en el centro
  con Share y Options a los costados, cruceta, botón PS, △ ○ ✕ □ con sus colores y los dos sticks juntos abajo.
  Al elegirlo, la PC lo ve como un DualShock 4. Se puede editar como cualquier otro control.
- Por dentro: el código quedó ordenado en partes y hay más de 50 pruebas automáticas (`probar.bat`).

## 1.3.0

- **iPhone:** versión propia de la página del control y de la guía del certificado (archivos aparte de los de
  Android). La PC elige sola cuál mostrar según el celular, con la misma dirección y el mismo QR. Incluye el permiso
  del giroscopio, «Agregar a inicio» y los pasos del certificado de iPhone (perfil + confianza total). En iPhone no
  hay vibración, porque Safari no la permite. *Todavía no se probó en un iPhone de verdad.*
- **English:** la página del control, la guía del certificado, la ventana del programa, el ícono y un `README.en.md`.
  Sigue el idioma del celular y el de Windows; en ⚙ Opciones → Idioma se puede elegir a mano.

## 1.2.0

- **Modo DualShock 4 (control de PlayStation):** en ⚙ Opciones → «La PC lo ve como» elegís Xbox 360 o
  DualShock 4. Con DualShock 4, los botones se muestran como ✕ ○ □ △, L1/R1, L2/R2, Share, Options y PS, y se puede
  usar el **touchpad** desde el editor.
- **Giroscopio «Movimiento real» (solo DualShock 4):** el celular manda su giroscopio y su acelerómetro como el
  sensor de un control de PlayStation. Lo usan Steam (el giroscopio de Steam Input) y emuladores como Cemu o Yuzu.
- **Modo zurdo:** da vuelta el control como un espejo. Los grupos de botones, como el rombo, mantienen su orden.
- **Opciones más limpias:** un botón ⚙ al lado del ☰ abre una ventana con pestañas (General, Giroscopio y Sticks),
  con interruptores y una explicación corta en cada opción. El ☰ queda para elegir el control y las acciones.

## 1.1.0

**Descargá `ControlCelular.exe`** (abajo, en «Assets»). Es un solo archivo y no hace falta instalar nada más. Si Windows
muestra «Windows protegió su PC», tocá **Más información → Ejecutar de todas formas**: aparece porque el programa no
está firmado.

**Conectarse:**
- **QR al abrir el programa:** lo escaneás con la cámara del celular y entrás emparejado, sin escribir nada.
- **Ícono al lado del reloj:** desde ahí se muestra el QR, se oculta la ventana, se activa el arranque con Windows,
  se ven los celulares emparejados y se puede **desinstalar**.
- **Guía del certificado según la marca del celular:** Samsung, Xiaomi, Motorola, Pixel y otras.

**Jugar:**
- **Hasta 4 celulares a la vez**, cada uno es un control de Xbox distinto (jugador 1 a 4).
- **Botones turbo y fijo** desde el editor: el turbo se repite solo mientras lo mantenés; el fijo queda apretado
  con un toque y se suelta con otro.
- **Ajustes de cada stick:** zona muerta, respuesta (suave, normal o rápida) y recorrido.
- **Demora visible** al lado del número de jugador.
- **Modo noche.**

**Personalizar:**
- **Tus ajustes y controles editados quedan en la PC**, separados por celular, y se pueden copiar de un celular a
  otro.
- **Editor de control** con deshacer y cuadrícula.
- **Tutorial** la primera vez que lo abrís.

**Seguridad:**
- **Límite de intentos** con el código de emparejamiento.
- **Olvidar celulares** desde el ícono: pierden el permiso al instante.

**Además:**
- El programa avisa si hay una **versión nueva**. Se puede apagar.
- Licencia **MIT**.

## 1.0.0

Primera versión: el celular como control de Xbox 360 para la PC, con control completo, alargado y por juego de Steam,
giroscopio, vibración y editor de control.
