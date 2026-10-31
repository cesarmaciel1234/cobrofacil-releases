# Auditoría de Inventario

Esta subcarpeta contiene la interfaz de usuario de **Auditoría de Stock Continua** del módulo de Administración.

Antes de modificar el módulo, leer `plano.md` de esta carpeta y el `README.md` del motor en `src/cerebro_global/auditoria/README.md`.

---

## 1. Qué hace

Permite al personal autorizado (administrador y jefe de local) auditar el inventario físico en tiempo real de forma continua, rápida y sin pasos redundantes:
- Carga el listado completo de productos desde la base de datos (con soporte dual MariaDB en red y SQLite offline).
- Permite pistolear con lector de código de barras o buscar por código/nombre/departamento.
- Abre una ventana táctil de conteo físico adaptada a la unidad del producto (unidades, kilos, litros, metros, cajas).
- **Aplica el ajuste de stock de forma inmediata al dar Enter o aceptar**: no requiere presionar botones de lote posteriores; cada conteo queda asentado y registrado en el historial de auditorías al instante.
- Ofrece exportación del estado de auditoría a planillas CSV compatibles con Microsoft Excel.
- Permite auditar el historial de movimientos de stock por producto o de todo el local con filtros y pantalla completa.

---

## 2. Qué función cumple cada componente

### `auditoria_main.py`
- **`AuditoriaMain`**: Widget principal que se monta en `Screen.AUDITORIA` (25) de `src/main_window.py`.
  - **Barra superior**: Botón «VOLVER AL PANEL», título con tipografía góndola (`font-weight: 900`) y mensaje de estado dinámico.
  - **KPIs en vivo**: Total SKU, productos contados, faltante acumulado y sobrante acumulado.
  - **Filtro y buscador**: `txt_buscar` con temporizador de escáner continuo de 180 ms y selector de vista (`Todos`, `Solo contados`, `Solo diferencias`).
  - **Tabla de auditoría**: Columnas `ID`, `Código`, `Nombre`, `Depto`, `Stock sist.`, `Conteo real`, `Diferencia`. Estilizada con las reglas de letras de góndola (`src/utils/letra.py`).
  - **Barra inferior empresarial**:
    - `📋 HISTORIAL DE AJUSTES`: Abre el diálogo avanzado `DialogoHistorialAuditoria` (`dialogo_historial.py`).
    - `📊 EXPORTAR AUDITORÍA (CSV / Excel)`: Genera un archivo CSV con codificación `UTF-8-SIG` con el detalle de conteos, diferencias y estados.
    - Badge en vivo: `⚡ Auditoría Automática en Vivo` (o `👁️ Modo Consulta` si el usuario es cajero).

### `dialogo_historial.py`
- **`DialogoHistorialAuditoria`**:
  - Ventana modal redimensionable con botón de **Maximizar / Pantalla Completa** nativo al lado de la `[X]` de Windows (`WindowMaximizeButtonHint`) y botón integrado `🗖 PANTALLA COMPLETA` / `🗗 RESTAURAR`.
  - **Filtros multidimensionales de trazabilidad**:
    - Selector desplegable por Producto para auditar cada artículo específico con conteo de movimientos.
    - Buscador en tiempo real por texto libre (descripción, código de barras, ID, usuario o motivo).
    - Selector por Usuario Responsable (`admin`, etc.).
    - Selector por tipo de ajuste: Faltantes (-), Sobrantes (+) o Sin diferencia (0).
  - **Tarjetas KPI dinámicas**: Total de registros, productos auditados, faltante neto y sobrante neto en tiempo real.
  - **Tabla con Letras de Góndola**: Resaltado inteligente en rojo para faltantes y verde para sobrantes.
  - **Exportación a Excel / CSV**: Botón `📥 EXPORTAR (CSV / Excel)` con codificación `utf-8-sig`.

### `dialogo_conteo.py`
- **`DialogoConteo`**: Cuadro de diálogo modal optimizado para pantallas táctiles y teclado físico.
  - Teclado numérico grande en pantalla (0-9, coma, borrar, limpiar, +1, +5, +10).
  - Admite ingreso directo desde el teclado físico o numpad de la PC.
  - **Enter inmediato**: Tanto `Key_Return` como `Key_Enter` disparan el guardado sin que el foco quede retenido por los botones numéricos.
  - Si el campo queda vacío y se presiona Enter, asume conteo `0` (quiebre de stock confirmado).

---

## 3. Cómo funciona

1. **Lectura / Escaneo continuo**:
   - El auditor apunta la pistola al código de barras o escribe `10*779001` / `5*Alitas`.
   - `_on_texto_buscar` y `_on_codigo_escaneado` usan `BarcodeParser.parse_scan_text` para descomponer multiplicador y código.
   - Si el código tiene 8 o más dígitos, el temporizador de 180 ms dispara automáticamente la búsqueda sin obligar a presionar Enter.
   - Se localiza la fila en la tabla, se resalta y se abre `DialogoConteo` precargando la cantidad multiplicada (si la hubo).

2. **Ingreso y Confirmación**:
   - El auditor visualiza el nombre del producto, código, unidad y stock de sistema.
   - Ingresa o ajusta el conteo real y pulsa **Enter**.
   - `dlg.exec()` retorna `Accepted`.

3. **Impacto en Vivo**:
   - `_aplicar_conteo_fila` toma el conteo y llama a `conector_auditoria.solicitar_ajuste_stock`.
   - El motor ejecuta un único `UPDATE productos SET stock = ? WHERE id = ?` en la BD viva.
   - Se inserta un registro en `auditorias_inventario` (con fecha, responsable, stock anterior, nuevo y diferencia). La consola del servidor lee esa tabla. No hay un archivo paralelo.
   - Se invalida la caché local y la del catálogo global para que todas las terminales vean el stock nuevo.
   - La fila en la tabla se pinta de verde, la diferencia se normaliza a 0.000, los KPIs se refrescan y el cursor vuelve a `txt_buscar` para continuar escaneando el siguiente artículo.

4. **Auditoría e Historial de Movimientos**:
   - Al pulsar `📋 HISTORIAL DE AJUSTES`, se abre `DialogoHistorialAuditoria`.
   - El auditor puede maximizar a pantalla completa mediante el botón nativo al lado de la `[X]` o el botón en cabecera.
   - Con los filtros multidimensionales (producto, usuario, faltantes/sobrantes y texto libre), se puede seguir el rastro exacto de quién y cuándo modificó cada producto, analizando pérdidas o desvíos del negocio.
   - Puede exportar los resultados filtrados a Excel con un clic.

5. **Exportación e Informes de Auditoría**:
   - Al pulsar `📊 EXPORTAR AUDITORÍA`, se genera el archivo CSV con delimitador `;` y BOM UTF-8 (`utf-8-sig`) para Excel.

---

## 4. Perfiles y Permisos

- **Admin / Jefe**: Control total. Carga de conteos, ajustes en tiempo real, consulta de historial y exportación.
- **Cajero**: Modo consulta (solo lectura). La tabla se muestra informativa, los botones de edición se bloquean y el badge indica `👁️ Modo Consulta: Perfil cajero (solo lectura de inventario)`.
