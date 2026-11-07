# Clientes en admin

Pantalla clara. Lista, alta, ficha, límite, abono e historial.

**Abonar** (acción primaria) abre F6 (`perfil=Admin`). **Límite**, **Editar**, **Suspender/Reactivar** y **Promesa** están en el menú `⋯`.

Tarjetas KPI corporativas: **Cartera en la calle** (verde #059669, capital activo colocado), **Cuentas activas** (azul #2563EB), **Cartera en riesgo** (rojo #DC2626, mora y sobregiro; clic filtra Críticos) y **Cobros del mes** (teal #0D9488). En la grilla, deuda sana viste verde esmeralda y deuda en mora o excedida viste rojo alerta.

Interfaz empresarial: columnas Estado / Tarifa, chip de políticas, tuerca ⚙ al lado de Nuevo cliente (políticas %). Mantenimiento **automático** al cargar cartera (3% o 3%+5% si >30d; no repite en 30 días). Menú `⋯`: Límite, Editar, Suspender, Promesa (sin Recalcular ni Mantenimiento manual).

**Planillas ▾** agrupa cobros y cargos.

Si hay ventas Fiado o Clientes completadas sin cargo, aparece una franja ámbar. CUADRAR abre la lista. **Cargar en la cuenta** usa `cerebro.anotar_faltantes` y refresca pendientes; no deja la grilla vieja tras el primer éxito.

Tras un abono ok, el cartel usa el mismo texto del mensajero de cobro (`COBRO EXITOSO` con nombre, pago y saldo).

El guardado no está en esta carpeta. Entra por `src/clientes_fiado`, objeto `cerebro` (`hallar_duplicado`, `alta_regular`, `actualizar_existente`, …). El plano de esta pantalla es `plano.md`. El crédito: `src/clientes_fiado/plano.md`.

En el historial: **Editar** / **Saldo +**; **ELIMINAR TICKET / DEUDA** solo con cargo vivo. Ver `componentes/README.md` y `plano.md`.

La lista calcula los días de atraso con `cerebro.ultimos_cargos()` por lotes de hasta 500 IDs. No volver a llamar `ultimo_cargo()` dentro del ciclo que dibuja las filas.

`dialogo_recalculo_fiado.py` solo analiza cargos. No escribe la deuda.

Al pasar el mouse por el nombre se ve la huella. AUDITORÍA lista alta, edición, límite, cargo, abono y fusión. Solo lee `clientes_auditoria`.
