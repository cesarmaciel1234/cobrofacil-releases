# Fiado en Paso 6

`panel.py`, clase `PanelFiadoCobro`, contiene la selección del cliente y confirma que la compra actual se cargue a su cuenta. `HojaCuentaCobro` conserva el flujo normal: elegir cliente, revisar saldo y presionar Enter. Ese Enter muestra la confirmación verde. El siguiente Enter, en el teclado o en la pantalla, llama `procesar_enter` y cierra la venta con `pago_listo`. Si el campo de texto oculto vuelve a emitir `listo`, esa repetición también cierra la venta.

## Abono previo opcional

En la pantalla de confirmación, F5 abre `cobranza.py::cobrar_deuda_previa` para la ficha ya seleccionada. El motor abre el Centro de Cobranza F6 directamente en ese cliente, deja elegir el abono y el medio, y espera el resultado autorizado.

Si el cobro se confirma, `medios/cerrar.py::asentar` registra el abono en `cuenta_corriente`. Si una parte fue efectivo, `MovimientosCajaService.registrar_ingreso_efectivo` registra solo esa parte en `movimientos_caja`; la ventana F6 ya abrió el cajón. No se imprime un comprobante aparte porque el ticket de la venta actual incluirá el importe del abono.

El abono no modifica `total_final`, los medios ni la transacción de la venta. La pantalla regresa a la confirmación Fiado; Enter sigue autorizando la compra normal. Si se cancela el abono, la compra sigue pendiente sin cambios. Si el abono ya se registró pero falla la anotación del efectivo en caja, se informa el problema y se conserva el abono: no se revierte una operación ya asentada.

`post_cobro.py` pasa `deuda_adicional` y el saldo previo al primer abono a `CobroController.procesar_cajon_impresion`, que los entrega a `imprimir_ticket_venta`. La impresión muestra el saldo previo, el abono, la compra y el disponible dentro del bloque de Cuenta Corriente. Es una sola impresión de venta y una sola escritura de venta + deuda para la compra actual.

## Qué no cambiar

- No sumar el abono previo a `total_final` ni a los pagos de la compra.
- No guardar el abono dentro de `persistir_cobro`: ya se registró por el motor de Cobranza.
- No reabrir ni imprimir una segunda copia del ticket de saldo desde este flujo.
- Si se cancela la venta después de un abono confirmado, el abono conserva su registro independiente.
