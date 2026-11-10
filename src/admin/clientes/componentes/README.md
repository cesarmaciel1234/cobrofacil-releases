# Componentes de cartera de clientes

Esta carpeta contiene los diálogos de la pantalla de cartera.

`filtro_periodo.py` arma los chips **Hoy / Semana / Semana p. / Mes / Año / Período** (misma lógica que la vitrina). Segundo clic suelta el filtro y muestra todo.

`dialogo_historial_cliente.py` pide los movimientos al hilo `consulta/hilo.py` y dibuja la grilla en lotes de 100 para no bloquear la interfaz con historiales grandes. La tabla queda temporalmente inactiva durante la carga y muestra el progreso. La ficha adapta su tamaño al espacio visible, distribuye los datos del cliente en dos líneas y da a la descripción el espacio sobrante; el texto truncado se consulta con tooltip. La grilla dispone de 8 columnas con Ticket antes de Descripción: `Fecha` (col 0), `Tipo` (col 1), `Monto` (col 2), `Saldo` (col 3), `Ticket / cobro` (col 4), `Descripción` (col 5), `Días` (col 6) e `Interés nuevo` (col 7). La descripción es sobria y armoniosa, sin alertas llamativas ni caracteres extraños. Los cargos manuales (cargas de saldo sin ticket) también acumulan interés y días como venta a crédito. Para mantener el historial limpio, simple y espacioso para el cajero y el cliente, el desglose ya no vive incrustado al pie; al hacer clic, doble clic o presionar **VER DETALLE** / `Enter`, se abre una ventana modal emergente (`DialogoDetalleTicket`) con los renglones, precios e importes del ticket (o los datos del cargo/cobro) y la opción de imprimir una copia. El resumen presenta el interés nuevo total y el total estimado. Cabecera: **Editar** y **Saldo +**. Filtro de período arriba de la grilla; la impresión usa solo lo filtrado. **IMPRIMIR HISTORIAL** manda a la tiketera cargos, abonos y totales. **ELIMINAR** solo con cargo vivo; el interés no se borra por separado, se revierte al cancelar el ticket o cargo. `dialogo_recalculo_fiado.py` simula; no escribe.

`dialogo_promesa.py` fija o quita `promesa_fecha` / `promesa_nota` vía `cerebro.fijar_promesa` / `limpiar_promesa`. No escribe interés.

`dialogo_politicas_credito.py` configura la regla interactiva de interés simple: tasa base mensual prorrateada por día sobre el capital pendiente, tasa de apalancamiento (+% extra por mora) y días de plazo acordados con previsualización en vivo.

`dialogo_cobros.py` es la planilla de abonos. Mismos chips de período + buscador con debounce. **Ticket cobro** = `COB-{id}`.

`dialogo_cargos.py` es la planilla de cargos. Mismos chips + estado (Vivos / Borrados / Cancelados).

`dialogo_cuadre.py` lista ventas sin cargo. **Cargar** usa `cerebro.anotar_faltantes`, refresca pendientes y solo cierra cuando no queda nada cargable (o el usuario vuelve).

`dialogo_auditoria_clientes.py` usa las mismas claves (referencia COB o ticket, medio, id de pago). Un evento sin vía ya no dice «Sin llegar»: si nació en la tienda dice «En esta tienda». Acciones `Borrado` y `Anulación` entran al filtro Borrados. Aplica letras de góndola (`letra.py`: Consolas Bold para IDs/referencias/PC, Segoe UI Bold para nombres y números/montos), tooltip completo en cada celda y distribución armónica con ancho flexible en Detalle para que los importes monetarios y ediciones nunca se corten.

`dialogo_ticket.py` contiene `DialogoDetalleTicket` y `PanelDetalleTicket` para visualizar el desglose del ticket o movimiento en una ventana emergente limpia y dedicada. Consulta en un `QThread` a `src/clientes_fiado/oficina/ticket/motor.py`. Si falla, informa; no cambia ni el ticket ni la deuda. Al cambiar de ticket cancela la señal del hilo anterior sin tocar un C++ ya borrado (`RuntimeError` / `deleteLater`).

El historial y el ticket inician sus consultas con `consulta/hilo.py` (`iniciar_hilo_seguro`): los hilos no son hijos de los diálogos, quedan retenidos hasta terminar y se esperan durante el cierre de la aplicación. Esto evita destruir un `QThread` que todavía trabaja al cerrar una ventana.

No mover la lectura de base de datos al hilo de interfaz ni conectar el diálogo a los motores que guardan ventas o deuda.
