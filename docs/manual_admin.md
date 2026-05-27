# 👑 MANUAL DE ADMINISTRACIÓN Y SUPERVISIÓN: ELITE 2026

Este manual está reservado para el personal de supervisión y dueños de negocio. Detalla las funciones de control, auditoría y seguridad avanzada.

---

## 🔐 1. INTERVENCIÓN DE SUPERVISOR (F11)
El comando **F11** es la herramienta de asistencia inmediata en el punto de venta.

1.  **Asistencia en Línea**: Si un cajero tiene un problema, presione F11.
2.  **Validación**: Ingrese su PIN de Administrador.
3.  **Apertura Autorizada**: El cajón se abrirá automáticamente para inspección. El sistema registrará este evento como "INTERVENCIÓN" en la auditoría, vinculando su nombre al del cajero actual.
4.  **Burbuja Bombero**: Podrá navegar por el inventario o configuración. Para volver al terminal, toque la burbuja parpadeante. Los precios se actualizarán en el carrito del cajero automáticamente.

---

## 📊 2. AUDITORÍA INDUSTRIAL Y ESTACIÓN DE CIERRE Z (F12)
El administrador cuenta con una consola interactiva de control dividido (Splitter) de tipo industrial que centraliza todo el control monetario y de seguridad sin interferir con las operaciones:

1.  **Arqueos y Cierres Z (Lado Izquierdo)**:
    *   **Ejecución de Cierre Z (F12)**: Acceso directo al asistente de arqueo ciego paso a paso para cerrar los turnos de cajeros o el balance general del día.
    *   **Historial de Cierres Z**: Una grilla con la lista de todos los cierres consolidados guardados en la base de datos, desglosando la fecha, el cajero que lo ejecutó, la diferencia monetaria (marcando sobrantes en verde y faltantes en rojo) y el efectivo físico contado.
    *   **Re-impresión Reconstruida**: Con doble clic sobre cualquier fila del historial, el sistema reconstruye en caliente todas las métricas de ese día y re-imprime el ticket de Cierre Z exacto por la impresora física de resguardo.

2.  **Bitácora de Auditoría y Vigilancia 24/7 (Lado Derecho)**:
    *   Un visor unificado e interactivo que captura al instante cualquier movimiento dentro del sistema:
        *   **🚨 Brechas de Seguridad (ALERTA_SEGURIDAD)**: Registros del monitor perimetral cuando el cajón de dinero es abierto mediante llave física o fuerza bruta sin una venta activa de por medio.
        *   **🔑 Intervenciones de Supervisor (INTERVENCIÓN)**: Reporte detallado de auditoría cada vez que un administrador usa su PIN para desbloquear el punto de venta o abrir el cajón (F11).
        *   **❌ Cancelaciones de Tickets (CANCELACIÓN)**: Registros del historial de folios cancelados, vinculando el usuario y el total anulado que fue devuelto al inventario.
        *   **👤 Turnos y Aperturas**: Control absoluto de la hora de entrada y salida de cada cajero y auxiliar.
        *   **💸 Movimientos (INGRESO / RETIRO)**: Auditoría de flujos de capital extra (retiros de resguardo).
    *   **Scroll Infinito de Auditoría**: Para garantizar un rendimiento fluido a 60 FPS, los eventos se renderizan dinámicamente en lotes de 50 filas a medida que se desliza por el visor, permitiendo auditar cientos de miles de registros sin pausas.
    *   **Exportación Profesional Inteligente a Excel**: Genera en caliente planillas Excel (`.xlsx`) completamente formateadas, coloreando con semáforos de advertencia las brechas perimetrales (rojo), intervenciones (ámbar) y cancelaciones (morado) para auditorías directivas directas.

*   **Auditoría de Ventas Industrial**:
    *   **Separación Unidades vs. Kilos (Balanza)**: Para evitar descuadres en los pesajes de la carnicería, el sistema separa estrictamente las magnitudes.
        *   **Unidades (UN)**: Acumula las ventas de productos envasados o unitarios.
        *   **Peso en Kilos (KG)**: Acumula los pesajes de balanza con una precisión milimétrica de **3 decimales** (`#.### kg`), garantizando que no se pierda ni una aguja de carne o ave.
    *   **Segmentación Atómica por Departamento**: En el pie de página de la auditoría se desglosa el dinero total recaudado en tiempo real para las áreas críticas: 🥩 Carnes, 🍗 Aves y 🥫 Almacén.
