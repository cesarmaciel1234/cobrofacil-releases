from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame)
from PyQt6.QtCore import Qt

class PanelEstadoCredito(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(10)
        
        # ── 1. Ficha del Cliente Ejecutiva ─────────────────────────────────────
        self.caja_ficha = QFrame()
        self.caja_ficha.setObjectName("CajaFichaCliente")
        self.caja_ficha.setStyleSheet(
            "QFrame#CajaFichaCliente { background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; }"
        )
        lay_ficha = QVBoxLayout(self.caja_ficha)
        lay_ficha.setContentsMargins(20, 14, 20, 14)
        lay_ficha.setSpacing(10)

        # Identidad del cliente con Avatar
        h_identidad = QHBoxLayout()
        h_identidad.setSpacing(12)
        self.icono = QLabel("👤")
        self.icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icono.setFixedSize(46, 46)
        self.icono.setStyleSheet(
            "QLabel { font-size: 24px; background: #F1F5F9; border-radius: 23px; border: 1px solid #CBD5E1; }"
        )
        h_identidad.addWidget(self.icono)

        v_nombres = QVBoxLayout()
        v_nombres.setSpacing(2)
        self.estado = QLabel("")
        self.estado.setStyleSheet("color: #0F172A; font-size: 22px; font-weight: 900; background: transparent; border: none;")
        self.ultimo_pago_lbl = QLabel("")
        self.ultimo_pago_lbl.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 700; background: transparent; border: none;")
        self.ultimo_pago_lbl.hide()
        v_nombres.addWidget(self.estado)
        v_nombres.addWidget(self.ultimo_pago_lbl)
        h_identidad.addLayout(v_nombres)
        h_identidad.addStretch()
        lay_ficha.addLayout(h_identidad)

        # Caja destacada de Estado Financiero (Deuda / Saldo a favor)
        self.caja_saldo = QFrame()
        self.caja_saldo.setObjectName("CajaSaldo")
        self.caja_saldo.setStyleSheet(
            "QFrame#CajaSaldo { background: #F8FAFC; border: 2px solid #CBD5E1; border-radius: 12px; }"
        )
        lay_saldo = QVBoxLayout(self.caja_saldo)
        lay_saldo.setContentsMargins(16, 12, 16, 12)
        lay_saldo.setSpacing(4)

        self.detalle = QLabel("")
        self.detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detalle.setStyleSheet("font-size: 30px; font-weight: 900; background: transparent; border: none;")
        lay_saldo.addWidget(self.detalle)

        self.lbl_subdetalle = QLabel("")
        self.lbl_subdetalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subdetalle.setStyleSheet("font-size: 13px; font-weight: 700; background: transparent; border: none;")
        lay_saldo.addWidget(self.lbl_subdetalle)
        lay_ficha.addWidget(self.caja_saldo)

        # Botones de Acción Principales
        lay_botones_accion = QHBoxLayout()
        lay_botones_accion.setSpacing(14)

        self.btn_imprimir_resumen = QPushButton("📄 Ver / Imprimir")
        self.btn_imprimir_resumen.setToolTip("Historial: ver movimientos e imprimir")
        self.btn_imprimir_resumen.setFixedHeight(50)
        self.btn_imprimir_resumen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_imprimir_resumen.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #1E293B; font-size: 16px; font-weight: 800; "
            "border-radius: 12px; border: 2px solid #CBD5E1; padding: 0 16px; } "
            "QPushButton:hover { background: #E2E8F0; color: #0F172A; border-color: #94A3B8; }"
        )
        lay_botones_accion.addWidget(self.btn_imprimir_resumen)

        self.btn_iniciar_pago = QPushButton("💳 PAGAR / ABONAR (Enter)")
        self.btn_iniciar_pago.setFixedHeight(50)
        self.btn_iniciar_pago.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_iniciar_pago.setStyleSheet(
            "QPushButton { background: #10B981; color: #FFFFFF; font-size: 16px; font-weight: 900; "
            "border-radius: 12px; border: none; padding: 0 18px; } "
            "QPushButton:hover { background: #059669; }"
        )
        lay_botones_accion.addWidget(self.btn_iniciar_pago)
        lay_ficha.addLayout(lay_botones_accion)

        self.lbl_guia_atajos = QLabel("💡 Presioná Enter para iniciar el cobro · Escape o Volver para cambiar de cliente")
        self.lbl_guia_atajos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_guia_atajos.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        lay_ficha.addWidget(self.lbl_guia_atajos)

        lay.addWidget(self.caja_ficha)

        # Compatibilidad / Ocultos
        self.lbl_total_estimado = QLabel("")
        self.lbl_total_estimado.hide()
        self.lbl_historial = QLabel("")
        self.lbl_historial.hide()

        # ── 2. Controles de Monto (Paso 3) ────────────────────────────────────
        self.lbl_pregunta_monto = QLabel("1. ¿Cuánto paga a la cuenta?")
        self.lbl_pregunta_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_pregunta_monto.setStyleSheet(
            "color: #1E3A8A; font-size: 16px; font-weight: 800; background: transparent; border: none;"
        )
        self.lbl_pregunta_monto.hide()
        lay.addWidget(self.lbl_pregunta_monto)

        lay_abono = QHBoxLayout()
        lay_abono.setContentsMargins(0, 0, 0, 0)
        lay_abono.setSpacing(12)

        self.txt_monto_abono = QLineEdit()
        self.txt_monto_abono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_monto_abono.setFixedHeight(68)
        self.txt_monto_abono.setPlaceholderText("Ejemplo: 100")
        self.txt_monto_abono.setStyleSheet(
            "QLineEdit { background: #FFFFFF; color: #065F46; border: 3px solid #10B981; border-radius: 16px; font-size: 40px; font-weight: 900; padding-left: 10px; }"
            "QLineEdit:focus { border: 3px solid #059669; background: #ECFDF5; }"
        )
        self.txt_monto_abono.hide()
        lay_abono.addWidget(self.txt_monto_abono, 1)

        self.btn_abono_libre = QPushButton("Cambiar")
        self.btn_abono_libre.setFixedHeight(68)
        self.btn_abono_libre.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_abono_libre.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #334155; font-size: 15px; font-weight: 800; border-radius: 14px; border: 2px solid #CBD5E1; padding: 8px 14px; }"
            "QPushButton:hover { background: #E2E8F0; }"
        )
        self.btn_abono_libre.hide()
        lay_abono.addWidget(self.btn_abono_libre)
        lay.addLayout(lay_abono)

        self.instruccion = QLabel("2. Tocá cómo paga")
        self.instruccion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruccion.setStyleSheet(
            "QLabel { color: #1E3A8A; background-color: #EFF6FF; font-size: 16px; font-weight: 800;"
            " border-radius: 10px; padding: 10px; border: 1.5px solid #BFDBFE; }"
        )
        self.instruccion.hide()
        lay.addWidget(self.instruccion)
