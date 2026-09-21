# Regla: request_id de venta

## Por qué
Un cobro no puede devolver un ticket inventado (`9999999`). Tampoco puede insertar dos veces la misma venta si la red corta a los 5 segundos y el cajero reintenta.

## Cómo funciona
1. La pantalla de cobro crea **un** `request_id` (UUID) al abrir.
2. `guardar_venta_completa` lo guarda en `ventas.request_id`.
3. Si ese id ya existe, se devuelve el ticket real. No se descuenta stock otra vez.
4. Si la API LAN falla, se cancela el cobro (no se simula éxito).

## Qué no romper
- No volver a devolver `9999999`.
- No borrar `request_id` de cobro / motor / controller.
- En bases viejas la migración agrega la columna; si aún no está, el INSERT cae al formato anterior (13 campos) para no frenar la caja.
- El índice único permite varios `NULL` (ventas viejas). No rellenar esas filas a la fuerza.
