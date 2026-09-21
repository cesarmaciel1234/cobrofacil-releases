# periodo/ — un filtro, todas las caras

```
periodo/
  constantes.py   nombres de chips (Hoy, Mes, Periodo...)
  fechas.py       rango_hoy / semana / mes
  resolver.py     nombre del chip → (inicio, fin, etiqueta)
  sql.py          WHERE fecha >= ? AND fecha < día_siguiente
  barra/          botones
  dialogo/        calendarios A→B + días verdes
```

## Arrancar

- Nuevo chip: agregalo en `constantes.py` y en `resolver.py`.
- “Hoy” es el calendario de hoy (`fechas.rango_hoy`). No uses la SQLite local para decidir.
- SQL de fechas: solo `sql.py`. Inclusive inicio, exclusivo día siguiente. Sin `DATE()` ni `LIKE` de más (rompe MariaDB y tira a SQLite).
- Verde en el almanaque: `dialogo/dias_trabajados.py`.
