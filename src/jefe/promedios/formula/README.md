# Fórmula de stock

Qué hace: guarda cómo se parte un producto base en mercadería de venta.

Qué función: `guardar` escribe la fórmula. `consumir_base` la aplica en la venta. `intermediario.resolver_cursor` y `aplicar_filas` responden cuánto queda sin leer el stock de la fracción.

Cómo funciona: el usuario indica el cajón, cuántas piezas trae (12 maples) y cada producto con las piezas que usa. El stock se carga en el cajón. La fracción no consulta su fila: pasa por el intermediario, que lee el base y aplica la fórmula. Si el base se pesa, responde kilos. Si se cuenta, responde cajas. Al cobrar, descuenta esa parte solo del base. El pedido de faltantes mira ese stock. Por departamento, toda venta de ese departamento descuenta la misma parte. `guardar` borra y vuelve a escribir la fórmula en un solo cierre. El stock de las porciones lo manda el motor de inventario de proveedores, que lee el cajón en el momento de enviar.
