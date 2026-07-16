"""Cliente Express Mostrador — Nombre doble confirmación en dos ventanas (F12 → Clientes)."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QApplication,
)
from PyQt6.QtCore import Qt

from src.repositories.cliente_repository import ClienteRepository, FIADO_EXPRESS_LIMITE_DEFAULT


def sonar_alarma_limite_fiado():
    """Triple beep — límite de crédito superado."""
    import threading

    def _beep():
        try:
            import winsound
            for freq in (1200, 900, 1200):
                winsound.Beep(freq, 280)
        except Exception:
            try:
                for _ in range(3):
                    QApplication.beep()
            except Exception:
                pass

    threading.Thread(target=_beep, daemon=True).start()


def sonar_dni_no_coincide():
    import threading

    def _beep():
        try:
            import winsound
            winsound.Beep(400, 400)
        except Exception:
            try:
                QApplication.beep()
            except Exception:
                pass

    threading.Thread(target=_beep, daemon=True).start()


class _FiadoExpressBase(QDialog):
    _FRAME_OK = """
        QFrame#FiadoExpressFrame {
            background: #0a0a0a; border: 2px solid #22C55E; border-radius: 4px;
        }
        QLabel { border: none; background: transparent; color: #94A3B8; }
        QLineEdit {
            background: #111827; color: #F8FAFC; border: 2px solid #22C55E;
            border-radius: 4px; padding: 10px 12px;
            font-family: 'Consolas', monospace; font-size: 18px; font-weight: 700;
        }
        QLineEdit:disabled { color: #64748B; border-color: #334155; }
    """
    _FRAME_ERR = """
        QFrame#FiadoExpressFrame {
            background: #0a0a0a; border: 2px solid #EF4444; border-radius: 4px;
        }
        QLabel { border: none; background: transparent; color: #94A3B8; }
        QLineEdit {
            background: #111827; color: #F8FAFC; border: 2px solid #EF4444;
            border-radius: 4px; padding: 10px 12px;
            font-family: 'Consolas', monospace; font-size: 18px; font-weight: 700;
        }
    """
    _FRAME_WARN = """
        QFrame#FiadoExpressFrame {
            background: #0a0a0a; border: 2px solid #FBBF24; border-radius: 4px;
        }
        QLabel { border: none; background: transparent; color: #94A3B8; }
        QLineEdit {
            background: #111827; color: #F8FAFC; border: 2px solid #FBBF24;
            border-radius: 4px; padding: 10px 12px;
            font-family: 'Consolas', monospace; font-size: 18px; font-weight: 700;
        }
    """

    def __init__(self, monto_total: float, parent=None):
        super().__init__(parent)
        self.monto_total = float(monto_total)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(620, 680)

    @staticmethod
    def _hint_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #64748B; font-size: 11px; font-family: 'Segoe UI';")
        return lbl

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #CBD5E1; font-size: 11px; font-weight: 700;")
        return lbl

    @staticmethod
    def _btn_verde() -> str:
        return (
            "QPushButton { background: #22C55E; color: #0a0a0a; border: none; "
            "font-weight: 900; font-size: 14px; border-radius: 4px; font-family: 'Consolas', monospace; }"
            "QPushButton:hover { background: #16A34A; color: white; }"
        )

    def _monto_readonly(self) -> QLineEdit:
        monto = QLineEdit(f"{self.monto_total:,.2f}")
        monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        monto.setReadOnly(True)
        monto.setEnabled(False)
        return monto


class DialogoClienteExpressPaso1(_FiadoExpressBase):
    """Paso 1 sobre pantalla de cobro: NOMBRE + CARGAR → cierra y pasa a confirmación."""

    def __init__(self, monto_total: float, parent=None):
        super().__init__(monto_total, parent)
        self.cliente = None
        self.cliente_id = None
        self.cliente_nombre = ""
        self.nombre_ref = ""
        self.confirmado = False
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        self.frame = QFrame()
        self.frame.setObjectName("FiadoExpressFrame")
        self.frame.setStyleSheet(self._FRAME_OK)
        outer = QVBoxLayout(self.frame)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(10)

        tit = QLabel("⚡  CLIENTE EXPRESS MOSTRADOR")
        tit.setStyleSheet(
            "color: #22C55E; font-size: 16px; font-weight: 900; "
            "font-family: 'Consolas', monospace; letter-spacing: 1px;"
        )
        outer.addWidget(tit)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #334155; border: none;")
        outer.addWidget(sep)

        body = QVBoxLayout()
        body.setContentsMargins(0, 8, 0, 0)
        body.setSpacing(12)

        body.addWidget(self._hint_label(
            f"Paso 1 — Ingrese el NOMBRE DEL CLIENTE y pulse CARGAR. Clientes nuevos: límite $50,000."
        ))
        body.addWidget(self._section_label("NOMBRE DEL CLIENTE (MANDATORIO) — luego pulse CARGAR"))

        row = QHBoxLayout()
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Juan Perez")
        self.txt_nombre.returnPressed.connect(self._cargar)
        row.addWidget(self.txt_nombre, stretch=1)

        self.btn_cargar = QPushButton("CARGAR")
        self.btn_cargar.setFixedSize(120, 44)
        self.btn_cargar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cargar.setStyleSheet(self._btn_verde())
        self.btn_cargar.clicked.connect(self._cargar)
        row.addWidget(self.btn_cargar)
        body.addLayout(row)

        self.lbl_cliente = QLabel("")
        self.lbl_cliente.setWordWrap(True)
        self.lbl_cliente.setStyleSheet(
            "color: #38BDF8; font-size: 14px; font-weight: 700; font-family: 'Consolas', monospace; min-height: 22px;"
        )
        body.addWidget(self.lbl_cliente)

        body.addWidget(self._section_label("MONTO DE LA VENTA ($)"))
        body.addWidget(self._monto_readonly())

        self.lbl_err = QLabel("")
        self.lbl_err.setWordWrap(True)
        self.lbl_err.setStyleSheet("color: #F87171; font-size: 12px; font-weight: 700;")
        body.addWidget(self.lbl_err)
        body.addStretch()

        outer.addLayout(body, stretch=1)

        foot = QHBoxLayout()
        foot.addStretch()
        btn_cancel = QPushButton("CANCELAR")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(
            "QPushButton { background: transparent; color: #EF4444; border: 2px solid #EF4444; "
            "font-weight: 900; padding: 10px 20px; border-radius: 4px; font-family: 'Consolas', monospace; }"
            "QPushButton:hover { background: #450a0a; }"
        )
        btn_cancel.clicked.connect(self.reject)
        foot.addWidget(btn_cancel)
        outer.addLayout(foot)

        root.addWidget(self.frame)
        self.txt_nombre.setFocus()

    def _cargar(self):
        self.lbl_err.clear()
        self.lbl_cliente.setText("Consultando…")
        self.btn_cargar.setEnabled(False)
        self.btn_cargar.setText("…")
        QApplication.processEvents()

        nombre_ingresado = self.txt_nombre.text().strip()
        if not nombre_ingresado:
            self.lbl_cliente.clear()
            self.lbl_err.setText("Ingrese un nombre válido")
            self.btn_cargar.setEnabled(True)
            self.btn_cargar.setText("CARGAR")
            return

        cliente, estado, msg = ClienteRepository.verificar_y_crear_por_nombre(nombre_ingresado)
        self.btn_cargar.setEnabled(True)
        self.btn_cargar.setText("CARGAR")

        if estado == "error" or not cliente:
            self.cliente = None
            self.lbl_cliente.clear()
            self.lbl_err.setText(msg)
            self.frame.setStyleSheet(self._FRAME_ERR)
            return

        disp = ClienteRepository.credito_disponible(cliente)
        if ClienteRepository.limite_credito_excedido(cliente, self.monto_total):
            limite = float(dict(cliente).get("limite_credito", 0))
            sonar_alarma_limite_fiado()
            self.lbl_cliente.clear()
            self.lbl_err.setText(
                f"⛔ LÍMITE SUPERADO — Cupo ${limite:,.0f}, disponible ${disp:,.2f}. "
                f"Venta ${self.monto_total:,.2f}."
            )
            self.frame.setStyleSheet(self._FRAME_ERR)
            return

        self.cliente = cliente
        self.nombre_ref = nombre_ingresado
        self.cliente_id = cliente["id"]
        self.cliente_nombre = cliente["nombre"]
        self.frame.setStyleSheet(self._FRAME_OK)
        self.confirmado = True
        self.accept()

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key.Key_Escape:
            self.reject()
        elif k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._cargar()
        else:
            super().keyPressEvent(event)


class DialogoClienteExpressPaso2(_FiadoExpressBase):
    """Paso 2 sobre el mostrador (paso6 oculto): repetir NOMBRE y confirmar fiado."""

    def __init__(self, monto_total: float, cliente: dict, nombre_ref: str, parent=None):
        super().__init__(monto_total, parent)
        self.cliente = cliente
        self.nombre_ref = nombre_ref
        self.nombre_esperado = nombre_ref
        self.cliente_id = cliente["id"]
        self.cliente_nombre = dict(cliente).get("nombre", "")
        self.confirmado = False
        self._nombre_verificado = False
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        self.frame = QFrame()
        self.frame.setObjectName("FiadoExpressFrame")
        self.frame.setStyleSheet(self._FRAME_WARN)
        outer = QVBoxLayout(self.frame)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(10)

        tit = QLabel("⚡  CLIENTE EXPRESS — VERIFICACIÓN FINAL")
        tit.setStyleSheet(
            "color: #FBBF24; font-size: 16px; font-weight: 900; "
            "font-family: 'Consolas', monospace; letter-spacing: 1px;"
        )
        outer.addWidget(tit)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #334155; border: none;")
        outer.addWidget(sep)

        body = QVBoxLayout()
        body.setContentsMargins(0, 8, 0, 0)
        body.setSpacing(12)

        body.addWidget(self._hint_label(
            "Paso 2 — El cliente debe repetir su NOMBRE. Debe coincidir con el paso anterior."
        ))

        nombre = dict(self.cliente).get("nombre", "")
        disp = ClienteRepository.credito_disponible(self.cliente)
        limite = float(dict(self.cliente).get("limite_credito", 0))

        lbl_cli = QLabel(f"Cliente: {nombre}")
        lbl_cli.setWordWrap(True)
        lbl_cli.setStyleSheet(
            "color: #38BDF8; font-size: 15px; font-weight: 800; font-family: 'Consolas', monospace;"
        )
        body.addWidget(lbl_cli)

        body.addWidget(self._section_label("VERIFICACIÓN DE NOMBRE (VUELVA A CARGAR)"))

        row = QHBoxLayout()
        self.txt_nombre2 = QLineEdit()
        self.txt_nombre2.setPlaceholderText("Reingrese Nombre")
        self.txt_nombre2.returnPressed.connect(self._verificar)
        row.addWidget(self.txt_nombre2, stretch=1)

        btn_verificar = QPushButton("VERIFICAR")
        btn_verificar.setFixedSize(120, 44)
        btn_verificar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_verificar.setStyleSheet(self._btn_verde())
        btn_verificar.clicked.connect(self._verificar)
        row.addWidget(btn_verificar)
        body.addLayout(row)

        self.lbl_ok = QLabel("")
        self.lbl_ok.setStyleSheet("color: #22C55E; font-size: 13px; font-weight: 800;")
        body.addWidget(self.lbl_ok)

        body.addWidget(self._section_label("MONTO DE LA VENTA ($)"))
        body.addWidget(self._monto_readonly())

        lbl_credito = QLabel(f"Crédito disponible: ${disp:,.2f} / límite ${limite:,.0f}")
        lbl_credito.setStyleSheet("color: #34D399; font-size: 12px; font-weight: 700;")
        body.addWidget(lbl_credito)

        self.lbl_err = QLabel("")
        self.lbl_err.setWordWrap(True)
        self.lbl_err.setStyleSheet("color: #F87171; font-size: 12px; font-weight: 700;")
        body.addWidget(self.lbl_err)
        body.addStretch()

        outer.addLayout(body, stretch=1)

        foot = QHBoxLayout()
        foot.addStretch()
        btn_cancel = QPushButton("CANCELAR")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(
            "QPushButton { background: transparent; color: #EF4444; border: 2px solid #EF4444; "
            "font-weight: 900; padding: 10px 20px; border-radius: 4px; font-family: 'Consolas', monospace; }"
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
        foot.addWidget(btn_cancel)
        foot.addSpacing(12)
        foot.addWidget(self.btn_ok)
        outer.addLayout(foot)

        root.addWidget(self.frame)
        self.txt_nombre2.setFocus()

    def _verificar(self):
        self.lbl_err.clear()
        self.lbl_ok.clear()
        self.btn_ok.setEnabled(False)
        self._nombre_verificado = False

        nombre2 = self.txt_nombre2.text().strip()
        if not nombre2:
            self.lbl_err.setText("Ingrese el nombre nuevamente")
            return

        if nombre2.lower() != self.nombre_esperado.lower():
            sonar_dni_no_coincide()
            self.lbl_err.setText(f"❌ ¡EL NOMBRE NO COINCIDE! (Esperaba: {self.nombre_esperado})")
            self.frame.setStyleSheet(self._FRAME_ERR)
            return

        self._nombre_verificado = True
        self.lbl_ok.setText("✓ Nombre verificado — puede confirmar el fiado")
        self.frame.setStyleSheet(self._FRAME_OK)
        self.btn_ok.setEnabled(True)
        self.btn_ok.setFocus()

    def _volver_otro_dni(self):
        self.reintentar_dni = True
        self.reject()

    def _confirmar(self):
        if not self._nombre_verificado:
            self._verificar()
            if not self._nombre_verificado:
                return
        self.confirmado = True
        self.accept()

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key.Key_Escape:
            self.reject()
        elif k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not self._nombre_verificado:
                self._verificar()
            elif self.btn_ok.isEnabled():
                self._confirmar()
        else:
            super().keyPressEvent(event)


def abrir_cliente_express(parent_widget, monto_total: float):
    """
    Controlador principal Cliente Express (2 ventanas modales).
    Retorna el dict del cliente si la transacción debe completarse, None si se cancela.
    """
    dlg1 = DialogoClienteExpressPaso1(monto_total, parent_widget)
    dlg1.exec()

    if not dlg1.confirmado:
        return None

    # Pasó el primer paso
    cliente_seleccionado = dlg1.cliente
    nombre_esperado = dlg1.nombre_ref

    dlg2 = DialogoClienteExpressPaso2(monto_total, cliente_seleccionado, nombre_esperado, parent_widget)
    dlg2.exec()

    if dlg2.confirmado:
        return cliente_seleccionado
    
    return None
