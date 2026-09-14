"""Texto de una sola pasada. En Windows, dos font-weight en QSS = letras dobles.

Usá etiqueta / vestir_fecha / vestir_calendario. Peso 400. Sin letter-spacing.
"""

from PyQt6.QtCore import QLocale, Qt
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QCalendarWidget, QDateEdit, QLabel, QWidget

QSS_UNA_LETRA = """
    letter-spacing: 0px;
    font-weight: 400 !important;
"""

QSS_CALENDARIO = """
QCalendarWidget {
    background: #FFFFFF;
    color: #0F172A;
    letter-spacing: 0px;
    font-weight: 400;
}
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background: #F1F5F9;
    border: none;
}
QCalendarWidget QToolButton {
    color: #0F172A;
    background: #F1F5F9;
    border: none;
    padding: 4px 8px;
    font-weight: 400;
    letter-spacing: 0px;
}
QCalendarWidget QSpinBox {
    background: #FFFFFF;
    color: #0F172A;
    font-weight: 400;
}
QCalendarWidget QAbstractItemView,
QCalendarWidget QTableView {
    background: #FFFFFF;
    color: #0F172A;
    alternate-background-color: #F8FAFC;
    selection-background-color: #3B82F6;
    selection-color: #FFFFFF;
    outline: none;
    font-weight: 400;
    letter-spacing: 0px;
}
QCalendarWidget QHeaderView::section {
    background: #F8FAFC;
    color: #334155;
    border: none;
    padding: 4px;
    font-weight: 400;
    letter-spacing: 0px;
}
"""


def fuente_limpia(px: int = 13) -> QFont:
    f = QFont("Segoe UI", px)
    f.setBold(False)
    f.setWeight(QFont.Weight.Normal)
    f.setStyleStrategy(QFont.StyleStrategy.PreferQuality)
    f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return f


def paleta_clara(w: QWidget) -> None:
    pal = w.palette()
    oscuro = QColor("#0F172A")
    pal.setColor(QPalette.ColorRole.Window, QColor("#F0F4F8"))
    pal.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor("#F8FAFC"))
    pal.setColor(QPalette.ColorRole.Text, oscuro)
    pal.setColor(QPalette.ColorRole.WindowText, oscuro)
    pal.setColor(QPalette.ColorRole.Button, QColor("#FFFFFF"))
    pal.setColor(QPalette.ColorRole.ButtonText, oscuro)
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    pal.setColor(QPalette.ColorRole.Highlight, QColor("#3B82F6"))
    w.setPalette(pal)


def etiqueta(texto: str, px: int = 13) -> QLabel:
    w = QLabel(texto)
    w.setFont(fuente_limpia(px))
    w.setStyleSheet("background: transparent; border: none; letter-spacing: 0px; font-weight: 400;")
    return w


def vestir_calendario(cal: QCalendarWidget) -> QCalendarWidget:
    cal.setLocale(QLocale(QLocale.Language.Spanish, QLocale.Country.Argentina))
    cal.setGridVisible(True)
    cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
    cal.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
    cal.setAutoFillBackground(True)
    cal.setFont(fuente_limpia(9))
    paleta_clara(cal)
    cal.setStyleSheet(QSS_CALENDARIO)
    return cal


def vestir_fecha(edit: QDateEdit) -> QDateEdit:
    edit.setCalendarPopup(True)
    edit.setDisplayFormat("dd/MM/yyyy")
    edit.setFont(fuente_limpia(13))
    vestir_calendario(edit.calendarWidget())
    return edit
