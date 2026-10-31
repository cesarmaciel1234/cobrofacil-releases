# Etiquetas de góndola

## Frente

Admin → Etiquetas Góndolas. Se seleccionan los productos del catálogo mediante la tabla o el buscador en tiempo real.

Dispone de dos modalidades de lanzamiento:
1. **«🖨️ IMPRIMIR EN TÉRMICA (CON CORTE)»**: Diseñado para pequeños comercios que no tienen impresora convencional ni hojas autoadhesivas. Abre un diálogo interactivo (`ConfigurarTermicaDialog`) con previsualización en vivo, selección de ancho (58mm o 80mm), cantidad de copias por artículo y corte automático tras cada etiqueta (o en tira continua).
2. **«🏭 LANZAR IMPRESIÓN GÓNDOLA (PDF)»**: Genera hojas de etiquetas en formato A4 (21, 30 o 40 por hoja) para impresoras láser o de tinta convencionales. El PDF queda en `Etiquetas_Impresas`.

Las letras de esta pantalla (Consolas Bold en id, Segoe UI Bold en nombre y precio, KPI 900 en QLabel) son la referencia del proyecto: `src/utils/letra.py`. Al tocar otro módulo admin/jefe se copian de ahí. No en el cajero.

Ecosistema: pide id, nombre y precio al catálogo para imprimir. No cambia stock ni promo.

## Fondo

1. **Modo Térmica (ESC/POS)**:
   - `AdminEtiquetas.imprimir_termica` abre `ConfigurarTermicaDialog`.
   - `armar_lote_etiquetas_termica` (en `generador_termica.py`) construye los bytes ESC/POS estándar con cabecera de comercio, nombre del artículo en negrita, precio gigante (`DOUBLE_HW_ON`), detalle de unidad (`x KILO`/`x UNIDAD`), fecha/PLU, código de barras térmico (EAN-13/Code128) y comando de avance y corte de papel (`CUT_PAPER = GS + b'\x56\x41\x00'`).
   - Se despacha vía `printer_manager.imprimir_etiquetas_gondola(lote_bytes)` a través del spooler de Windows o puerto Serial. En modo offline o simulación, procesa sin congelar la interfaz.

2. **Modo PDF**:
   - `AdminEtiquetas.generar_pdf` llama a `_armar_pdf_gondola`.
   - El PDF lo escribe `EtiquetaRenderer.generar_pdf_gondola_personalizado` con `abrir_documento_pdf` (`QPdfWriter`).
   - No usar `QPrinter` para este PDF: en el ejecutable no va el plugin de impresión y Qt cierra el programa.

3. **Manejo de Excepciones**:
   - Un error de una fila (precio vacío, código de barras) se muestra en un cartel. No puede salir de `cargar_productos`, `generar_pdf` ni `imprimir_termica`: PyQt cierra el ejecutable si una señal tira una excepción.
   - Las librerías `reportlab` y `barcode` están en `requirements.txt` y en `01_Compiladores_y_Ejecutables/empaquetar_pos.py`.
