"""Calendario del F3: los días con tickets se pintan en verde."""

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QCalendarWidget


class CalendarioTrabajo(QCalendarWidget):
    def __init__(self):
        super().__init__()
        self._dias: set[str] = set()

    def marcar(self, dias: set[str]) -> None:
        self._dias = set(dias or ())
        self.updateCells()

    def paintCell(self, painter: QPainter, rect, date: QDate) -> None:
        iso = date.toString("yyyy-MM-dd")
        en_este_mes = date.month() == self.monthShown() and date.year() == self.yearShown()
        if iso not in self._dias or not en_este_mes:
            super().paintCell(painter, rect, date)
            return
        painter.save()
        painter.fillRect(rect.adjusted(1, 1, -1, -1), QColor("#D1FAE5"))
        if date == self.selectedDate():
            painter.setPen(QColor("#059669"))
            painter.drawRect(rect.adjusted(2, 2, -3, -3))
        painter.setPen(QColor("#065F46"))
        painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), str(date.day()))
        painter.restore()
