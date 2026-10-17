# Sync tienda (esclava → maestra)

Qué hace: copia productos, PNG y token de red hacia la PC maestra (`:8000`). El ranking de «lo más vendido» sale de `ranking/`: la esclava lo baja por HTTP; la maestra lo arma con sus ventas.

Qué función: `enviar_png_a_maestra`, `empujar_producto_a_maestra`, `cabeceras_lan`, `pedir_a_maestra`.

Cómo funciona: `rol.py` arma Bearer + `X-LAN-Token`. Si el host de la maestra es esta misma PC, no hay POST. PNG: `png/`. Inventario: `inventario/`. Tras cada PNG o producto, `aviso_tv/` pisa el sello y la TV de la maestra recarga **datos** (no F5).

Qué no debe cambiar: la clave LAN (`CLAVE_RED`). No mostrar `HTTP Error` al cajero de vitrina.
