# Barrial

Cobranza de barrio sobre la cuenta revolving. No hay cuotas ni mora diaria automática. No hay WhatsApp.

## Qué hace

- **Aging** (`aging.py`): clasifica días sin movimiento en `ok` / `d30` / `d60` / `d90`. `cumple_filtro` arma los chips 30+ / 60+ / 90+.
- **Estado** (`estado.py`): `activo` | `suspendido` en `clientes.estado_cuenta`. `suspender` / `reactivar` escriben con auditoría.
- **Promesa** (`promesa.py`): una fecha `promesa_fecha` + nota. `vencida` compara con hoy.
- **Mantenimiento legado** (`mantenimiento.py`): el recargo plano de mantenimiento fue retirado. La regla activa vive en `oficina/cuenta/interes.py`: interés simple por ticket prorrateado por días, con escalado configurable de apalancamiento al superar los días de plazo.

La tasa activa se calcula sobre el capital pendiente, no sobre cargos de mantenimiento ni sobre intereses anteriores. Se asienta una sola línea al registrar un abono. La anulación de ticket revierte su interés asociado. Los motores están estrictamente aislados de ventas.

## Cómo entra

Solo por `cerebro` (estado, promesa, aging y compatibilidad histórica de políticas). Admin no importa esta carpeta directo.

## Qué no cambiar

- No cobrar dos veces dentro de la ventana de 30 días.
- No conectar Wasap.
- No inventar tabla de cuotas.
