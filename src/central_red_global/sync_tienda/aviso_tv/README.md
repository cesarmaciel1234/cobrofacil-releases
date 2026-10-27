# Aviso TV (datos al instante)

Qué hace: cuando se guarda un PNG, un precio, una oferta, un combo o un producto, las dos teles pisan **solo el catálogo**. No recarga Chrome ni F5.

Qué función: `avisar_datos_nuevos`, `repartir_desde_maestra`, `asegurar_escucha_datos`, `pisar_sello`, `leer_sello`.

`repartir_desde_maestra` corre solo en la maestra: pisa el sello y manda UDP `DATOS` a teles y esclavas, con la IP de ahora. Cada minuto el servidor titular lo vuelve a mandar para repartir el espejo. No se lo pide a sí misma. La esclava, al oírlo, sigue esa IP si cambió, actualiza espejo y tele, y no vuelve a mandar el aviso.

Cómo funciona: escribe `carteleria_datos.sello` (atómico `.part`), manda UDP `DATOS` y, si esta caja es esclava, POST `:8000/api/carteleria/datos_nuevos`. La otra PC, al oír `DATOS` o `PRECIOS_ACTUALIZADOS`, solo pisa su sello: no lo vuelve a mandar. El lanzador mira el sello cada 1 s y vuelve a leer MariaDB. La cara pide `/api/state`; si cambió precio, oferta, relámpago, condición o publicidad, redibuja sin `location.reload`.

Qué no debe cambiar: F5 sigue siendo recarga visual total. No tocar el tema oscuro del cajero.
