"""Diálogo de Ingreso de Dinero (F6) — Estilo global premium, exclusivo para FIADO."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame,
)
from PyQt6.QtCore import Qt, QTimer


class DialogoIngresoEfectivo(QDialog):
    """Diálogo premium para ingresar abonos de fiado (F6)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monto_ingresado = 0.0
        self.motivo = ""
        self.tipo_ingreso = "FIADO"
        self.cliente_id = None
        self.cliente_nombre = ""
        self.en_venta = False
        self.deuda_actual = 0.0

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        from src.cajero.ingresar_efectivo.paso5cobranza import (
            COBRANZA_DIALOG_ANCHO, COBRANZA_DIALOG_ALTO_FIADO,
            _EXEC,
        )
        self._ancho = COBRANZA_DIALOG_ANCHO
        self._altura = COBRANZA_DIALOG_ALTO_FIADO
        self._EXEC = _EXEC
        
        self.setFixedSize(self._ancho, self._altura)
        self._build()
        
        # Cargar deudores de inicio
        self.panel_fiado.cargar_clientes_abono()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame()
        self._card.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 3px solid #1E3A8A; border-radius: 18px; }"
        )
        outer.addWidget(self._card)

        lay = QVBoxLayout(self._card)
        lay.setContentsMargins(10, 10, 10, 20)
        lay.setSpacing(10)

        from src.cajero.ingresar_efectivo.paso5cobranza import CentroCobranzasPanel
        self.panel_fiado = CentroCobranzasPanel()
        if self.panel_fiado.txt_monto is not None:
            self.panel_fiado.txt_monto.returnPressed.connect(self._procesar)
        lay.addWidget(self.panel_fiado)

        self.lbl_err = QLabel("")
        self.lbl_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_err.setStyleSheet("font-size: 12px; color: #DC2626; font-weight: bold; border: none;")
        lay.addWidget(self.lbl_err)

        h_btns = QHBoxLayout()
        h_btns.setContentsMargins(20, 0, 20, 0)
        h_btns.setSpacing(14)

        btn_cancel = QPushButton("  ESC  Cancelar")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(
            "QPushButton { background: #DC2626; color: white; font-weight: bold; "
            "font-size: 14px; padding: 12px 20px; border-radius: 10px; border: none; }"
            "QPushButton:hover { background: #B91C1C; }"
        )
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("✅ CONFIRMAR")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: 900; font-size: 14px; "
            "padding: 12px 20px; border-radius: 10px; border: none; letter-spacing: 1px; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_ok.clicked.connect(self._procesar)

        h_btns.addWidget(btn_cancel, 1)
        h_btns.addWidget(btn_ok, 1)
        lay.addLayout(h_btns)

    def _procesar(self):
        ok, err = self.panel_fiado.validar()
        if not ok:
            self.lbl_err.setText(err)
            return
        data = self.panel_fiado.cliente_actual()
        self.monto_ingresado = self.panel_fiado.monto()
        self.deuda_actual = self.panel_fiado.deuda_actual()
        self.cliente_id = data["id"]
        self.cliente_nombre = data["nombre"]
        self.tipo_ingreso = "FIADO"
        self.motivo = f"Abono Fiado: {self.cliente_nombre}"
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._procesar()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
