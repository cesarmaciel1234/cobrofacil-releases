# Plano - Motor de Inventario (`src/motor_inventario`)

El catálogo, los departamentos y la alarma de reposición viven acá. Otras ramas preguntan. No leen la grilla.

## Frente
El operador lo ve en Admin → Inventario: grilla de productos, pie «Stock crítico» cuando la existencia es cero, y el piso `stock_minimo` / techo `stock_maximo` en la ficha. Esta rama no pinta Pedidos Faltantes. Esa pantalla lee `planilla_reposicion`.

## Fondo
* `MotorCatalogo` (`motor_catalogo.py`) busca, cuenta y guarda productos. `productos_con_alarma_reposicion()` delega en `alarma/consulta.py`.
* `alarma/productos_con_alarma_reposicion()`: stock crítico (≤ 0) o stock en el piso o debajo. Solo `SELECT`.
* `procesos/` busca y guarda. `guardar_producto_en_db` escribe y llama a `empujar_producto_a_maestra`. En casa eso entra en la cola. `buscar_productos_en_db`, `buscar_producto_por_id` y `buscar_producto_por_codigo` pasan por `_fusionar_ediciones`, que pisa la copia con `productos_pendientes()`. La ficha vuelve a abrir el código, el precio y el stock guardados.
* `base/` cuenta, borra, asocia el icono y administra departamentos y categorías. No es la ficha. La alarma no escribe. En casa el borrado se anota y la grilla deja de mostrar ese producto aunque la copia de la tienda todavía lo tenga. El código no se repite. El nombre sí, si el código es otro.
* `unidad_medida/` dice si el stock se cuenta en kilo, unidad, litro o metro.

El stock no sabe de pedidos. `planilla/MotorPlanilla` lee el stock ya guardado y reescribe `planilla_reposicion` en su hilo. `MotorPlanilla.avisar()` solo despierta ese hilo: lo llaman el conteo de auditoría, el ingreso de recepción y `piso/guardar_piso_techo` después de grabar. `guardar_piso_techo` es el único que escribe `stock_minimo` y `stock_maximo`, y lo hace desde `HiloGuardarPiso`, nunca desde la venta. Pedidos solo llama a `MotorPlanilla.leer()`.

## Qué no romper
La venta no llama a la planilla. La recepción suma al stock actual y después llama a `avisar()`. La ficha y la auditoría fijan el stock, copian ese número a las ofertas del corte y también llaman a `avisar()`. La planilla no escribe `productos`. Pedidos no llama a `actualizar()` ni a `avisar()`. No cambiar la regla de alarma desde abastecimiento. No tocar el cajero para que salte un pedido.

## Crítico, probado, no se toca
`tests/test_inventario_critico.py` corre el alta, el stock y el borrado en una base aparte. No escribe la tienda.

Los otros módulos preguntan a `puerta/`. No escriben `productos`. Si la puerta no contesta, siguen con vacío o falso. La venta y el remito no usan `sumar`: el stock baja o sube en la misma transacción del ticket.

* Alta: `guardar_producto_en_db` inserta. La ficha y la importación frenan el código repetido. El mismo nombre entra si el código es otro.
* Ficha: guardar con id reemplaza el stock. No suma.
* Carga: `inventario.aceptar` suma. Con código, suma solo a ese código. Sin código, suma a todos los que se llaman igual. Esa es la falla abierta: dos Alitas sin código recibirían las dos el stock. No se cambia hasta que lo pidan.
* Borrado: `eliminar_producto_de_db` saca ese id. El otro producto con el mismo nombre queda. En casa la baja esconde la fila de la copia.
