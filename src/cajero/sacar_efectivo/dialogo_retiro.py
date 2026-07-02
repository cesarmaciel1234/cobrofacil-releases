"""Diálogo de Retiro de Efectivo (F5) — Estilo global premium."""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
from PyQt6.QtCore import Qt, QTimer


class DialogoRetiroEfectivo(QDialog):
    """Diálogo industrial rápido para retirar efectivo de caja (F5)."""
    def __init__(self, efectivo_actual, parent=None):
        super().__init__(parent)
        self.efectivo_actual = efectivo_actual
        self.monto_retirado = 0.0
        self.motivo = ""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(420, 400)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 3px solid #1E3A8A; border-radius: 18px; }"
        )
        outer.addWidget(card)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.setSpacing(10)

        lbl = QLabel("💸  RETIRO DE EFECTIVO")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 20px; font-weight: 900; color: #1E3A8A; border: none; background: transparent;")
        lay.addWidget(lbl)

        lbl_disp = QLabel(f"Disponible en Caja: ${self.efectivo_actual:,.2f}")
        lbl_disp.setAlignment(Qt.AlignCenter)
        lbl_disp.setStyleSheet("font-size: 13px; color: #64748b; font-weight: bold; border: none; background: transparent;")
        lay.addWidget(lbl_disp)

        lbl2 = QLabel("Monto a retirar ($):")
        lbl2.setStyleSheet("font-size: 13px; color: #334155; font-weight: bold; border: none; background: transparent;")
        lay.addWidget(lbl2)

        self.txt_monto = QLineEdit()
        self.txt_monto.setAlignment(Qt.AlignCenter)
        sugerido = max(0.0, self.efectivo_actual - 40000) if self.efectivo_actual > 50000 else 0.0
        if sugerido > 0:
            self.txt_monto.setText(f"{int(sugerido)}")
        self.txt_monto.setStyleSheet("""
            QLineEdit {
                font-size: 32px; font-weight: 900; color: #DC2626;
                border: 2px solid #cbd5e1; border-radius: 10px;
                padding: 6px; background: #f8fafc;
            }
            QLineEdit:focus { border-color: #1E3A8A; }
        """)
        lay.addWidget(self.txt_monto)

        lbl_m = QLabel("Motivo / Descripción (Opcional):")
        lbl_m.setStyleSheet("font-size: 13px; color: #334155; font-weight: bold; border: none; background: transparent;")
        lay.addWidget(lbl_m)

        self.txt_motivo = QLineEdit()
        self.txt_motivo.setPlaceholderText("Ej: Pago proveedor, Viáticos...")
        self.txt_motivo.setStyleSheet("""
            QLineEdit {
                font-size: 14px; color: #1E293B; font-weight: 600;
                border: 2px solid #cbd5e1; border-radius: 8px;
                padding: 8px; background: #f8fafc;
            }
            QLineEdit:focus { border-color: #1E3A8A; background: white; }
        """)
        self.txt_motivo.returnPressed.connect(self._procesar)
        self.txt_monto.returnPressed.connect(self.txt_motivo.setFocus)
        lay.addWidget(self.txt_motivo)

        self.lbl_err = QLabel("")
        self.lbl_err.setAlignment(Qt.AlignCenter)
        self.lbl_err.setStyleSheet("font-size: 12px; color: #DC2626; font-weight: bold; border: none; background: transparent;")
        lay.addWidget(self.lbl_err)

        h_btns = QHBoxLayout()
        h_btns.setSpacing(14)

        btn_cancel = QPushButton("  ESC  Cancelar")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: bold; "
            "font-size: 14px; padding: 12px 20px; border-radius: 10px; border: none; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("💸 RETIRAR")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet(
            "QPushButton { background: #DC2626; color: white; font-weight: 900; "
            "font-size: 14px; padding: 12px 20px; border-radius: 10px; border: none; }"
            "QPushButton:hover { background: #B91C1C; }"
        )
        btn_ok.clicked.connect(self._procesar)

        h_btns.addWidget(btn_cancel, 1)
        h_btns.addWidget(btn_ok, 1)
        lay.addLayout(h_btns)

        QTimer.singleShot(100, self.txt_monto.setFocus)
        QTimer.singleShot(120, self.txt_monto.selectAll)

    def _procesar(self):
        try:
            val = float(self.txt_monto.text().strip())
            if val <= 0:
                self.lbl_err.setText("⚠️ Ingresa un monto mayor a 0")
                return
            if val > self.efectivo_actual:
                self.lbl_err.setText("⚠️ No hay suficiente efectivo en caja")
                return
            self.monto_retirado = val
            mot = self.txt_motivo.text().strip()
            self.motivo = mot if mot else "Retiro rápido de efectivo en terminal"
            self.accept()
        except ValueError:
            self.lbl_err.setText("⚠️ Monto inválido")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._procesar()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
