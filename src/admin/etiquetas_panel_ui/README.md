# Módulo de Etiquetas de Góndola (`etiquetas_panel_ui`)

## ¿Qué hace?
Este módulo permite la emisión e impresión industrial de etiquetas de precios para estanterías, góndolas, heladeras y vitrinas comerciales. Permite a los negocios minoristas (carnicerías, fiambrerías, almacenes, verdulerías y minimarkets) rotular sus precios de manera clara y profesional sin necesidad de adquirir costosas impresoras láser convencionales o planchas de stickers.

## Componentes y Funciones

1. **`etiquetas_panel_main.py` (`AdminEtiquetas`)**:
   - Panel principal de administración de etiquetas.
   - Tarjetas Hero compactas de métricas clave (Catálogo disponible, Lote seleccionado, Membrete comercial).
   - Buscador en tiempo real por código de barras, ID/PLU o descripción.
   - Filtro ágil por categorías (cargadas dinámicamente desde la base de datos).
   - Tabla industrial con selección rápida: clic en cualquier celda o pulsación de la tecla <kbd>Espacio</kbd> alterna el estado de selección del producto.
   - Compatibilidad completa SQLite offline y MariaDB online (conversión segura de filas `sqlite3.Row` a diccionario).
   - Botones rápidos: `☑️ Marcar Todo` y `◻️ Desmarcar` con contador dinámico en tiempo real (`📌 X producto(s) marcado(s)`).
   - Aplicación estricta de **Letras de Góndola** (`src/utils/letra.py`): IDs en Consolas Bold, descripciones y precios en Segoe UI Bold, títulos y KPIs en peso 900.
   - Marcado inteligente en tabla de productos ya impresos (`🏷️ [ETIQUETA]`, `🔥 [OFERTA]`, `🏷️🔥 [AMBOS]`).
   - Botón `🖨️ IMPRIMIR EN TÉRMICA (CON CORTE)`: Dispara el flujo de impresión directa por ticketera ESC/POS mostrando la cantidad seleccionada.
   - Botón `📄 LANZAR IMPRESIÓN GÓNDOLA (PDF)`: Genera grillas A4 personalizadas para impresión convencional.

2. **`generador_termica.py`**:
   - Construcción de comandos binarios ESC/POS a bajo nivel.
   - `armar_etiqueta_termica()`: Aplica márgenes, cabecera de comercio, nombre envuelto según el ancho de papel, precio gigante con doble alto y doble ancho (`DOUBLE_HW_ON`), unidad normalizada (`x KILO`/`x UNIDAD`), fecha y código de barras térmico (EAN-13 / Code128).
   - Inyección de salto y corte automático de papel (`CUT_PAPER = GS + b'\x56\x41\x00'`) tras cada etiqueta para que salgan listas para ser colocadas en los perfiles porta-precios.
   - `armar_preview_texto()`: Generador de simulación textual para previsualización inmediata en pantalla.
   - `armar_lote_etiquetas_termica()`: Ensambla el lote con soporte de múltiples copias por producto.

3. **`dialogo_termica.py` (`ConfigurarTermicaDialog`)**:
   - Diálogo modal interactivo con adaptación temática automática (Modo Día / Modo Noche).
   - Selector de ancho de papel: 58 mm (32 columnas) u 80 mm (48 columnas).
   - Selector de copias por producto (1 a 50).
   - Opciones de corte: corte individual automático (recomendado) o corte único al final de la tira.
   - Conmutadores de contenido: mostrar/ocultar rubro, código de barras y fecha/PLU.
   - Panel de previsualización en vivo (simulación monospace idéntica al ticket térmico).
   - Indicador de estado de la ticketera configurada.

## ¿Cómo funciona?
1. El usuario busca y selecciona uno o más artículos desde la tabla de productos.
2. Al presionar **«IMPRIMIR EN TÉRMICA (CON CORTE)»**, se valida la selección y se abre el diálogo de configuración.
3. El comerciante confirma el ancho (ej. 58mm) y la cantidad de copias, visualizando la etiqueta en tiempo real.
4. Al hacer clic en **«INICIAR IMPRESIÓN TÉRMICA»**, el módulo genera la trama de bytes ESC/POS y la envía a través de `printer_manager.imprimir_etiquetas_gondola()`.
5. La ticketera imprime cada etiqueta con el precio legible a distancia y realiza un corte limpio de papel, entregando los rótulos listos para colocar en la góndola.
6. La interfaz actualiza el estado de los artículos a impresos y restablece la selección automáticamente.
