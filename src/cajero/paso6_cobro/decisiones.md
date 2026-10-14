# Decisiones a propósito (no son defectos)

Leé esto antes de “arreglar” F9, el PIN de fiado o el token de Mercado Pago.

## F9 sin PIN

F9 es cobro de emergencia cuando **no hay internet** (luz TPV roja). Con red, QR / tarjeta / transferencia cierran solos: el cajero no toca F9. No borres F9.

El perfil jefe marca el pago digital como no firmado. F9 sirve para **amaestrar** a los cajeros en cancha: que sepan cerrar la venta a mano. Cuando el equipo esté entrenado, el jefe podrá **ocultar F9** o **ponerle PIN**. Eso todavía no está. No lo implementes en este pase.

No borres F9. No le pidas PIN ahora.

El cobro F9 se anota en `motor_auditoria_digital` (hilo aparte) para el monitor. Si esa nota falla, la venta igual queda.

## PIN de fiado / cuenta corriente

El PIN de cobranza está apagado. El PIN de supervisor solo aparece si el cupo no alcanza.

El PIN para fiado y cuenta corriente se pedirá después. No lo enciendas en cobranza ni en el abono verde.

## Dos motores (no unificar)

Hay dos piezas y no son el mismo motor duplicado:

1. **Motor real de la venta:** `motor_pagos/MotorPrincipalCobros`. Asienta el ticket.
2. **Intermediario de cobranza:** `MotorCobranzaMedios` en el módulo de cobranza. Cobra el abono, da el ok, y el orquestador manda `pago_completado` al motor real.

No fusionar cobranza con el motor de paso 6. El intermediario no cierra la venta.

## Token de Mercado Pago en Admin

El token se carga en **Admin → Terminales TPV** y la caja lo lee de la config de la estación. La caja tiene que hablar con Mercado Pago en el local: sin ese dato en la estación no hay QR ni Point.

Es una brecha a propósito, de etapa: más adelante el token lleva **código** (no queda solo el secreto en el archivo). No lo saques de Admin ahora. No lo pidas en cada cobro. `_tpv_qr_listo` y `_tpv_point_listo` siguen con `config._load_config()`.
