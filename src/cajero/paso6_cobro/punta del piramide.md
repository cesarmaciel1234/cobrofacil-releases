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

La tabla `clientes` no se lee al abrir el cobro. `_asegurar_lista_clientes` la carga la primera vez que se abre Fiado o Clientes. No la vuelvas al `__init__`.

Elegir QR abre la pantalla del monto, igual que tarjeta. El código se pinta ahí, en `qr_en_cobro/`. En QR no se ven «paga con» ni el neto: quedan redondeo y recargo, y si el código está en vivo se vuelve a pedir con el monto nuevo. Si Mercado Pago lo entrega, el cartel dice EN VIVO y la venta se cierra sola. Si el TPV está en rojo, el cartel dice FOTO y se carga una imagen. Point no entra en ese panel. El punto de venta es `mp_qr_pos_external_id`, no `mp_external_pos_id`.

Los seis botones de la derecha están en tres columnas fijas. Ocultar Point o el último monto deja el hueco: F1 a F4 no se estiran. Efectivo y QR no muestran esos dos. Tarjeta muestra Point. En mixto no se ve F2: Enter registra y F1 imprime. En el lugar de F2 queda «último monto» y en el hueco de la tercera columna «Verif QR». Point sigue en mixto. Transferencia muestra «último monto» y el interruptor «Cajero silencioso» / «Con sonido». Debajo de Salir y Enter está F10: imprime ticket y, abajo, fiscal. Si `facturacion_afip_global` está apagado, el botón se ve gris y no factura. F2 dice «sin ticket». Si todavía se espera la tarjeta, la transferencia o el QR, F1, F2 y F10 no cierran: el cartel avisa una vez y queda elegido para cuando pague. F1 imprime el ticket. F2 cierra la venta sola, sin ticket; si el cliente lo pide, F1 vuelve a imprimir. F10 imprime el fiscal. Si no se tocó ninguna, al pagar se imprime. Si no hay espera, F1, F2 y F10 cierran en el momento. Un segundo clic de la misma tecla no repite el cartel. El token es el del TPV. Si coincide, registra sin preguntar. Con sonido usa el aviso del monitor de admin.

`NETO A PAGAR` no se muestra. El número grande de arriba es lo que se cobra. Si el ticket trae oferta, o se toca el redondeo o el recargo, el importe anterior queda tachado en rojo, en cualquier forma de pago.

En transferencia no se escribe el monto: lo cambian el redondeo y el recargo. En ese lugar, `transferencia_en_cobro/` muestra el alias y, debajo, el nombre. El lápiz guarda el alias si la API no lo trae.

Efectivo y transferencia arman el medio en `monto_en_cobro/`. Un marco para el casillero y otro para el vuelto o la escucha. El QR ocupa el alto libre, en `qr_en_cobro/`. La tarjeta no pide el monto y no abre la ventana chica de espera: `aviso_en_cobro/` pinta un cartel con margen y el botón Cancelar. El mismo envío cobra en Tarjeta y en el paso de tarjeta del mixto. Elegir Tarjeta no cancela el cobro que ya está en el Point. Cancelar en el cartel, o que la terminal cancele, vuelve a la página de métodos. El QR no sale en el Point: se ve en el sistema. Si la terminal no toma el importe, Enter registra la venta. El mixto admite solo dos medios. Esos avisos son un cartel en `aviso_en_cobro/`: no hay ventana que cerrar.

Mixto abre la misma hoja, en `mixto_en_cobro/`. No abre `widgets/pagos_mixtos.py`. El teclado escribe en el casillero con foco. F1 imprime. Enter registra, que es lo que hacía F2.

Al confirmar, la misma hoja sigue el reparto: Point cobra solo la parte de tarjeta, la escucha de Mercado Pago espera solo la transferencia, y el panel de QR muestra el código por el monto de QR. El efectivo queda anotado. Al terminar esos pasos, el motor mixto guarda una sola venta. El botón Point de mixto manda esa parte de tarjeta aunque el resto todavía no cubra el total.

`vinculo_mp/libro.py` guarda en `reportes/mp_vinculos.json` el id del cobro de Mercado Pago junto al ticket. La escucha muestra la transferencia apenas llega. Si el monto coincide, registra. Si llega otro importe y no tiene ticket, el cartel pregunta si se asocia o se espera otro monto: Enter acepta «Asociar» y la diferencia queda en redondeo o recargo. Si ya tiene ticket, el cartel dice que no hay nueva transferencia. Con la luz del TPV en verde, Enter no registra mientras se espera transferencia, QR o tarjeta: sale el cartel rojo de alarma. F9, debajo de F10, cobra a mano y no se aprieta con el mouse. Llega aunque el cursor esté en el monto o en el mixto. Si el Point está esperando, suelta esa espera y guarda. Con la luz en rojo (`_tpv_listo` es falso: no hay token con Point ni token con el QR), F9 no está. Enter llama `_guardar_sin_tpv`: guarda la venta en efectivo, tarjeta, transferencia, QR y mixto, sin mandar el Point, sin esperar la transferencia y sin pedir el QR en vivo. Fiado y clientes siguen pidiendo el cliente.

## Producción

El flujo de clientes y `_abrir_fiado_express_original` repiten el diálogo con `while True`. Cancelar hace `return`.

`persistir_cobro` llama `guardar_venta_completa`. Esa es la transacción de la venta. No se parte en varios commits para un pase a producción.

## Descuentos y Recargos

Los inputs de redondeo y recargo incluyen botones de cambio rpido entre $ y %. Al presionarlos, el estado del botn cambia y recalcula el monto automticamente (pasando de un valor fijo a un porcentaje del total original o viceversa). Si se teclea manualmente el smbolo % al final del texto (ej. 10%), el sistema lo toma como porcentaje ignorando el estado visual del botn.
