from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QGridLayout, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from src.ui_components.alerts import MensajeAtencion

class PantallaCobroIndustrial(QDialog):
    """
    MODULO APARTE: Ventana de Cobro Industrial
    Clonado pixel-perfect de la interfaz legacy.
    Independiente de la terminal de venta.
    """
    def __init__(self, total_a_cobrar, parent=None):
        super().__init__(parent)
        self.total = total_a_cobrar
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(680, 520) 
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #F0F0F0; border: 2px solid #0055AA; }
            QLabel { font-family: 'SimSun', 'Consolas', monospace; font-weight: bold; color: #000088; font-size: 14px; }
            QLineEdit { background-color: #FFFFFF; border: 1px solid #777; color: #000000; font-size: 16px; font-weight: bold; }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        title_bar = QLabel("  Medios de Pago  0")
        title_bar.setFixedHeight(28)
        title_bar.setStyleSheet("background-color: #0055AA; color: white; font-size: 13px;")
        main_layout.addWidget(title_bar)
        
        banner_rojo = QLabel("  SE UTILIZO CUPON EN EFECTIVO, MONTO (.....) :0.00")
        banner_rojo.setStyleSheet("background-color: #F0F0F0; color: #FF0000; font-size: 11px; font-weight: bold;")
        main_layout.addWidget(banner_rojo)
        
        content = QFrame()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        top_h = QHBoxLayout()
        lbl_icon = QLabel("🧺")
        lbl_icon.setStyleSheet("font-size: 40px;")
        top_h.addWidget(lbl_icon)
        
        sub_v = QVBoxLayout()
        sub_v.addWidget(QLabel("Sub. Total:"))
        self.lbl_subtotal_val = QLabel(f"{self.total:.2f}")
        self.lbl_subtotal_val.setStyleSheet("""
            background-color: #FFFFCC; border: 1px solid #999; color: #FF0000; font-size: 32px; padding: 5px; font-weight: bold;
        """)
        self.lbl_subtotal_val.setAlignment(Qt.AlignCenter)
        sub_v.addWidget(self.lbl_subtotal_val)
        top_h.addLayout(sub_v)
        
        f_grid = QGridLayout()
        f_grid.addWidget(QLabel("F1-Descuent"), 0, 0)
        f_grid.addWidget(QLineEdit("0.00"), 0, 1)
        f_grid.addWidget(QLabel("%"), 0, 2)
        f_grid.addWidget(QLabel("F5-Recarg"), 1, 0)
        f_grid.addWidget(QLineEdit("0.00"), 1, 1)
        f_grid.addWidget(QLabel("%"), 1, 2)
        top_h.addLayout(f_grid)
        layout.addLayout(top_h)
        
        mid_grid = QGridLayout()
        mid_grid.addWidget(QLabel("Redondeo:"), 0, 0)
        self.box_redondeo = QLabel("0.00")
        self.box_redondeo.setStyleSheet("background-color: #FFFFFF; border: 1px solid #999; color: #FF0000; font-size: 26px;")
        self.box_redondeo.setAlignment(Qt.AlignCenter)
        mid_grid.addWidget(self.box_redondeo, 0, 1)
        
        mid_grid.addWidget(QLabel("Sub. Pagos:"), 1, 0)
        self.box_subpagos = QLabel(f"{self.total:.2f}")
        self.box_subpagos.setStyleSheet("background-color: #FFFFFF; border: 1px solid #999; color: #FF0000; font-size: 26px;")
        self.box_subpagos.setAlignment(Qt.AlignCenter)
        mid_grid.addWidget(self.box_subpagos, 1, 1)
        layout.addLayout(mid_grid)
        
        pay_h = QHBoxLayout()
        self.ef_frame = QFrame()
        self.ef_frame.setStyleSheet("border: 3px solid #FF00FF; background-color: #FFFFFF;")
        ef_v = QVBoxLayout(self.ef_frame)
        ef_v.setContentsMargins(2, 2, 2, 2)
        ef_head = QLabel("● F2-Efectivo")
        ef_head.setStyleSheet("background-color: #00AA00; color: #FFFFFF; padding: 3px;")
        ef_v.addWidget(ef_head)
        self.txt_recibido = QLineEdit(f"{self.total:.2f}")
        self.txt_recibido.setStyleSheet("background-color: #3399FF; color: #FFFFFF; font-size: 50px; border: none; font-weight: bold;")
        self.txt_recibido.setAlignment(Qt.AlignCenter)
        self.txt_recibido.setFixedHeight(110)
        ef_v.addWidget(self.txt_recibido)
        pay_h.addWidget(self.ef_frame)
        
        others_f = QFrame()
        others_f.setStyleSheet("background-color: #E8E8E8; border: 1px solid #AAA;")
        og = QGridLayout(others_f)
        og.addWidget(QRadioButton("F3-Tarjeta"), 0, 0)
        og.addWidget(QRadioButton("F4-Deuda"), 1, 0)
        og.addWidget(QRadioButton("F6-M.Pago POS"), 2, 0)
        og.addWidget(QRadioButton("F7-M.Pago QR"), 3, 0)
        og.addWidget(QLabel("D.N.I:"), 0, 1)
        og.addWidget(QLineEdit(), 0, 2)
        og.addWidget(QLabel("Tarjeta №:"), 1, 1)
        og.addWidget(QLineEdit(), 1, 2)
        lbl_pt = QLabel("Pagos Total:")
        lbl_pt.setStyleSheet("color: #FF0000;")
        og.addWidget(lbl_pt, 3, 1)
        self.lbl_p_val = QLabel("0.00")
        self.lbl_p_val.setStyleSheet("color: #FF0000; font-size: 20px; border-bottom: 2px solid #FF0000;")
        og.addWidget(self.lbl_p_val, 3, 2)
        pay_h.addWidget(others_f)
        layout.addLayout(pay_h)
        
        bot_h = QHBoxLayout()
        bot_h.addWidget(QLabel("Pagados:"))
        self.lbl_pagados = QLabel("0.00")
        self.lbl_pagados.setStyleSheet("background-color: #BBCCFF; border: 1px solid #888; font-size: 24px; min-width: 140px;")
        self.lbl_pagados.setAlignment(Qt.AlignCenter)
        bot_h.addWidget(self.lbl_pagados)
        bot_h.addStretch()
        bot_h.addWidget(QLabel("Cambio:"))
        self.lbl_cambio = QLabel("0.00")
        self.lbl_cambio.setStyleSheet("background-color: #FFFFCC; border: 1px solid #888; font-size: 24px; min-width: 140px; color: #FF0000;")
        self.lbl_cambio.setAlignment(Qt.AlignCenter)
        bot_h.addWidget(self.lbl_cambio)
        layout.addLayout(bot_h)
        
        btn_h = QHBoxLayout()
        btn_h.addStretch()
        btn_si = QPushButton("ENT=Sí")
        btn_no = QPushButton("✖ ESC=NO")
        for b in [btn_si, btn_no]:
            b.setStyleSheet("background-color: #D4D0C8; border: 1px solid #888; padding: 4px 12px; color: black; font-size: 12px;")
        btn_si.clicked.connect(self.finalizar)
        btn_no.clicked.connect(self.reject)
        btn_h.addWidget(btn_si)
        btn_h.addWidget(btn_no)
        layout.addLayout(btn_h)
        main_layout.addWidget(content)
        
        self.txt_recibido.textChanged.connect(self.actualizar_vuelto)
        self.txt_recibido.setFocus()
        self.txt_recibido.selectAll()

    def actualizar_vuelto(self):
        try:
            from src.utils.parser import parse_float_regional
            recibido = parse_float_regional(self.txt_recibido.text())
            cambio = recibido - self.total
            self.lbl_cambio.setText(f"{max(0, cambio):.2f}")
            self.lbl_pagados.setText(f"{recibido:.2f}")
            self.lbl_p_val.setText(f"{recibido:.2f}")
        except: pass

    def finalizar(self):
        try:
            from src.utils.parser import parse_float_regional
            recibido = parse_float_regional(self.txt_recibido.text())
            if recibido < self.total:
                alert = MensajeAtencion(f"PAGO INSUFICIENTE\nFaltan: {self.total - recibido:.2f}", self)
                qt_exec(alert)
                return
            self.accept()
        except: pass

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter, Qt.Key_F12]: self.finalizar()
        elif event.key() == Qt.Key_Escape: self.reject()
        super().keyPressEvent(event)