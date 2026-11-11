# Config Tienda (Maestra como única fuente de verdad)

Qué hace: centraliza y sincroniza los parámetros globales de la tienda (`fiado_mantenimiento_pct`, `fiado_apalancamiento_pct`, `fiado_plazo_dias`, `business_name`, `address`, `phone`, `business_cuit`, `footer_message`, `mensaje_zocalo` y claves `mp_*`).

Qué función: `guardar_y_sincronizar`, `aplicar_en_maestra`, `leer_estado_maestra`, `sincronizar_desde_maestra`.

Cómo funciona: cualquier PC puede iniciar un cambio llamando a `guardar_y_sincronizar()`. Si es la Maestra, valida, sube `tienda_config_version`, guarda en MariaDB (`configuracion`) + `config.json` y emite aviso UDP `CONFIG_TIENDA` al resto de las cajas. Si es una Esclava, envía `POST /api/tienda/config` a la Maestra; **no** modifica su `config.json` local hasta que la Maestra acepte y devuelva el snapshot oficial, pisando su copia local con la respuesta autoritativa. Al conectar o recibir el aviso periódico, todas las Esclavas descargan `GET /api/tienda/config`.

Qué no sincronizar acá: configuración propia de cada PC (rol maestra/esclava, impresora, balanza, puertos o rutas locales).