*   **Ranking Top 6 de Departamentos (Pre-carga de Emojis)**:
    *   El módulo de reportes incluye un motor inteligente de asignación de iconos (`get_depto_icon`). Cada vez que creas un departamento (ej: *Achuras, Preparados, Embutidos, Verdulería, Bebidas, etc.*), el sistema le asocia automáticamente su emoji correspondiente.
    *   Muestra el **Top 6 de Departamentos más vendidos** en gráficos y leyendas interactivas de forma 100% automatizada.
*   **Preservación Automática de Ofertas**:
    *   El sistema cuenta con un blindaje en el módulo de Inventario. Al editar los datos básicos de cualquier artículo, sus precios promocionales activos (`precio_oferta`) y umbrales de cantidad mínima para ofertas (`cant_oferta`) se mantienen intactos en la base de datos de manera transparente.
*   **Reportes AI Boss**: Acceda a análisis predictivos sobre qué productos se venderán más mañana basado en el historial.

---

## ⚙️ 3. GESTIÓN DE CATÁLOGO, OFERTAS Y MARGEN INDUSTRIAL
Para optimizar al 100% el flujo de trabajo administrativo, el sistema cuenta con dos estaciones independientes y especializadas:

1.  **Inventario Tradicional (F2 - Sin Distracciones)**:
    *   Un visor limpio a pantalla completa para auditar stock, costos y departamentos de manera rápida y sin elementos distractores.
    *   Hacer doble clic sobre cualquier fila permite abrir la ficha detallada tradicional para ediciones masivas o cambio de códigos de barra.
    *   **Carga con Scroll Infinito (Lazy Loading)**: Para evitar cuelgues o congelamientos visuales al cargar catálogos con miles de productos, el visor implementa renderizado paginado en caliente. Carga de manera instantánea bloques ligeros de 50 productos y los despliega fluidamente a 60 FPS a medida que desliza la barra de desplazamiento hacia abajo.

2.  **Estación de Ofertas y Precios (F3 - El Inventario con Herramientas)**:
    *   Una consola unificada de control dividido (Splitter) que expone todo el catálogo de productos con búsqueda instantánea y un panel lateral derecho scrollable con herramientas delta rápidas (`-10`, `-1`, `+1`, `+10`) para regular existencias sin entrar en menús secundarios.
    *   **Selección Múltiple y Libro de Carteles A4 (Impresión Masiva)**: Para evitar crear y mandar a imprimir carteles de ofertas uno por uno, ahora puede seleccionar varios artículos en la tabla a la vez (manteniendo presionado `Ctrl`, `Shift` o simplemente arrastrando el mouse sobre la grilla). Al hacerlo, se activará el botón superior **📚 IMPRIMIR MASIVO (A4)**, el cual compilará todas las ofertas activas del lote seleccionado y generará un **único archivo PDF continuo (Libro desglosado de promociones)** listo para mandarse a la impresora física en un solo lote.
    
*   **📊 Simulador de Margen Industrial en Caliente**:
    *   Calcula y actualiza de forma matemática la rentabilidad comercial del negocio en tiempo real a medida que el supervisor edita los valores en los campos de edición rápida:
        *   **Margen Regular %**: Rentabilidad base a precio de venta regular: `((Precio Regular - Costo) / Precio Regular) * 100`.
        *   **Margen Promo %**: Rentabilidad neta aplicando la oferta especial: `((Precio Oferta - Costo) / Precio Oferta) * 100`.
        *   **Ahorro Cliente por Compra**: El incentivo exacto de ahorro total que se le otorga al cliente al cumplir la condición de compra mínima (`cant_oferta`).
    *   **Semáforo Financiero de Viabilidad**:
        *   🔴 **🚨 PÉRDIDA (Rojo)**: Se activa si el precio de oferta cae por debajo del costo de compra del producto. Advierte pérdida directa de capital.
        *   ⚠️ **MARGEN CRÍTICO (Amarillo)**: Advierte si el margen de la oferta cae por debajo del 10%. Ideal para regular promociones agresivas pero controladas.
        *   🟢 **PROMOCIÓN RENTABLE (Verde)**: Indica un margen neto saludable mayor o igual al 10% de ganancia por artículo vendido.

---

## 🚨 4. PROTOCOLO ANTE ALERTAS SOS
Si el marco de la pantalla parpadea en **Rojo**:
1.  **Cajón Abierto**: El sensor detecta que el cajón no se ha cerrado tras una venta o intervención.
2.  **Exceso de Efectivo**: Se ha superado el umbral de seguridad (ej. $70,000). Instruya al cajero a realizar un **Retiro de Resguardo (F5)** inmediatamente.

---
*Manual de Supervisión Administrativa - Cobro Fácil POS*
