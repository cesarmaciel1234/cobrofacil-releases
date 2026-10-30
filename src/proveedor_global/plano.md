# Plano - Proveedor Global (`src/proveedor_global`)

Este módulo centraliza la gestión de Proveedores, Abastecimiento Automático, Recepción de Mercadería por Escáner y Compras Tradicionales (Romaneos de carne/frigorífico). Al ser un módulo transversal, es utilizado directamente por:
- `src/admin` (Gestión de compras, pedidos de reposición e ingreso de mercadería)
- `src/contabilidad` (Control de deudas de proveedores del Jefe y Cuenta Corriente)
- `src/carteleria` (Consulta rápida de ingresos de mercadería)

---

## 🖥️ Frente
La interfaz visual vive en `frontend/vista_proveedor.py`. El dashboard abre seis tarjetas: Realizar pedido (`frontend/pedido/`), Cargar pedido (`frontend/carga/`), Proveedores (`frontend/fichas/`), Pago centralizado (`frontend/pago/`), Historial (`frontend/historial/`) y Fórmula (`frontend/formula/`). La carga no muestra el histórico. «← Módulos» vuelve a las seis. Fórmula abre Carne, Cerdo, Pollo, Huevo, Congelado y Compra predictiva. La predictiva guarda stock, no compras, y el porqué sale en el WhatsApp. Cada fórmula marca sus días. El suelto marca los días en el proveedor. Huevo muestra los cortes de Promedios, lo que rinde 1 cajón (12 maples, 360 huevos) y, en la misma tabla, las columnas Vendido y Reajuste. El reajuste sale solo del total de huevos que queda. El filtro es hoy, semana, semana pasada y mes. El costo de cada fórmula sale del costo de reposición del cajón, partido por lo que esa fórmula rinde. No muestra el precio de venta. Ese costo lo lee el pedido automatizado cuando la reposición ya lo cargó. El stock de las porciones lo manda `frontend/formula/motores/inventario.py` cuando hay un cajón: lee el cajón y, si el cajero vende en ese instante, envía el stock nuevo. Carne pasa antes por Media res, Mocho y Pecho. El nombre de un activo abre el historial (`frontend/fichas/panel.py`).

1. **Realizar pedido (`frontend/pedido/panel.py`):**
   - **Qué ve el usuario:** Tarjetas KPI con artículos en quiebre, proveedores involucrados y presupuesto estimado de reposición. Selector de proveedor con tabla de pedidos y exportación directa a WhatsApp. En el historial del proveedor, «Productos asociados» busca por nombre o código y desenlaza uno o varios.
   - **Botones:** "🔄 Actualizar Faltantes", "🔗 Asignar Proveedor" y "📋 Copiar para WhatsApp". En Asignar, el departamento sale del inventario, el producto se busca por el nombre, por otra palabra o por el código de la pistola, y solo dentro de ese departamento, y el proveedor se escribe: si no existe, se crea. Se ve igual en casa y en el negocio.

2. **Recepción por escáner (`frontend/carga/recepcion.py`), subtartjeta de Cargar pedido:**
   - **Estructura Espejo (2 Columnas Superiores):**
     - **Columna Izquierda ( stretch 6 ):** Datos del remito, fecha, selector de proveedor con las fichas ya cargadas y `"Sin Proveedor (Proveedor General)"` predeterminada, sin alta, barra de escaneo verde (`7*codigo`) y, debajo, una sola línea Por bulto. El selector es Huevo, Media res, Mocho, Pecho, Cerdo, Pollo y Congelado. Al elegir uno, entra solo la receta que guardó el jefe en Promedios, con el código de cada corte. En las fórmulas por kilo, el precio del cajón se divide por los kilos que quedan, sin la merma. Borrar menudos o carcasa sube ese costo. Huevo no usa esa cuenta. El precio de compra se escribe en el bulto y la fórmula devuelve el costo de cada presentación. El total es la cantidad de bultos por ese precio.
     - **Columna Derecha ( stretch 4 ):** Card oscura con `RESUMEN DE RECEPCIÓN` (contador de bultos y monto total gigante en verde `#10B981`), selector de `CONDICIÓN DE PAGO` (Cta. Cte. / Contado), botón `📥 CONFIRMAR INGRESO A STOCK`, botón `📱 Copiar WhatsApp` y `🗑️ Limpiar`.

