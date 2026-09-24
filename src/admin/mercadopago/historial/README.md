# Historial del monitor

El CSV local `reportes/mercado_pago_sync.csv`. La grilla y las tarjetas leen de acá.

`archivo.py`

- `guardar(pagos)` agrega filas nuevas. No repite el id. No guarda un id con `SIMULADO`. Si no puede escribir, devuelve 0.
- `leer()` devuelve los pagos y los totales del mes y de hoy. Una fila simulada vieja no entra.
- `omitir(id_pago)` cambia `APPROVED` por `OMITIDO`, o al revés. Devuelve False si no hay archivo.

`sincronizar.py`, `bajar_mes(token)`. Baja los cobros aprobados del mes con el token de la configuración del TPV y los pasa a `guardar`. Si no hay token, devuelve 0. No pide el token en pantalla.
