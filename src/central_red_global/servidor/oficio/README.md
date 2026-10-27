# Oficio del servidor

El proceso `--server` es el agente de la PC. Arranca con Windows en los dos puestos. El cajero, el admin y el jefe no leen este módulo para vender: siguen con la base de la maestra o con su offline.

## Qué hace la carpeta
Mira `config.json` y cumple un solo oficio. No mezcla los dos.

## Qué función, con el nombre real
* `oficio()`: `maestra` si `es_pc_maestra_local()`, si no `esclava`.
* `vigila_mariadb()`: verdadero solo en maestra. La esclava no llama a `start_server()`.
* `cumplir_esclava()`: prende tres hilos y la pareja. `oficio-esclava` sube la cola y, si la maestra contestó, llama a `refrescar()`. Si la IP guardada no contesta, `buscar()` pregunta en la red. Cada ticket sube entero o sigue en la cola. Si en la bajada hay un ticket a medio cargar, esa vuelta no se pasa y el espejo queda como estaba. Si pasa, la copia entera va a las tres rutas del nodo. `oficio-carteleria` llama a `pulso_vitrina()`. `oficio-cola` sube `offline_queue.json` y `offline_cambios.json` apenas la maestra contesta; si salió algo, despierta esa bajada sin esperar el minuto. La esclava de nombre más bajo es la reserva: contesta el descubrimiento con el espejo y la IP de la titular, y no abre MariaDB. No reescribe `carteleria_global` y no vacía `punpro.db`. Si la maestra no contesta, la cola y el espejo quedan. Si una vuelta falla, ese hilo sigue y el otro no se entera.
* `pedir_reparto()`: la esclava adelanta la misma vuelta (cola y después espejo) y la tele cuando la maestra manda `DATOS`. No reenvía el aviso.
* `pedir_bajada()`: la cola de esta PC ya subió. Adelanta el espejo.
* `agente_tiene_el_espejo()`: verdadero si esta PC es esclava y el proceso `--server` ya está vivo. La ventana del jefe, en ese caso, no prende otro hilo de copia.
* `rearmar_arranque()`: vuelve a escribir el acceso directo de Inicio con el programa de ahora, si `auto_start_store_server` está prendido.
* `retomar_oficio()`: mata el `--server` viejo, apaga MariaDB local si el puesto pasó a esclava, rearma el acceso directo y lanza el proceso de nuevo.

## Cómo funciona, en el orden en que corre
1. Windows o el lanzador abren `--server`.
2. `bandeja.py` o `headless.py` preguntan `oficio()`.
3. Maestra: MariaDB, API y presencia, como hasta ahora. El watchdog la levanta si se cayó.
4. Esclava: `cumplir_esclava()` abre tres hilos. El watchdog, cada 10 segundos, los vuelve a pedir si se murieron, y no toca MariaDB. Cada minuto, y también al aviso de la maestra, la vuelta es una sola: subir la cola y, si contestó, bajar al espejo lo que falta. La tele va en su hilo. Si no llegan precios, la caché anterior queda. El cajero sigue en su offline.
5. Maestra: el mismo proceso corre `sincronizador_carteleria`, que reescribe `carteleria_global` desde `productos` y, si la grilla cambió, avisa a teles y esclavas. La esclava no llama a ese sincronizador: un `DELETE` desde acá pisaría la grilla de la tienda. Un dato que llega por `/api/carteleria/datos_nuevos` también se reparte desde acá.
6. Al convertir el puesto, `retomar_oficio()` cambia el proceso. No borra el arranque de Windows.

## Qué devuelve cuando falla
`cumplir_esclava()` no lanza. Si el espejo no arranca, queda la última copia. `rearmar_arranque()` devuelve falso si no pudo escribir el acceso directo. `retomar_oficio()` no deshace el puesto ya guardado en `config.json`.

## Qué no debe cambiar una mejora futura
* No hacer que la esclava ejecute `UPDATE` de la tienda ni encienda MariaDB.
* No meter el espejo en `punpro.db`. La cola offline del cajero sigue en su camino.
* No llamar a `retomar_oficio()` desde el cajero.
* No llamar a `sincronizador_carteleria` desde el oficio esclava.
