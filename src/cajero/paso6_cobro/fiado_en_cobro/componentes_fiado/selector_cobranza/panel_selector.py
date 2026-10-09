from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
from PyQt6.QtCore import pyqtSignal

from src.cajero.ingresar_efectivo.medios.efectivo.lienzo import LienzoEfectivo
from src.cajero.ingresar_efectivo.medios.qr.lienzo import LienzoQr
from src.cajero.ingresar_efectivo.medios.tarjeta.lienzo import LienzoTarjeta
from src.cajero.ingresar_efectivo.medios.transferencia.lienzo import LienzoTransferencia

class PanelSelectorCobranza(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self.cont_botones = QWidget()
        h_lay = QHBoxLayout(self.cont_botones)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(20)
        
        btn_style = """
            QPushButton {
                background-color: #F8FAFC;
                color: #1E3A8A;
                border-radius: 12px;
                padding: 20px;
                font-size: 24px;
                font-weight: 900;
                border: 3px solid #94A3B8;
            }
            QPushButton:hover {
                background-color: #EFF6FF;
                border: 3px solid #3B82F6;
                color: #1D4ED8;
            }
        """
        
        self.btn_efectivo = QPushButton("Efectivo")
        self.btn_efectivo.setStyleSheet(btn_style)
        
        self.btn_tarjeta = QPushButton("Tarjeta")
        self.btn_tarjeta.setStyleSheet(btn_style)
        
        self.btn_qr = QPushButton("QR")
        self.btn_qr.setStyleSheet(btn_style)
        
        self.btn_transferencia = QPushButton("Transferencia")
        self.btn_transferencia.setStyleSheet(btn_style)
        
        h_lay.addWidget(self.btn_efectivo)
        h_lay.addWidget(self.btn_tarjeta)
        h_lay.addWidget(self.btn_qr)
        h_lay.addWidget(self.btn_transferencia)
        
        lay.addWidget(self.cont_botones)
        self.cont_botones.hide()

        # LIENZOS PARA COBRO
        self.cont_lienzos = QStackedWidget()
        self.lienzo_efectivo = LienzoEfectivo()
        self.lienzo_qr = LienzoQr()
        self.lienzo_tarjeta = LienzoTarjeta()
        self.lienzo_transferencia = LienzoTransferencia()
        self.cont_lienzos.addWidget(self.lienzo_efectivo)
        self.cont_lienzos.addWidget(self.lienzo_qr)
        self.cont_lienzos.addWidget(self.lienzo_tarjeta)
        self.cont_lienzos.addWidget(self.lienzo_transferencia)
        
        self.cont_lienzos.hide()
        lay.addWidget(self.cont_lienzos)
