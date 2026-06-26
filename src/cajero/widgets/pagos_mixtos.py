from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QGridLayout, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

class DialogoPagosMixtos(QDialog):
    """
    Dialogo Avanzado para Pagos Multimoneda y Multimetodo
    Permite dividir el pago entre Efectivo, Tarjeta, MercadoPago y Dólares.
    """
    
    def __init__(self, total_a_pagar, tasa_usd=1000.0, parent=None):
        super().__init__(parent)
        self.total_a_pagar = total_a_pagar
        self.tasa_usd = tasa_usd
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(600, 600)
        
        self.valores = {
            "efectivo": 0.0,
            "tarjeta": 0.0,
            "mercadopago": 0.0,
            "usd": 0.0
        }
        
        self._setup_ui()
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 20px;
                border: 2px solid #3B82F6;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 10)
        frame.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(20)
        
        # Título
        lbl_titulo = QLabel("DIVISIÓN DE PAGOS MIXTOS")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: 900; color: #1E3A8A; border: none; letter-spacing: 2px;")
        layout.addWidget(lbl_titulo)
        
        # Total a pagar
        lbl_total = QLabel(f"TOTAL A CUBRIR: ${self.total_a_pagar:,.2f}")
        lbl_total.setAlignment(Qt.AlignCenter)
        lbl_total.setStyleSheet("font-size: 32px; font-weight: 900; color: #EF4444; border: none;")
        layout.addWidget(lbl_total)
        
        # Inputs Grid
        grid = QGridLayout()
        grid.setSpacing(15)
        
        def crear_input(nombre, icono, color):
            lbl = QLabel(f"{icono} {nombre}:")
            lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color}; border: none;")
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            txt = QLineEdit()
            txt.setPlaceholderText("0.00")
            txt.setStyleSheet(f"""
                QLineEdit {{
                    background: #F8FAFC;
                    border: 2px solid {color};
                    border-radius: 10px;
                    padding: 8px;
                    font-size: 20px;
                    font-weight: bold;
                    color: {color};
                }}
            """)
            txt.textChanged.connect(self._recalcular)
            return lbl, txt
            
        self.lbl_ef, self.txt_efectivo = crear_input("Efectivo ($)", "💵", "#10B981")
        self.lbl_tj, self.txt_tarjeta = crear_input("Tarjeta ($)", "💳", "#F59E0B")
        self.lbl_mp, self.txt_mercadopago = crear_input("Transferencia ($)", "🏦", "#0EA5E9")
        self.lbl_us, self.txt_usd = crear_input(f"Dólares (U$S)", "🗽", "#8B5CF6")
        
        self.lbl_tasa = QLabel(f"(Tasa de cambio: ${self.tasa_usd:,.2f})")
        self.lbl_tasa.setStyleSheet("font-size: 12px; color: #94A3B8; border: none;")
        self.lbl_tasa.setAlignment(Qt.AlignCenter)
        
        grid.addWidget(self.lbl_ef, 0, 0); grid.addWidget(self.txt_efectivo, 0, 1)
        grid.addWidget(self.lbl_tj, 1, 0); grid.addWidget(self.txt_tarjeta, 1, 1)
        grid.addWidget(self.lbl_mp, 2, 0); grid.addWidget(self.txt_mercadopago, 2, 1)
        grid.addWidget(self.lbl_us, 3, 0); grid.addWidget(self.txt_usd, 3, 1)
        grid.addWidget(self.lbl_tasa, 4, 1)
        
        layout.addLayout(grid)
        
        # Restante / Vuelto
        self.lbl_restante = QLabel("Falta cubrir: $0.00")
        self.lbl_restante.setAlignment(Qt.AlignCenter)
        self.lbl_restante.setStyleSheet("font-size: 20px; font-weight: bold; color: #E11D48; border: none;")
        layout.addWidget(self.lbl_restante)
        
        # Botones de Acción
        btn_layout = QHBoxLayout()
        
        btn_cancelar = QPushButton("CANCELAR")
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background: #EF4444; color: white; border-radius: 12px; font-weight: bold; font-size: 16px; padding: 12px;
            }
        """)
        btn_cancelar.clicked.connect(self.reject)
        
        self.btn_confirmar = QPushButton("CONFIRMAR PAGO")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background: #10B981; color: white; border-radius: 12px; font-weight: bold; font-size: 16px; padding: 12px;
            }
            QPushButton:disabled {
                background: #94A3B8;
            }
        """)
        self.btn_confirmar.clicked.connect(self.accept)
        self.btn_confirmar.setEnabled(False)
        
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(self.btn_confirmar)
        layout.addLayout(btn_layout)
        
        main_layout.addWidget(frame)
        self._recalcular()

    def _safe_float(self, text):
        try:
            if not text.strip(): return 0.0
            return float(text.replace(',', '.'))
        except:
            return 0.0

    def _recalcular(self):
        efectivo = self._safe_float(self.txt_efectivo.text())
        tarjeta = self._safe_float(self.txt_tarjeta.text())
        mp = self._safe_float(self.txt_mercadopago.text())
        usd = self._safe_float(self.txt_usd.text())
        
        usd_en_pesos = usd * self.tasa_usd
        
        self.valores["efectivo"] = efectivo
        self.valores["tarjeta"] = tarjeta
        self.valores["mercadopago"] = mp
        self.valores["usd"] = usd
        
        total_ingresado = efectivo + tarjeta + mp + usd_en_pesos
        diferencia = total_ingresado - self.total_a_pagar
        
        if diferencia < -0.01: # Faltante
            self.lbl_restante.setText(f"Falta cubrir: ${abs(diferencia):,.2f}")
            self.lbl_restante.setStyleSheet("font-size: 20px; font-weight: bold; color: #E11D48; border: none;")
            self.btn_confirmar.setEnabled(False)
        elif diferencia > 0.01: # Vuelto
            self.lbl_restante.setText(f"VUELTO (Efectivo): ${diferencia:,.2f}")
            self.lbl_restante.setStyleSheet("font-size: 20px; font-weight: bold; color: #10B981; border: none;")
            self.btn_confirmar.setEnabled(True)
        else: # Exacto
            self.lbl_restante.setText("Pago Exacto")
            self.lbl_restante.setStyleSheet("font-size: 20px; font-weight: bold; color: #3B82F6; border: none;")
            self.btn_confirmar.setEnabled(True)

    def get_valores(self):
        return self.valores
