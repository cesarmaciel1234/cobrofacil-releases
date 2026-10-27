# Monitor de Mercado Pago

La carpeta contiene el monitor de pagos del panel admin.

- `mercadopago_main.py`: ventana `Admin10MP`; carga pagos guardados, calcula tarjetas y filtros, muestra el vínculo a ticket, y arranca el escucha compartido mediante `EscuchaMP.asegurar()`. Las tarjetas KPI miden 44 px de alto (mitad). Abre en Hoy. **Filtros** abre la lista: Cruce (Todos, Cruzados, Ticket sin id, Id sin ticket) y, si en el período hay más de una cuenta, Cuenta. La línea bajo la barra dice cuánto entró a cada token. Un clic sobre el período ya marcado lo suelta y muestra todas las fechas. El cruce no corre en el clic: `empleado.pedir` pinta la copia y el hilo la rearma.
- `filtros/`: la lista del botón Filtros y la clasificación cruzado / ticket sin id / id sin ticket. Ver `filtros/README.md`.
- `historial/`: baja pagos aprobados desde la API, guarda el historial CSV, los períodos de cada token, y sincroniza historial y vínculos al nodo portable. Ver `historial/README.md`.
- `componentes/`: hilo de escucha MP compartido con el cajero. Ver `componentes/README.md`.

## Uso fuera de red

1. Con la unidad del nodo conectada, abrir el monitor y usar **Actualizar**. Primero incorpora la copia del nodo, después baja el mes desde la API y combina automáticamente `reportes/mercado_pago_sync.csv` y `reportes/mp_vinculos.json` con el nodo. Los pagos que entren en vivo también se escriben al nodo.
2. En la notebook sin conexión, abrir el monitor con el mismo nodo conectado: importa los últimos pagos y vínculos guardados. Sin token o sin respuesta de la API, muestra la copia local y su estado.
3. Omitir/restaurar pagos o asociarlos a tickets mientras se trabaja. Los cambios se conservan localmente.
4. Al volver a tener conexión, usar **Actualizar**: baja los pagos aprobados del mes y combina ambas copias por ID, llevando también los cambios de omitido/restaurado y los vínculos al nodo.

La auditoría muestra tres cosas: el ticket de venta o de cobro que no tiene id de Mercado Pago, el id de Mercado Pago que no tiene ticket, y el titular del token que estaba activo cuando entró ese id. Si se guarda otro token en Terminal TPV, el período del anterior se cierra y el nombre nuevo es el que Mercado Pago devuelve para ese token. La línea de cuentas suma el monto de cada una en lo que se está viendo.

La columna Ticket sale del vínculo (`mp_vinculos.json`) cuando el pago digital ya firmó la venta. Las ventas QR/tarjeta/transferencia sin id aparecen igual: fecha, monto y número de ticket, sin cuenta.

El historial conserva los meses previamente guardados y la API completa el mes actual durante **Actualizar**. El historial puede contener nombres y correos de pagadores. Proteger el nodo como los demás datos del negocio. La consulta en vivo sigue dependiendo de conexión y del token de Mercado Pago; la copia no crea pagos ni permite conciliar cobros a la API sin red. Si el nodo está desconectado, el monitor informa que la actualización del nodo quedó pendiente.

No copiar el token de Mercado Pago al nodo. No abrir un segundo hilo de escucha ni mezclar este CSV con `punpro.db` o con la tabla `mp_pagos` de `src/motor_cobros_digitales`.
