# Historial

## Qué hace la carpeta
La tarjeta de compras a proveedores. El armado está en `VistaProveedor.cargar_datos` y la nota vive acá para no mezclarla con la carga.

## Qué función, con el nombre real
* `VistaProveedor.cargar_datos`: lee `MotorProveedor.load_proveedores`.
* `VistaProveedor._pintar_historial`: aplica período, proveedor y estado, y suma pagado, restante y monto.
* `VistaProveedor._show_remito_detail`: abre el remito y, si hay saldo, el pago.
* `VistaProveedor._ir("historial")`: entra a esta pantalla y refresca la lista.

## Cómo funciona, en el orden en que corre
1. La tarjeta Historial abre los períodos (hoy, ayer, semana, semana pasada, mes, mes pasado, año, todo), el proveedor y el estado.
2. Debajo van las compras del filtro y tres totales: pagado, restante y monto.
3. Cada fila muestra monto, pagado, restante, fecha, contado, fiado o anulada, y Ver Remito. Anular deja el registro y devuelve el stock de esa carga.
4. La recepción y la carga por peso no muestran esta tabla. Al guardar, la fila queda para cuando se abre Historial.

## Qué devuelve cuando falla
Si la consulta no trae filas, la tabla queda vacía.

## Qué no debe cambiar una mejora futura
No volver a pegar el histórico debajo del escáner ni de la carga por peso.
