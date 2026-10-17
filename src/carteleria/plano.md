# Plano Cartelería

Rama: `src/carteleria`. Subcarpetas con README. La TV kiosk está en `lanzador_tv/directo/`. El pulso de datos está en `vitrina/`.

## Frente

Admin → Cartelería abre el dashboard. Lanzar TV pone Chrome kiosk en `http://127.0.0.1:8765/`. El usuario ve precios, PNG, rotación. F10 cambia monitor. F11 apaga. Esc en el panel no apaga. F5 no recarga Chrome: la cara pide `/api/state` sola.

Si no hay MariaDB, se ve **Caché local** (último `carteleria_cache.json`). Si vuelve la red, pasa a **En línea**. Un sync vacío no deja la TV en negro.

## Fondo

1. `lanzador_tv/lanzador_directo.py` → `get_lanzador_directo()` (singleton).
2. `directo/cache_inicial/cargar.py` lee JSON. No espera DB.
3. `directo/arranque/lanzar.py` inicia `ServidorCuello` (reintento).
4. `directo/motores/pulso.py` dispara `vitrina.pulso.pulso_vitrina` en hilo: MariaDB → HTTP maestra → caché.
5. `directo/catalogo/aplicar.py` no pisa precios con lista vacía.
6. `directo/paneles/hilo.py` arma columnas; si falla, lista simple.
7. `directo/estado/publicar.py` deja `/api/state` listo. Si falla, queda el snapshot anterior.
8. `la_cara_web/app.js` pide cada 400 ms hasta tener precios+rotación, después 3 s. Un JSON sin precios no borra lo pintado.

Qué no romper: `src/cajero`, `qt_dpi`, puerto 8765, singleton `_lanzador_directo` (la esclava lo patea en `al_conectar.py`).
