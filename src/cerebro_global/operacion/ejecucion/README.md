# Ejecución de planes

## Qué hace la carpeta

Persiste un plan y controla sus estados, sin enviar mensajes ni crear recepciones.

## Qué función, con el nombre real

* `crear_borrador(db, plan)`: guarda el plan inicial.
* `aprobar`, `marcar_despachado`, `marcar_recibido`, `cancelar`: cambian de estado de forma controlada.

## Cómo funciona

Un plan nace `BORRADOR`; puede aprobarse o cancelarse. Solo un aprobado puede marcarse despachado y solo uno despachado puede recibirse. Cada cambio deja un evento auditable.

## Qué devuelve cuando falla

Devuelve falso o `None`; no modifica inventario ni altera el plan previo.

## Qué no debe cambiar una mejora futura

`DESPACHADO` todavía no significa que se mandó WhatsApp: la futura integración debe registrar el canal y la confirmación del proveedor antes de usar ese estado.
