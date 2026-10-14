from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt

from src.cajero.ingresar_efectivo.medios.efectivo.lienzo import LienzoEfectivo
from src.cajero.ingresar_efectivo.medios.qr.lienzo import LienzoQr
from src.cajero.ingresar_efectivo.medios.tarjeta.lienzo import LienzoTarjeta
from src.cajero.ingresar_efectivo.medios.transferencia.lienzo import LienzoTransferencia
from src.cajero.ingresar_efectivo.medios.mixto.lienzo import LienzoMixto

class PanelSelectorCobranza(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self.cont_botones = QWidget()
        h_lay = QHBoxLayout(self.cont_botones)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(12)
        
        def make_btn(texto, color_border, color_hover_bg, color_text):
            btn = QPushButton(texto)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(68)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FFFFFF;
                    color: {color_text};
                    border-radius: 12px;
                    font-size: 19px;
                    font-weight: 900;
                    border: 2px solid {color_border};
                    padding: 8px 12px;
                }}
                QPushButton:hover {{
                    background-color: {color_hover_bg};
                    border: 2px solid {color_text};
                }}
                QPushButton:pressed {{
                    background-color: {color_border};
                    color: #FFFFFF;
                }}
            """)
            return btn
        
        self.btn_efectivo = make_btn("Efectivo", "#10B981", "#ECFDF5", "#047857")
        self.btn_tarjeta = make_btn("Tarjeta", "#3B82F6", "#EFF6FF", "#1D4ED8")
        self.btn_qr = make_btn("QR", "#6366F1", "#EEF2FF", "#4338CA")
        self.btn_transferencia = make_btn("Transf.", "#06B6D4", "#ECFEFF", "#0E7490")
        self.btn_mixto = make_btn("Mixto", "#8B5CF6", "#F5F3FF", "#6D28D9")
        
        h_lay.addWidget(self.btn_efectivo)
        h_lay.addWidget(self.btn_tarjeta)
        h_lay.addWidget(self.btn_qr)
        h_lay.addWidget(self.btn_transferencia)
        h_lay.addWidget(self.btn_mixto)
        
        lay.addWidget(self.cont_botones)
        self.cont_botones.hide()

        # LIENZOS PARA COBRO
        self.cont_lienzos = QStackedWidget()
        self.cont_lienzos.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.lienzo_efectivo = LienzoEfectivo()
        self.lienzo_qr = LienzoQr()
        self.lienzo_tarjeta = LienzoTarjeta()
        self.lienzo_transferencia = LienzoTransferencia()
        self.lienzo_mixto = LienzoMixto()
        self.cont_lienzos.addWidget(self.lienzo_efectivo)
        self.cont_lienzos.addWidget(self.lienzo_qr)
        self.cont_lienzos.addWidget(self.lienzo_tarjeta)
        self.cont_lienzos.addWidget(self.lienzo_transferencia)
        self.cont_lienzos.addWidget(self.lienzo_mixto)
        
        self.cont_lienzos.hide()
        lay.addWidget(self.cont_lienzos, 1)
