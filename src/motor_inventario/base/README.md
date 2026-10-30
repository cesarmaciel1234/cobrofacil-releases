# Base del catálogo

## Qué hace la carpeta

Lecturas y escrituras puntuales de `productos` y `departamentos` que no son la búsqueda de la grilla ni el guardado de la ficha. Esas dos viven en `procesos/`.

## Qué función, con el nombre real

* `productos_db.py`: `contar_todos_los_productos`, `contar_productos_sin_stock`, `eliminar_producto_de_db`, `actualizar_precio_por_nombre`, `asegurar_columna_icono`, `listar_productos_png`, `guardar_icono_producto`, `asociar_png_un_producto`, `asociar_png_por_nombre`. En casa `eliminar_producto_de_db` anota la baja: la grilla deja de mostrar ese id.
* `departamentos_db.py`: `obtener_departamentos`, `obtener_categorias`, `obtener_iva_de_departamento`, `guardar_departamento_en_db`, `borrar_departamento_de_db`, `guardar_categoria_en_db`, `borrar_categoria_de_db`.

## Cómo funciona, en el orden en que corre

1. Departamentos prepara la tabla si falta y después lista o guarda.
2. El icono se asocia después de guardar la ficha, si el producto no trae uno.
3. El conteo sin stock es el pie «Stock crítico». No arma el pedido: eso lo lee la planilla.

## Qué devuelve cuando falla

Conteo en cero, lista vacía o `False` en el borrado y en el icono. El error queda en el log de la base.

## Qué no debe cambiar una mejora futura

No mover acá la búsqueda ni el guardado de la ficha. No escribir `planilla_reposicion`. No tocar el cajero.
