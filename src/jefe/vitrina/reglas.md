# vitrina/ — publicidad del panel jefe

Columna izquierda (50%). Cuatro plazas. No inventa anuncios.

```
vitrina/
  consulta.py   precio real + uno menor = oferta
  tarjeta.py    una plaza
  vista.py      pinta saludo, KPIs, pagos y deuda de clientes, y grilla 2×2

Exportar ganancias guarda el Excel de ganancias y la hoja Auditoria de la cartera.
```

## Oferta

Hay oferta si existe un precio de lista y otro más bajo (`precio_oferta`, relámpago o promedio). Misma idea que `leerPrecios` de la TV.

Tachado: número blanco, línea naranja `#FF4D00`.

Esclava: `db_manager` = maestra.
