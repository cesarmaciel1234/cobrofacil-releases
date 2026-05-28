from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QDoubleSpinBox, QPushButton, QHBoxLayout, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

class DialogoMontoRápido(QDialog):
    def __init__(self, titulo, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setFixedSize(300, 180)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setStyleSheet("background: white; border: 2px solid #1E3A8A; border-radius: 12px;")
        
        self.monto = 0.0
        
        layout = QVBoxLayout(self)
        lbl = QLabel(titulo)
        lbl.setStyleSheet("font-weight: bold; color: #1E3A8A; font-size: 14px; border: none;")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)
        
        self.spin = QDoubleSpinBox()
        self.spin.setRange(0, 999999)
        self.spin.setDecimals(2)
        self.spin.setStyleSheet("font-size: 24px; padding: 10px; border: 1px solid #CBD5E1;")
        self.spin.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.spin)
        
        btns = QHBoxLayout()
        btn_ok = QPushButton("ACEPTAR (ENTER)")
        btn_ok.setStyleSheet("background: #1E3A8A; color: white; padding: 10px; border-radius: 6px;")
        btn_ok.clicked.connect(self.accept_val)
        
        btn_cancel = QPushButton("ESC")
        btn_cancel.setStyleSheet("background: #64748B; color: white; padding: 10px; border-radius: 6px;")
        btn_cancel.clicked.connect(self.reject)
        
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        
        self.spin.setFocus()
        self.spin.selectAll()

    def accept_val(self):
        self.monto = self.spin.value()
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept_val()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

class DialogoPorcentajeRapido(QDialog):
    """
    Diálogo industrial para la aplicación de descuentos o recargos en formato porcentual (%).
    Muestra previsualización en tiempo real y aplica restricciones estrictas de seguridad.
    """
    def __init__(self, tipo="descuento", total_base=0.0, parent=None):
        super().__init__(parent)
        self.tipo = tipo.lower()
        self.total_base = total_base
        self.porcentaje = 0.0
        self.monto_equivalente = 0.0
        
        self.setFixedSize(420, 360)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setup_ui()
        self.apply_glow()
        
    def apply_glow(self):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(20)
        glow.setColor(QColor(30, 58, 138, 150))
        glow.setOffset(0, 0)
        self.main_frame.setGraphicsEffect(glow)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("background-color: white; border-radius: 12px; border: 2px solid #1E3A8A;")
        layout.addWidget(self.main_frame)
        
        main_lay = QVBoxLayout(self.main_frame)
        main_lay.setContentsMargins(20, 20, 20, 20)
        main_lay.setSpacing(15)
        
        # Título con icono dinámico
        ico = "🏷️" if self.tipo == "descuento" else "📈"
        tit_text = f"{ico} DESCUENTO PORCENTUAL (%)" if self.tipo == "descuento" else f"{ico} RECARGO PORCENTUAL (%)"
        lbl_title = QLabel(tit_text)
        lbl_title.setStyleSheet("font-weight: 900; color: #1E3A8A; font-size: 15px; border: none; background: transparent; letter-spacing: 1px;")
        lbl_title.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(lbl_title)
        
        # SpinBox de Porcentaje con tipografía pesada
        self.spin = QDoubleSpinBox()
        self.spin.setRange(0.00, 100.00 if self.tipo == "descuento" else 500.00)
        self.spin.setDecimals(2)
        self.spin.setSuffix(" %")
        self.spin.setStyleSheet("""
            QDoubleSpinBox {
                font-family: 'Segoe UI Black';
                font-size: 28px;
                font-weight: bold;
                padding: 10px;
                border: 2px solid #CBD5E1;
                border-radius: 8px;
                color: #1E3A8A;
                background-color: #F8FAFC;
            }
            QDoubleSpinBox:focus {
                border-color: #3B82F6;
                background-color: white;
            }
        """)
        self.spin.setAlignment(Qt.AlignCenter)
        self.spin.valueChanged.connect(self.actualizar_vista)
        main_lay.addWidget(self.spin)
        
        # Panel de Vista Previa Contable en Tiempo Real
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px;")
        prev_lay = QVBoxLayout(self.preview_frame)
        prev_lay.setSpacing(6)
        prev_lay.setContentsMargins(15, 12, 15, 12)
        
        self.lbl_base = QLabel(f"Base Original:  ${self.total_base:,.2f}")
        self.lbl_base.setStyleSheet("font-size: 12px; color: #64748B; font-weight: bold; border: none; background: transparent;")
        
        self.lbl_operacion = QLabel("Ahorro (0%):  -$0.00" if self.tipo == "descuento" else "Recargo (0%):  +$0.00")
        color_op = "#E11D48" if self.tipo == "descuento" else "#D97706"
        self.lbl_operacion.setStyleSheet(f"font-size: 12px; color: {color_op}; font-weight: bold; border: none; background: transparent;")
        
        self.lbl_final = QLabel(f"Total Neto:   ${self.total_base:,.2f}")
        self.lbl_final.setStyleSheet("font-size: 15px; color: #1E3A8A; font-weight: 900; border: none; background: transparent;")
        
        prev_lay.addWidget(self.lbl_base)
        prev_lay.addWidget(self.lbl_operacion)
        prev_lay.addWidget(self.lbl_final)
        main_lay.addWidget(self.preview_frame)
        
        # Botones de Acción
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(12)
        
        btn_ok = QPushButton("ACEPTAR")
        btn_ok.setStyleSheet("background: #1E3A8A; color: white; padding: 12px; border-radius: 8px; font-weight: 900; font-size: 12px; border: none;")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(self.accept_val)
        
        btn_cancel = QPushButton("CANCELAR")
        btn_cancel.setStyleSheet("background: #64748B; color: white; padding: 12px; border-radius: 8px; font-weight: 900; font-size: 12px; border: none;")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        
        btn_lay.addWidget(btn_ok, 7)
        btn_lay.addWidget(btn_cancel, 3)
        main_lay.addLayout(btn_lay)
        
        self.spin.setFocus()
        self.spin.selectAll()
        
    def actualizar_vista(self, val):
        self.porcentaje = val
        self.monto_equivalente = self.total_base * (val / 100.0)
        
        if self.tipo == "descuento":
            total_neto = max(0.0, self.total_base - self.monto_equivalente)
            self.lbl_operacion.setText(f"Ahorro ({val:g}%):  -${self.monto_equivalente:,.2f}")
            self.lbl_final.setText(f"Total Neto:  ${total_neto:,.2f}")
        else:
            total_neto = self.total_base + self.monto_equivalente
            self.lbl_operacion.setText(f"Recargo ({val:g}%):  +${self.monto_equivalente:,.2f}")
            self.lbl_final.setText(f"Total Neto:  ${total_neto:,.2f}")

    def accept_val(self):
        self.porcentaje = self.spin.value()
        self.monto_equivalente = self.total_base * (self.porcentaje / 100.0)
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept_val()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
