# Jefe — por dónde empezar

Backoffice claro (`styles_light.qss`). No tocar `src/cajero/` ni el tema oscuro del terminal.

## Carpetas

| Carpeta | Qué es | Empezá por |
|---|---|---|
| `reportes/` | Ventas, auditoría, historial | `reportes/reglas.md` |
| `contabilidad/` | Costos fijos / resumen | `styles_light.py` |
| `ia/` | Cerebro Jefe (frases, no inventa números) | `jefe_ia_proactiva.py` |
| `vitrina/` | Publicidad izquierda del home (4 plazas) | `vitrina/reglas.md` |

## Números

Un solo dueño: `reportes/financiero/consulta.py` (`payload_reporte_global`).  
La TV y las esclavas **leen**. No recalculan.

## Red

Cualquier perfil en PC esclava lee la maestra. Ver `src/base_de_datos/reglas.md`.
