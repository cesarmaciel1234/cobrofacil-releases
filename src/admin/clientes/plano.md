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

Tarjetas KPI empresariales: **Cartera en la calle** (verde esmeralda, capital activo colocado rindiendo), **Cuentas activas** (azul, clientes con saldo operativo), **Cartera en riesgo** (rojo alerta, suma total de cuentas en mora +30d o excedidas; clic filtra chip Críticos) y **Cobros del mes** (teal, recupero de caja). En la tabla, la deuda sana al día viste verde (#059669); solo la deuda en mora o excedida viste rojo (#DC2626). Saldo a favor en azul (#2563EB). Disponible se lee `Excedido $X` si pasó el límite. Encabezados ordenan la grilla. **Planillas ▾** junta cobros y cargos.

La ficha abre `componentes/dialogo_historial_cliente.py`. Cabecera: **Editar** y **Saldo +** (textos distintos). Filtro **Hoy / Semana / Semana p. / Mes / Año / Período** (segundo clic = todo el historial). El ticket se ve abajo. **Imprimir historial** saca a la tiketera solo el período filtrado, con totales. **Eliminar** solo se habilita con un cargo vivo seleccionado; marca `BORRADO` y, si hay venta, la deja `CANCELADA`. Un ticket cancelado en F3 se ve `CARGO · CANCELADO` y `TICKET CANCELADO`. Planilla y auditoría: ticket de venta, `COB-`, id de pago o `F9 MANUAL`.

Buscador con debounce (~280 ms). Los chips de cartera filtran la cache local sin volver a la maestra. Contador `N de M` al lado del buscador.

En el header: **Planilla de cobros** (ABONO / COB-) y al lado **Planilla de cargos** (CARGO / #venta o MANUAL). Ambas usan el mismo filtro de período.

## Fondo

El historial lo pide `consulta/hilo.py` (`HiloMovimientosAdmin`) a `src/clientes_fiado/oficina/consulta_historial`. Si ese hilo falla, la ficha sigue. El ticket va por otro hilo (`PanelDetalleTicket` → `MotorTicket`). F6 tiene su propio hilo (`f6_centro_cobranzas/consulta_historial`). Los dos leen el mismo libro: un BORRADO de admin o una anulación del cajero quedan en ambos. Borrar escribe solo por `cerebro.borrar_cargo`.

Alta: `cerebro.hallar_duplicado(nombre, dni)` decide si ya existe; la UI pregunta y llama `actualizar_existente` o `alta_regular`. Cuadre: `cerebro.anotar_faltantes` carga el lote y refresca pendientes en el diálogo.

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

Frente empresarial: chip de políticas, tuerca ⚙ junto a Nuevo cliente (abre políticas). Mantenimiento automático al cargar. Chips cartera + riesgo. Columnas Estado y Tarifa. Menú `⋯`: Límite, Editar, Suspender, Promesa.

Fondo: `_correr_mantenimiento_auto` → `cerebro.aplicar_mantenimientos_auto`. Políticas en `dialogo_politicas_credito.py`. Sin Recalcular ni mantenimiento manual.

Plazo: columna `clientes.plazo_dias` (0 = sin plazo). Se edita en `componentes/dialogo_editar_cliente.py` → `cerebro.actualizar_ficha(..., plazo_dias)`; queda en la auditoría (`CAMPOS_FICHA`).
- Sin plazo: Días = días corridos desde el último cargo.
- Con plazo: cuenta regresiva `⏳ N días` → `⚠ Vence hoy` → `🔴 -1 día`, `-2 días`… (vencido).
- `plazo_dias=None` en `actualizar_ficha` no toca el valor guardado.
