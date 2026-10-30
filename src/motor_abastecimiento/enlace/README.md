# Subcarpeta Enlace (Puente Productos/Departamentos con Proveedores)

## Qué hace la carpeta
Gestiona la asociación entre artículos/departamentos y sus proveedores correspondientes sin modificar ni alterar la tabla original `productos`. Utiliza la tabla satélite `abastecimiento_proveedor_map`.

## Qué función, con el nombre real
* `asegurar_tabla_enlace()`: Crea de forma no destructiva la tabla `abastecimiento_proveedor_map` si no existe. Si el CREATE sale bien, no lo repite en el mismo proceso.
* `asignar_proveedor(criterio_tipo, criterio_valor, proveedor_nombre, proveedor_telefono, proveedor_email, proveedor_id=None)`: Registra o actualiza el mapeo. Sigue guardando el nombre. Con la tienda escribe el id de la maestra. Sin tienda deja el enlace en `offline_cambios.json` y en la copia local; al volver, la nutrición crea el id y reescribe el vínculo.
* `quitar_proveedor(criterio_tipo, criterio_valor)`: Borra ese enlace en esta PC y anota la baja en la cola. Al reconectar, la nutrición lo borra en la tienda y no lo vuelve a subir.
* `obtener_mapeos()`: Consulta y devuelve la lista de asociaciones vigentes, cada una como diccionario. Antes del JOIN crea `proveedores` si falta, así el perfil admin no falla cuando la esclava está en SQLite.
* `asociar_proveedores_a_productos(productos_faltantes)`: Clasifica y agrupa los productos bajo stock mínimo bajo su proveedor correspondiente.

## Cómo funciona, en el orden en que corre
1. Al invocar la asociación, lee todas las reglas de `abastecimiento_proveedor_map`. `_fila` convierte la fila de SQLite local en diccionario antes de usar `.get`. Si no, el pedido entero no se pinta.
2. Para cada producto faltante, busca primero si tiene un proveedor directo por `producto_id`.
3. Si no lo tiene, busca si su `departamento` está asignado a un proveedor general.
4. Si no tiene ninguna regla, lo coloca bajo el grupo `"SIN PROVEEDOR ASIGNADO"`.
5. Agrupa los ítems acumulando cantidades y costos estimados por proveedor. Cada proveedor activo entra en el selector aunque hoy no tenga faltantes.

## Qué devuelve cuando falla
* Si falla la lectura o no hay reglas, no lanza errores fatales: retorna los productos bajo el grupo `"SIN PROVEEDOR ASIGNADO"` para que el usuario no pierda visibilidad de los faltantes.

## Qué no debe cambiar una mejora futura
* No agregar claves foráneas destructivas (`FOREIGN KEY ... ON DELETE CASCADE`) que puedan interferir con la tabla `productos` del inventario existente.
* No borrar `proveedor_nombre` al agregar `proveedor_id`. El pedido y el WhatsApp siguen agrupando por nombre.
