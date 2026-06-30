"""Centro de cobranzas (F6 → FIADO) — buscador inteligente + look ejecutivo."""
from __future__ import annotations

import re
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QAbstractItemView, QFrame,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

from src.base_de_datos.database import db_manager
from src.repositories.cliente_repository import ClienteRepository

# Diálogo F6 — FIADO (+20% ancho vs 500px base)
COBRANZA_DIALOG_ANCHO = 600
COBRANZA_DIALOG_ALTO_FIADO = 780
COBRANZA_DIALOG_ALTO_NORMAL = 620

# Paleta ejecutiva 2026 — clara, lustrada, 3D suave
_EXEC = {
    "navy": "#0F172A",
    "navy_mid": "#334155",
    "gold": "#B45309",
    "gold_soft": "#FFFBEB",
    "bg": "#F8FAFC",
    "card": "#FFFFFF",
    "border": "#E2E8F0",
    "text": "#0F172A",
    "text_soft": "#475569",
    "text_muted": "#94A3B8",
    "accent": "#0D9488",
    "accent_soft": "#CCFBF1",
    "deuda": "#DC2626",
    "row_sel": "#E0F2FE",
    "head_from": "#FFFFFF",
    "head_to": "#F0FDFA",
}
from src.cajero.componentes_paso5cobranza.logica_cobranza import parse_consulta_cobranza, buscar_deudores


