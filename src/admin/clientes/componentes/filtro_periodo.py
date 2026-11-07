"""Chips Hoy / Semana / Semana p. / Mes / Año / Período — misma lógica que la vitrina."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton

from src.jefe.reportes.periodo.fechas import (
    rango_hoy,
    rango_mes,
    rango_semana,
    rango_semana_pasada,
)
from src.jefe.reportes.periodo.sql import en_rango
from src.utils.qt_compat import qt_exec

PERIODOS_UI = ("Hoy", "Semana", "Semana p.", "Mes", "Año", "Período")

_CHIP_IDLE = """
    QPushButton {
        background: white; color: #334155; border: 1px solid #E2E8F0;
        border-radius: 14px; padding: 5px 12px; font-weight: 800; font-size: 11px;
    }
    QPushButton:hover { border-color: #3B82F6; color: #1D4ED8; }
"""
_CHIP_ACTIVO = """
    QPushButton {
        background: #0F172A; color: white; border: 1px solid #0F172A;
        border-radius: 14px; padding: 5px 12px; font-weight: 800; font-size: 11px;
    }
"""


def resolver_ui(clave: str, parent=None):
    """Devuelve (inicio, fin, etiqueta) o None si cancela Período."""
    if clave == "Hoy":
        return rango_hoy()
    if clave == "Semana":
        return rango_semana()
    if clave == "Semana p.":
        return rango_semana_pasada()
    if clave == "Mes":
        return rango_mes()
    if clave == "Año":
        from datetime import date

        hoy = date.today()
        return (
            hoy.replace(month=1, day=1).strftime("%Y-%m-%d 00:00:00"),
            hoy.strftime("%Y-%m-%d 23:59:59"),
            "Año actual",
        )
    if clave == "Período":
        from src.jefe.reportes.periodo.dialogo.calendarios import DialogoSeleccionPeriodo

        dialog = DialogoSeleccionPeriodo(parent)
        if int(qt_exec(dialog)) != 1:
            return None
        inicio, fin = dialog.get_fechas()
        etiqueta = f"{inicio[8:10]}/{inicio[5:7]}/{inicio[:4]} – {fin[8:10]}/{fin[5:7]}/{fin[:4]}"
        return f"{inicio[:10]} 00:00:00", f"{fin[:10]} 23:59:59", etiqueta
    return None


def filtrar_por_rango(filas, inicio, fin, campo="fecha_raw"):
    if not inicio or not fin:
        return list(filas or [])
    salida = []
    for fila in filas or []:
        fecha = fila.get(campo) if isinstance(fila, dict) else None
        if fecha is None and isinstance(fila, dict):
            fecha = fila.get("fecha")
        if en_rango(fecha, inicio, fin):
            salida.append(fila)
    return salida


def montar_chips(parent, al_elegir, activo="Hoy", color_activo=None):
    """Arma la fila de chips. `al_elegir(clave)` recibe el texto del chip."""
    lay = QHBoxLayout()
    lay.setSpacing(8)
    lay.setContentsMargins(0, 0, 0, 0)
    grupo = QButtonGroup(parent)
    grupo.setExclusive(True)
    botones = {}
    estilo_on = _CHIP_ACTIVO
    if color_activo:
        estilo_on = _CHIP_ACTIVO.replace("#0F172A", color_activo)
    for clave in PERIODOS_UI:
        chip = QPushButton(clave)
        chip.setCheckable(True)
        chip.setCursor(Qt.CursorShape.PointingHandCursor)
        chip.setStyleSheet(estilo_on if clave == activo else _CHIP_IDLE)
        chip.clicked.connect(lambda _=False, c=clave: al_elegir(c))
        grupo.addButton(chip)
        lay.addWidget(chip)
        botones[clave] = chip
        if clave == activo:
            chip.setChecked(True)
    lay.addStretch()
    return lay, botones, grupo


def pintar_chips(botones, activo, etiqueta_periodo="", color_activo=None):
    estilo_on = _CHIP_ACTIVO
    if color_activo:
        estilo_on = _CHIP_ACTIVO.replace("#0F172A", color_activo)
    for clave, chip in (botones or {}).items():
        chip.setStyleSheet(estilo_on if clave == activo else _CHIP_IDLE)
        chip.setChecked(clave == activo)
        if clave == "Período":
            chip.setText(etiqueta_periodo if activo == "Período" and etiqueta_periodo else "Período")
