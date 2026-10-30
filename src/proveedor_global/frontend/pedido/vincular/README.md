# Vincular

## Qué hace la carpeta
Asigna un proveedor a un departamento o a un producto.

## Qué función, con el nombre real
* `_HiloDepartamentos`: pide los departamentos fuera de la ventana.
* `_HiloProductos`: busca por nombre, por otra palabra o por código, solo en el departamento elegido.
* `DialogoVincularProveedor`: el cuadro. Enter en el proveedor o en el teléfono guarda.
* `DialogoVincularProveedor._guardar`: no enlaza un producto que ya tiene proveedor.

## Cómo funciona, en el orden en que corre
1. Se elige el departamento.
2. La lista muestra solo productos de ahí. Si ya tiene proveedor, la fila queda en ámbar y el nombre del proveedor va primero.
3. Guardar llama a `MotorAbastecimiento.vincular_proveedor`. Si la ficha no existe, la crea.

## Qué devuelve cuando falla
Avisa y no cierra el cuadro. Un producto ocupado no pasa a otro proveedor.

## Qué no debe cambiar una mejora futura
Enter en la lista elige el producto. El Enter siguiente es el que guarda.
