# Aviso TV (datos al instante)

Qué hace: cuando se guarda un PNG, un precio o un producto, la TV de la maestra pisa **solo el catálogo**. No recarga Chrome ni F5.

Qué función: `avisar_datos_nuevos`, `pisar_sello`, `leer_sello`.

Cómo funciona: escribe `carteleria_datos.sello` (atómico `.part`). Si esta caja es esclava, POST `:8000/api/carteleria/datos_nuevos`. El lanzador de TV mira el sello cada 1 s y vuelve a leer MariaDB. La cara web pide `/api/state` cada 3 s; si el hash de datos cambió, actualiza precios y fotos sin `location.reload`.

Qué no debe cambiar: F5 sigue siendo recarga visual total. No tocar el tema oscuro del cajero.
