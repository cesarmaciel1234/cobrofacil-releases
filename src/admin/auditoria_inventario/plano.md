# Plano — auditoría de inventario

Esta carpeta es donde arranca la rama. El frente está acá. El fondo está en `src/cerebro_global/auditoria/`.

## Frente

Pantalla: `auditoria_main.py`, clase `AuditoriaMain`. La abre el admin en la pestaña 25 de `main_window.py`.

Al mostrarse, `showEvent` aplica el perfil, el tema claro u oscuro y a los 80 ms pone el foco en el buscador.

`_es_lectura` es verdadero solo si el rol es `cajero`. Ese perfil ve la lista y no puede sumar conteos ni aplicar stock. Admin y jefe sí.

`cargar_datos` pide el inventario al conector y arma la tabla. Columnas: id, código, nombre, departamento, stock del sistema, conteo real, diferencia. El stock del sistema no se edita. El conteo real, en admin, nace vacío y en ámbar. En el id de la fila se guardan `es_pesable` y `unidad`.

`_info_unidad` elige la unidad:

- metros si la unidad es MT, M, METRO o METROS, o el departamento dice textil o tela
- kilos si es pesable o la unidad es KG, KILO o KILOS
- litros si es LT, L, LITRO o LITROS
- cajas si es CJ, CAJA o CAJAS
- si no, unidades

Escanear (`_on_codigo_escaneado`) busca la fila por código o por id. Si es kilos, metros o litros, abre `DialogoConteo` y ese número reemplaza el conteo. Si es unidades o cajas, suma 1 al conteo que ya había. El cajero no entra a esa suma.

Doble clic o editar abre `DialogoConteo`. El teclado escribe el número con coma. `valor()` lo pasa a float. Aceptar escribe el conteo en la celda. No toca la base todavía.

Al cambiar el conteo, `_on_item_changed` calcula diferencia = conteo − stock del sistema. Azul si sobra, rojo si falta. `_actualizar_kpis` cuenta SKU, contados, faltante y sobrante.

El filtro de texto busca en id, código, nombre y departamento. La vista puede ser todos, solo contados o solo con diferencia.

Historial: `_ver_historial_ajustes` abre un diálogo y `_cargar_historial_producto` pide al conector las filas de ese producto. Muestra fecha, usuario, stock anterior, stock nuevo, diferencia y motivo.

Aplicar: `_recoger_ajustes` junta solo las filas con conteo y con diferencia distinta de cero. `_aplicar_ajustes` pide confirmación y llama `aplicar_lote_ajustes` con el nombre del usuario de `config.current_user`. Después recarga la tabla desde la base.

## Fondo

El conector es `obtener_conector_auditoria()` en `motor_conector_auditoria.py`. Hay una sola instancia.

`obtener_inventario_para_auditoria` usa una caché de 15 segundos. Si se fuerza o venció, `_actualizar_cache` lee `MotorAuditoria.obtener_inventario`: `SELECT` de `productos` ordenado por departamento y nombre. Si eso falla, cae a `MotorCatalogo.obtener_productos`.

`solicitar_ajuste_stock` rechaza stock negativo. Si la diferencia es cero, no escribe. Si hay diferencia:

1. `MotorAuditoria.aplicar_ajuste_stock` hace un solo `UPDATE productos SET stock = ? WHERE id = ?`. Es un SET al conteo, no una resta de venta.
2. Después `registrar_ajuste` hace un INSERT en `auditorias_inventario`. Ese insert no vuelve a tocar `productos.stock`.
3. Se invalida la caché del conector y la del catálogo global.

`aplicar_lote_ajustes` repite eso producto por producto. No llama `procesar_auditoria` después del UPDATE: eso volvería a hacer el SET y podría pisar una venta del medio.

`procesar_auditoria` existe en el motor y también hace SET más log. No usarlo encima de `solicitar_ajuste_stock`.

No usar `guardar_producto` para este ajuste: ese update puede pisar departamento u otros campos.

La venta no pasa por acá. El descuento de una venta está en `descontar_stock`. Si `opt_stock_negativo` está apagado, el update exige `stock >= cantidad`. Si otra caja se llevó el resto, la venta se deshace con `SinStock`.

## Qué no cambiar

- El log no escribe `productos.stock`.
- Cancelar una venta restaura stock solo con `WHERE id = ?`. No sumar `OR codigo = ?`.
- El cajero en esta pantalla es solo lectura.
