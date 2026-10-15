# auditoria/ — líneas de venta, no tickets

Dueño de las filas (producto × ticket). Los tickets viven en `historial_ventas/`.

```
auditoria/
  consulta.py   SQL + totales + vs periodo anterior
  kpis.py       textos de las 4 tarjetas y el pie
  exportar.py   Excel
  vista.py      pinta. Arranca en Hoy.
```

## Arrancar

- Nueva columna: `consulta.listar_lineas` y después la tabla en `vista.py`.
- Buscar: `consulta.filtro(texto, metodo)`. El texto busca en producto, código, pago, cajero, estado, depto y categoría; si es número (o `#número`) también busca el ticket. El combo «Pago» filtra por método exacto (`METODOS`); Efectivo incluye pago vacío. La misma condición va al listado y a «Vs periodo anterior».
- Fechas: `periodo/sql.where_fecha`. No copies DATE() ni LIKE.
- Comparar: `financiero.rango_igual_anterior`.
- Totales y Facturado: solo tickets vivos. Las líneas `CANCELADA` se listan (rojo) y van al KPI Cancelados. No se suman al monto del reporte de ventas.
- Esclava: `db_manager` = maestra.
- Letras de góndola en la grilla (`src/utils/letra.py`). Calendarios: peso 400 en `../letra.py`. Compat: `../vista_auditoria.py` reexporta `VistaAuditoria`.
