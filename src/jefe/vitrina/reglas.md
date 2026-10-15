# vitrina/ — columna izquierda del panel jefe

KPIs del período. No pinta ofertas ni plazas de cartelería.

```
vitrina/
  metricas.py   KPIs por rango
  vista.py      saludo, chips, huecos reservados
```

`consulta.py` y `tarjeta.py` quedan por si vuelve una plaza. El home no los llama.

## Período

Al arrancar: **Mes** (cierre del mes, como en el home). **Hoy** es el día, un clic. Semana / Año / Período no arrancan. Emite `periodo_cambiado`. El reloj de 60 s solo tiene sentido si el rango llega a hoy. Si el rango todavía no se eligió, el dashboard usa el mes: no pinta el día con el chip de Mes.

## KPIs

| Chip | Origen |
|---|---|
| Ganancia | `metricas.ganancia` |
| Inventario al costo | foto del momento |
| Pagos clientes | abonos de `cuenta_corriente` |
| Deuda clientes | foto del momento |
| Tickets digitales | `cobros_auditoria.tickets_digitales` (mismo motor que el monitor). Plata **con ticket**: entra al libro de ventas y a la facturación. |
| Cliente | cobranza F6 digital del período (factura el mes del cobro) |
| Sin firmar / F9 | monto a la izquierda; `5/25` a la derecha (no firmados / tickets digitales). Abajo: «5 tickets no firmados de 25». El ticket ya existe: se puede facturar. Falta el id MP. |
| MP sin ticket | cobros de Mercado Pago **sin** ticket de venta. Monto y cantidad. No se mezcla con el 5/25. No está en `ventas`: hay que asociar o emitir ticket para facturarlo. |
| Redondeo | F3. `redondeo_y_descuento[0]`. Fila propia con Descuento (2 por línea). |
| Descuento | Ofertas del ticket. `redondeo_y_descuento[1]`. Al lado de Redondeo. |
| Tickets | todas las ventas vigentes |
| Cancelaciones | por `fecha_cancel` |

Abajo: cuatro huecos «Reservado» para tarjetas futuras. No se rellenan con ofertas.

Esclava: `db_manager` = maestra. Sin red, espejo + libros locales de auditoría.
