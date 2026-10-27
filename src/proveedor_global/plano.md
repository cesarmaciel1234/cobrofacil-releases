# Plano - Proveedor Global (`src/proveedor_global`)

Este módulo centraliza la gestión de Proveedores, Abastecimiento Automático, Recepción de Mercadería por Escáner y Compras Tradicionales (Romaneos de carne/frigorífico). Al ser un módulo transversal, es utilizado directamente por:
- `src/admin` (Gestión de compras, pedidos de reposición e ingreso de mercadería)
- `src/contabilidad` (Control de deudas de proveedores del Jefe y Cuenta Corriente)
- `src/carteleria` (Consulta rápida de ingresos de mercadería)

---

## 🖥️ Frente
La interfaz visual vive en `frontend/vista_proveedor.py` y se organiza en tres pestañas principales con estructura simétrica para que el operador nunca se desoriente:

1. **Pestaña 1: 📦 Pedidos Faltantes (`frontend/panel_pedidos_automaticos.py`):**
   - **Qué ve el usuario:** Tarjetas KPI con artículos en quiebre, proveedores involucrados y presupuesto estimado de reposición. Selector de proveedor con tabla de pedidos y exportación directa a WhatsApp.
   - **Botones:** "🔄 Actualizar Faltantes", "🔗 Asignar Proveedor" y "📋 Copiar para WhatsApp".

2. **Pestaña 2: ⚡ Recepción Rápida por Escáner (`frontend/panel_recepcion_rapida.py`):**
   - **Estructura Espejo (2 Columnas Superiores):**
     - **Columna Izquierda ( stretch 6 ):** Datos del remito, fecha, selector de proveedor con opción `"Sin Proveedor (Proveedor General)"` predeterminada, botón `＋ Id` para crear proveedores al vuelo, barra de escaneo verde (`7*codigo`) y tabla en vivo de artículos escaneados con costos editables y botón `❌` para quitar ítems erróneos.
     - **Columna Derecha ( stretch 4 ):** Card oscura con `RESUMEN DE RECEPCIÓN` (contador de bultos y monto total gigante en verde `#10B981`), selector de `CONDICIÓN DE PAGO` (Cta. Cte. / Contado), botón `📥 CONFIRMAR INGRESO A STOCK`, botón `📱 Copiar WhatsApp` y `🗑️ Limpiar`.

3. **Pestaña 3: 🥩 Romaneo y Frigorífico (Romaneo Tradicional):**
   - **Estructura Espejo:** Misma división de 2 columnas superiores (Izquierda: tropa, precio unitario, carga de peso y tabla de garrotes; Derecha: Card oscura de totales, condición de pago y botón `✅ PROCESAR COMPRA`).

4. **Sección Inferior Compartida (Pestañas 2 y 3):**
   - `📋 Histórico de Compras a Proveedores (Cuentas Corrientes)`:
     - Tabla unificada (`ID`, `Proveedor`, `Monto Total`, `Pagado`, `Restante`, `Fecha`, `Estado`, `Acción`). La fecha es el día de la compra (`20/10/2026`), no la hora del sistema.
     - Al confirmar un remito (sea por escáner o romaneo), el remito impacta de inmediato en el renglón 1 del historial.
     - Si se cargó como `A Pagar (Cta. Cte.)`, figura con estado `⏳ Pendiente` y saldo restante.
     - Botón `👁️ Ver Remito` para ver detalle y amortizar/liquidar deudas con `💳 Pagar Deuda`.

---

## ⚙️ Fondo
La lógica de negocio se divide limpiamente en servicios especializados en `backend/`:
1. **Pedidos Automáticos:** Consume `src/motor_abastecimiento` (modo solo-lectura sobre `productos` y tabla satélite `abastecimiento_proveedor_map`).
2. **Recepción Rápida:** Consume `backend/recepcion_service.py` (`RecepcionService`).
   - `buscar_producto_por_escaneo(texto)`: parsea multiplicador `7*` y consulta en `productos` por código o nombre.
   - `procesar_ingreso_mercaderia(...)`: en una sola conexión hace el remito, `stock = stock + cantidad`, el costo, los ítems y el gasto. Si una línea falla, deshace el remito. El id sale de la fila insertada, no del último id de la tabla. Después arma el texto de WhatsApp.
   - Si no se especifica proveedor, lo asocia a `"Proveedor General"` sin trabar el flujo.
3. **Compras y Deudas de Frigorífico:** Consume `backend/motor_proveedor.py` (`MotorProveedor`).
   - `FichaProveedor.crear` / `listar` (tabla `proveedores`), `save_proveedor`, `load_proveedores`, `pagar_proveedor`.
   - **En qué tablas toca:** `productos`, `proveedores`, `romaneos`, `romaneo_items` y `gastos`.
   - **Contabilidad:** Todo remito cargado a Cta. Cte. se asienta en `gastos` bajo la categoría `"Mercadería / Stock"` con status `"Pendiente"`. El asiento de compra usa la cuenta `1.1.03.01` Mercaderías y la moneda de la config (`currency_code` / `currency_symbol`), no un peso argentino fijo.
   - **Moneda:** `backend/moneda.py` (`texto`, `leer`, `codigo`, `contable`). Pedido, recepción y romaneo muestran y leen el mismo símbolo. `$2.250,00` y `$2,250.00` son el mismo número. Euro, real, sol y libra pisan un código ARS viejo.
