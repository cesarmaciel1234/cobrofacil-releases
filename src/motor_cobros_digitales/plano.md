# Plano — motor de cobros digitales (el empleado)

La rama arranca en esta carpeta. La base es `src` y no lleva plano.

Es el único encargado de enlazar número de ticket con id de pago de Mercado Pago y de decir si un cobro digital es verdadero. Los demás módulos no esperan por él: el cajero cobra, el monitor muestra y el jefe lee. El empleado trabaja en su propio hilo.

## Frente

No tiene pantalla propia. Se ve en:

- Jefe, vitrina: «Digitales sin firmar / total» usa `veredicto.conciliar.tickets_firmados`.
- Monitor MP: la columna Ticket combina el libro local con `mp_pagos.ticket`; las firmas de otra PC de la LAN aparecen al refrescar la consulta de fondo.
- Logs: `[Cobros digitales] bajados=… enlazados=…`.
- `estado()` devuelve el último turno en memoria (para una pantalla futura, sin tocar red ni base).

## Fondo

Arranque: `main.py` llama `arrancar()`. A los 20 s empieza la jornada en el hilo `cobros_digitales`. Con varias ventanas del TPV en la misma PC, trabaja una sola (`locks/cobros_digitales.lock`, bajo la carpeta base de la app).

`empleado.turno()`, cada 5 minutos o 90 s después de un cobro detectado:

1. `bajada/mp.py`, `ponerse_al_dia(token)`: lo que cambió en MP desde la marca `mp_historial_hasta` → tabla `mp_pagos`. Recupera lo que entró con la PC apagada y las devoluciones.
2. `enlace/caja.py`, `subir_vinculos()`: siempre intenta subir las firmas del cajero de esta PC (`reportes/mp_vinculos.json`, solo lectura) → `mp_pagos.ticket` con `enlace='caja'`, aunque falle el token o la bajada de MP. Si no hay conexión a la tienda, no borra el archivo fuente: el siguiente turno vuelve a intentar.
3. `enlace/automatico.py`, `enlazar()`: solo corre si la bajada terminó y la subida de firmas tuvo éxito. Desde la marca `mp_enlace_hasta` (menos 1 día), ventas digitales sin firma ↔ pagos sueltos del mismo monto a menos de 10 minutos, solo si los dos se eligen y no hay empate → `enlace='motor'`. La marca avanza hasta donde bajó MP.

`EscuchaMP.publicar` (`src/services/mp_escucha.py`) llama `anotar_llegada(pago)`: guarda el pago al toque en otro hilo y pide un turno.
Al asociar un pago en caja o sincronizar los vínculos del nodo, se despierta el empleado para publicar la firma sin esperar la cadencia periódica.

El veredicto se lee cuando se pide: `veredicto/conciliar.py` (`por_metodo`, `ticket_por_ticket`, `resumen`).

Tablas: `mp_pagos` (propia; el cruce con ventas va por `venta_id`, con índice), `configuracion` (marcas `mp_historial_desde`, `mp_historial_hasta`, `mp_enlace_hasta`), `ventas` (solo lectura). Todo en la base de la tienda (MariaDB de la maestra) cuando está conectada. La creación de `mp_pagos` se recuerda por identidad de base: al pasar de SQLite local a MariaDB vuelve a comprobar y crear el esquema de la tienda.

Pruebas: `tests/test_motor_cobros_digitales.py` (sin base real ni red).

Token: `EscuchaMP.token()`; la esclava lo trae de la tienda (`src/central_red_global/sync_tienda/mp_token`).

## Qué no romper

- El cajero no se toca: el motor solo lee `vinculo_mp/libro.py`.
- Las rutas del libro local y del candado del motor parten de `get_base_path()`, no del directorio de trabajo del proceso.
- Un error al bajar pagos no debe saltarse la subida durable de firmas de caja. Si falla una etapa, se registra y se reintenta en otro turno; el enlace automático no corre sobre datos incompletos ni si falló la firma manual.
- Una firma de caja manda sobre una del motor. El motor nunca pisa un ticket puesto.
- Un pago = una fila por `payment_id`. Bajar dos veces no duplica.
- No abrir un segundo hilo de escucha MP: la escucha sigue siendo `EscuchaMP`.
- Las marcas nunca van para atrás. La del enlace no pasa a la de la bajada.
- Filtros de fecha con rango (`fecha >= ? AND fecha < ?`), no con `date(fecha)`.
