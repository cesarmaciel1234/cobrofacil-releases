# financiero/ — números que se pueden firmar

Dueño de la verdad. Cartelería y esclavas consultan; no inventan.

| Archivo | Para qué |
|---|---|
| `consulta.py` | `kpis_rango` y `payload_reporte_global` (hoy / semana / mes) |
| `dinero.py` | `fmt_plata`, `fmt_entero`, `pct_vs` |
| `eje.py` | Tope del gráfico = máximo real × 1.08 |
| `insights.py` | Cerebro Jefe: 3 frases = mismos KPI |
| `periodo_previo.py` | Misma duración, inmediatamente antes (Hoy → ayer) |
| `paleta.py` | Colores y tablas claras (`_FIN`) |

## Arrancar

- Nuevo KPI: calcularlo en `consulta.py` y que `insights.py` lo lea. No copies SUM en la vista.
- Comparar periodos: `rango_igual_anterior`, no “el año pasado”.
- Gráfico: líneas rectas (`lineTo`), no Bézier.
- API: `GET /api/carteleria/reporte` ← `payload_reporte_global()`.

Vista que pinta: `../vista_financiero.py`.
