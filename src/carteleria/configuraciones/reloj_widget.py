from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QTimer, QTime
from src.carteleria.theme import C_THEME

class RelojWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__("00:00:00", parent)
        self.setStyleSheet(f"font-family: -apple-system; font-size: 26px; font-weight: 700; color: {C_THEME['blue']}; background: transparent;")
        
        self.timer_reloj = QTimer(self)
        self.timer_reloj.timeout.connect(self.actualizar_reloj)
        self.timer_reloj.start(1000)
        self.actualizar_reloj()

    def actualizar_reloj(self):
        hora_actual = QTime.currentTime().toString("HH:mm:ss")
        self.setText(hora_actual)
