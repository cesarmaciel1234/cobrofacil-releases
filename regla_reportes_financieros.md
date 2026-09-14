# Reglas Arquitectónicas: Reportes Financieros y Estadísticos

## 1. Formateo de Fechas Amigable (Lectura Rápida)
- **Regla:** Queda prohibido mostrar rótulos genéricos como "Día 1", "Día 17" o "Mes 2" en las tablas y gráficos.
- **Implementación:** Las vistas de reportes (ista_financiero.py, 
eportes_main.py, jefe_reportes.py) deben interceptar los cálculos de datetime y utilizar abreviaturas nativas legibles:
  - Para reportes diarios: Formato "Día Abv + Fecha" (ej: Lun 17, Mar 18). Se calcula dinámicamente con curr_d.weekday().
  - Para reportes mensuales: Formato "Mes Abv" (ej: Ene, Feb, Mar).
- **Objetivo:** Permitir que los gerentes analicen el rendimiento atado al día de la semana sin depender de un calendario externo.
