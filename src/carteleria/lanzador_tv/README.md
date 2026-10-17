# Lanzador TV

Qué hace: abre la cartelería en Chrome/Edge a pantalla completa. HTTP fijo `http://127.0.0.1:8765/`.

Qué función: `get_lanzador_directo().lanzar()` / `detener()` en `lanzador_directo.py`. La lógica está en `directo/`.

Cómo funciona: caché JSON antes de Chrome. Pulso MariaDB/HTTP en hilo. Cara web pide `/api/state` sola. F5 no reabre el navegador. Watchdog reabre Chrome si se cayó, mismo puerto.

Perfil: Chromium con tema **premium** (el más premium estable). GPU raster + sRGB, sin zero-copy. Ticker 96 filas, PNG en caché, config de admin cacheada 20 s (no MariaDB en cada frame). El vidrio/blur queda en cabecera y tarjetas, no en el scroll de precios.

Qué no debe cambiar: Esc en el panel no apaga. F11 sí. No hacer SELECT a MariaDB en el hilo de la UI.
