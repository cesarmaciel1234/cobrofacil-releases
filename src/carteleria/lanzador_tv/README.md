# Lanzador TV

Qué hace: abre la cartelería en Chrome/Edge a pantalla completa. HTTP fijo `http://127.0.0.1:8765/`.

Qué función: `get_lanzador_directo().lanzar()` / `detener()` en `lanzador_directo.py`. La lógica está en `directo/`.

Cómo funciona: caché JSON antes de Chrome. Pulso MariaDB/HTTP en hilo. Cara web pide `/api/state` sola. F5 no reabre el navegador. Watchdog reabre Chrome si se cayó de verdad (el Popen no basta: Chrome deja la ventana y el proceso hijo). Mismo puerto, una sola ventana.

Perfil Chromium: look premium estable (GPU raster + sRGB, sin zero-copy). Tema visual: apple / temu / premium / black / blackfriday. Admin elige; `aplicar_config_tv_memoria` en `cerebro_lanzador_tv.py` deja el tema en cache 20 s para que `/api/state` no espere MariaDB. `loadTheme` solo cambia CSS. Ticker 96 filas. Foto: `la_cara_web/modules/shared/foto_tarjeta/`.

Qué no debe cambiar: Esc en el panel no apaga. F11 sí. No SELECT a MariaDB en el hilo de la UI. Un tema nuevo no vuelve a armar las columnas.
