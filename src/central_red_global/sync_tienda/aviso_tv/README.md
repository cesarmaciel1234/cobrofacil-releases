# Aviso TV (datos al instante)

Qué hace: cuando se guarda un PNG, un precio, una oferta, un combo o un producto, las dos teles pisan **solo el catálogo**. No recarga Chrome ni F5.

Qué función: `avisar_datos_nuevos`, `asegurar_escucha_datos`, `pisar_sello`, `leer_sello`.

Cómo funciona: escribe `carteleria_datos.sello` (atómico `.part`), manda UDP `DATOS` y, si esta caja es esclava, POST `:8000/api/carteleria/datos_nuevos`. La otra PC, al oír `DATOS` o `PRECIOS_ACTUALIZADOS`, solo pisa su sello: no lo vuelve a mandar. El lanzador mira el sello cada 1 s y vuelve a leer MariaDB. La cara pide `/api/state`; si cambió precio, oferta, relámpago, condición o publicidad, redibuja sin `location.reload`.

Qué no debe cambiar: F5 sigue siendo recarga visual total. No tocar el tema oscuro del cajero.
