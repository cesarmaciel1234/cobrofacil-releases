# Etiquetas de góndola

## Frente

Admin → Etiquetas Góndolas. Se eligen productos y «Lanzar impresión góndola (PDF)». El PDF queda en `Etiquetas_Impresas`.

## Fondo

`AdminEtiquetas.generar_pdf` llama a `_armar_pdf_gondola`. El PDF lo escribe `EtiquetaRenderer.generar_pdf_gondola_personalizado` con `abrir_documento_pdf` (`QPdfWriter`).

No usar `QPrinter` para este PDF. En el ejecutable no va el plugin de impresión y Qt cierra el programa.

Un error de una fila (precio vacío, código de barras) se muestra en un cartel. No puede salir de `cargar_productos` ni de `generar_pdf`: PyQt cierra el ejecutable si una señal tira una excepción.

La librería `reportlab` y el paquete `barcode` tienen que ir en `requirements.txt` y en `01_Compiladores_y_Ejecutables/empaquetar_pos.py`.
