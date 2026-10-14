# Punta — F3 historial de caja

Paso 5, tecla F3. Lista del turno: tickets a la izquierda, detalle a la derecha. No vende. No cobra.

```
paso8_historial/
  punta del piramide.md
  README.md
  dialogo.py                 DialogoHistorialDia
  paso8_historial.py         reexporta el diálogo
  logica/                    consultas y cancelar
  ui/                        cabecera, lista, filtros
  componentes_paso8_historial/  detalle y sello CANCELADO
```

## Frente

El cajero oprime F3. Gris `#334155`. Hoja clara.

Pinta: folio, artículos, hora, total, redondeo, cliente. El detalle: ítems, sello CANCELADO si el estado es `CANCELADA`, Cancelar venta, imprimir copia, notas.

No pinta: alta de cliente, cobro, F2/F5/F6.

Cancelar pide PIN de admin (el admin no). El ticket **queda** en la lista, tachado. No se borra el folio.

## Fondo

1. `HistorialController.get_ventas` lee `ventas` + `detalles_ventas`.
2. Cancelar → `cancelar_venta` → `db_manager.cancelar_venta_transaccional` (`src/base_de_datos/repos/ventas.py`).
3. Esa transacción: stock de vuelta, estado `CANCELADA`, auditoría, retiro de efectivo si corresponde.
4. Fiado / Clientes: `_anular_cargo` marca el cargo `CANCELADO ·` y deja `Ticket cancelado #N (F3)` en `cuenta_corriente`. El historial del cliente lo lee `oficina/consulta_historial`.

Qué no romper: no escribir movimientos de caja desde esta pantalla; no borrar la fila de `ventas`; no tocar el paso 6.
