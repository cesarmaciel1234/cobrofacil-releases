# financiero/ — números que se pueden firmar

Dueño de la verdad. Cartelería y esclavas consultan; no inventan.

| Archivo | Para qué |
|---|---|
| `consulta.py` | `kpis_rango` y `payload_reporte_global` (hoy / semana / mes) |
| `dinero.py` | `fmt_plata`, `fmt_entero`, `pct_vs` |
| `eje.py` | Tope del gráfico = máximo real × 1.08 |
| `insights.py` | Cerebro Jefe: 3 frases = mismos KPI |
| `periodo_previo.py` | `rango_completo_anterior`, `clave_anterior`, `mismo_tramo`, `rango_anio_pasado`, `proyectar`. `rango_igual_anterior` queda solo para un rango suelto A→B |
| `feriados.py` | `es_feriado`. Marca el día. No lo borra. Un feriado futuro suma cero en la proyección |
| `paleta.py` | Colores y tablas claras (`_FIN`) |
| `rotulos.py` | Días, títulos y avisos. Escapes Unicode, no letras pegadas mal |

## Arrancar

- Nuevo KPI: calcularlo en `consulta.py` y que `insights.py` lo lea. No copies SUM en la vista.
- Comparar Hoy / Semana / Mes / Año: `rango_completo_anterior` y `clave_anterior`. No uses `rango_igual_anterior` ahí: recorta la semana pasada al día de hoy y los días que faltan quedan en cero. `rango_igual_anterior` es solo para un rango elegido a mano.
- Las tarjetas salen de `kpis_rango`. Los días, de `serie_diaria`. «Mismo tramo» es la hora de ahora en el periodo anterior. «Año pasado» es la misma semana (364 días), el mismo mes o el mismo día. La fila Proyección es lo vendido más los días que faltan; un feriado futuro suma cero.
- Gráfico: líneas rectas (`lineTo`), no Bézier.
- API: `GET /api/carteleria/reporte` ← `payload_reporte_global()`.

Vista que pinta: `../vista_financiero.py`.
