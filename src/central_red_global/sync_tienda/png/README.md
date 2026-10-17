# PNG maestra ↔ esclava

Qué hace: sube y baja PNG de producto entre la esclava y la maestra.

Qué función: `enviar_png_a_maestra`, `bajar_pngs_de_maestra`.

Cómo funciona: POST `/api/carteleria/upload_png` en el puerto 8000 con `pedir_a_maestra` (Authorization + X-LAN-Token; urllib no pierde el Bearer). Si el host de la maestra es esta misma PC, no envía. 200: `aviso_tv` pisa el sello para que la TV recargue datos. 401 u otro fallo: el PNG local queda; el texto para el usuario no muestra `HTTP Error`.

Qué no debe cambiar: la TV lee la carpeta local. No debilitar el token de la red.
