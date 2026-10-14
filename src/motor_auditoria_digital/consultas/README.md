# Consultas

Motores locales de solo lectura sobre motores principales. No escriben `ventas` ni `mp_pagos`. El asiento de tickets va a `libro_tickets`.

| Archivo | Pregunta a | Función | Si falla |
|---|---|---|---|
| `ids.py` | nada | `ticket_venta`, `ticket_cobro`, `id_pago`, `es_cobro` | `""` |
| `rango.py` | nada | `filtro(Hoy/Semana/Mes/Año/Período)`, `en_rango` | Mes |
| `pagos_mp.py` | `admin/mercadopago/historial/archivo.leer` | `listar()` | `[]` |
| `tickets.py` | `ventas` + `medios.clase`; asienta `libro_tickets` | `listar`, `volcar` | libro local; si tampoco hay, `[]` |
| `cobranzas.py` | `cuenta_corriente` ABONO + `medios.clase`; asienta `libro_cobranzas` | `listar`, `volcar` | libro local; si tampoco hay, `[]` |
| `vinculos.py` | `vinculo_mp.libro._leer` (solo lectura) | `mapas()` → (pago→ticket, set tickets) | `{}`, `set()` |

No importan pantallas. No llaman a `MotorPrincipalCobros`.
