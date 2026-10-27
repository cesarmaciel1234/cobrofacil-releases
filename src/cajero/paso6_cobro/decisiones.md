# Decisiones a propósito (no son defectos)

Leé esto antes de “arreglar” F9, el PIN de fiado, el token de Mercado Pago, F6 o el botón COBRANZA.

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

## F6 y COBRANZA del paso 6 (mismo motor, distinta entrada)

**F6** es una tecla del **paso 5**. Cobranza pura: no hay carrito, no se vende nada. El cajero la aprieta y abre la ventana para cobrarle al cliente una deuda.

**COBRANZA** es un medio del **paso 6**. El cliente **está comprando**. Si además quiere pagar una deuda, toca ese botón en los medios de pago. Mismos medios (efectivo, tarjeta, QR, transferencia, mixto) y el mismo `MotorCobranzaMedios`. La diferencia es el ticket: acá hay venta.

No abrir la ventana de F6 desde el cobro. No poner el carrito en F6.

| | **F6 (paso 5)** | **COBRANZA (paso 6)** |
|---|---|---|
| Dónde | Tecla / botón en el carrito | Botón verde en los medios de pago |
| Hay venta | No | Sí: el cliente compra |
| Carrito | No lleva | Sí |
| Motor del abono | `MotorCobranzaMedios` | El mismo |
| Mixto | Abono. No pone resto a crédito | Venta (puede ir resto a cliente) |

Hay **otro** motor, el de la venta: `MotorPrincipalCobros`. Asienta el ticket. CRÉDITO solo carga la compra a la cuenta. No unificar ese motor con F6.

Si el cupo no alcanza en **CRÉDITO**, PIN de supervisor o Esc.

Tabla corta también en `src/cajero/README.md`.

## Token de Mercado Pago en Admin

El token se carga en **Admin → Terminales TPV** y la caja lo lee de la config de la estación. La caja tiene que hablar con Mercado Pago en el local: sin ese dato en la estación no hay QR ni Point.

Es una brecha a propósito, de etapa: más adelante el token lleva **código** (no queda solo el secreto en el archivo). No lo saques de Admin ahora. No lo pidas en cada cobro. `_tpv_qr_listo` y `_tpv_point_listo` siguen con `config._load_config()`.

## Corregir en código: el Point no muestra el monto

El 26/10/2026 el Point `NEWLAND_N950__N950NCBA01604854` no mostraba el importe. El payload de `enviar_monto` estaba bien. El token guardado en la caja era de otra cuenta que la sesión abierta en el equipo.

Prueba con el mismo device y el mismo `POST /v1/orders`:

- Token de Gabriel Maciel (usuario `140284216`): Mercado Pago responde 201 y la orden queda en `created`. El Point no la toma.
- Token de Cristina Báez Rodríguez (usuario `680256868`), que es la sesión abierta en ese Point: la orden pasa a `at_terminal` y el monto aparece.

La caja usa el token de Cristina, el mismo que publicó la maestra en `192.168.0.7`. `enviar_monto` ya no trata un 201 como «ya está en la terminal»: espera `at_terminal` y, si sigue en `created`, cancela y avisa `otra_cuenta`.

Al corregir `src/cajero/paso6_cobro/tarjeta_en_cobro/envio.py`:

1. `enviar_monto` no devuelve `ok` solo porque el POST dio 201. El cobro llegó al Point cuando `status` es `at_terminal`.
2. Si la orden sigue en `created`, cancelarla con `POST /v1/orders/{id}/cancel` y devolver `motivo: "otra_cuenta"`.
3. Antes de crear la orden, `GET /point/integration-api/devices` con ese token. Si `mp_device_id` no está, `sin_terminal`. Si `operating_mode` no es `PDV`, `standalone` y no enviar: en STANDALONE el equipo no recibe el monto.
4. `point_service._avisar_motivo` y `PanelTarjetaCobro._pintar` tienen que decir, para `otra_cuenta`, que el Point está abierto con otro usuario de Mercado Pago que el token de la caja.
5. No hardcodear un usuario. El token que manda el cobro es el de la cuenta logueada en el Point.
6. `sync_tienda/mp_token/tienda.py` `traer()` pisa el token local con el de la maestra. Si la maestra tiene la otra cuenta, el monto deja de aparecer. La corrección no puede volver a guardar un token cuyo device no está en PDV.
