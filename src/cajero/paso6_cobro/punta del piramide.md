# Punta de la pirámide — cobro

La ventana de cobrar. El gris tapa el paso 5. Esta carpeta no arma el ticket.

```
paso6_cobro/
  punta del piramide.md
  paso6_cobro.py           la ventana
  componentes_paso6_cobro/
    selector_metodo_pago/  tres tarjetas arriba y dos abajo
  mercadopago_core/        Point y QR, si el TPV está activo
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

Los seis botones de la derecha están en tres columnas fijas. Ocultar Point o el último monto deja el hueco: F1 a F4 no se estiran. Efectivo y QR no muestran esos dos. Tarjeta muestra Point. En mixto no se ve F2: Enter registra y F1 imprime. En el lugar de F2 queda «último monto» y en el hueco de la tercera columna «Verif QR». Point sigue en mixto. Transferencia muestra «último monto» y el interruptor «Cajero silencioso» / «Con sonido». Debajo de Salir y Enter está F10: imprime ticket y, abajo, fiscal. Si `facturacion_afip_global` está apagado, el botón se ve gris y no factura. El token es el del TPV. Si coincide, registra sin preguntar. Con sonido usa el aviso del monitor de admin.

`NETO A PAGAR` no se muestra. El número grande de arriba es lo que se cobra. Si el ticket trae oferta, o se toca el redondeo o el recargo, el importe anterior queda tachado en rojo, en cualquier forma de pago.

En transferencia no se escribe el monto: lo cambian el redondeo y el recargo. En ese lugar, `transferencia_en_cobro/` muestra el alias y, debajo, el nombre. El lápiz guarda el alias si la API no lo trae.

Efectivo y transferencia arman el medio en `monto_en_cobro/`. Un marco para el casillero y otro para el vuelto o la escucha. El QR ocupa el alto libre, en `qr_en_cobro/`. La tarjeta no pide el monto: `tarjeta_en_cobro/` manda el importe al TPV y, si la terminal no lo toma, Enter registra la venta. El mixto admite solo dos medios. Esos avisos son un cartel en `aviso_en_cobro/`: no hay ventana que cerrar.

Mixto abre la misma hoja, en `mixto_en_cobro/`. No abre `widgets/pagos_mixtos.py`. El teclado escribe en el casillero con foco. F1 imprime. Enter registra, que es lo que hacía F2.

Al confirmar, la misma hoja sigue el reparto: Point cobra solo la parte de tarjeta, la escucha de Mercado Pago espera solo la transferencia, y el panel de QR muestra el código por el monto de QR. El efectivo queda anotado. Al terminar esos pasos, el motor mixto guarda una sola venta.

## Producción

El flujo de clientes y `_abrir_fiado_express_original` repiten el diálogo con `while True`. Cancelar hace `return`.

`persistir_cobro` llama `guardar_venta_completa`. Esa es la transacción de la venta. No se parte en varios commits para un pase a producción.
