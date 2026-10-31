# Puerta del inventario

Los otros módulos preguntan acá. No escriben `productos` por su cuenta. Si esta puerta no contesta, el módulo sigue: una lectura vacía o un falso.

La raíz del inventario ya está. Un módulo nuevo pide stock o costo, o envía stock y costo de un producto que ya existe (Suprema, un id, un código). No manda una fórmula. No explica el cálculo. El inventario no pregunta para qué.

## Qué función, con el nombre real

* `por_id`, `por_codigo`, `catalogo`, `precios`: leen. No escriben.
* `alta`: crea el producto. El código repetido no entra.
* `fijar`: deja el stock en el número que le pasan. No suma.
* `sumar`: suma al stock de ese código, en su propia conexión.
* `borrar`: saca ese id. En casa anota la baja.

## Cómo funciona, en el orden en que corre

1. El módulo llama una de esas funciones.
2. La puerta habla con `procesos/`, `base/` o con `formula/motores/inventario.py`.
3. Si la base tira error, la puerta lo anota en el log y devuelve `None`, `[]`, `{}` o `False`.

## Qué devuelve cuando falla

Vacío o falso. No hay excepción hacia el módulo que preguntó.

## Qué no debe cambiar una mejora futura

La venta y el remito no pasan por `sumar`: van en la misma transacción del ticket. No mover ese `UPDATE` acá. No tocar el cajero. No ensanchar esta puerta para que entienda recetas: la receta se queda en su módulo.
