"""Período de reportes — pirámide: constantes → resolver → diálogo A/B → barra."""

from src.jefe.reportes.periodo.constantes import PERIODOS_FILTRO
from src.jefe.reportes.periodo.resolver import resolver_rango_periodo
from src.jefe.reportes.periodo.dialogo.calendarios import DialogoSeleccionPeriodo
from src.jefe.reportes.periodo.barra.botones import montar_botones_periodo, pintar_activo
from src.jefe.reportes.periodo.sql import en_rango, where_fecha, where_ventas

__all__ = [
    "PERIODOS_FILTRO",
    "resolver_rango_periodo",
    "DialogoSeleccionPeriodo",
    "montar_botones_periodo",
    "pintar_activo",
    "en_rango",
    "where_fecha",
    "where_ventas",
]
