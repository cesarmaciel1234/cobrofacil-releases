# Cuenta

`motor.py`, clase `MotorCuenta`. Libro de `clientes` y `cuenta_corriente`.
`cancelacion.py` contiene la lógica de cartera para el reverso F3 y conserva esa reversión
en la cola offline; no pertenece al motor de ventas.

`movimientos` trae `id`, fecha, tipo, monto, saldo, descripcion y `venta_id`.

`borrar_cargo` no borra la fila: marca `BORRADO ·`, inserta `ANULACION` y cancela el ticket en la misma transacción. En tickets y cargos manuales, la anulación revierte el capital original y el interés ya asentado; el interés pagado queda como saldo a favor. No se puede borrar una línea consolidada de interés por separado.

Al cancelar en F3, `cancelacion.py` revierte capital e interés, marca `CANCELADO ·` y deja `Ticket cancelado #N (F3)`. `ventas.py` conserva solo el cambio físico del ticket, stock y caja, dentro de la misma transacción. Si el ticket ya estaba `CANCELADA` y el cargo seguía vivo, cartera vuelve a anular el cargo.

`cargo_inactivo` cubre BORRADO y CANCELADO. `ultimo_cargo` / `ultimos_cargos` los ignoran.

ABONO y CARGO dejan `cobro_id` o `cargo_id` en la huella.

`cuadre.py` lista ventas fiadas sin cargo. No cancela tickets.

`listar_cargos` arma la planilla de admin (`oficina/cargos/lista.py`): ticket de venta o MANUAL, estado vivo/borrado/cancelado.

`abonar` usa `proyectar_interes` antes de guardar. La tasa es configurable (base mensual simple prorrateada por días + apalancamiento al superar el plazo), sobre el capital pendiente de tickets y de cargos manuales (ventas cargadas sin ticket, identificadas como `M:{id}`), sin retroactividad anterior a `configuracion.interes_ticket_activado_en`. Si el cálculo de interés se interrumpe, el abono liquida el pago normalmente sin trabar las operaciones. El detalle por ticket/cargo se conserva dentro de la descripción de una única línea consolidada de interés. El abono liquida primero intereses y luego capital FIFO; no capitaliza intereses.

La vista previa la comparte Admin y F6 mediante `oficina/consulta_historial`. El abono vuelve a calcular dentro de la misma transacción, sin confiar en la vista previa. Todas las escrituras de saldo son atómicas: SQLite inicia con `BEGIN IMMEDIATE`; MariaDB bloquea la ficha con `SELECT ... FOR UPDATE`. El cuadre también vuelve a validar el estado de la venta y la existencia del cargo antes de escribir. Las líneas de interés no reinician el aging del ticket o cargo.

Al trabajar offline, los eventos de interés, abono y anulación viajan en `clientes_auditoria`. Los detalles apuntan a `request_id`, no dependen del `id` local de la venta. Cartera guarda su reverso en `offline_cancelaciones`; el sincronizador de cartera coordina su aplicación idempotente con la cancelación física que ventas reproduce. La cola se borra solo después de confirmar ambas partes.
