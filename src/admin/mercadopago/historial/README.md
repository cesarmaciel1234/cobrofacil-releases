# Historial del monitor

El CSV local `reportes/mercado_pago_sync.csv`. La grilla y las tarjetas leen de acá.

`archivo.py`

- `guardar(pagos)` agrega filas nuevas y, si el id ya estaba, corrige la hora de Argentina, el nombre y el tipo. No repite el id. No guarda un id con `SIMULADO`. Una transferencia por CVU queda como `transferencia` y se ve en la grilla: no es una carga propia. Point queda «Venta con Point Smart» y el QR de mostrador «Venta con código QR». Si no puede escribir, devuelve 0. Lo llama el hilo y también el cobro cuando detecta un QR o una transferencia.
- `leer()` devuelve los pagos y los totales del mes y de hoy. Una fila simulada vieja no entra.
- `omitir(id_pago)` cambia `APPROVED` por `OMITIDO`, o al revés. Devuelve False si no hay archivo.

`sincronizar.py`, `bajar_mes(token)`. Baja los cobros aprobados del mes, página por página, con el token de la configuración del TPV y los pasa a `guardar`. La búsqueda lleva `begin_date` (día 1) y `end_date` (ahora), las dos en el formato de `fecha_busqueda_mp`. Sin `end_date` Mercado Pago responde 400 y no entra nada. Cada página se intenta tres veces. Recorre el mes entero: no corta porque la primera página ya esté en el archivo. Si no hay token, devuelve 0. Si no pudo leer la primera página, o había pagos nuevos y no pudo escribirlos, devuelve -1. No pide el token en pantalla.
