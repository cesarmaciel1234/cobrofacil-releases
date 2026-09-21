"""Calendario A (desde) y calendario B (hasta). Días verdes = se trabajó."""

from PyQt6.QtWidgets import (
    QCalendarWidget,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)
from PyQt6.QtCore import QDate, QLocale, Qt

from src.jefe.reportes.letra import vestir_calendario
from src.jefe.reportes.periodo.dialogo.dias_trabajados import (
    fechas_trabajadas,
    pintar_dias_trabajados,
)

_QSS = """
QDialog#DialogoPeriodo { background: #F8FAFC; }
QDialog#DialogoPeriodo QLabel#TituloCal {
    color: #0F172A;
    background: transparent;
    font-weight: 700;
    font-size: 13px;
}
QCalendarWidget QAbstractItemView {
    background: #FFFFFF;
    color: #0F172A;
    selection-background-color: #3B82F6;
    selection-color: #FFFFFF;
}
QCalendarWidget QToolButton {
    color: #0F172A;
    background: #F1F5F9;
    border: none;
    padding: 4px 8px;
    font-weight: 400;
}
QPushButton#BtnOkPeriodo {
    background: #3B82F6;
    color: #FFFFFF;
    min-width: 88px;
    padding: 8px 16px;
    border: none;
    border-radius: 8px;
    font-weight: 400;
}
QPushButton#BtnCancelPeriodo {
    background: #F1F5F9;
    color: #334155;
    min-width: 88px;
    padding: 8px 16px;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    font-weight: 400;
}
"""


def _armar_cal(parent):
    return vestir_calendario(QCalendarWidget(parent))


class DialogoSeleccionPeriodo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DialogoPeriodo")
        self.setWindowTitle("Elegir periodo")
        self.setModal(True)
        self.setMinimumWidth(680)
        self.setLocale(QLocale(QLocale.Language.Spanish, QLocale.Country.Argentina))
        self.setStyleSheet(_QSS)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        hint = QLabel("Verde = día trabajado (hubo tickets).")
        hint.setObjectName("TituloCal")
        lay.addWidget(hint)
        fila = QHBoxLayout()
        col_a = QVBoxLayout()
        la = QLabel("Desde")
        la.setObjectName("TituloCal")
        col_a.addWidget(la)
        self.cal_a = _armar_cal(self)
        col_a.addWidget(self.cal_a)
        col_b = QVBoxLayout()
        lb = QLabel("Hasta")
        lb.setObjectName("TituloCal")
        col_b.addWidget(lb)
        self.cal_b = _armar_cal(self)
        col_b.addWidget(self.cal_b)
        fila.addLayout(col_a)
        fila.addLayout(col_b)
        lay.addLayout(fila)
        fila_btn = QHBoxLayout()
        fila_btn.addStretch()
        btn_ok = QPushButton("Aceptar")
        btn_ok.setObjectName("BtnOkPeriodo")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("BtnCancelPeriodo")
        btn_cancel.clicked.connect(self.reject)
        fila_btn.addWidget(btn_cancel)
        fila_btn.addWidget(btn_ok)
        lay.addLayout(fila_btn)
        hoy = QDate.currentDate()
        self.cal_a.setSelectedDate(hoy)
        self.cal_b.setSelectedDate(hoy)
        dias = fechas_trabajadas()
        pintar_dias_trabajados(self.cal_a, dias)
        pintar_dias_trabajados(self.cal_b, dias)

    def get_fechas(self):
        a = self.cal_a.selectedDate().toPyDate()
        b = self.cal_b.selectedDate().toPyDate()
        if a > b:
            a, b = b, a
        return a.strftime("%Y-%m-%d 00:00:00"), b.strftime("%Y-%m-%d 23:59:59")
