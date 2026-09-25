# Punta de la pirámide — cobro

La ventana de cobrar. El gris tapa el paso 5. Esta carpeta no arma el ticket.

```
paso6_cobro/
  punta del piramide.md
  paso6_cobro.py           la ventana
  componentes_paso6_cobro/
    selector_metodo_pago/  tres tarjetas arriba y dos abajo
  mercadopago_core/        Point y QR, si el TPV está activo
  vinculo_mp/              el id de Mercado Pago queda junto al ticket
  motor_pagos/             guarda la venta
  widgets/                 pago mixto, fiado y cliente
```

Si el TPV no está activo, tarjeta y QR se registran igual. La luz está en el encabezado: verde listo, roja sin terminal.

## Fondo

`MotorPrincipalCobros.iniciar_transaccion` busca la clase en `REGISTRO` y llama `ejecutar`. Las claves son efectivo, tarjeta, crédito, débito, mixto, transferencia, qr, mercadopago, fiado y clientes. Crédito y débito usan `MotorTarjeta`. QR y Mercado Pago usan `MotorQR`.

`CobroController.validar_monto_suficiente` suma. No abre la base. Si falta dinero, devuelve `(None, None)`.

## Qué no cambiar

No inyectar `db_manager` en `validar_monto_suficiente`. No hacer que los motores se llamen entre sí.

`_tpv_point_listo` y `_tpv_qr_listo` llaman `config._load_config()` antes del token. `config.get` no lee el disco. No saques esas llamadas. Lo mismo en `PointService.procesar_pago_mercadopago_point`. `_pintar_luz_tpv` lee el config una sola vez y no llama a esos dos métodos.

La tabla `clientes` no se lee al abrir el cobro. `_asegurar_lista_clientes` llama `cerebro.listar` la primera vez que se abre Fiado o Clientes. No la vuelvas al `__init__`.

Fiado y Clientes no se mezclan con efectivo, tarjeta, transferencia, QR ni mixto. Se piden en `HojaCuentaCobro`, en `src/clientes_fiado/interfaz/cobro/hoja.py`. No abren la ventana oscura. Fiado solo toma números. Cuenta corriente toma el nombre. El primer Enter muestra saldo y disponible y limpia el campo para confirmar. El segundo Enter registra. El cartel no repite el monto ni trae Cancelar. Esc vuelve a los medios. Si el DNI ya está en el módulo, Fiado cruza con ese cliente. `MotorFiado` y `MotorClientes` solo llaman `cerebro.cobrar`. El cerebro autoriza el cupo y, si la orden viene ok, `garante/despacho/despacho.py` llama `ejecutar_comun`. El plano está en `src/clientes_fiado/plano.md`.

Elegir QR abre la pantalla del monto, igual que tarjeta. El código se pinta ahí, en `qr_en_cobro/`. En QR no se ven «paga con» ni el neto: quedan redondeo y recargo, y si el código está en vivo se vuelve a pedir con el monto nuevo. Si Mercado Pago lo entrega, el cartel dice EN VIVO y la venta se cierra sola. Si el TPV está en rojo, el cartel dice FOTO y se carga una imagen. Point no entra en ese panel. El punto de venta es `mp_qr_pos_external_id`, no `mp_external_pos_id`.

Los seis botones de la derecha están en tres columnas fijas. Ocultar Point o el último monto deja el hueco: F1 a F4 no se estiran. Efectivo y QR no muestran esos dos. Tarjeta muestra Point. En mixto no se ve F2: Enter registra y F1 imprime. En el lugar de F2 queda «último monto» y en el hueco de la tercera columna «Verif QR». Point sigue en mixto. Transferencia muestra «último monto» y el interruptor «Cajero silencioso» / «Con sonido». Debajo de Salir y Enter está F10: imprime ticket y, abajo, fiscal. Si `facturacion_afip_global` está apagado, el botón se ve gris y no factura. F2 dice «sin ticket». Si todavía se espera la tarjeta, la transferencia o el QR, F1, F2 y F10 no cierran: el cartel avisa una vez y queda elegido para cuando pague. F1 imprime el ticket. F2 cierra la venta sola, sin ticket; si el cliente lo pide, F1 vuelve a imprimir. F10 imprime el fiscal. Si no se tocó ninguna, al pagar se imprime. Si no hay espera, F1, F2 y F10 cierran en el momento. Un segundo clic de la misma tecla no repite el cartel. El token es el del TPV. Si coincide, registra sin preguntar. Con sonido usa el aviso del monitor de admin.

`NETO A PAGAR` no se muestra. El número grande de arriba es lo que se cobra. Si el ticket trae oferta, o se toca el redondeo o el recargo, el importe anterior queda tachado en rojo, en cualquier forma de pago.

En transferencia no se escribe el monto: lo cambian el redondeo y el recargo. En ese lugar, `transferencia_en_cobro/` muestra el alias y, debajo, el nombre. El lápiz guarda el alias si la API no lo trae.

