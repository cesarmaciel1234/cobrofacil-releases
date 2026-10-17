# Vitrina (pulso de la TV)

Qué hace: arma el catálogo que ve la cartelería.

Qué función: `pulso_vitrina()` → `(data, status)` con `online` | `offline` | `error`. El kiosk llama esto desde `DbSyncWorker`.

Cómo funciona: MariaDB local; si es esclava y la DB no está, HTTP de la maestra; si ambos fallan, `carteleria_cache.json`. Un catálogo vacío no se guarda ni pisa el JSON bueno. Toda excepción se come y vuelve caché o `{"precios": []}`.

Qué no debe cambiar: no lanzar excepción al hilo Qt. No borrar caché con 0 productos.
