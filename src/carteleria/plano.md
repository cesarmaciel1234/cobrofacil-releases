# Plano Cartelería

Rama: `src/carteleria`. Subcarpetas con README. La TV kiosk está en `lanzador_tv/directo/`. El pulso de datos está en `vitrina/`.

## Frente

Admin → Cartelería abre el dashboard. Lanzar TV pone **una** Chrome kiosk en `http://127.0.0.1:8765/`. El usuario ve precios, PNG, rotación. F10 cambia monitor (cierra y abre esa misma). F11 apaga. Esc en el panel no apaga. F5 no recarga Chrome: la cara pide `/api/state` sola. Si el kiosk ya está, Lanzar TV no abre otra ventana.

Si no hay MariaDB, se ve **Caché local** (último `carteleria_cache.json`). Si vuelve la red, pasa a **En línea**. Un sync vacío no deja la TV en negro.

## Fondo

1. `lanzador_tv/lanzador_directo.py` → `get_lanzador_directo()` (singleton).
2. `directo/cache_inicial/cargar.py` lee JSON. No espera DB.
3. `directo/arranque/lanzar.py` inicia `ServidorCuello` (reintento). Chrome: `navegador_kiosk.py` (`perfil_kiosk_ocupado`, `cerrar_kiosk_perfil`) + `ServidorCuello.navegador_vivo` (lock del perfil `tpv-carteleria-kiosk` + 15 s de gracia). El watchdog en `directo/motores/pulso.py` no reabre si eso da vivo. No usa `os.startfile`.
4. `directo/motores/pulso.py` dispara `vitrina.pulso.pulso_vitrina` en hilo: MariaDB → HTTP maestra → caché. La maestra, si el pulso no trae ranking, lo arma con `completar_ranking_local`. Un dict vacío no cuenta: `armar_paneles` lee las ventas locales.
5. `directo/catalogo/aplicar.py` no pisa precios con lista vacía.
6. `directo/paneles/hilo.py` arma columnas; si falla, lista simple.
7. `directo/estado/publicar.py` deja `/api/state` listo. Si falla, queda el snapshot anterior.
8. Admin → Configuración está en `configuracion/` (no en el archivo suelto). El panel pinta con `config.json`. MariaDB corre en `configuracion/motor/hilo.py`. Guardar pisa memoria TV al toque; REPLACE `carteleria_config` no congela la lista de temas. `loadTheme` solo cambia CSS. `lastDataHash` no incluye el tema. Falla el REPLACE → `invalidar_cache_config_tv`.
9. `la_cara_web/app.js` pide cada 600 ms hasta tener precios+rotación, después 4 s. Un JSON sin precios no borra lo pintado.
10. `motor_carteleria/iconos_tv.py` pone `icono_url`. La cara precarga PNG en `la_cara_web/modules/shared/foto_tarjeta/` y no deja el recuadro vacío hasta `.is-ready`.

Qué no romper: `src/cajero`, `qt_dpi`, puerto 8765, singleton `_lanzador_directo` (la esclava lo patea en `al_conectar.py`). El zócalo se desliza; no rediseñar el naranja por nitidez de letras.
