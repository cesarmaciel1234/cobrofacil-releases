# Cambio de rol del servidor

Esta carpeta convierte una PC entre **MAESTRA** y **ESCLAVA**. `motor.py` es la fachada que usa la pantalla; `maestra.py` y `esclava.py` validan el cambio y actualizan la conexión y la configuración.

`convertir_en_esclava()` comprueba el anuncio de la IP por UDP 37020, la identidad estable `store_id` y que la MariaDB tenga la tienda antes de enlazar. Si la identidad no coincide, no cambia el motor ni la configuración de tienda. `puede_corregir_rol_a_maestra_local()` solo habilita reparar una esclava si su `db_host` es una IP de esta PC y MariaDB local responde. `convertir_en_maestra()` valida la conexión local, normaliza el host a `localhost` y relanza el oficio. El flujo de reserva/promoción está separado en `servidor/pareja/`.

No usar una dirección IP como identidad del negocio: una dirección puede cambiar. Consultar `../reglas_servidor.md` y `../pareja/README.md` para el comportamiento de red y recuperación.
