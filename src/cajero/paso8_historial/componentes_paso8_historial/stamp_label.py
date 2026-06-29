from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter

class StampLabel(QLabel):
    def __init__(self, text="CANCELADO", parent=None):
        super().__init__(text, parent)
        self.setFixedSize(400, 150)
        self.setAlignment(Qt.AlignCenter)
        # Estilo de sello de goma industrial
        self.setStyleSheet("""
            QLabel {
                color: #ef4444;
                font-size: 55px;
                font-weight: 900;
                border: 10px double #ef4444;
                border-radius: 20px;
                background-color: rgba(255, 255, 255, 180);
                padding: 10px;
                letter-spacing: 5px;
            }
        """)
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Rotación diagonal clásica de sello
        painter.translate(self.width()/2, self.height()/2)
        painter.rotate(-25)
        painter.translate(-self.width()/2, -self.height()/2)
        super().paintEvent(event)
