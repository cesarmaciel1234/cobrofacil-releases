# Reportes (jefe) — pirámide

Puerta: `reportes_main.py` (pantalla 20). Tres caras, un motor de fechas, un número global.

```
reportes/
  reportes_main.py     abre las 3 pestañas + engancha maestra
  letra.py             texto de una pasada (sin letras dobles)
  vista_financiero.py  pinta KPIs / gráficos
  auditoria/           líneas de venta (consulta / kpis / excel / vista)
  vista_auditoria.py   reexporta auditoria.vista
  vista_historial.py   reexporta historial/vista.py
  financiero/          números que se firman
  periodo/             Hoy / semana / mes / A→B
  historial/           cara clara de tickets
  admin_reportes/      legado admin — no es la puerta del jefe
  jefe_reportes.py     legado — no tocar
```

## Cómo trabajar

1. ¿Cambia un número? → `financiero/consulta.py` (y `periodo/sql.py` si es el filtro de fecha).
2. ¿Cambia Hoy / Mes / calendarios? → `periodo/` (leer `periodo/reglas.md`).
3. ¿Cambia la lista de tickets? → `src/historial_ventas/` (motor) y `historial/vista.py` (solo UI).
3b. ¿Cambia las líneas de producto? → `auditoria/consulta.py`. La vista solo pinta.
4. ¿Letras dobles? → `letra.py`, peso 400, `letter-spacing: 0`. Nunca font 900.
5. ¿Ganancia? Sin costo cargado no se firma. Nunca uses `s/d` para “sin costo” (`s/d` = sin departamento).

Compat: los `vista_*.py` de esta raíz se quedan para no romper imports. La lógica nueva no se agrega ahí.
