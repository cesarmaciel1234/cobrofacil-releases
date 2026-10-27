# Plano — motor de auditoría digital

Rama: `src/motor_auditoria_digital/`. Base: `src` (sin plano). No cobra. No cierra la venta. Si se cae, la caja y el motor de cobros digitales siguen.

## Frente

Admin → **Auditoría de cobros digitales** (`admin/mercadopago/mercadopago_main.py`).

Filtro de fechas: Hoy (al abrir) / Semana / Mes / Año / Período. El botón **Filtros** vive en `admin/mercadopago/filtros/`: cruzados, ticket sin id, id sin ticket y, si hubo más de un token, la cuenta.

Tarjetas del rango: **Bruto MP** y **Neto MP** vs **Tickets digitales** vs **Firmados** vs **Sin firmar / F9** vs **Cliente** (cobranza F6 en QR/tarjeta/transferencia). Esa cobranza queda en el mes en que **entró la plata**, aunque la venta a fiado sea de otro mes. La línea de cuentas suma el id de pago de cada titular.

Grilla: **Concepto** `Venta QR` o `Cobranza QR · nombre`. **ID de pago** = id MP, o `F9 MANUAL` solo si fue F9. **Ticket venta** y **Ticket cobro** en columnas distintas. Pie: leyenda de los tres números.

No pinta: efectivo, fiado, clientes / cuenta corriente, DNI, el cobro en vivo, el token.

## Fondo

`main.py` llama `arrancar()`. Hilo `auditoria_digital`. El estado vive en un dict (`_estado`): no hay `global _clave`, así no vuelve el `UnboundLocalError` al abrir admin o jefe.

```
motor_auditoria_digital/
  empleado.py
  consultas/          pregunta, no escribe motores principales
  libro_tickets/      historial local de tickets digitales (no se borra)
  libro_cobranzas/    abonos digitales F6 (cuenta el mes del cobro)
  libro_f9/
  cruces/
```

IDs (`consultas/ids.py`):

| Qué ves | Qué es | De dónde |
|---|---|---|
| `1090135` | Ticket de venta | `ventas.id` |
| `COB-98` | Ticket de cobro (abono F6) | `cuenta_corriente.id` |
| `182678953829` | Id digital de Mercado Pago | CSV / vínculo |
| `F9 MANUAL` | Se cerró a mano, sin id MP | libro F9 o abono sin enlace |

Historial permanente, enlazado:

- cobros MP → `reportes/mercado_pago_sync.csv`
- firmas ticket↔pago → `reportes/mp_vinculos.json`
- tickets digitales POS → `reportes/tickets_digitales.json`
- F9 → `reportes/f9_manuales.json`

Con red, el hilo y `post_cobro` fusionan al libro. Sin red, las tarjetas leen el libro y el CSV. El nodo portable mezcla las tres copias. No se tira historia al desconectar.

## Qué no romper

- No esperar este motor en `MotorPrincipalCobros`.
- No abrir un segundo EscuchaMP.
- Un error de una consulta no tumba las otras.
- No escribir `ventas` ni `mp_pagos`.
- No borrar un ticket o un pago ya asentado.
