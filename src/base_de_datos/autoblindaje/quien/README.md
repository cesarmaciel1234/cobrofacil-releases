# quien — de qué máquina sale el .sql

`maestra.py`, clase `Quien`.

## Qué hace

Elige el MariaDB vivo sin quedar atado a una IP de `config.json`. La maestra puede ser esta PC o otra, y esa otra puede cambiar de dirección.

## Funciones

- `host_vivo(pedido)`: devuelve el host, o `""` si no hay nadie. Guarda el resultado 20 segundos para no repetir el aviso en el mismo ciclo.
- `_soy_maestra()`: `True` solo si `config` dice `is_master` y no dice esclava de cartelería. Si falla la lectura, `False`.
- `_maestra_anunciada()`: llama a `elegir()` de `servidor/pareja/buscar.py`. Junta las respuestas de UDP 37020. Usa la MariaDB que abre el 3306. Si la IP guardada sigue entre ellas, esa. Si la reserva contesta, sigue la `titular_ip` que indica, y solo si ese puerto abre. Si nadie contesta, `""`.
- `_es_esta_pc(host)`: la IP anunciada es esta máquina (localhost, nombre o alguna IP local).
- `_host_local(host)`: `127.0.0.1`, `localhost`, el nombre de la PC o vacío.
- `_host_es_esta_pc(host)`: la usa el restaurar para no aplicar un `.sql` de MariaDB sobre el SQLite de otra caja. Vacío, localhost y `::1` cuentan como esta PC. Si no puede resolver el nombre, `False`.

## Cómo corre `host_vivo`

1. Si `_soy_maestra` y el puerto 3306 de `127.0.0.1` abre en 0,8 s, devuelve `127.0.0.1`.
2. Si no, escucha el anuncio. Si la IP anunciada es esta PC y el 3306 local abre, `127.0.0.1`. Si es otra PC y su 3306 abre en 3 s, esa IP.
3. Si hubo anuncio pero el puerto está cerrado, devuelve `""`. No prueba la IP vieja.
4. Si no hubo anuncio, usa `pedido` solo cuando ese puerto está abierto ahora. Si `pedido` es esta PC, queda en `127.0.0.1`.
5. Si nada de eso, `""`.

## Qué no debe cambiar

- No volver a leer `db_host`, `preferred_master_ip` ni `carteleria_master_ip` para decidir el volcado.
- No devolver `127.0.0.1` en una esclava solo porque el pedido decía localhost y el puerto está cerrado.
