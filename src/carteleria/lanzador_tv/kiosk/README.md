# Kiosk (una ventana)

Qué hace: decide si Chrome de la TV está vivo, para no apilar ventanas.

Qué función:
- `perfil_kiosk_ocupado` / `cerrar_kiosk_perfil` / `GRACIA_NAV_S` en `lanzador_tv/navegador_kiosk.py`
- `ServidorCuello.navegador_vivo` / `asegurar_navegador` / `_lanzar_navegador` en `lanzador_tv/cerebro_lanzador_tv.py`
- `_vigilar_navegador` en `directo/motores/pulso.py`

Cómo funciona: en Windows el `chrome.exe` que se lanza a veces termina y deja el kiosk en otro proceso. `navegador_vivo` da True si el Popen sigue, si el lock del perfil `tpv-carteleria-kiosk` está tomado, o si hace menos de 15 s que se lanzó. El watchdog cada 3 s no abre otra. Lanzar TV con el HTTP ya arriba llama `asegurar_navegador` y sale. F11 / `detener` mata el árbol y el perfil kiosk (no el Chrome del cajero). F10 usa `_lanzar_navegador(forzar=True)`: cierra esa y abre una en el otro monitor. No hay `os.startfile`.

Qué devuelve cuando falla: `last_error` (sin Chrome/Edge). No abre el navegador por defecto.

Qué no debe cambiar: un solo `--user-data-dir` (`tpv-carteleria-kiosk`). No matar `chrome.exe` de toda la PC. Los flags de calidad viven en `perfil_pc.flags_chrome_perfil` (un solo `--disable-features`). No zero-copy, no Vulkan, no más de 2 hilos de raster. `rect_chrome_tv` abre al tamaño físico del panel con `--force-device-scale-factor=1`.
