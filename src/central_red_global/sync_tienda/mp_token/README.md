# mp_token — token Mercado Pago de la tienda

Maestra publica `mp_access_token` (y claves TPV) en MariaDB `configuracion`.
Esclava lee por `db_manager` y lo cachea en su `config.json`.

| Función | Quién |
|---|---|
| `publicar()` | Al guardar Terminal TPV en la maestra; al migrar |
| `traer()` | Al conectar esclava; `EscuchaMP.token()` |

No pide el token en el monitor MP. No usa HTTP aparte: es la misma base de la tienda.
