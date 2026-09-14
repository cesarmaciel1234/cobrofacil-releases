"""Pinta los chips de período. La vista solo pasa el layout y el callback."""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt

from src.jefe.reportes.periodo.constantes import PERIODOS_FILTRO


def montar_botones_periodo(layout, al_elegir, estilo_idle: str, estilo_activo: str | None = None):
    botones = {}
    for nombre in PERIODOS_FILTRO:
        btn = QPushButton(nombre)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(estilo_idle)
        btn.clicked.connect(lambda checked=False, t=nombre: al_elegir(t))
        layout.addWidget(btn)
        botones[nombre] = btn
    return botones


def pintar_activo(botones: dict, periodo: str, estilo_activo: str, estilo_idle: str, etiqueta_rango: str = ""):
    for nombre, btn in (botones or {}).items():
        btn.setStyleSheet(estilo_activo if nombre == periodo else estilo_idle)
    btn_rango = (botones or {}).get("Periodo...")
    if btn_rango:
        btn_rango.setText(etiqueta_rango if periodo == "Periodo..." and etiqueta_rango else "Periodo...")
