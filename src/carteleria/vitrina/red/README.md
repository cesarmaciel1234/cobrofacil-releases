# Red vitrina

Qué hace: HTTP a la maestra y archivo `carteleria_cache.json`.

Qué función: `leer_http_maestra`, `guardar_cache`, `leer_cache`.

Cómo funciona: timeout 3 s. Guardado atómico (`.tmp` + `replace`). No escribe si `precios` está vacío.

Qué devuelve cuando falla: `None` (HTTP/lectura). El pulso usa caché.

Qué no debe cambiar: no pisar un JSON bueno con uno vacío.
