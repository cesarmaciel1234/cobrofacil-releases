# Creador PNG

Qué hace: recorta la foto (IA) y asocia el PNG al producto de la vitrina.

Qué función: `DialogoCreadorPNG` (HTML), `PanelPngProductos` (vitrina).

Cómo funciona: el panel está en `panel_vitrina/`. Galería en `panel_vitrina/galeria/` (grande, borrar, un archivo por producto). El recorte corre en `servidor.py` + `app.py`. El PNG vivo se pisa; el anterior va a `_anteriores/`. Copia a otra PC: `sync_tienda/png/esclava.py`.

Qué no debe cambiar: el PNG local. Un solo proceso de cartelería. Plano en `plano.md`.
