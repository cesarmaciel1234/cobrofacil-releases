"""Transición de bienvenida ligera (sin partículas ni capas translúcidas pesadas)."""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QPainter, QColor, QFont

ANIMATION_MS = 900
TICK_MS = 32


class WelcomeOverlay(QWidget):
  def __init__(self, parent):
    super().__init__(parent)
    self.setGeometry(parent.rect())
    self.setAttribute(Qt.WA_DeleteOnClose)
    self.setAttribute(Qt.WA_TransparentForMouseEvents)
    parent.installEventFilter(self)

    self._elapsed = 0
    self._opacity = 1.0

    self._timer = QTimer(self)
    self._timer.timeout.connect(self._tick)

  def eventFilter(self, obj, event):
    if obj == self.parent() and event.type() == QEvent.Resize:
      self.setGeometry(self.parent().rect())
    return super().eventFilter(obj, event)

  def showEvent(self, event):
    super().showEvent(event)
    self._elapsed = 0
    self._opacity = 1.0
    if not self._timer.isActive():
      self._timer.start(TICK_MS)

  def _tick(self):
    self._elapsed += TICK_MS
    t = min(1.0, self._elapsed / ANIMATION_MS)
    self._opacity = max(0.0, 1.0 - t)
    if t >= 1.0:
      self._timer.stop()
      self.close()
      return
    self.update()

  def paintEvent(self, event):
    painter = QPainter(self)
    painter.fillRect(self.rect(), QColor(15, 23, 42, int(220 * self._opacity)))

    if self._opacity > 0.15:
      painter.setOpacity(self._opacity)
      font = QFont("Segoe UI")
      font.setPixelSize(28)
      font.setBold(True)
      painter.setFont(font)
      painter.setPen(QColor(248, 250, 252))
      painter.drawText(self.rect(), Qt.AlignCenter, "Bienvenido")
