package io.github.markbackend.controlcelular

import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.Configuration
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.provider.Settings
import android.view.View
import android.view.WindowInsets
import android.view.WindowInsetsController
import android.view.WindowManager
import android.webkit.JavascriptInterface
import android.webkit.JsResult
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.webkit.WebViewAssetLoader
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayInputStream
import java.net.HttpURLConnection
import java.net.URL

/**
 * La app de Control Celular: muestra la misma página del control que sirve la PC (la lleva adentro, carpeta web/)
 * y le da a esa página lo que el navegador no puede:
 *  - encontrar la PC sola (Buscador: el aviso de la PC por WiFi o por el cable USB),
 *  - conectarse por WiFi / cable USB (ConexionRed) o por Bluetooth (ConexionBluetooth),
 *  - vibrar y quedar siempre en pantalla completa y acostada.
 * La página habla con la app a través de window.ControlCelularApp (Puente) y recibe los eventos en window.ccEvento.
 */
class MainActivity : Activity() {

    private lateinit var web: WebView
    private lateinit var buscador: Buscador
    private val principal = Handler(Looper.getMainLooper())

    @Volatile private var conexion: Conexion? = null
    @Volatile private var pcIp: String? = null
    @Volatile private var pcPuerto = 8765
    private var esperandoBluetooth = false

    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        // Toda la pantalla, también al lado de la cámara (si no, queda una franja negra) y detrás de las barras.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            window.attributes = window.attributes.apply {
                layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.setDecorFitsSystemWindows(false)
            // Android vuelve a mostrar las barras cuando el celular gira (y al deslizar desde el borde): si aparecen,
            // se vuelven a esconder a los 2,5 s (alcanza para usarlas si uno las sacó a propósito).
            window.decorView.setOnApplyWindowInsetsListener { vista, insets ->
                if (insets.isVisible(WindowInsets.Type.statusBars()) || insets.isVisible(WindowInsets.Type.navigationBars())) {
                    principal.removeCallbacks(esconderBarras)
                    principal.postDelayed(esconderBarras, 2500)
                }
                vista.onApplyWindowInsets(insets)
            }
        }
        buscador = Buscador(this)

        val cargador = WebViewAssetLoader.Builder()
            .addPathHandler("/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()
        web = WebView(this)
        web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            textZoom = 100
            setSupportZoom(false)
            builtInZoomControls = false
        }
        web.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(vista: WebView, pedido: WebResourceRequest): WebResourceResponse? {
                val url = pedido.url
                if (url.host == "appassets.androidplatform.net" && url.path?.startsWith("/pc/") == true) {
                    return pedirALaPC(url)
                }
                return cargador.shouldInterceptRequest(url)
            }
        }
        // Sin esto, el WebView no muestra los carteles de la página (alert/confirm): confirm() daría siempre «no».
        web.webChromeClient = object : WebChromeClient() {
            override fun onJsAlert(vista: WebView, url: String?, texto: String?, resultado: JsResult): Boolean {
                cartel(texto, false, resultado)
                return true
            }
            override fun onJsConfirm(vista: WebView, url: String?, texto: String?, resultado: JsResult): Boolean {
                cartel(texto, true, resultado)
                return true
            }
        }
        web.addJavascriptInterface(Puente(), "ControlCelularApp")
        setContentView(web)
        pantallaCompleta()
        web.loadUrl("https://appassets.androidplatform.net/index.html")
    }

    override fun onResume() {
        super.onResume()
        pantallaCompleta()
        buscador.empezar()
    }

    override fun onPause() {
        buscador.parar()
        super.onPause()
    }

    override fun onDestroy() {
        conexion?.cerrar()
        conexion = null
        web.destroy()
        super.onDestroy()
    }

    override fun onWindowFocusChanged(foco: Boolean) {
        super.onWindowFocusChanged(foco)
        if (foco) pantallaCompleta()
    }

    override fun onConfigurationChanged(nueva: Configuration) {
        super.onConfigurationChanged(nueva)
        pantallaCompleta()  // al girar, Android vuelve a mostrar las barras
    }

    private val esconderBarras = Runnable { if (hasWindowFocus()) pantallaCompleta() }

    @Deprecated("Atrás deja la app abierta de fondo, sin cortar la conexión")
    override fun onBackPressed() {
        moveTaskToBack(true)
    }

    private fun pantallaCompleta() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.insetsController?.let {
                it.hide(WindowInsets.Type.systemBars())
                it.systemBarsBehavior = WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            }
        } else {
            @Suppress("DEPRECATION")
            window.decorView.systemUiVisibility = (View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY or View.SYSTEM_UI_FLAG_FULLSCREEN
                or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION)
        }
    }

    private fun cartel(texto: String?, pregunta: Boolean, resultado: JsResult) {
        if (isFinishing) { resultado.cancel(); return }
        val dialogo = AlertDialog.Builder(this, android.R.style.Theme_DeviceDefault_Dialog_Alert)
            .setMessage(texto ?: "")
            .setPositiveButton(android.R.string.ok) { _, _ -> resultado.confirm() }
            .setOnCancelListener { resultado.cancel() }
        if (pregunta) dialogo.setNegativeButton(android.R.string.cancel) { _, _ -> resultado.cancel() }
        dialogo.show()
    }

    // ---------- Eventos hacia la página ----------

    private fun evento(origen: Conexion, tipo: String, dato: String) {
        principal.post {
            if (origen !== conexion) return@post  // de una conexión vieja: no le importa a la página
            web.evaluateJavascript(
                "window.ccEvento && window.ccEvento(${JSONObject.quote(tipo)}, ${JSONObject.quote(dato)})", null
            )
        }
    }

    private fun errorALaPagina(texto: String) {
        principal.post {
            web.evaluateJavascript("window.ccEvento && window.ccEvento('error', ${JSONObject.quote(texto)})", null)
        }
    }

    // ---------- Conectar ----------

    private fun abrir(destino: JSONObject) {
        conexion?.cerrar()
        conexion = null
        if (destino.optString("tipo") == "bt") {
            abrirBluetooth()
            return
        }
        val ip = destino.optString("ip")
        val puerto = destino.optInt("puerto", 8765)
        if (ip.isEmpty()) {
            errorALaPagina(getString(R.string.sin_pc))
            return
        }
        pcIp = ip
        pcPuerto = puerto
        lateinit var nueva: Conexion
        nueva = ConexionRed("ws://$ip:$puerto/ws") { tipo, dato -> evento(nueva, tipo, dato) }
        conexion = nueva
    }

    private fun abrirBluetooth() {
        val permisos = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S)
            arrayOf(Manifest.permission.BLUETOOTH_ADVERTISE, Manifest.permission.BLUETOOTH_CONNECT) else emptyArray()
        val faltan = permisos.filter { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }
        if (faltan.isNotEmpty()) {
            esperandoBluetooth = true
            requestPermissions(faltan.toTypedArray(), PEDIDO_PERMISOS)
            return
        }
        val adaptador = (getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager).adapter
        if (adaptador == null) {
            errorALaPagina(getString(R.string.sin_bluetooth))
            return
        }
        if (!adaptador.isEnabled) {
            esperandoBluetooth = true
            try {
                @Suppress("DEPRECATION")
                startActivityForResult(Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE), PEDIDO_PRENDER)
            } catch (e: SecurityException) {
                errorALaPagina(getString(R.string.prender_bluetooth))
            }
            return
        }
        lateinit var nueva: ConexionBluetooth
        nueva = ConexionBluetooth(this) { tipo, dato -> evento(nueva, tipo, dato) }
        conexion = nueva
        nueva.empezar()?.let { error ->
            conexion = null
            nueva.cerrar()
            errorALaPagina(error)
        }
    }

    override fun onRequestPermissionsResult(pedido: Int, permisos: Array<out String>, resultados: IntArray) {
        super.onRequestPermissionsResult(pedido, permisos, resultados)
        if (pedido != PEDIDO_PERMISOS || !esperandoBluetooth) return
        esperandoBluetooth = false
        if (resultados.isNotEmpty() && resultados.all { it == PackageManager.PERMISSION_GRANTED }) abrirBluetooth()
        else errorALaPagina(getString(R.string.sin_permiso_bluetooth))
    }

    @Deprecated("Se usa la forma clásica: alcanza y anda en todas las versiones")
    override fun onActivityResult(pedido: Int, resultado: Int, datos: Intent?) {
        @Suppress("DEPRECATION")
        super.onActivityResult(pedido, resultado, datos)
        if (pedido != PEDIDO_PRENDER || !esperandoBluetooth) return
        esperandoBluetooth = false
        if (resultado == RESULT_OK) abrirBluetooth() else errorALaPagina(getString(R.string.prender_bluetooth))
    }

    // ---------- Biblioteca de Steam y portadas: la página las pide a /pc/... y la app las trae de la PC ----------

    private fun pedirALaPC(url: Uri): WebResourceResponse {
        val ip = pcIp ?: return respuestaVacia(503)
        return try {
            val ruta = url.path!!.removePrefix("/pc") + (url.encodedQuery?.let { "?$it" } ?: "")
            val con = URL("http://$ip:$pcPuerto$ruta").openConnection() as HttpURLConnection
            con.connectTimeout = 5000
            con.readTimeout = 10000
            val codigo = con.responseCode
            val cuerpo = (if (codigo < 400) con.inputStream else con.errorStream)?.use { it.readBytes() } ?: ByteArray(0)
            val tipo = (con.contentType ?: "application/octet-stream").substringBefore(";").trim()
            WebResourceResponse(tipo, "utf-8", codigo, con.responseMessage ?: "OK",
                mapOf("Cache-Control" to "no-cache"), ByteArrayInputStream(cuerpo))
        } catch (e: Exception) {
            respuestaVacia(502)
        }
    }

    private fun respuestaVacia(codigo: Int) =
        WebResourceResponse("text/plain", "utf-8", codigo, "Sin PC", emptyMap(), ByteArrayInputStream(ByteArray(0)))

    // ---------- Vibrar ----------

    private fun vibrar(patron: String) {
        val vibrador: Vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S)
            (getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager).defaultVibrator
        else @Suppress("DEPRECATION") (getSystemService(Context.VIBRATOR_SERVICE) as Vibrator)
        try {
            val valor = patron.trim()
            if (valor.startsWith("[")) {
                val lista = JSONArray(valor)
                val tiempos = LongArray(lista.length()) { lista.optLong(it) }
                if (tiempos.isEmpty() || tiempos.all { it <= 0 }) vibrador.cancel()
                else vibrador.vibrate(VibrationEffect.createWaveform(longArrayOf(0) + tiempos, -1))
            } else {
                val ms = valor.toDoubleOrNull()?.toLong() ?: 0
                if (ms <= 0) vibrador.cancel()
                else vibrador.vibrate(VibrationEffect.createOneShot(ms, VibrationEffect.DEFAULT_AMPLITUDE))
            }
        } catch (e: Exception) {
        }
    }

    // ---------- Ajustes de «Anclaje USB» ----------

    private fun abrirAnclaje() {
        val intentos = listOf(
            Intent().setClassName("com.android.settings", "com.android.settings.TetherSettings"),
            Intent().setClassName("com.android.settings", "com.android.settings.Settings\$TetherSettingsActivity"),
            Intent(Settings.ACTION_WIRELESS_SETTINGS),
            Intent(Settings.ACTION_SETTINGS),
        )
        for (intento in intentos) {
            try {
                startActivity(intento.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                return
            } catch (e: Exception) {
            }
        }
    }

    /** Lo que la página puede pedirle a la app (window.ControlCelularApp). Corre en otro hilo. */
    inner class Puente {
        @JavascriptInterface fun pcs(): String = buscador.lista()
        @JavascriptInterface fun conectar(destino: String) {
            principal.post { abrir(try { JSONObject(destino) } catch (e: Exception) { JSONObject() }) }
        }
        @JavascriptInterface fun enviar(mensaje: String) { conexion?.enviar(mensaje) }
        @JavascriptInterface fun cerrar() { principal.post { conexion?.cerrar(); conexion = null } }
        @JavascriptInterface fun vibrar(patron: String) { this@MainActivity.vibrar(patron) }
        @JavascriptInterface fun abrirAnclaje() { principal.post { this@MainActivity.abrirAnclaje() } }
        /** Abre un enlace en el navegador (para bajar la app nueva). Solo http/https. */
        @JavascriptInterface fun abrirEnlace(url: String) {
            val uri = Uri.parse(url)
            if (uri.scheme != "http" && uri.scheme != "https") return
            principal.post {
                try { startActivity(Intent(Intent.ACTION_VIEW, uri).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) } catch (e: Exception) { }
            }
        }
        @JavascriptInterface fun version(): String =
            try { packageManager.getPackageInfo(packageName, 0).versionName ?: "" } catch (e: Exception) { "" }
    }

    companion object {
        private const val PEDIDO_PERMISOS = 7
        private const val PEDIDO_PRENDER = 8
    }
}
