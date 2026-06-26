"""Fiado Express Mostrador — DNI + creación al vuelo (F12 → Fiado)."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit,
)
from PyQt6.QtCore import Qt

from src.repositories.cliente_repository import ClienteRepository, FIADO_EXPRESS_LIMITE_DEFAULT


def sonar_alarma_limite_fiado():
    """Triple beep — límite de crédito superado en mostrador."""
    import threading

    def _beep():
        try:
            import winsound
            for freq in (1200, 900, 1200):
                winsound.Beep(freq, 280)
        except Exception:
            try:
                from PyQt6.QtWidgets import QApplication
                for _ in range(3):
                    QApplication.beep()
            except Exception:
                pass

    threading.Thread(target=_beep, daemon=True).start()


class DialogoFiadoExpress(QDialog):
    """Ventana negra terminal: DNI → identificar o crear Express → confirmar fiado."""

    def __init__(self, monto_total: float, parent=None, lista_clientes=None):
        super().__init__(parent)
        self.monto_total = float(monto_total)
        self.lista_clientes = lista_clientes  # compat legacy, no usado en flujo DNI
        self.cliente_id = None
        self.cliente_nombre = ""
        self._cliente = None
        self._estado = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(560, 450)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        frame = QFrame()
        frame.setObjectName("FiadoExpressFrame")
        self.frame = frame
        frame.setStyleSheet("""
            QFrame#FiadoExpressFrame {
                background: #0a0a0a;
                border: 2px solid #22C55E;
                border-radius: 4px;
            }
            QLabel { border: none; background: transparent; color: #94A3B8; }
            QLineEdit {
                background: #111827;
                color: #F8FAFC;
                border: 2px solid #22C55E;
                border-radius: 4px;
                padding: 10px 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 18px;
                font-weight: 700;
            }
            QLineEdit:disabled {
                color: #64748B;
                border-color: #334155;
            }
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        tit = QLabel("⚡  FIADO EXPRESS MOSTRADOR")
        tit.setStyleSheet(
            "color: #22C55E; font-size: 16px; font-weight: 900; "
            "font-family: 'Consolas', monospace; letter-spacing: 1px;"
        )
        lay.addWidget(tit)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #334155; border: none;")
        lay.addWidget(sep)

        hint = QLabel(
            f"Fiado rápido por DNI. Clientes nuevos: límite ${FIADO_EXPRESS_LIMITE_DEFAULT:,.0f}. "
            "Si supera el cupo, suena alarma — el admin puede ampliar el límite."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #64748B; font-size: 11px; font-family: 'Segoe UI';")
        lay.addWidget(hint)

        lbl_dni = QLabel("DNI DEL CLIENTE (MANDATORIO) — luego pulse CARGAR")
        lbl_dni.setStyleSheet("color: #CBD5E1; font-size: 11px; font-weight: 700;")
        lay.addWidget(lbl_dni)

        dni_row = QHBoxLayout()
        dni_row.setSpacing(10)
        self.txt_dni = QLineEdit()
        self.txt_dni.setPlaceholderText("Ej: 12345678")
        self.txt_dni.returnPressed.connect(self._verificar_dni)
        dni_row.addWidget(self.txt_dni, stretch=1)

        self.btn_cargar = QPushButton("CARGAR")
        self.btn_cargar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cargar.setFixedWidth(120)
        self.btn_cargar.setFixedHeight(44)
        self.btn_cargar.setStyleSheet(
            "QPushButton { background: #22C55E; color: #0a0a0a; border: none; "
            "font-weight: 900; font-size: 14px; border-radius: 4px; "
            "font-family: 'Consolas', monospace; }"
            "QPushButton:hover { background: #16A34A; color: white; }"
            "QPushButton:pressed { background: #15803D; }"
        )
        self.btn_cargar.clicked.connect(self._verificar_dni)
        dni_row.addWidget(self.btn_cargar)
        lay.addLayout(dni_row)

        self.lbl_cliente = QLabel("")
        self.lbl_cliente.setWordWrap(True)
        self.lbl_cliente.setStyleSheet(
            "color: #38BDF8; font-size: 14px; font-weight: 700; "
            "font-family: 'Consolas', monospace; min-height: 22px;"
        )
        lay.addWidget(self.lbl_cliente)

        lbl_m = QLabel("MONTO DE LA VENTA ($)")
        lbl_m.setStyleSheet("color: #CBD5E1; font-size: 11px; font-weight: 700;")
        lay.addWidget(lbl_m)

        self.txt_monto = QLineEdit(f"{self.monto_total:,.2f}")
        self.txt_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_monto.setReadOnly(True)
        self.txt_monto.setEnabled(False)
        lay.addWidget(self.txt_monto)

        self.lbl_err = QLabel("")
        self.lbl_err.setWordWrap(True)
        self.lbl_err.setStyleSheet("color: #F87171; font-size: 12px; font-weight: 700;")
        lay.addWidget(self.lbl_err)

        self.lbl_alerta = QLabel("")
        self.lbl_alerta.setWordWrap(True)
        self.lbl_alerta.setStyleSheet("color: #FBBF24; font-size: 12px; font-weight: 700;")
        lay.addWidget(self.lbl_alerta)

        lay.addStretch()

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("CANCELAR")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(
            "QPushButton { background: transparent; color: #EF4444; border: 2px solid #EF4444; "
            "font-weight: 900; padding: 10px 20px; border-radius: 4px; "
            "font-family: 'Consolas', monospace; }"
            "QPushButton:hover { background: #450a0a; }"
        )
        btn_cancel.clicked.connect(self.reject)

        self.btn_ok = QPushButton("CONFIRMAR FIADO")
        self.btn_ok.setEnabled(False)
        self.btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ok.setStyleSheet(
            "QPushButton { background: #22C55E; color: #0a0a0a; border: none; "
            "font-weight: 900; padding: 10px 20px; border-radius: 4px; "
            "font-family: 'Consolas', monospace; font-size: 13px; }"
            "QPushButton:hover { background: #16A34A; color: white; }"
            "QPushButton:disabled { background: #1E293B; color: #475569; border: 1px solid #334155; }"
        )
        self.btn_ok.clicked.connect(self._confirmar)
        self.btn_ok.setDefault(True)

        btns.addWidget(btn_cancel)
        btns.addSpacing(12)
        btns.addWidget(self.btn_ok)
        lay.addLayout(btns)

        root.addWidget(frame)
        self.txt_dni.setFocus()

    def _verificar_dni(self):
        self.lbl_err.clear()
        self.lbl_alerta.clear()
        self.lbl_cliente.setText("Consultando…")
        self.lbl_cliente.setStyleSheet(
            "color: #94A3B8; font-size: 14px; font-weight: 700; font-family: 'Consolas', monospace;"
        )
        self.btn_ok.setEnabled(False)
        self.btn_cargar.setEnabled(False)
        self.btn_cargar.setText("…")

        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        cliente, estado, msg = ClienteRepository.verificar_y_crear_cliente(self.txt_dni.text())
        self.btn_cargar.setEnabled(True)
        self.btn_cargar.setText("CARGAR")

        if estado == "error" or not cliente:
            self._cliente = None
            self.lbl_cliente.clear()
            self.lbl_err.setText(msg)
            return

        self._cliente = cliente
        self._estado = estado
        disp = ClienteRepository.credito_disponible(cliente)

        if estado == "identificado":
            self.lbl_cliente.setText(f"✓  {cliente['nombre']}")
            self.lbl_cliente.setStyleSheet(
                "color: #38BDF8; font-size: 14px; font-weight: 700; font-family: 'Consolas', monospace;"
            )
        else:
            self.lbl_cliente.setText(f"✚  {msg}  (registrado en Clientes)")
            self.lbl_cliente.setStyleSheet(
                "color: #22C55E; font-size: 14px; font-weight: 700; font-family: 'Consolas', monospace;"
            )

        if ClienteRepository.limite_credito_excedido(cliente, self.monto_total):
            limite = float(cliente.get("limite_credito", 0))
            sonar_alarma_limite_fiado()
            self.lbl_err.setText(
                f"⛔ LÍMITE SUPERADO — Cupo ${limite:,.0f}, disponible ${disp:,.2f}. "
                f"Venta ${self.monto_total:,.2f}. Pida al admin ampliar límite."
            )
            self.frame.setStyleSheet("""
                QFrame#FiadoExpressFrame {
                    background: #0a0a0a;
                    border: 2px solid #EF4444;
                    border-radius: 4px;
                }
                QLabel { border: none; background: transparent; color: #94A3B8; }
                QLineEdit {
                    background: #111827; color: #F8FAFC; border: 2px solid #EF4444;
                    border-radius: 4px; padding: 10px 12px;
                    font-family: 'Consolas', monospace; font-size: 18px; font-weight: 700;
                }
            """)
            self.btn_ok.setEnabled(False)
            return

        self.frame.setStyleSheet("""
            QFrame#FiadoExpressFrame {
                background: #0a0a0a;
                border: 2px solid #22C55E;
                border-radius: 4px;
            }
            QLabel { border: none; background: transparent; color: #94A3B8; }
            QLineEdit {
                background: #111827; color: #F8FAFC; border: 2px solid #22C55E;
                border-radius: 4px; padding: 10px 12px;
                font-family: 'Consolas', monospace; font-size: 18px; font-weight: 700;
            }
            QLineEdit:disabled { color: #64748B; border-color: #334155; }
        """)

        self.lbl_alerta.setText(f"Crédito disponible: ${disp:,.2f} / límite ${float(cliente.get('limite_credito', 0)):,.0f}")
        self.lbl_alerta.setStyleSheet("color: #34D399; font-size: 12px; font-weight: 700;")

        self.btn_ok.setEnabled(True)
        self.btn_ok.setFocus()

    def _confirmar(self):
        if not self._cliente:
            self._verificar_dni()
            if not self._cliente or not self.btn_ok.isEnabled():
                return
        self.cliente_id = self._cliente["id"]
        self.cliente_nombre = self._cliente["nombre"]
        self.accept()

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key.Key_Escape:
            self.reject()
        elif k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.focusWidget() == self.txt_dni or not self._cliente:
                self._verificar_dni()
            elif self.btn_ok.isEnabled():
                self._confirmar()
        else:
            super().keyPressEvent(event)
