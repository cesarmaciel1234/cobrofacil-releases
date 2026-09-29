# Monitor de Mercado Pago

La carpeta contiene el monitor de pagos del panel admin.

- `mercadopago_main.py`: ventana `Admin10MP`; carga pagos guardados, calcula tarjetas y filtros, muestra el vínculo a ticket, y arranca el escucha compartido mediante `EscuchaMP.asegurar()`.
- `historial/`: baja pagos aprobados desde la API, guarda el historial CSV, y sincroniza historial y vínculos al nodo portable. Ver `historial/README.md`.
- `componentes/`: hilo de escucha MP compartido con el cajero. Ver `componentes/README.md`.

## Uso fuera de red

1. Con la unidad del nodo conectada, abrir el monitor y usar **Actualizar**. Primero incorpora la copia del nodo, después baja el mes desde la API y combina automáticamente `reportes/mercado_pago_sync.csv` y `reportes/mp_vinculos.json` con el nodo. Los pagos que entren en vivo también se escriben al nodo.
2. En la notebook sin conexión, abrir el monitor con el mismo nodo conectado: importa los últimos pagos y vínculos guardados. Sin token o sin respuesta de la API, muestra la copia local y su estado.
3. Omitir/restaurar pagos o asociarlos a tickets mientras se trabaja. Los cambios se conservan localmente.
4. Al volver a tener conexión, usar **Actualizar**: baja los pagos aprobados del mes y combina ambas copias por ID, llevando también los cambios de omitido/restaurado y los vínculos al nodo.

La columna Ticket combina el vínculo local/nodo con `mp_pagos.ticket` de la base compartida. Así las asociaciones subidas por otra caja aparecen también en este monitor; la tabla se consulta fuera del hilo de interfaz cada 5 segundos. Asociar un pago en caja o sincronizar el nodo despierta el motor de subida sin esperar el ciclo periódico.

El historial conserva los meses previamente guardados y la API completa el mes actual durante **Actualizar**. El historial puede contener nombres y correos de pagadores. Proteger el nodo como los demás datos del negocio. La consulta en vivo sigue dependiendo de conexión y del token de Mercado Pago; la copia no crea pagos ni permite conciliar cobros a la API sin red. Si el nodo está desconectado, el monitor informa que la actualización del nodo quedó pendiente.

No copiar el token de Mercado Pago al nodo. No abrir un segundo hilo de escucha ni mezclar este CSV con `punpro.db` o con la tabla `mp_pagos` de `src/motor_cobros_digitales`.
