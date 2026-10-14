"""F6: solo cobranza de cuentas. No abre ingreso de caja."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QDialog, QFrame, QVBoxLayout

from src.cajero.f6_centro_cobranzas.panel import CentroCobranzasPanel


class DialogoCentroCobranzas(QDialog):
    def __init__(self, parent=None, perfil="Cajero"):
        super().__init__(parent)
        self._perfil = (perfil or "Cajero").strip() or "Cajero"
        self.tipo_ingreso = "COBRANZA"
        self.monto_ingresado = 0.0
        self.cliente_id = None
        self.cliente_nombre = ""
        self.deuda_actual = 0.0
        self.resultado = None
        self.motivo = ""

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._armar()
        self._atajo_f9 = QShortcut(QKeySequence(Qt.Key.Key_F9), self)
        self._atajo_f9.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._atajo_f9.activated.connect(self._f9)

    def showEvent(self, event):
        from src.utils.fondo_gris import cubrir
        cubrir(self)
        self._ajustar_pagina()
        super().showEvent(event)

    def paintEvent(self, event):
        from src.utils.fondo_gris import pintar
        pintar(self)

    def _armar(self):
        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(0, 0, 0, 0)
        exterior.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hoja = QFrame()
        hoja.setObjectName("HojaF6")
        hoja.setStyleSheet(
            "QFrame#HojaF6 { background: #FFFFFF; border: 2px solid #E2E8F0; border-radius: 18px; }"
        )
        caja = QVBoxLayout(hoja)
        caja.setContentsMargins(12, 12, 12, 12)
        self.panel = CentroCobranzasPanel(perfil=self._perfil)
        self.panel.abono_registrado.connect(self._on_abono)
        self.panel.cancelado.connect(self.reject)
        caja.addWidget(self.panel)
        exterior.addWidget(hoja)
        self.hoja = hoja

    def _ajustar_pagina(self):
        ancho = max(400, min(1050, self.width() - 64))
        alto = max(400, min(800, self.height() - 40))
        self.hoja.setFixedSize(ancho, alto)

    def abrir_para_cliente(self, cliente, monto_sugerido=None):
        ficha = dict(cliente) if hasattr(cliente, "keys") else {}
        self.panel.seleccionar_cliente_directo(ficha, monto_sugerido)

    def _on_abono(self, resultado):
        self.resultado = resultado
        self.monto_ingresado = getattr(resultado, "monto", 0.0)
        self.cliente_id = getattr(resultado, "cliente_id", None)
        self.cliente_nombre = getattr(resultado, "nombre", "")
        self.deuda_actual = float(getattr(self.panel, "_deuda_actual", 0.0) or 0.0)
        self.motivo = f"Cobranza cuenta corriente: {self.cliente_nombre}"
        self.accept()

    def _f9(self):
        if hasattr(self.panel, "procesar_f9"):
            self.panel.procesar_f9()

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key.Key_F9:
            self._f9()
            event.accept()
            return
        if k == Qt.Key.Key_Escape:
            if hasattr(self.panel, "eventFilter"):
                if self.panel.eventFilter(None, event):
                    event.accept()
                    return
            self.panel.keyPressEvent(event)
            event.accept()
            return
        if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if hasattr(self.panel, "procesar_enter"):
                self.panel.procesar_enter()
            event.accept()
            return
        if hasattr(self.panel, "tecla") and self.panel.tecla(k):
            event.accept()
            return
        super().keyPressEvent(event)
