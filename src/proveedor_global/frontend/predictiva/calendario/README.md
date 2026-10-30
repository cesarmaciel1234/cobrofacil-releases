# Calendario del local

## Qué hace la carpeta
Dice qué días abre este negocio, a qué hora, y si la mercadería fresca llega a la mañana o a la tarde. No pide la compra. La predictiva le pregunta.

## Qué función, con el nombre real
* `jornada.leer` / `jornada.guardar`: el calendario de este local en `reportes/calendario_local.json`.
* `jornada.abierto`: un día de venta. El feriado nacional y el cierre propio no cuentan.
* `jornada.turno`: `manana` o `tarde`. `turnos` puede cambiar un solo día de la semana.
* `jornada.fraccion`: 1 es la jornada patrón. Un día corto o solo el segundo turno pesan menos.
* `jornada.preparar`: el último día abierto antes de la llegada.
* `jornada.dias_cubiertos`: jornadas que cubre esa carga.
* `jornada.hasta_el_camion`: igual, y si el horario es doble turno suma la mañana del próximo reparto.
* `jornada.texto`: la línea que ve el centro de la pantalla.
* `dialogo.DialogoConfiguracion`: la tuerca. Cada día tiene corrido o doble turno, y el segundo horario al lado. Después del domingo, el feriado no abre.

## Cómo funciona, en el orden en que corre
1. Si no hay archivo, abre los siete días, de 08:00 a 20:00, y la carga llega a la mañana.
2. `calcular.proyectar` usa `preparar` y `dias_cubiertos` en vez de contar el domingo o el feriado como si se vendiera.
3. El horario general es la jornada patrón. Horario corrido parte el día por la mitad si la mercadería llega a la tarde. Doble turno separa la mañana y la tarde. Un día con otro horario se compara contra esa jornada: si es más corto, pesa menos; no pesa más de un día.

## Qué devuelve cuando falla
Si el archivo no se lee, vuelve a la base: semana completa y llegada a la mañana. Una hora mal escrita no pisa la anterior.

## Qué no debe cambiar una mejora futura
El feriado nacional sigue en `motor/feriados.py`. Este calendario no lo recalcula. Cada local tiene el suyo: la esclava no hereda el domingo de otra sucursal. No cerrar el local desde el cerebro operativo.
