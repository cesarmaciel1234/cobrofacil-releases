# Catálogo MariaDB

Qué hace: SELECT de productos para la TV.

Qué función: `leer_catalogo_db`.

Cómo funciona: `PRECIOS_SELECT`; si falta una columna, SELECT corto. Serializa filas. `top10` sale vacío: el ranking de la TV lo arma `MotorVentas`, no un `ORDER BY` al azar.

Qué devuelve cuando falla: el pulso atrapa y usa caché. No llamar esto desde el hilo de la UI.
