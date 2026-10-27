# Plano - Motor de Inventario (`src/motor_inventario`)

El catálogo, los departamentos y la alarma de reposición viven acá. Otras ramas preguntan. No leen la grilla.

## Frente
El operador lo ve en Admin → Inventario: grilla de productos, pie «Stock crítico» cuando la existencia es cero, y el piso `stock_minimo` / techo `stock_maximo` en la ficha. Esta rama no pinta Pedidos Faltantes. Esa pantalla lee `planilla_reposicion`.

## Fondo
* `MotorCatalogo` (`motor_catalogo.py`) busca, cuenta y guarda productos. `productos_con_alarma_reposicion()` delega en `alarma/consulta.py`.
* `alarma/productos_con_alarma_reposicion()`: stock crítico (≤ 0) o stock en el piso o debajo. Solo `SELECT`.
* `base/` y `procesos/` leen y escriben `productos` y `departamentos` para el catálogo. La alarma no escribe.
* `unidad_medida/` dice si el stock se cuenta en kilo, unidad, litro o metro.

El stock no sabe de pedidos. `planilla/MotorPlanilla` lee el stock ya guardado y reescribe `planilla_reposicion` en su hilo. `MotorPlanilla.avisar()` solo despierta ese hilo: lo llaman el conteo de auditoría, el ingreso de recepción y `piso/guardar_piso_techo` después de grabar. `guardar_piso_techo` es el único que escribe `stock_minimo` y `stock_maximo`, y lo hace desde `HiloGuardarPiso`, nunca desde la venta. Pedidos solo llama a `MotorPlanilla.leer()`.

## Qué no romper
La venta no llama a la planilla. La recepción y la auditoría solo llaman a `avisar()` cuando el stock ya quedó. La planilla no escribe `productos`. Pedidos no llama a `actualizar()` ni a `avisar()`. No cambiar la regla de alarma desde abastecimiento. No tocar el cajero para que salte un pedido.
