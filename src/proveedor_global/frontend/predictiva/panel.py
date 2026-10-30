"""Pantalla de compra predictiva. El centro es el pedido. La tuerca guarda el horario."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt

from src.utils.letra import vestir_id, vestir_numero

_COLUMNAS = (
    ("pollo", "Pollo (cajas)"),
    ("media", "Carne (medias)"),
    ("cerdo", "Cerdo (kg)"),
    ("congelado", "Congelado (kg)"),
    ("huevo", "Huevo (cajones)"),
)


class PanelPredictiva(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #F8FAFC;")
        self._cajas = {}
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F8FAFC; border: none; }")
        cuerpo = QWidget()
        lay = QVBoxLayout(cuerpo)
        lay.setContentsMargins(28, 18, 28, 24)
        lay.setSpacing(16)
        lay.addLayout(self._cabeza())
        lay.addLayout(self._ciclos())
        self._tabla = self._armar_tabla()
        lay.addWidget(self._tabla, 1)
        scroll.setWidget(cuerpo)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.addWidget(scroll)
        self.refrescar()

    def _cabeza(self):
        fila = QHBoxLayout()
        texto = QVBoxLayout()
        texto.setSpacing(4)
        titulo = QLabel("Pedido de este ciclo")
        titulo.setStyleSheet("font-size: 22px; font-weight: 700; color: #0F172A; background: transparent;")
        texto.addWidget(titulo)
        fila.addLayout(texto, 1)
        tuerca = QPushButton("⚙")
        tuerca.setFixedSize(44, 44)
        tuerca.setCursor(Qt.CursorShape.PointingHandCursor)
        tuerca.setToolTip("Configuración")
        tuerca.setStyleSheet(
            "QPushButton { background: white; color: #1E293B; border: 1px solid #CBD5E1; "
            "border-radius: 12px; font-size: 20px; }"
            "QPushButton:hover { background: #EFF6FF; }"
        )
        tuerca.clicked.connect(self._abrir_configuracion)
        fila.addWidget(tuerca, 0, Qt.AlignmentFlag.AlignTop)
        return fila

    def _ciclos(self):
        fila = QHBoxLayout()
        fila.setSpacing(12)
        for nombre in ("Pollo", "Carne"):
            tarjeta = QFrame()
            tarjeta.setStyleSheet(
                "QFrame { background: white; border: 1px solid #E2E8F0; border-radius: 12px; }"
            )
            caja = QVBoxLayout(tarjeta)
            caja.setContentsMargins(16, 14, 16, 14)
            nombre_lbl = QLabel(nombre)
            nombre_lbl.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 700; border: none;")
            valor = QLabel("0")
            valor.setStyleSheet("color: #0F172A; font-size: 28px; font-weight: 700; border: none;")
            caja.addWidget(nombre_lbl)
            caja.addWidget(valor)
            self._cajas[nombre] = valor
            fila.addWidget(tarjeta, 1)
        return fila

    def _armar_tabla(self) -> QTableWidget:
        tabla = QTableWidget(0, 1 + len(_COLUMNAS))
        tabla.setHorizontalHeaderLabels(["Fecha"] + [titulo for _clave, titulo in _COLUMNAS])
        tabla.verticalHeader().setVisible(False)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for indice in range(1, 1 + len(_COLUMNAS)):
            tabla.horizontalHeader().setSectionResizeMode(indice, QHeaderView.ResizeMode.Stretch)
        tabla.setStyleSheet(
            "QTableWidget { background: white; border: 1px solid #E2E8F0; border-radius: 8px; }"
            "QHeaderView::section { background: #F8FAFC; color: #0F172A; font-weight: 700; border: none; padding: 8px; }"
        )
        tabla.setMinimumHeight(240)
        return tabla

    def refrescar(self):
        from src.proveedor_global.frontend.predictiva.consultar import hoy_en_curso

        try:
            from src.base_de_datos.database import db_manager
            proy = hoy_en_curso(db_manager)
        except Exception:
            proy = hoy_en_curso(None)
        self._cajas["Pollo"].setText(_pedido(proy["pollo"], "cajas"))
        self._cajas["Carne"].setText(_pedido(proy["media"], "medias"))
        self._pintar(proy.get("historial") or [])

    def _abrir_configuracion(self):
        from src.proveedor_global.frontend.predictiva.calendario.dialogo import DialogoConfiguracion

        dialogo = DialogoConfiguracion(self)
        if dialogo.exec():
            self.refrescar()

    def _pintar(self, filas):
        self._tabla.setRowCount(len(filas))
        for i, fila in enumerate(reversed(filas)):
            self._tabla.setItem(i, 0, vestir_id(QTableWidgetItem(str(fila.get("fecha") or ""))))
            for columna, (clave, _titulo) in enumerate(_COLUMNAS, start=1):
                valor = fila.get(clave) if clave in fila else None
                self._tabla.setItem(i, columna, vestir_numero(QTableWidgetItem("" if valor is None else _txt(valor))))


def _pedido(item, unidad) -> str:
    bajo = item.get("pedir_min")
    alto = item.get("pedir_max")
    if bajo is None or alto is None:
        return f"{item.get('pedir', 0)} {unidad}"
    if int(bajo) == int(alto):
        return f"{int(alto)} {unidad}"
    return f"{int(bajo)} a {int(alto)} {unidad}"


def _txt(numero) -> str:
    try:
        numero = float(numero)
    except (TypeError, ValueError):
        return ""
    return f"{numero:.2f}".rstrip("0").rstrip(".")
