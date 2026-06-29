from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

class ResumenVuelto(QWidget):
    """
    Componente extraído de paso6_cobro.py: Muestra el Vuelto/Cambio.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        vuelto_lay = QHBoxLayout(self)
        vuelto_lay.setContentsMargins(0, 0, 0, 0)
        vuelto_lay.setSpacing(15)
        
        self.lbl_vuelto_tit = QLabel("SU CAMBIO:")
        self.lbl_vuelto_tit.setStyleSheet("font-weight: 900; color: #64748B; font-size: 20px;")
        self.lbl_vuelto_tit.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.lbl_vuelto_val = QLabel("$0.00")
        self.lbl_vuelto_val.setStyleSheet("color: #10B981; font-size: 36px; font-weight: 900;")
        
        vuelto_lay.addStretch()
        vuelto_lay.addWidget(self.lbl_vuelto_tit)
        vuelto_lay.addWidget(self.lbl_vuelto_val)
        vuelto_lay.addStretch()

    def actualizar_vuelto(self, vuelto: float):
        """Actualiza el texto y color dependiendo de si falta dinero o sobra."""
        if vuelto < 0:
            self.lbl_vuelto_tit.setText("FALTA:")
            self.lbl_vuelto_val.setText(f"${abs(vuelto):,.2f}")
            self.lbl_vuelto_val.setStyleSheet("color: #EF4444; font-size: 40px; font-weight: 900;")
        else:
            self.lbl_vuelto_tit.setText("SU CAMBIO:")
            self.lbl_vuelto_val.setText(f"${vuelto:,.2f}")
            self.lbl_vuelto_val.setStyleSheet("color: #10B981; font-size: 40px; font-weight: 900;")
