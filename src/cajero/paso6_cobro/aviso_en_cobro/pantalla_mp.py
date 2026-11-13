from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QGraphicsOpacityEffect, QWidget, QPushButton
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette

class PantallaMP(QFrame):
    """
    Overlay gigante de confirmación estilo Mercado Pago.
    Cubre toda la pantalla de cobro para dar seguridad absoluta al cajero.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PantallaMP")
        # Cubrir todo y atrapar clics para que el cajero no toque nada por error
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.hide()
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_icono = QLabel("✔️")
        self.lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_titulo = QLabel("¡Listo!")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_monto = QLabel(".00")
        self.lbl_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lay.addStretch()
        lay.addWidget(self.lbl_icono)
        lay.addSpacing(20)
        lay.addWidget(self.lbl_titulo)
        lay.addSpacing(10)
        lay.addWidget(self.lbl_monto)
        lay.addStretch()
        
        self.lbl_footer = QLabel("Cobro Autónomo")
        self.lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_footer.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        lay.addWidget(self.lbl_footer)
        
        self._callback = None
        
        # Ocultar por defecto
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._cerrar)
        
    def ubicar(self):
        if self.parent():
            self.resize(self.parent().size())
            self.move(0, 0)

    def mostrar_aprobado(self, monto_str: str, on_finish=None, es_autonomo=False, duracion_ms: int = 2000):
        if es_autonomo:
            self.lbl_footer.show()
        else:
            self.lbl_footer.hide()
            
        import logging
        logging.getLogger("PunPro").info(f"MOSTRAR APROBADO START, monto={monto_str}")
        self._callback = on_finish
        self.setStyleSheet('''
            QFrame#PantallaMP {
                background-color: #00A650;
                border: none;
            }
        ''')
        self.lbl_icono.setText("✔️")
        self.lbl_icono.setStyleSheet("color: white; font-size: 120px; font-weight: bold;")
        
        self.lbl_titulo.setText("¡Cobro Exitoso!")
        self.lbl_titulo.setStyleSheet("color: white; font-size: 50px; font-weight: 900; font-family: 'Segoe UI';")
        
        self.lbl_monto.setText(monto_str)
        self.lbl_monto.setStyleSheet("color: white; font-size: 40px; font-weight: bold;")
        
        self.ubicar()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.show()
        self.raise_()
        self.setFocus()
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        self.repaint()
        self._timer.start(duracion_ms)  # Tiempo de feedback visual antes de cerrar

    def mousePressEvent(self, event):
        self._cerrar_inmediato()
        event.accept()

    def keyPressEvent(self, event):
        self._cerrar_inmediato()
        event.accept()

    def _cerrar_inmediato(self):
        if self._timer.isActive():
            self._timer.stop()
        self._cerrar()
        
    def mostrar_rechazado(self, motivo: str = "Pago Rechazado", on_finish=None):
        self._callback = on_finish
        self.setStyleSheet('''
            QFrame#PantallaMP {
                background-color: #F23D4F;
                border: none;
            }
        ''')
        self.lbl_icono.setText("✖️")
        self.lbl_icono.setStyleSheet("color: white; font-size: 120px; font-weight: bold;")
        
        self.lbl_titulo.setText(motivo)
        self.lbl_titulo.setStyleSheet("color: white; font-size: 50px; font-weight: 900; font-family: 'Segoe UI';")
        
        self.lbl_monto.setText("Intentá nuevamente")
        self.lbl_monto.setStyleSheet("color: white; font-size: 30px;")
        
        self.ubicar()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.show()
        self.raise_()
        self.setFocus()
        self._timer.start(3500)
        
    def _cerrar(self):
        self.hide()
        if self._callback:
            cb = self._callback
            self._callback = None
            cb()

    def resizeEvent(self, event):
        self.ubicar()
        super().resizeEvent(event)

    def paintEvent(self, event):
        from PyQt6.QtWidgets import QStyleOption, QStyle
        from PyQt6.QtGui import QPainter
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)
        super().paintEvent(event)
