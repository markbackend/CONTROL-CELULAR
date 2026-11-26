# La página llama a estos métodos por nombre (window.ControlCelularApp): R8 no los puede sacar ni renombrar.
-keepattributes JavascriptInterface
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
