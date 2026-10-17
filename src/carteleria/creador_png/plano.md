# Plano — Creador PNG y vitrina

Rama: `src/carteleria/creador_png/`

## Frente

Cartelería → PNG productos. Un PNG vivo por producto. Crear o cargar **pisa** ese archivo (no `asado_2`, `asado_3`). El que había va a `Catalogos/png_productos/_anteriores/` y en la galería está **Volver al anterior** si la prueba no gustó.

Galería: ventana maximizada, **F11** pantalla completa, miniaturas rápidas, casillero + ✕ para borrar.

## Fondo

- Panel: `panel_vitrina/panel.py`
- Nombre vivo de TV: `asado.png` (no `asado_4`). Respaldo: `panel_vitrina/archivo.py`
- Galería: `panel_vitrina/galeria/` (`dialogo.py`, `tarjetas.py`, `thumbs.py`, `cargar.py`)
- Recorte IA: `ventana_html.py` + `servidor.py` + `app.py` escribe a `.part` y publica con `publicar_nuevo` (no incrementa `_2`)
- LAN: `sync_tienda/png/esclava.py`. Tras el envío, `aviso_tv` pisa datos en la TV de la maestra (sin recargar la cara).

## Qué no romper

El PNG local. La TV lee el mismo nombre de archivo. No la galería de rubros de inventario.
