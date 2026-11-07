# Componentes de cartera de clientes

Esta carpeta contiene los diálogos de la pantalla de cartera.

`filtro_periodo.py` arma los chips **Hoy / Semana / Semana p. / Mes / Año / Período** (misma lógica que la vitrina). Segundo clic suelta el filtro y muestra todo.

`dialogo_historial_cliente.py` pide los movimientos al hilo `consulta/hilo.py`. Cabecera: **Editar** y **Saldo +**. Filtro de período arriba de la grilla; la impresión usa solo lo filtrado. El ticket se ve abajo (`PanelDetalleTicket`). Un abono muestra `COB-{id}`. **IMPRIMIR HISTORIAL** manda a la tiketera cargos, abonos y totales. **ELIMINAR** solo con cargo vivo. `dialogo_recalculo_fiado.py` simula; no escribe.

`dialogo_promesa.py` fija o quita `promesa_fecha` / `promesa_nota` vía `cerebro.fijar_promesa` / `limpiar_promesa`. No escribe interés.

`dialogo_politicas_credito.py` edita % mantenimiento y % apalancamiento (`cerebro.guardar_politicas_credito`). Preview con ejemplo $100.000.

`dialogo_cobros.py` es la planilla de abonos. Mismos chips de período + buscador con debounce. **Ticket cobro** = `COB-{id}`.

`dialogo_cargos.py` es la planilla de cargos. Mismos chips + estado (Vivos / Borrados / Cancelados).

`dialogo_cuadre.py` lista ventas sin cargo. **Cargar** usa `cerebro.anotar_faltantes`, refresca pendientes y solo cierra cuando no queda nada cargable (o el usuario vuelve).

`dialogo_auditoria_clientes.py` usa las mismas claves (referencia COB o ticket, medio, id de pago). Un evento sin vía ya no dice «Sin llegar»: si nació en la tienda dice «En esta tienda». Acciones `Borrado` y `Anulación` entran al filtro Borrados.

`dialogo_ticket.py` es el panel de lectura. Consulta en un `QThread` a `src/clientes_fiado/oficina/ticket/motor.py`. Si falla, informa; no cambia ni el ticket ni la deuda. Al cambiar de ticket cancela la señal del hilo anterior sin tocar un C++ ya borrado (`RuntimeError` / `deleteLater`).

No mover la lectura de base de datos al hilo de interfaz ni conectar el diálogo a los motores que guardan ventas o deuda.