Efectivo y transferencia arman el medio en `monto_en_cobro/`. Un marco para el casillero y otro para el vuelto o la escucha. El QR ocupa el alto libre, en `qr_en_cobro/`. La tarjeta no pide el monto y no abre la ventana chica de espera: `aviso_en_cobro/` pinta un cartel con margen y el botón Cancelar. El mismo envío cobra en Tarjeta y en el paso de tarjeta del mixto. Elegir Tarjeta no cancela el cobro que ya está en el Point. Cancelar en el cartel, o que la terminal cancele, vuelve a la página de métodos. El QR no sale en el Point: se ve en el sistema. Si la terminal no toma el importe, Enter registra la venta. El mixto admite solo dos medios. Esos avisos son un cartel en `aviso_en_cobro/`: no hay ventana que cerrar.

Mixto abre la misma hoja, en `mixto_en_cobro/`. No abre `widgets/pagos_mixtos.py`. El teclado escribe en el casillero con foco. F1 imprime. Enter registra, que es lo que hacía F2.

Al confirmar, la misma hoja sigue el reparto: Point cobra solo la parte de tarjeta, la escucha de Mercado Pago espera solo la transferencia, y el panel de QR muestra el código por el monto de QR. El efectivo queda anotado. Al terminar esos pasos, el motor mixto guarda una sola venta. El botón Point de mixto manda esa parte de tarjeta aunque el resto todavía no cubra el total.

`vinculo_mp/libro.py` guarda en `reportes/mp_vinculos.json` el id del cobro de Mercado Pago junto al ticket. La escucha muestra la transferencia apenas llega. Si el monto coincide, registra. Si llega otro importe y no tiene ticket, el cartel pregunta si se asocia o se espera otro monto: Enter acepta «Asociar» y la diferencia queda en redondeo o recargo. Si ya tiene ticket, el cartel dice que no hay nueva transferencia. Con la luz del TPV en verde, Enter no registra mientras se espera transferencia, QR o tarjeta: sale el cartel rojo de alarma. F9, debajo de F10, cobra a mano y no se aprieta con el mouse. Llega aunque el cursor esté en el monto o en el mixto. Si el Point está esperando, suelta esa espera y guarda. Con la luz en rojo (`_tpv_listo` es falso: no hay token con Point ni token con el QR). El QR usa `mp_qr_pos_external_id`. La tarjeta solo manda el Point si hay `mp_device_id`. Al aprobar, el id de la tarjeta y el del QR quedan en el ticket. F9 no está. Enter llama `_guardar_sin_tpv`: guarda la venta en efectivo, tarjeta, transferencia, QR y mixto, sin mandar el Point, sin esperar la transferencia y sin pedir el QR en vivo. Fiado y clientes siguen pidiendo el cliente.

## Producción

Fiado y Clientes usan `HojaCuentaCobro` en la hoja del cobro. Cancelar vuelve a los medios. No se vuelve a abrir la ventana oscura.

`persistir_cobro` llama `guardar_venta_completa`. Esa es la transacción de la venta. No se parte en varios commits para un pase a producción.

## Redondeo

Es automático. El cajero no redondea a mano. La función es `redondear_dinero` en `src/utils/dinero.py`: `Decimal` a dos centavos, `ROUND_HALF_UP`. Si el valor no es un número, devuelve `0.0`. No la cambies por `round` de float.

El total que cobra sale de la suma de la columna de subtotales del ticket, ya pasada por `redondear_dinero` en `finalizar_venta`. No se lee el rótulo grande. Cada renglón entra por `redondear_items_carrito`: precio y subtotal a dos centavos. Si el subtotal ya viene pintado, se redondea ese número. No se vuelve a multiplicar cantidad por precio.

En el cobro, `recargar_total_final` hace `redondear_dinero(max(0, total_original - redondeo + recargo))`. Ese es el número grande. F3 y F4 lo recalculan al escribir. Tarjeta, transferencia y el QR en vivo copian ese número al pago. El precio tachado es `redondear_dinero(total_original + oferta)`.

F3 se llama redondeo. Es un descuento. F4 es el recargo. El botón al lado cambia `$` y `%` y vuelve a calcular. Si el texto termina en `%`, es porcentaje del total original aunque el botón diga `$`. El porcentaje del redondeo no pasa de 100. El importe del porcentaje no se redondea antes de restar: se redondea el total a pagar, una sola vez.

`CobroController.validar_monto_suficiente` redondea los dos montos y compara `redondear_dinero(p1 + p2) + 0.001` contra el total ya redondeado. El `0.001` es el margen del centavo. No abre la base. `calcular_vuelto_y_totales` no redondea y no lo llama nadie. El total vivo es `recargar_total_final`.

En mixto, cada casillero pasa por `PanelMixtoCobro._numero`, que llama `redondear_dinero`. `cubre` usa el mismo margen de `0.001`. `_reparto_mixto` vuelve a redondear efectivo, tarjeta, transferencia y QR. `confirmar.py` redondea otra vez la parte de tarjeta, la de transferencia y la de QR antes de cobrarlas.

Al guardar, `armar_resultado_venta` redondea total, pagos, vuelto, redondeo, oferta y recargo. El vuelto solo existe en efectivo y en mixto. `persistir_cobro` redondea los renglones otra vez y, si es fiado, el total de la deuda.

Si la transferencia no coincide y se asocia, la diferencia de más de `0.05` se escribe sola en F3 o en F4 y el total se recalcula. Hasta `0.05` se toma como el mismo monto y no toca el redondeo. Ese `0.05` no es el redondeo a dos centavos. No los juntes.
