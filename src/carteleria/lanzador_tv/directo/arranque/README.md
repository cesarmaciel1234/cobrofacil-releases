# Arranque del kiosk

Qué hace: abre y cierra Chrome en el monitor de la TV.

Qué función: `ArranqueMixin.lanzar` / `detener` / `on_tv_control`. El vivo del kiosk está documentado en `lanzador_tv/kiosk/README.md`.

Cómo funciona: si el HTTP ya está, no mata el navegador. Carga la caché, inicia `ServidorCuello` (reintento una vez), arranca motores a los 50 ms. Una sola ventana: lock del perfil + 15 s de gracia. No se usa el navegador por defecto (`startfile`). Esc no apaga. F11 sí. F10 cierra y abre una en el otro monitor.

Qué devuelve cuando falla: `lanzar` → `False` y `last_error`. No tira excepción al panel.

Qué no debe cambiar: puerto 8765, no recargar Chrome con F5.
