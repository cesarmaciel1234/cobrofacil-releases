# Regla: auditoría de stock

## Por qué existe
El recuento físico no es una venta. Hay que **poner** el stock en el número contado (SET), no restar como en caja. El historial tiene que quedar aparte para saber quién ajustó y cuánto.

## Cómo funciona
1. La pantalla `AuditoriaMain` pide el inventario al conector.
2. Cada escaneo **suma** al conteo (unidades). Los pesables piden kilos y también suman.
3. Al confirmar, `solicitar_ajuste_stock` hace **un** `UPDATE productos SET stock = ? WHERE id = ?` y **después** un INSERT en `auditorias_inventario`.
4. El log **nunca** vuelve a escribir `productos.stock`.

## Venta y la opción de stock negativo
El descuento de una venta vive en `descontar_stock`. Si `opt_stock_negativo` está apagado, el `UPDATE` exige `stock >= cantidad`. Si otra caja se llevó el resto, la venta entera se deshace (`SinStock`). Si está prendido, la venta sigue y el stock puede quedar negativo. No volver a ignorar esa opción ni a restar stock sin esa condición.

## Qué no hay que romper
- No usar `guardar_producto` para un ajuste de auditoría: ese UPDATE parcial puede pisar departamento u otros campos.
- No llamar `MotorAuditoria.procesar_auditoria` después de haber actualizado el stock (eso duplicaba el SET y podía pisar una venta en el medio).
- Cancelar una venta solo restaura stock con `WHERE id = ?`. `OR codigo = ?` mezclaba productos.
- El perfil cajero es solo lectura: no suma conteos ni aplica.

## Piezas
- `src/admin/auditoria_inventario/auditoria_main.py`
- `src/cerebro_global/auditoria/motor_conector_auditoria.py`
- `src/cerebro_global/auditoria/motor_auditoria.py`
