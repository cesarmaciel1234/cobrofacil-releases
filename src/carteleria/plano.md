# Plano Cartelería

Rama: `src/carteleria`. Subcarpetas con README. La TV kiosk está en `lanzador_tv/directo/`. El pulso de datos está en `vitrina/`.

## Frente

Admin → Cartelería abre el dashboard. Lanzar TV pone **una** Chrome kiosk en `http://127.0.0.1:8765/`. El usuario ve precios, PNG, rotación. F10 cambia monitor (cierra y abre esa misma). F11 apaga. Esc en el panel no apaga. F5 no recarga Chrome: la cara pide `/api/state` sola. Si el kiosk ya está, Lanzar TV no abre otra ventana.

Si no hay MariaDB, se ve **Caché local** (último `carteleria_cache.json`). Si vuelve la red, pasa a **En línea**. Un sync vacío no deja la TV en negro.

## Fondo

1. `lanzador_tv/lanzador_directo.py` → `get_lanzador_directo()` (singleton).
2. `directo/cache_inicial/cargar.py` lee JSON. No espera DB.
3. `directo/arranque/lanzar.py` inicia `ServidorCuello` (reintento). Chrome: `navegador_kiosk.py` (`perfil_kiosk_ocupado`, `cerrar_kiosk_perfil`) + `ServidorCuello.navegador_vivo` (lock del perfil `tpv-carteleria-kiosk` + 15 s de gracia). El watchdog en `directo/motores/pulso.py` no reabre si eso da vivo. No usa `os.startfile`.
4. `directo/motores/pulso.py` dispara `vitrina.pulso.pulso_vitrina` en hilo: MariaDB → HTTP maestra → caché. La maestra arma el ranking en ese hilo (`completar_ranking_local`). El slot de la pantalla no consulta la red ni la base.
5. `directo/catalogo/aplicar.py` no pisa precios con lista vacía. El índice de PNG no se borra en cada pulso.
6. `directo/paneles/hilo.py` arma columnas en un hilo. Si ya hay uno corriendo, queda un pendiente. No pisa `rows_precios`. Si falla, lista simple.
7. `directo/estado/publicar.py` deja `/api/state` listo desde memoria. Si falla, queda el snapshot anterior. La lectura de MariaDB del tema la hace el pedido HTTP, no este paso.
8. Admin → Configuración está en `configuracion/` (no en el archivo suelto). El panel pinta con `config.json`. MariaDB corre en `configuracion/motor/hilo.py`. Guardar pisa memoria TV al toque; REPLACE `carteleria_config` no congela la lista de temas. `loadTheme` solo cambia CSS. `lastDataHash` no incluye el tema. Falla el REPLACE → `invalidar_cache_config_tv`.
9. `la_cara_web/app.js` pide cada 600 ms hasta tener precios+rotación, después 4 s. Un JSON sin precios no borra lo pintado.
10. `motor_carteleria/iconos_tv.py` pone `icono_url`. La cara precarga PNG en `la_cara_web/modules/shared/foto_tarjeta/` y no deja el recuadro vacío hasta `.is-ready`.
11. Columna 3 («¿Llevás…?»): `motor_carteleria/columna3/armar.py` llama `venta_cruzada/motor.py` (`VentaCruzadaInteligente.armar_slides`). Cuenta líneas del mismo ticket en `detalles_ventas`. El rubro solo rellena si no hay ventas. La cara está en `la_cara_web/modules/columna3/` y pinta el JSON; no rearma los pares.
12. Medida del panel: `rect_chrome_tv` lee los píxeles físicos y no los recorta. Una TV nueva en 4K abre a 3840×2160; si el panel es 5K u 8K, abre a ese tamaño. Chrome lleva `--force-device-scale-factor=1`. El diseño sigue en 1920×1080; `app.js` lo encaja con `zoom` (en 4K el zoom queda en 2 y las letras se rasterizan a 4K).
13. Motor Chromium (`perfil_pc.flags_chrome_perfil`): ANGLE D3D11, raster en GPU, raster fuera del hilo de la página, canvas 2D acelerado, color sRGB, letras en gris. Fotos con `image-rendering: high-quality`. Siguen 2 hilos de raster, sin zero-copy y sin Vulkan.

Qué no romper: `src/cajero`, `qt_dpi`, puerto 8765, singleton `_lanzador_directo` (la esclava lo patea en `al_conectar.py`). El zócalo se desliza; no rediseñar el naranja por nitidez de letras.
