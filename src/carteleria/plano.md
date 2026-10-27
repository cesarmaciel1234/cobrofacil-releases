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
7. `directo/estado/publicar.py` deja `/api/state` listo desde memoria. Si falla, queda el snapshot anterior. El pedido HTTP lee el tema de esa memoria: no espera a MariaDB.
8. Admin → Configuración está en `configuracion/` (no en el archivo suelto). El panel pinta con `config.json`. MariaDB corre en `configuracion/motor/hilo.py`. Guardar pisa memoria TV al toque; REPLACE `carteleria_config` no congela la lista de temas. `loadTheme` solo cambia CSS. `lastDataHash` no incluye el tema. Falla el REPLACE → `invalidar_cache_config_tv`.
9. `la_cara_web/app.js` pide cada 600 ms hasta tener precios, después 4 s. El hash incluye precio, oferta, foto, publicidad y el texto del ranking. Un JSON sin precios no borra lo pintado.
10. `motor_carteleria/iconos_tv.py` pone `icono_url`. La cara precarga PNG en `la_cara_web/modules/shared/foto_tarjeta/` y no deja el recuadro vacío hasta `.is-ready`.
11. Columna 3 («¿Llevás…?»): `motor_carteleria/columna3/armar.py` llama `venta_cruzada/motor.py` (`VentaCruzadaInteligente.armar_slides`). Cuenta líneas del mismo ticket en `detalles_ventas`. El rubro solo rellena si no hay ventas. La cara está en `la_cara_web/modules/columna3/` y pinta el JSON; no rearma los pares.
12. Medida del panel: `rect_chrome_tv` lee los píxeles físicos y no los recorta. Una TV nueva en 4K abre a 3840×2160; si el panel es 5K u 8K, abre a ese tamaño. Chrome lleva `--force-device-scale-factor=1`. El diseño sigue en 1920×1080; `app.js` lo encaja con `zoom` (en 4K el zoom queda en 2 y las letras se rasterizan a 4K).
13. Motor Chromium (`perfil_pc.flags_chrome_perfil`): ANGLE D3D11, raster en GPU, raster fuera del hilo de la página, canvas 2D acelerado, color sRGB, letras en gris. Fotos con `image-rendering: high-quality`. Siguen 2 hilos de raster, sin zero-copy y sin Vulkan.

Qué no romper: `src/cajero`, `qt_dpi`, puerto 8765, singleton `_lanzador_directo` (la esclava lo patea en `al_conectar.py`). El zócalo se desliza; no rediseñar el naranja por nitidez de letras.

## Carga y actualización automática

La cara no consulta MariaDB. Al abrir pinta la plantilla guardada en el navegador (la última forma) y pide `http://127.0.0.1:8765/api/state` (600 ms hasta que haya precios, después 4 s). Si la página queda en los recuadros grises, se recarga sola; si Chrome no responde, el kiosk se vuelve a abrir. Un JSON sin precios no borra lo que ya se ve. Si cambia una venta, una foto o un precio, la cara lo pinta en el siguiente pedido. `/api/state` no espera a MariaDB.

De dónde sale cada cosa, en el pulso (`vitrina/pulso.py`, cada 15 s, o al instante si cambia el sello):

| Qué ve la TV | De dónde | Al guardar |
| --- | --- | --- |
| Precio de lista | `productos.precio` | Inventario llama `avisar_datos_nuevos` |
| Oferta y relámpago | `precio_oferta`, `precio_oferta_relampago`, `cant_oferta` | `MotorOfertas` avisa al activar, quitar o agotar el cupo |
| Combos | tabla `combos` | `MotorCombos` avisa al guardar o borrar |
| Publicidad | lista `promocionados` / `ids` | Guardar en maestra o esclava reemplaza la lista en las dos |
| Ranking | `MotorVentas` (hoy, si no hay ayer, si no hay la semana) | El pulso lo vuelve a armar. El texto de la columna 1 camufla la cifra |
| PNG | `productos.icono` + archivo en `Catalogos/png_productos` | Guardar el icono avisa. La esclava baja los PNG de la maestra |

Aviso a la otra PC: `avisar_datos_nuevos` pisa `carteleria_datos.sello` en esta máquina, manda UDP `DATOS` y, si esta PC es esclava, POST `:8000/api/carteleria/datos_nuevos`. La otra PC solo pisa su sello (no reenvía). El lanzador mira el sello cada 1 s y vuelve a leer. Si el UDP no llega, el pulso de 15 s igual lee MariaDB.

Maestra y esclava leen la misma base mientras hay red. Por eso un precio nuevo no se copia a mano: se escribe una vez y las dos teles lo levantan. El servidor esclava, en el hilo `oficio-carteleria`, llama a `pulso_vitrina` cada minuto. Si esa vuelta no trae precios, `carteleria_cache.json` queda como estaba y la TV sigue en caché. Ese hilo no ejecuta `sincronizador_carteleria`.
