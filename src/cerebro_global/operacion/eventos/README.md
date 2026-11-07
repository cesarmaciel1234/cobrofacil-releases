# Eventos operativos

## Qué hace la carpeta

Guarda hechos que llegan desde el servidor, periféricos o motores sin depender de una pantalla abierta. Durante la validación física guarda solo en `reportes/cerebro_operativo.json`.

## Qué función, con el nombre real

* `registrar(tipo, origen, cuerpo, evento_id=None)`: anota un hecho idempotente en el JSON local.
* `listar(limite=100)`: recupera los hechos recientes.

## Cómo funciona

Cada hecho tiene un `evento_id` único, tipo, origen, fecha y cuerpo JSON. Si un periférico reintenta con el mismo id, no duplica el hecho. No hay tabla ni conexión a SQLite o MariaDB en esta etapa.

## Qué devuelve cuando falla

Devuelve `None` o una lista vacía; no interrumpe ventas, stock ni recepción.

## Qué no debe cambiar una mejora futura

Un evento ya escrito no se edita ni se borra para “corregir” historia: una corrección entra como otro evento.