class CentroCobranzasPanel(QWidget):
    """Panel F6 → FIADO: buscador centrado, foco siempre en cliente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cliente: dict | None = None
        self._deuda_actual = 0.0
        self.setStyleSheet(f"background: transparent; border: none;")
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Tarjeta ejecutiva centrada
        row_center = QHBoxLayout()
        row_center.addStretch(1)
        self.card = QFrame()
        self.card.setObjectName("CobranzaCard")
        self.card.setMinimumWidth(520)
        self.card.setMaximumWidth(560)
        self.card.setStyleSheet(f"""
            QFrame#CobranzaCard {{
                background: {_EXEC['card']};
                border: 1px solid {_EXEC['border']};
                border-radius: 18px;
            }}
        """)
        # Se elimina la sombra (QGraphicsDropShadowEffect) para optimizar rendimiento.

        lay = QVBoxLayout(self.card)
        lay.setContentsMargins(22, 18, 22, 20)
        lay.setSpacing(10)

        # Cabecera
        head = QFrame()
        head.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"stop:0 {_EXEC['head_from']}, stop:1 {_EXEC['head_to']}); "
            f"border: 1px solid {_EXEC['border']}; border-radius: 12px;"
        )
        head_lay = QVBoxLayout(head)
        head_lay.setContentsMargins(16, 14, 16, 14)
        head_lay.setSpacing(4)

        tit = QLabel("CENTRO DE COBRANZAS")
        tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tit.setStyleSheet(
            f"color: {_EXEC['navy']}; font-size: 14px; font-weight: 900; "
            "letter-spacing: 2px; border: none; background: transparent;"
        )
        sub = QLabel("Busque cliente por DNI · nombre · monto · fecha")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet(
            f"color: {_EXEC['text_soft']}; font-size: 11px; font-weight: 500; "
            "border: none; background: transparent;"
        )
        head_lay.addWidget(tit)
        head_lay.addWidget(sub)
        lay.addWidget(head)

        self.lbl_modo = QLabel("Mostrando: todos los deudores")
        self.lbl_modo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_modo.setStyleSheet(
            f"font-size: 11px; color: {_EXEC['accent']}; font-weight: 700; "
            "border: none; background: transparent; padding-top: 4px;"
        )
        lay.addWidget(self.lbl_modo)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("DNI, nombre, monto o fecha…")
        self.txt_buscar.setClearButtonEnabled(True)
        self.txt_buscar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_buscar.setStyleSheet(f"""
            QLineEdit {{
                font-size: 16px; font-weight: 700; color: {_EXEC['text']};
                padding: 14px 16px;
                border: 2px solid {_EXEC['border']};
                border-radius: 10px;
                background: {_EXEC['bg']};
            }}
            QLineEdit:focus {{
                border: 2px solid {_EXEC['accent']};
                background: white;
            }}
        """)
        self.txt_buscar.textChanged.connect(self._on_buscar_cambio)
        self.txt_buscar.returnPressed.connect(self._on_enter_buscar)
        lay.addWidget(self.txt_buscar)

        self.lista = QListWidget()
        self.lista.setMinimumHeight(150)
        self.lista.setMaximumHeight(190)
        self.lista.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lista.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.lista.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {_EXEC['border']};
                border-radius: 10px;
                background: {_EXEC['bg']};
                font-size: 13px;
                padding: 6px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px 10px;
                border-radius: 8px;
                color: {_EXEC['text']};
            }}
            QListWidget::item:selected {{
                background: {_EXEC['row_sel']};
                color: {_EXEC['navy']};
                font-weight: 700;
            }}
            QListWidget::item:hover {{
                background: #F1F5F9;
            }}
        """)
        self.lista.itemClicked.connect(self._on_item_seleccionado)
        self.lista.itemDoubleClicked.connect(lambda _: self.focus_monto())
        lay.addWidget(self.lista)

        # Cliente seleccionado — centrado
        self.lbl_cliente = QLabel("Seleccione un cliente")
        self.lbl_cliente.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cliente.setWordWrap(True)
        self.lbl_cliente.setStyleSheet(
            f"font-size: 15px; color: {_EXEC['navy']}; font-weight: 800; "
            "border: none; background: transparent; padding: 4px 0;"
        )
        lay.addWidget(self.lbl_cliente)

        self.lbl_deuda = QLabel("")
        self.lbl_deuda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_deuda.setStyleSheet(
            f"font-size: 17px; color: {_EXEC['deuda']}; font-weight: 900; "
            "border: none; background: transparent;"
        )
        lay.addWidget(self.lbl_deuda)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {_EXEC['border']}; border: none;")
        lay.addWidget(sep)

        lbl_m = QLabel("MONTO A ABONAR")
        lbl_m.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_m.setStyleSheet(
            f"font-size: 10px; color: {_EXEC['text_muted']}; font-weight: 800; "
            "letter-spacing: 1.5px; border: none; background: transparent;"
        )
        lay.addWidget(lbl_m)

        self.txt_monto = QLineEdit()
        self.txt_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_monto.setStyleSheet(f"""
            QLineEdit {{
                font-size: 34px; font-weight: 900; color: {_EXEC['accent']};
                border: 2px solid {_EXEC['border']};
                border-radius: 12px;
                padding: 10px;
                background: white;
            }}
            QLineEdit:focus {{
                border: 2px solid {_EXEC['accent']};
            }}
        """)
        lay.addWidget(self.txt_monto)

        row_center.addWidget(self.card, stretch=0)
        row_center.addStretch(1)
        outer.addLayout(row_center)

        self._timer_buscar = QTimer(self)
        self._timer_buscar.setSingleShot(True)
        self._timer_buscar.setInterval(280)
        self._timer_buscar.timeout.connect(self._ejecutar_busqueda)

    def cargar_clientes_abono(self):
        self.reset()

    def reset(self):
        self._cliente = None
        self._deuda_actual = 0.0
        self.txt_buscar.clear()
        self.lbl_deuda.clear()
        self.lbl_cliente.setText("Seleccione un cliente")
        self.txt_monto.clear()
        self.lista.clear()
        self._ejecutar_busqueda()
        QTimer.singleShot(120, self.focus_busqueda)

    def focus_busqueda(self):
        self.txt_buscar.setFocus()
        self.txt_buscar.selectAll()

    def focus_monto(self):
        if self.txt_monto is not None:
            self.txt_monto.setFocus()
            self.txt_monto.selectAll()

    def _on_enter_buscar(self):
        if self.lista.count() == 1 and not self._cliente:
            self.lista.setCurrentRow(0)
            self._on_item_seleccionado(self.lista.item(0))
            self.focus_monto()
        else:
            self._ejecutar_busqueda()

    def _on_buscar_cambio(self, _text: str):
        self._timer_buscar.start()

    def _ejecutar_busqueda(self):
        consulta = self.txt_buscar.text()
        p = parse_consulta_cobranza(consulta)
        self.lbl_modo.setText(f"Mostrando: {p['etiqueta']}")

        resultados = buscar_deudores(consulta)
        self.lista.clear()
        if not self._cliente or consulta:
            self._cliente = None
            self._deuda_actual = 0.0
            self.lbl_deuda.clear()

        if not resultados:
            self.lbl_cliente.setText("Sin resultados — pruebe otro criterio")
            if not self._cliente:
                self.txt_monto.clear()
            return

        for r in resultados:
            dni = (r.get("dni") or "").strip()
            deuda = float(r.get("deuda_actual") or 0)
            ult = r.get("ultimo_cargo")
            ult_txt = f" · {str(ult).split('.')[0][:10]}" if ult else ""
            dni_txt = f"DNI {dni} · " if dni else ""
            texto = f"{r['nombre']}\n{dni_txt}Deuda ${deuda:,.2f}{ult_txt}"
            item = QListWidgetItem(texto)
            item.setData(Qt.ItemDataRole.UserRole, r)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if (r.get("tipo_cliente") or "") == "express":
                item.setForeground(QColor(_EXEC["accent"]))
                f = item.font()
                f.setWeight(QFont.Weight.Bold)
                item.setFont(f)
            self.lista.addItem(item)

        self.lbl_cliente.setText(f"{len(resultados)} deudor(es) — seleccione uno")
        if len(resultados) == 1:
            self.lista.setCurrentRow(0)
            self._on_item_seleccionado(self.lista.item(0))

    def _on_item_seleccionado(self, item: QListWidgetItem | None):
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        self._cliente = data
        self._deuda_actual = float(data.get("deuda_actual") or 0)
        dni = (data.get("dni") or "").strip()
        nombre = data.get("nombre", "")
        if dni:
            self.lbl_cliente.setText(f"{nombre}\nDNI {dni}")
        else:
            self.lbl_cliente.setText(nombre)
        self.lbl_deuda.setText(f"Deuda: ${self._deuda_actual:,.2f}")
        self.txt_monto.setText(f"{self._deuda_actual:.2f}")

    def cliente_actual(self):
        return self._cliente

    def deuda_actual(self) -> float:
        return self._deuda_actual

    def monto(self) -> float:
        if self.txt_monto is None:
            return 0.0
        return float(self.txt_monto.text().strip() or 0)

    def validar(self) -> tuple[bool, str]:
        if not self._cliente:
            return False, "⚠️ Seleccione un cliente de la lista"
        monto = self.monto()
        if monto <= 0:
            return False, "⚠️ Ingresa un abono mayor a 0"
        if monto > self._deuda_actual + 0.01:
            return False, "⚠️ El abono no puede superar la deuda"
        return True, ""
