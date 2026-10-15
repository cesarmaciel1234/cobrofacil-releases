# Decisiones a propósito (no son defectos)

Leé esto antes de “arreglar” F9, el PIN de fiado o el token de Mercado Pago.

## F9 sin PIN

F9 queda **siempre visible** en el teclado del cobro. Es cobro de emergencia: en QR / tarjeta / transferencia / mixto cierra a mano si el pago no llega. En transferencia (venta o cobranza), si llegó otro monto, F9 **asocia** ese cobro al ticket o al abono. Enter no asocia: espera el exacto (luz verde) o guarda sin TPV (luz roja). No borres F9.

El perfil jefe marca el pago digital como no firmado. F9 sirve para **amaestrar** a los cajeros en cancha: que sepan cerrar la venta a mano. Cuando el equipo esté entrenado, el jefe podrá **ocultar F9** o **ponerle PIN**. Eso todavía no está. No lo implementes en este pase.

No borres F9. No le pidas PIN ahora.

El cobro F9 se anota en `motor_auditoria_digital` (hilo aparte) para el monitor. Si esa nota falla, la venta igual queda.

## PIN de fiado / cuenta corriente

El PIN de cobranza está apagado. El PIN de supervisor solo aparece si el cupo no alcanza.

El PIN para fiado y cuenta corriente se pedirá después. No lo enciendas en cobranza ni en el abono verde.

## Tendido por venta (no reutilizar)

La caja se reusa (`preparar_para_venta`). Cada venta y cada vuelta a los medios vacían el tendido: mixto, efectivo, cliente, QR y los ids de Mercado Pago. Si el total coincide con el ticket anterior, Enter no cubre con esos importes. No se deja el cliente del ticket previo en el combo.

## Esc: un paso atrás y el campo vacío

Esc (y «Cambiar») vuelve a la grilla de medios. **El medio que se deja queda en cero.** Si el cajero vuelve a Mixto, Efectivo o Clientes, escribe de nuevo. No se reusa el importe, el cliente ni la palomita. Es un error humano grave: el total igual al ticket anterior y Enter cobraban el tendido viejo.

Esc con el cursor en el casillero (mixto o efectivo) también sale: no se queda el texto. En la grilla, Esc sale al carrito.

## Mixto (no cobrar de más)

El Point de mixto cobra solo la parte de tarjeta, y solo después de cubrir el total. Enter (o F11 cubierto) manda el Point. Verde: palomita y, si hay efectivo, cajón. Después transferencia, QR o cliente. No se reescribe el reparto ni se manda el Point otra vez. Un excedente digital no es vuelto. Confirmar el cliente del resto no reclasifica la venta a Fiado. Un abono no cierra el carrito. F9 no saltea el cliente de ese resto.

## Dos motores (no unificar)

Hay dos piezas y no son el mismo motor duplicado:

1. **Motor real de la venta:** `motor_pagos/MotorPrincipalCobros`. Asienta el ticket. Crédito solo carga la venta a la cuenta.
2. **Intermediario de cobranza:** `MotorCobranzaMedios` en **F6**. Cobra el abono.

En el paso 6, **COBRANZA** (verde) y **F6** abren el mismo `DialogoCentroCobranzas` del paso 5. No cargan deuda en el ticket. No fusionar ese diálogo con el motor de la venta. Si el cupo no alcanza, PIN de supervisor o Esc.

Mapa: paso 5 llena el carrito. Paso 6 cobra la venta (mixto puede incluir cliente). F6 / Admin Abonar cobran deuda con el mismo diálogo; mixto de F6 no pone resto a crédito.

## Token de Mercado Pago en Admin

El token se carga en **Admin → Terminales TPV** y la caja lo lee de la config de la estación. La caja tiene que hablar con Mercado Pago en el local: sin ese dato en la estación no hay QR ni Point.

Es una brecha a propósito, de etapa: más adelante el token lleva **código** (no queda solo el secreto en el archivo). No lo saques de Admin ahora. No lo pidas en cada cobro. `_tpv_qr_listo` y `_tpv_point_listo` siguen con `config._load_config()`.
