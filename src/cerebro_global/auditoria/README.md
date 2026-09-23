# Motor de auditoría

Fondo del conteo físico. Esta carpeta no pinta la pantalla. La pantalla está en `src/admin/auditoria_inventario/`.

## motor_auditoria.py

Clase `MotorAuditoria`. Todo es estático y habla con la base que le pasan.

`asegurar_tabla_auditorias` crea `auditorias_inventario` si no existe: id, fecha, producto_id, nombre_producto, stock_sistema, stock_fisico, diferencia, responsable, motivo. Si la tabla vieja no tiene `motivo`, intenta un `ALTER` y ignora el error si la columna ya está.

`obtener_inventario` lee `productos`: id, codigo, nombre, departamento, precio, stock, unidad, es_pesable. Orden: departamento, nombre. Si falla, devuelve lista vacía.

`aplicar_ajuste_stock` ejecuta `UPDATE productos SET stock = ? WHERE id = ?`. Un solo update. Pone el stock en el número contado. No resta.

`registrar_ajuste` solo inserta en `auditorias_inventario`. No toca `productos`. Campos: producto_id, nombre_producto, stock_sistema, stock_fisico, diferencia, responsable, motivo.

`procesar_auditoria` recorre la lista y, por cada ítem, primero aplica el stock y después registra. Devuelve falso si alguno falla. No llamarla después de que el conector ya aplicó el stock.

`obtener_historial_ajustes` devuelve hasta 200 filas, las más nuevas primero. Si hay producto_id, filtra por ese id. Si hay código, une con `productos` por id y filtra `p.codigo`. Si no hay ninguno, trae el historial general con nombre y producto_id.

## motor_conector_auditoria.py

Clase `MotorConectorAuditoria`. `obtener_conector_auditoria` guarda una sola instancia en `_conector_global`.

Carga `MotorCatalogo` y `db_manager` la primera vez que hacen falta. Si el import falla, queda en None y el método que lo necesitaba devuelve vacío o falso.

La caché dura 15 segundos (`_cache_duration`). `invalidar_cache` la vacía. `_validar_cache` mira la edad. `_fila_auditoria` normaliza id, codigo, nombre, departamento, stock, precio, unidad y es_pesable. Si es_pesable viene vacío y la unidad es KG, KILO o KILOS, lo marca pesable.

`obtener_inventario_para_auditoria(forzar_actualizacion)` refresca si se pide o si la caché venció. Primero intenta `MotorAuditoria.obtener_inventario`. Si no hay base, usa `MotorCatalogo.obtener_productos` con límite 10000.

`buscar_producto_por_codigo` y `buscar_producto_por_id` van al catálogo, no a la caché, y devuelven la fila normalizada.

`solicitar_ajuste_stock(producto_id, stock_nuevo, usuario, motivo)`:

1. Si no hay base, falso y el texto «Base de datos no disponible».
2. Si `stock_nuevo` es menor que 0, falso y «El stock no puede ser negativo».
3. Busca el producto. Si no está, falso.
4. Diferencia = stock nuevo − stock anterior. Si es casi cero (menos de 1e-9), verdadero y «Sin cambio», sin escribir.
5. `aplicar_ajuste_stock`. Si falla, no registra el log.
6. `registrar_ajuste`.
7. Invalida esta caché y llama `invalidar_catalogo` del motor global. Si eso falla, el ajuste igual ya quedó.

`aplicar_lote_ajustes` llama `solicitar_ajuste_stock` por cada ítem. El motivo, si no viene, es «Ajuste de auditoría. Diferencia: …». Junta los errores con el nombre del producto. Al final invalida la caché otra vez. Devuelve `(True, [])` solo si no hubo errores.

`obtener_historial_ajustes` delega en el motor. `verificar_integridad` dice si hay catálogo, base, caché válida, cuántos productos hay y la hora de la última carga. No repara nada.

## __init__.py

Deja la carpeta como paquete. La pantalla importa `obtener_conector_auditoria` desde `motor_conector_auditoria`.
