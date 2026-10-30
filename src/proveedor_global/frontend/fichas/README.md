# Fichas

## Qué hace la carpeta
Lista los proveedores activos y abre el historial de cada uno.

## Qué función, con el nombre real
* `DialogoProveedoresActivos`: la grilla. Con `embebido=True` se usa dentro de la tarjeta, sin botón Cerrar.
* `DialogoHistorialProveedor`: compras de un nombre, misma forma que el historial de un cliente.
* `DialogoProductosAsociados`: busca en el catálogo para asociar, y desenlaza los que ya están. En ámbar ya tienen otro proveedor.

## Cómo funciona, en el orden en que corre
1. `FichaProveedor.listar` trae las fichas.
2. Un clic en el nombre abre el historial.
3. Productos asociados busca por nombre o código. Desenlazar llama a `quitar_proveedor`.
4. Editar datos cambia nombre, teléfono y los días de reparto. Si el proveedor no tiene días, abre lunes, miércoles y viernes. El marcado se ve azul. Esos días los usa el pedido de lo suelto.

## Qué devuelve cuando falla
Si el enlace no sale, el aviso dice que sigue activo y la fila no se borra.

## Qué no debe cambiar una mejora futura
El código interno EN CASA no se muestra. Un producto en ámbar no se enlaza a un segundo proveedor.
