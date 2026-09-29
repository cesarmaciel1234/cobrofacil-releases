# Historial del monitor

El CSV local `reportes/mercado_pago_sync.csv`. La grilla y las tarjetas leen de acá.

`archivo.py`

- `guardar(pagos)` agrega filas nuevas y, si el id ya estaba, corrige la hora de Argentina, el nombre y el tipo. No repite el id. No guarda un id con `SIMULADO`. Una transferencia por CVU queda como `transferencia` y se ve en la grilla: no es una carga propia. Point queda «Venta con Point Smart» y el QR de mostrador «Venta con código QR». Si no puede escribir, devuelve 0. Lo llama el hilo y también el cobro cuando detecta un QR o una transferencia.
- `leer()` devuelve los pagos y los totales del mes y de hoy. Una fila simulada vieja no entra.
- `omitir(id_pago)` cambia `APPROVED` por `OMITIDO`, o al revés, conservando las demás filas y sus marcas de estado. Devuelve False si no hay archivo.
- `nodo.py`, `sincronizar_nodo(root)`: une el CSV local con `root/reportes/mercado_pago_sync.csv` por ID de pago y actualiza ambas copias. `sincronizar_nodo_configurado()` usa la ruta del nodo en configuración; informa si el nodo asignado no está conectado.
- Al abrir el monitor, se combina la copia del nodo antes de pintar la grilla. **Actualizar** baja el mes actual desde la API y después sincroniza al nodo; cada pago que llega en vivo también se guarda allí. La escritura al USB desde el hilo de pagos se agrupa brevemente y se hace en segundo plano.
- El cambio de estado lleva su propia marca de tiempo para que omitir/restaurar viaje sin reemplazar cambios más recientes.
- `mp_vinculos.json` viaja junto con el CSV. Los vínculos se combinan por mes e ID de pago; si el mismo pago tiene dos vínculos, se conserva el más antiguo porque una asociación existente no se pisa en el flujo local.
- Después de combinar el nodo se despierta el motor de cobros digitales para publicar los vínculos en `mp_pagos` de la tienda; si no hay LAN disponible, el motor conserva el reintento periódico.

El historial largo (tabla `mp_pagos` de la tienda, recuperar lo que entró con la PC apagada, enlace ticket ↔ pago y veredicto) es otra rama: `src/motor_cobros_digitales/plano.md`.

`sincronizar.py`, `bajar_mes(token)`. Baja los cobros aprobados del mes, página por página, con el token de la configuración del TPV y los pasa a `guardar`. La búsqueda lleva `begin_date` (día 1) y `end_date` (ahora), las dos en el formato de `fecha_busqueda_mp`. Sin `end_date` Mercado Pago responde 400 y no entra nada. Cada página se intenta tres veces. Recorre el mes entero: no corta porque la primera página ya esté en el archivo. Si no hay token, devuelve 0. Si no pudo leer la primera página, o había pagos nuevos y no pudo escribirlos, devuelve -1. No pide el token en pantalla.

Fuera de red se consulta la última copia sincronizada con el nodo. Al volver a conectar el dispositivo y sincronizar el nodo, las altas locales y los estados omitido/restaurado regresan al archivo maestro del historial; los pagos repetidos se deduplican por su ID.
