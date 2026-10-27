# Pareja de maestras

Dos puestos se anuncian en la misma red. Una sola abre MariaDB.

## Qué hace
La titular guarda la tienda y, cada minuto, avisa su IP para que las esclavas bajen el espejo. La reserva es una esclava: guarda ese espejo y contesta el descubrimiento si la titular cambió de IP. Un ticket sale de la cola de la esclava recién cuando la reserva lo tiene en el espejo. Si la titular no contesta durante cinco minutos, la reserva abre MariaDB, suma ese espejo (no borra ni pisa) y pasa a ser la titular. Si la PC vieja vuelve y ya hay otra titular viva, se queda esclava.

## Qué función
* `buscar()` en `buscar.py`: si la IP guardada no abre el 3306, pregunta por UDP 37020 y se queda con la MariaDB que contesta. `tiene_la_tienda()` exige la tabla `productos`: un MariaDB vacío no se adopta. `adoptar()` escribe esa IP en la config. `elegir()` prefiere la IP guardada si sigue viva y tiene la tienda.
* `prender()` en `reserva.py`: entre las esclavas, la de nombre más bajo es la reserva. Responde `PUNPRO_DISCOVER` con `reserva` y la IP de la titular. `rol_latido()` pone `reserva` en el aviso de presencia.
* `vigilar()` en `promover.py`: si esta PC es la reserva y nadie abre el 3306 durante cinco minutos, prende MariaDB local, crea el esquema y `sumar()` vuelca el espejo. Después guarda `is_master` y rearranca el servidor como titular. `ceder_si_hay_otra()` al arrancar: si otra titular ya contesta, esta PC no abre una segunda tienda.
* `debe_esperar()`, `pedir()`, `responder()` y `soltar_propios()` en `acuse.py`: la cola marca `en_titular` y no borra el ticket hasta el acuse `ESPEJO_LISTO`. Si la titular cambia de PC, ese ticket se vuelve a mandar.

## Cómo funciona
1. La titular sigue anunciando `MAESTRA` con MariaDB, como hasta ahora, y además empuja `DATOS` con `server_ip`.
2. Cada esclava, si la IP vieja no contesta, busca en la red. Si la reserva contesta, usa la `titular_ip` que ella indica, y solo si ese 3306 abre.
3. Con tres esclavas, una queda de reserva (el nombre de PC más bajo). Las otras siguen de esclava. El espejo de la reserva es el backup. No se crea una tercera base.
4. Si nadie abre el 3306 durante cinco minutos, la reserva suma su espejo a una MariaDB local y pasa a ser la titular. Si la titular vuelve mientras tanto, la reserva apaga esa MariaDB y sigue esclava. Si el espejo no entra, tampoco cambia de puesto. Las demás la buscan en la red y le suben lo que la reserva todavía no tenía, aunque ya se lo hubieran mandado a la titular vieja. La PC vieja, si vuelve y ya hay titular, queda esclava y apaga su MariaDB.

## Qué no debe cambiar
* No abrir MariaDB en la reserva mientras la titular contesta. Solo a los cinco minutos de silencio.
* No meter el espejo en `punpro.db`. La promoción suma el espejo a la MariaDB local.
* No elegir la reserva por la IP: el nombre de la PC no cambia cuando cambia la dirección.
* No soltar un ticket de la cola antes de que la reserva lo tenga, salvo que esta PC ya sea la única titular.