3. **Pestaña 3: Carga al proveedor.** La línea es cajas × kilos × precio. Sirve para media res, queso o cualquier mercadería. A la derecha, el total y `✅ PROCESAR COMPRA`.

4. **Historial (`frontend/historial/`):** tarjeta propia, no va debajo de la carga. Arriba: hoy, semana, semana pasada, mes y el resto; proveedor y estado. Debajo, pagado, restante y monto de ese filtro.
   - `📋 Compras a proveedores`:
     - Tabla unificada (`ID`, `Proveedor`, `Monto Total`, `Pagado`, `Restante`, `Fecha`, `Estado`, `Acción`). La fecha es el día de la compra (`20/10/2026`), no la hora del sistema.
     - Al confirmar un remito (sea por escáner o romaneo), el remito impacta de inmediato en el renglón 1 del historial.
     - El contado y el fiado entran los dos. Contado figura pagado. Fiado figura con saldo. En casa se suman los remitos de esta PC a la copia del negocio.
     - Botón `👁️ Ver Remito` para ver detalle y amortizar/liquidar deudas con `💳 Pagar Deuda`.

---

## ⚙️ Fondo
La lógica de negocio se divide limpiamente en servicios especializados en `backend/`:
1. **Pedidos Automáticos:** Consume `src/motor_abastecimiento` (modo solo-lectura sobre `productos` y tabla satélite `abastecimiento_proveedor_map`).
2. **Recepción Rápida:** Consume `backend/recepcion_service.py` (`RecepcionService`).
   - `buscar_producto_por_escaneo(texto)`: parsea multiplicador `7*` y consulta en `productos` por código o nombre.
   - `procesar_ingreso_mercaderia(...)`: en una sola conexión hace el remito, el costo, los ítems y el gasto. Un producto suelto suma su cantidad. Una fórmula no: manda los kilos del jefe y el costo, y el inventario los escribe sin revisarlos. La recepción no avisa a la maestra: un hilo consulta y el servidor nutre, sin bajar el catálogo. Carne, Cerdo y Pollo usan el mismo método de bulto: el precio se divide por los kilos que quedan, el enlace copia stock y costo y no suma, y la fórmula solo cuenta los cortes. El ejemplo que ya cuadró está en `src/jefe/promedios/pollo/README.md`. Si una línea falla, deshace el remito. El id sale de la fila insertada, no del último id de la tabla. Después arma el texto de WhatsApp.
   - Si no se especifica proveedor, lo asocia a `"Proveedor General"` sin trabar el flujo.
3. **Compras y Deudas de Frigorífico:** Consume `backend/motor_proveedor.py` (`MotorProveedor`).
   - `FichaProveedor.crear` / `listar` (tabla `proveedores`), `save_proveedor`, `load_proveedores`, `pagar_proveedor`. En casa el alta y el enlace quedan en `offline_cambios.json`. El id `P00012` nace en la maestra al reconectar. La pantalla no distingue ese caso. El editor del proveedor y su historial salen de esta ficha y de `romaneos` / `gastos`.
   - **En qué tablas toca:** `productos`, `proveedores`, `romaneos`, `romaneo_items` y `gastos`.
   - **Contabilidad:** Todo remito cargado a Cta. Cte. se asienta en `gastos` bajo la categoría `"Mercadería / Stock"` con status `"Pendiente"`. El asiento de compra usa la cuenta `1.1.03.01` Mercaderías y la moneda de la config (`currency_code` / `currency_symbol`), no un peso argentino fijo.
   - **Moneda:** `backend/moneda.py` (`texto`, `leer`, `codigo`, `contable`). Pedido, recepción y romaneo muestran y leen el mismo símbolo. `$2.250,00` y `$2,250.00` son el mismo número. Euro, real, sol y libra pisan un código ARS viejo.
