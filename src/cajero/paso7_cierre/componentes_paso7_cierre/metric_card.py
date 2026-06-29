from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

class MetricCard(QFrame):
    def __init__(self, titulo, icon, color="#3B82F6", parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.color = color
        self.setFixedHeight(100)
        self.setStyleSheet(f"""
            QFrame#MetricCard {{
                background: white; border: 1px solid #E2E8F0; border-radius: 16px;
            }}
        """)
        
        # Sombra premium
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 10, 20, 10)
        lay.setSpacing(15)
        
        # Contenedor del ícono para darle un fondo suave
        icon_frame = QFrame()
        icon_frame.setObjectName("MetricIconFrame")
        icon_frame.setFixedSize(50, 50)

        i_lay = QVBoxLayout(icon_frame)
        i_lay.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)

        i_lay.addWidget(icon_lbl)
        lay.addWidget(icon_frame)
        
        v_lay = QVBoxLayout()
        v_lay.setSpacing(2)
        v_lay.setAlignment(Qt.AlignVCenter)
        self.lbl_tit = QLabel(titulo.upper())
        self.lbl_tit.setObjectName("MetricTit")

        v_lay.addWidget(self.lbl_tit)
        
        self.lbl_val = QLabel("••••••")

        v_lay.addWidget(self.lbl_val)
        lay.addLayout(v_lay)
        lay.addStretch()

    def revelar(self, valor, formato=True):

        self._animar(valor, formato)

    def _animar(self, final, formato):
        steps = 15
        self._curr_step = 0
        def tick():
            self._curr_step += 1
            v = final * (self._curr_step / steps)
            if formato: self.lbl_val.setText(f"$ {v:,.2f}")
            else: self.lbl_val.setText(f"{int(v)}")
            if self._curr_step < steps: QTimer.singleShot(30, tick)
            else: 
                if formato: self.lbl_val.setText(f"$ {final:,.2f}")
                else: self.lbl_val.setText(f"{int(final)}")
        tick()
