from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit
from PyQt6.QtCore import Qt

class PanelIngresoEfectivo(QWidget):
    """Panel para Cambio / Fondo Fijo."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_titulo_monto = QLabel("Monto de Fondo Fijo / Cambio ($):")
        self.lbl_titulo_monto.setStyleSheet("font-size: 13px; color: #334155; font-weight: bold; border: none;")
        lay.addWidget(self.lbl_titulo_monto)

        self.txt_monto = QLineEdit()
        self.txt_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_monto.setStyleSheet("""
            QLineEdit {
                font-size: 36px; font-weight: 900; color: #059669;
                border: 2px solid #cbd5e1; border-radius: 10px;
                padding: 8px; background: white;
            }
            QLineEdit:focus { border-color: #10B981; }
        """)
        lay.addWidget(self.txt_monto)
        lay.addStretch(1)

    def validar(self):
        try:
            val = float(self.txt_monto.text().strip())
            if val <= 0:
                return False, "⚠️ Ingresa un monto mayor a 0"
            return True, ""
        except ValueError:
            return False, "⚠️ Monto inválido"

    def monto(self):
        return float(self.txt_monto.text().strip())

    def reset(self):
        self.txt_monto.clear()
        self.txt_monto.setFocus()
