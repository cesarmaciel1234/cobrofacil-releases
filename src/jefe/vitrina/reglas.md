# vitrina/ — publicidad del panel jefe

Columna izquierda (50%). Cuatro plazas. No inventa anuncios.

```
vitrina/
  consulta.py   precio real + uno menor = oferta
  tarjeta.py    una plaza
  vista.py      pinta saludo, KPIs, pagos y deuda de clientes, y grilla 2×2
  metricas.py   KPIs por rango: ganancia, tickets, cancelaciones, redondeo, digitales, pagos

Exportar ganancias guarda el Excel de ganancias y la hoja Auditoria de la cartera.
```

## Período

Al lado de «Vitrina de tienda»: Hoy / Semana / Mes / Año / Período (calendario A→B de `reportes/periodo`). El panel emite `periodo_cambiado(desde, hasta, etiqueta)` y `jefe0_dashboard` repinta con ese rango. En Hoy los títulos quedan como siempre; si no, «Tickets · Semana», «Redondeo · 01/09 – 15/09». El reloj de 60 s solo repinta si el rango llega a hoy.

## KPIs

| Chip | Origen | ¿Sigue el período? |
|---|---|---|
| Ganancia | `metricas.ganancia` → `reportes/financiero.kpis_rango`. Sin costo cargado dice «Sin costo cargado», no inventa | Sí |
| Inventario al costo | `WorkerAnaliticaJefe` (stock × costo actual) | No, foto del momento |
| Pagos clientes | `metricas.pagos_clientes` → abonos de `cuenta_corriente` | Sí |
| Deuda clientes | `cerebro.resumen_cuentas` | No, foto del momento |
| Redondeo | `metricas.redondeo` → `SUM(descuento)` de ventas vigentes | Sí |
| Digitales sin firmar / total | `metricas.digitales` → `sin / total` | Sí |
| Tickets | `metricas.tickets` → `cantidad · total`; abajo, promedio por ticket | Sí |
| Cancelaciones | `metricas.cancelaciones` → `cantidad · monto` por `fecha_cancel`; abajo, cuándo y quién la última | Sí |

La ganancia de `WorkerAnaliticaJefe` ya no se pinta: contaba solo COMPLETADA, sin redondeo y cruzaba el costo por `p.codigo` (vacío), así que mostraba ventas como si fueran ganancia.

Vigentes = `COMPLETADA` + `CERRADA`. El Z pasa las ventas a `CERRADA`: contar solo `COMPLETADA` deja las tarjetas en cero después del cierre. Filtros de fecha con rango (`fecha >= día AND fecha < día siguiente`), no con `date(fecha)`.

`_chip` tiene una línea chica de detalle (`_poner_detalle`) que se oculta si está vacía. Se refresca con el reloj del panel, cada 60 s (`jefe0_dashboard._pintar_cobros_dia`).

## Oferta

Hay oferta si existe un precio de lista y otro más bajo (`precio_oferta`, relámpago o promedio). Misma idea que `leerPrecios` de la TV.

Tachado: número blanco, línea naranja `#FF4D00`.

Esclava: `db_manager` = maestra. El libro MP (`mp_vinculos`) es local a la PC, pero el motor de cobros digitales de cada PC sube sus tickets a `mp_pagos.ticket` de la tienda y enlaza solo los seguros (`src/motor_cobros_digitales/`). «Digitales sin firmar» suma los dos: la esclava ve lo que firmó la maestra, con hasta 5 minutos de atraso.
