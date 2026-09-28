# mp_token — token Mercado Pago de la tienda

Maestra publica `mp_access_token` (y claves TPV) en MariaDB `configuracion`.
Esclava lee por `db_manager` y lo cachea en su `config.json`.

| Función | Quién |
|---|---|
| `publicar()` | Al guardar Terminal TPV en la maestra; al migrar |
| `traer()` | Al conectar esclava; `EscuchaMP.token()` |

No pide el token en el monitor MP. No usa HTTP aparte: es la misma base de la tienda.


## ⚠️ Bug Histórico (Corrupción de Token)
En versiones anteriores, si el cajero guardaba un token correcto, el sistema funcionaba bien de inmediato. Sin embargo, "al rato" (cuando la esclava llamaba a 	raer()), el token se rompía y la auto-configuración daba Error 403. Esto pasaba porque al leer MariaDB/SQLite en modo fallback, el objeto devuelto era un <sqlite3.Row object...> y, al intentar convertirlo a string directamente sin acceder al índice (ila["valor"]), se guardaba la referencia de memoria literal sobreescribiendo el token original en config.json. Esto ya está solucionado en 	ienda.py comprobando el índice del diccionario explícitamente.