# Barrial

Cobranza de barrio sobre la cuenta revolving. No hay cuotas ni mora diaria automática. No hay WhatsApp.

## Qué hace

- **Aging** (`aging.py`): clasifica días sin movimiento en `ok` / `d30` / `d60` / `d90`. `cumple_filtro` arma los chips 30+ / 60+ / 90+.
- **Estado** (`estado.py`): `activo` | `suspendido` en `clientes.estado_cuenta`. `suspender` / `reactivar` escriben con auditoría.
- **Promesa** (`promesa.py`): una fecha `promesa_fecha` + nota. `vencida` compara con hoy.
- **Mantenimiento** (`mantenimiento.py`): base **3%** + apalancamiento **5%** si >30 días (`tarifar`). `aplicar_automatico` corre al cargar la cartera; no vuelve a cobrar si ya hubo `MANTENIMIENTO` en 30 días. Config vía tuerca (políticas).

La lista de pantalla solo identifica las cuentas a revisar. Antes de cobrar, `MotorCuenta` vuelve a leer saldo, antigüedad y último mantenimiento bajo bloqueo y escribe deuda y movimiento en una transacción; si falla la lectura o la escritura, el mantenimiento no se aplica. Esto evita usar saldo desactualizado y duplicar el cargo cuando dos cajas cargan la cartera a la vez.

## Cómo entra

Solo por `cerebro` (`aplicar_mantenimientos_auto`, `tarifar_mantenimiento`, `guardar_politicas_credito`, …). Admin no importa esta carpeta directo.

## Qué no cambiar

- No cobrar dos veces dentro de la ventana de 30 días.
- No conectar Wasap.
- No inventar tabla de cuotas.
