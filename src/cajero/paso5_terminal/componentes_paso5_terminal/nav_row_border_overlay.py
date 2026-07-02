from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPen, QColor

NAV_ROW_BORDER = "#F59E0B"

class NavRowBorderOverlay(QWidget):
    """Marco naranja flotante: no se ancla a celdas, sigue la fila activa con flechas."""
    def __init__(self, tabla):
        super().__init__(tabla.viewport())
        self.tabla = tabla
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()

    def _sync_geometry(self):
        vp = self.tabla.viewport()
        if vp:
            self.setGeometry(vp.rect())

    def sync_and_repaint(self):
        self._sync_geometry()
        t = self.tabla
        if t.hasFocus() and t.currentRow() >= 0:
            self.show()
            self.raise_()
            self.update()
        else:
            self.hide()

    def paintEvent(self, event):
        t = self.tabla
        if not t.hasFocus() or t.currentRow() < 0:
            return
        model = t.model()
        if model is None or t.columnCount() <= 0:
            return
        row = t.currentRow()
        r0 = t.visualRect(model.index(row, 0))
        rN = t.visualRect(model.index(row, t.columnCount() - 1))
        if r0.width() <= 0 or rN.width() <= 0:
            return
        rect = QRect(r0.topLeft(), rN.bottomRight()).adjusted(2, 2, -2, -2)
        if not self.rect().intersects(rect):
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(NAV_ROW_BORDER), 3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, 6, 6)
        p.end()
