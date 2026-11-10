# Plano — cartera de clientes

La rama arranca en esta carpeta. El crédito vive en `src/clientes_fiado/`.

```
admin/clientes/
  plano.md
  admin_clientes_main.py     pantalla
  theme.py
  consulta/                  HiloMovimientosAdmin
  componentes/               diálogos
```

Ecosistema: la pantalla pide historial y cargos al motor de fiado. Cobra con F6 en perfil Admin. No lee el estado en vivo del cajero.

## Frente

**Abonar** es la acción primaria de cada fila. Límite, editar ficha, suspender/reactivar y promesa viven en el menú `⋯`. **Abonar** abre F6 con `perfil=Admin`. Sin deuda deja saldo a favor. Sin PIN.

Tarjetas KPI empresariales: **Cartera en la calle** (verde esmeralda, capital activo colocado rindiendo), **Cuentas activas** (azul, clientes con saldo operativo), **Cartera en riesgo** (rojo alerta, suma total de cuentas en mora +30d o excedidas; clic filtra chip Críticos) y **Cobros del mes** (teal, recupero de caja). En la tabla principal (10 columnas: ID, DNI, Nombre, Tipo, Estado, Deuda, Mantenimiento, Días, Tarifa, Acciones), DNI antecede a Nombre y los anchos se distribuyen dinámicamente de forma armónica para erradicar espacios vacíos. **Límite** y **Disponible** se ocultan para lograr un diseño visual limpio y ágil (disponibles en el sidebar del historial y configurables en `⋯`). La columna **Deuda** exhibe la deuda total a cobrar con intereses incluidos (capital + mantenimiento acumulado); a su lado, la columna **Mantenimiento** refleja el interés nuevo devengado (+$$$). La deuda sana al día viste verde (#059669); la deuda en mora o riesgo viste rojo (#DC2626). Saldo a favor en azul (#2563EB). Encabezados ordenan la grilla. **Planillas ▾** junta cobros y cargos.

La ficha abre `componentes/dialogo_historial_cliente.py`. Interfaz limpia con botón `☰` junto al avatar que despliega u oculta un **sidebar lateral a la izquierda**, integrando en su interior los botones **Editar** y **Saldo +** junto a la ficha completa del cliente y sus métricas financieras (Límite, Deuda Capital, Mantenimiento, Total Estimado y Disponibilidad). El interés corre estrictamente por ticket en su propio contenedor (camuflado bajo el nombre "mantenimiento"), sin generar ni cargar jamás cargos planos de mantenimiento que ensucien el historial o la planilla de cargos. En la columna **Tipo**, se diferencian con claridad visual inmediata: **`VENTA`** (rojo #DC2626) para ventas a crédito con ticket, **`CARGO MANUAL`** (púrpura bold #7C3AED) para cargos manuales a mano cargados en cuenta sin ticket de venta, y **`COBRO`** (verde esmeralda #059669) para abonos o pagos recibidos, desglosando al pie los subtotales respectivos. La columna **Descripción** no carga textos redundantes para ventas normales al estar el número ya presente en la columna `Ticket / cobro`, reservándose para destacar nítidamente las excepciones o alarmas reales (`⚠️ Excepción admin`, `⚠️ Excepción PIN`, etc.) en tono ámbar de advertencia. Se adapta al 94% del ancho y al 90% del alto disponibles. Cada ticket muestra mantenimiento nuevo y días transcurridos. Las filas de cobro (COBRO) se pintan completas en verde (tipografía y fondo esmeralda) para demarcar claramente el antes y el después de cada cancelación de saldo. Al pie, el **Total estimado** resalta con badge KPI prominente (16px, peso 900) para lectura instantánea del cliente. Los cargos de interés muestran el concepto en la grilla y conservan el reparto por ticket en el tooltip. El historial se pinta en lotes de 100 movimientos para mantener activo el hilo visual con cuentas grandes. Filtro **Hoy / Semana / Semana p. / Mes / Año / Período** (segundo clic = todo el historial). El ticket se ve abajo. **Imprimir historial** saca a la tiketera solo el período filtrado, con totales. **Eliminar** solo se habilita con un cargo vivo seleccionado; marca `BORRADO` y, si hay venta, la deja `CANCELADA`, revirtiendo su interés generado. Un ticket cancelado en F3 se ve `VENTA · CANCELADA` y `TICKET CANCELADO`. Planilla y auditoría: ticket de venta, `COB-`, id de pago o `F9 MANUAL`.

Buscador con debounce (~280 ms). Los chips de cartera filtran la cache local sin volver a la maestra. Contador `N de M` al lado del buscador.

En el header: **Planilla de cobros** (ABONO / COB-) y al lado **Planilla de cargos** (CARGO / #venta o MANUAL). Ambas usan el mismo filtro de período.

## Fondo

El historial lo pide `consulta/hilo.py` (`HiloMovimientosAdmin`) a `src/clientes_fiado/oficina/consulta_historial`. Si ese hilo falla, la ficha sigue. El ticket va por otro hilo (`PanelDetalleTicket` → `MotorTicket`). F6 tiene su propio hilo (`f6_centro_cobranzas/consulta_historial`). Los dos leen el mismo libro: un BORRADO de admin o una anulación del cajero quedan en ambos. Borrar escribe solo por `cerebro.borrar_cargo`.

Alta: `cerebro.hallar_duplicado(nombre, dni)` decide si ya existe; la UI pregunta y llama `actualizar_existente` o `alta_regular`. Cuadre: `cerebro.anotar_faltantes` carga el lote y refresca pendientes en el diálogo.

Las consultas de historial y ticket usan hilos sin padre Qt, retenidos hasta finalizar y esperados al cerrar la aplicación. Cerrar una ficha no destruye una consulta que sigue activa. Si no se puede consultar el cuadre, la pantalla muestra error y no lo presenta como una lista vacía. La carga por lote revalida el ticket y evita duplicar el cargo dentro de una transacción.

El lector busca la venta en la base activa, la copia portable y la SQLite local pendiente. Solo consulta. Si no encuentra la venta, el panel lo informa; nunca altera el registro de deuda.

## Qué no cambiar

- No abrir otra ventana para ver el ticket.
- No borrar físicamente un cargo ni su ticket: se marca `BORRADO`.
- No abrir desglose de venta para abonos ni para cargos sin `venta_id`.
- No mover la consulta de venta al hilo de interfaz.
- No unir el lector de tickets con los motores que guardan ventas o deuda.
- No volver a llamar `ultimo_cargo()` por fila al pintar la cartera.
- No consultar la maestra en cada tecla del buscador ni al cambiar solo un chip.


## Cartera: filtros y plazo

Frente empresarial: chip de políticas (`Interés simple · X% mensual (+Y% >Zd)`), tuerca ⚙ junto a Nuevo cliente (abre diálogo interactivo de políticas de crédito). Permite configurar tasa mensual base, recargo de apalancamiento y días de plazo. Chips cartera + riesgo. Columnas Estado y Tarifa. Menú `⋯`: Límite, Editar, Suspender, Promesa.

Fondo: sin recargo plano de mantenimiento automático. El interés corre por ticket sobre capital pendiente, prorrateado por días con escalado de apalancamiento si supera los días de plazo configurados. Motores estrictamente separados e independientes de ventas: si el cálculo de interés se interrumpe, las ventas, los cobros y la cartera continúan funcionando con total normalidad. El abono calcula el interés vigente, asienta una sola línea consolidada y aplica el pago primero al interés y luego al capital FIFO.

Plazo: columna `clientes.plazo_dias` (0 = sin plazo). Se edita en `componentes/dialogo_editar_cliente.py` → `cerebro.actualizar_ficha(..., plazo_dias)`; queda en la auditoría (`CAMPOS_FICHA`).
- Sin plazo: Días = días corridos desde el último cargo.
- Con plazo: cuenta regresiva `⏳ N días` → `⚠ Vence hoy` → `🔴 -1 día`, `-2 días`… (vencido).
- `plazo_dias=None` en `actualizar_ficha` no toca el valor guardado.
