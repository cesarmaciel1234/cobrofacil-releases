# -*- coding: utf-8 -*-
"""Reglas del desanclaje. Un proceso, hasta tres hojas."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

from src.navigation.screen_indices import Screen

MAX_SUELTAS = 3
NO_DESANCLAR = {Screen.ADMIN_DASHBOARD, Screen.CAJERO, Screen.JEFE_DASHBOARD, Screen.CARTELERIA}

TITULOS = {
    Screen.INVENTARIO: "Inventario",
    Screen.OFERTAS: "Ofertas",
    Screen.REPORTES: "Reportes",
    Screen.CONFIGURACION: "Configuración",
    Screen.RED_LAN: "Red LAN",
    Screen.CIERRE: "Cierre",
    Screen.ETIQUETAS: "Etiquetas",
    Screen.CONTABILIDAD: "Contabilidad",
    Screen.MERCADO_PAGO: "Mercado Pago",
    Screen.PROVEEDORES: "Proveedores",
    Screen.HARDWARE: "Hardware",
    Screen.VENTAS_DIGITALES: "Ventas digitales",
    Screen.CLIENTES: "Clientes",
    Screen.NEXUS: "Nexus",
    Screen.JEFE_REPORTES: "Reportes",
    Screen.CARTELERIA_DASHBOARD: "Cartelería",
    Screen.IA_BOSS: "IA",
    Screen.PROMEDIOS: "Promedios",
    Screen.AUDITORIA: "Auditoría inventario",
    Screen.PROVEEDORES_JEFE: "Proveedores",
    Screen.PROVEEDORES_CARTELERIA: "Proveedores",
}


def titulo(index: int) -> str:
    return TITULOS.get(int(index), f"Módulo {index}")


def se_puede(index: int, abiertas: dict) -> tuple[bool, str]:
    idx = int(index)
    if idx in NO_DESANCLAR:
        return False, "Ese módulo se queda en el hub (venta y TV no se desanclan)."
    if idx in abiertas:
        return False, "Ya está en otro monitor."
    if len(abiertas) >= MAX_SUELTAS:
        return False, f"Como mucho {MAX_SUELTAS} módulos sueltos. Traé uno al hub."
    return True, ""


def poner_en_otro_monitor(hoja, ventana_hub):
    from src.utils.qt_compat import screen_count, screen_geometry_at

    n = screen_count()
    if n < 2:
        hoja.resize(1100, 720)
        hoja.show()
        return
    hub = ventana_hub.frameGeometry()
    cx = hub.center().x()
    cy = hub.center().y()
    destino = None
    for i in range(n):
        geo = screen_geometry_at(i)
        if geo is None:
            continue
        if not geo.contains(cx, cy):
            destino = geo
            break
    if destino is None:
        destino = screen_geometry_at(1)
    hoja.setGeometry(destino)
    hoja.showMaximized()


def marcador(index: int, al_traer) -> QWidget:
    w = QWidget()
    w.setObjectName(f"_suelta_marcador_{index}")
    w.setStyleSheet("background: #F8FAFC;")
    lay = QVBoxLayout(w)
    lay.setContentsMargins(48, 48, 48, 48)
    nombre = titulo(index)
    lbl = QLabel(f"{nombre} está en otro monitor.")
    lbl.setStyleSheet("color: #0F172A; font-size: 18px; font-weight: 800; background: transparent;")
    hint = QLabel("Mismo proceso. Cerrar esa hoja o Traer al hub la vuelve acá.")
    hint.setStyleSheet("color: #1E293B; font-size: 14px; font-weight: 600; background: transparent;")
    btn = QPushButton("Traer al hub")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedHeight(40)
    btn.setStyleSheet(
        "QPushButton { background: #2563EB; color: #FFFFFF; border: none; border-radius: 10px; "
        "padding: 0 20px; font-size: 14px; font-weight: 700; }"
        "QPushButton:hover { background: #1D4ED8; }"
    )
    btn.clicked.connect(al_traer)
    lay.addStretch(1)
    lay.addWidget(lbl)
    lay.addWidget(hint)
    lay.addWidget(btn)
    lay.addStretch(2)
    return w
