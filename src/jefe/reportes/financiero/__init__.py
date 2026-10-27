from src.jefe.reportes.financiero.consulta import kpis_rango, payload_reporte_global, serie_diaria
from src.jefe.reportes.financiero.dinero import fmt_entero, fmt_plata, pct_vs
from src.jefe.reportes.financiero.eje import maximo_eje
from src.jefe.reportes.financiero.insights import texto_insights
from src.jefe.reportes.financiero.periodo_previo import (
    clave_anterior,
    mismo_tramo,
    proyectar,
    rango_anio_pasado,
    rango_completo_anterior,
    rango_igual_anterior,
)
from src.jefe.reportes.financiero.rotulos import (
    ENCABEZADO_DIA,
    es_anio,
    nombre_dia,
    nombres_comparacion,
    titulo_serie,
)

__all__ = [
    "fmt_plata",
    "fmt_entero",
    "pct_vs",
    "maximo_eje",
    "rango_igual_anterior",
    "rango_completo_anterior",
    "clave_anterior",
    "mismo_tramo",
    "proyectar",
    "rango_anio_pasado",
    "serie_diaria",
    "nombres_comparacion",
    "texto_insights",
    "kpis_rango",
    "payload_reporte_global",
    "ENCABEZADO_DIA",
    "es_anio",
    "nombre_dia",
    "titulo_serie",
]
