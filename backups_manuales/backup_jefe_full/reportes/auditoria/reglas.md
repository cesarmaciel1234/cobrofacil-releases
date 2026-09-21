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
- Fechas: `periodo/sql.where_fecha`. No copies DATE() ni LIKE.
- Comparar: `financiero.rango_igual_anterior`.
- Esclava: `db_manager` = maestra.
- Letras: peso 400. Compat: `../vista_auditoria.py` reexporta `VistaAuditoria`.
