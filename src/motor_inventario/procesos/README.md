# Procesos del catálogo

## Qué hace la carpeta

Busca y guarda productos. La grilla y la ficha preguntan acá. No pintan.

## Qué función, con el nombre real

* `buscar_productos_en_db(buscar, depto, limite, offset)`: página de la grilla. Devuelve `(filas, hay_mas)`.
* `buscar_producto_por_id(producto_id)`: una ficha para editar.
* `buscar_producto_por_codigo(codigo)`: el alta, cuando se escanea un código que ya existe.
* `contar_productos_en_db(buscar, depto)`: el total del filtro.
* `_fusionar_ediciones(filas)`: pisa la copia de la tienda con lo guardado en casa.
* `guardar_producto_en_db(datos_producto, es_nuevo, producto_id)`: INSERT o UPDATE y empuja a la maestra.
* `comprobar_si_codigo_existe`: el alta bloquea el código repetido. El nombre puede repetirse si el código es otro.
* `unificar_productos_duplicados()`: junta filas repetidas. No corre al guardar una ficha.

## Cómo funciona, en el orden en que corre

1. La búsqueda lee `productos` con el JOIN a `departamentos`. En casa esa lectura sale de la copia de la tienda.
2. `_fusionar_ediciones` pide `productos_pendientes()` y, si el id coincide, copia código, nombre, precio, stock y el resto de campos que no sean nulos. El id no se pisa.
3. La grilla y la ficha muestran esa fila. Por eso, al volver a abrir, se ve lo que se guardó.
4. `guardar_producto_en_db` escribe con `execute_non_query`. Si hay id, es UPDATE. Si no, INSERT. Si la ficha cambia el stock, ese número pasa a las ofertas del mismo corte y la planilla se despierta. No suma: la carga es la que suma.
5. Después llama a `empujar_producto_a_maestra` con el id. En casa eso encola y no espera a la maestra. Al volver a la tienda, la misma cola sube.

## Qué devuelve cuando falla

La búsqueda devuelve `([], False)` o `None`. Guardar devuelve `(False, mensaje)` con `last_error` si la base lo dejó. Si la cola no se puede leer, `_fusionar_ediciones` deja la fila de la copia.

## Qué no debe cambiar una mejora futura

No escribir la copia de la tienda. No dejar de fusionar por id: si no, la ficha vuelve al valor viejo. No tocar el cajero. La venta sigue buscando `id` o `codigo` en su propio camino. El alta, el stock de la ficha y el borrado están probados en `tests/test_inventario_critico.py` y no se reescriben.
