# Caché inicial

Qué hace: pinta la TV antes de abrir Chrome, sin esperar MariaDB.

Qué función: `CacheInicialMixin._cargar_datos_iniciales`.

Cómo funciona: `leer_cache()` → precios, ranking, publicidad. Marca `data_status=offline`. Si no hay JSON, publica vacío y el pulso sigue.

Qué devuelve cuando falla: estado mínimo; Chrome igual abre.

Qué no debe cambiar: no hacer `execute_query` en este hilo.
