# Panel vitrina PNG

Qué hace: asocia un PNG a cada producto para la TV.

Qué función: `PanelPngProductos` en `panel.py`. `lista.cargar`, `preview.pintar`, `guardar.asociar`, `guardar.copiar_a_maestra`, `guardar.texto_listo`.

Cómo funciona: clic en la lista → preview. Galería (`galeria/`) maximizada, F11, casillero y ✕. Crear o cargar pisa el PNG de ese producto; el anterior queda en `_anteriores/`. Guardar escribe el nombre en el producto y copia a la maestra si aplica. El cartel no muestra `HTTP Error`.

Qué no debe cambiar: el PNG local se guarda aunque falle la maestra. No abrir un segundo proceso de cartelería.
