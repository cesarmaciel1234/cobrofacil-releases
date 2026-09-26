"""Monto recibido y vuelto del abono en efectivo. Abre el cajón. No abre la venta."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from src.utils.dinero import redondear_dinero


class LienzoEfectivo(QWidget):
    listo = pyqtSignal(float)
    volver = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._deuda = 0.0
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)
        self.lbl_abono = QLabel("")
        self.lbl_abono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_abono.setStyleSheet(
            "color: #64748B; font-size: 14px; font-weight: 700; background: transparent; border: none;"
        )
        lay.addWidget(self.lbl_abono)
        self.lbl_tit = QLabel("MONTO RECIBIDO")
        self.lbl_tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_tit.setStyleSheet(
            "color: #0F172A; font-size: 16px; font-weight: 800; background: transparent; border: none;"
        )
        lay.addWidget(self.lbl_tit)
        self.txt = QLineEdit()
        self.txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt.setPlaceholderText("$0.00")
        self.txt.setFixedHeight(72)
        self.txt.setStyleSheet(
            "QLineEdit { background: #FFFFFF; color: #0F172A; border: 2px solid #CBD5E1;"
            " border-radius: 12px; font-size: 32px; font-weight: 900; }"
            "QLineEdit:focus { border-color: #2563EB; }"
        )
        self.txt.textChanged.connect(self._calcular)
        self.txt.returnPressed.connect(self._confirmar)
        lay.addWidget(self.txt)
        self.lbl_vuelto_tit = QLabel("SU CAMBIO:")
        self.lbl_vuelto_tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vuelto_tit.setStyleSheet(
            "color: #64748B; font-size: 16px; font-weight: 800; background: transparent; border: none;"
        )
        lay.addWidget(self.lbl_vuelto_tit)
        self.lbl_vuelto = QLabel("$0.00")
        self.lbl_vuelto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vuelto.setStyleSheet(
            "color: #10B981; font-size: 36px; font-weight: 900; background: transparent; border: none;"
        )
        lay.addWidget(self.lbl_vuelto)
        self.aviso = QLabel("")
        self.aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aviso.setStyleSheet(
            "color: #B91C1C; font-weight: 800; background: transparent; border: none;"
        )
        lay.addWidget(self.aviso)
        confirmar = QPushButton("Confirmar")
        confirmar.setMinimumHeight(48)
        confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        confirmar.setStyleSheet(
            "QPushButton { background: #0F172A; color: white; border: none; border-radius: 12px;"
            " font-weight: 800; font-size: 14px; }"
        )
        confirmar.clicked.connect(self._confirmar)
        lay.addWidget(confirmar)
        volver = QPushButton("Volver")
        volver.setMinimumHeight(40)
        volver.setCursor(Qt.CursorShape.PointingHandCursor)
        volver.setStyleSheet(
            "QPushButton { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1;"
            " border-radius: 10px; font-weight: 800; }"
        )
        volver.clicked.connect(self._al_volver)
        lay.addWidget(volver)

    def arrancar(self, monto):
        self._deuda = redondear_dinero(monto)
        self.lbl_abono.setText(f"Abono ${self._deuda:,.2f}")
        self.txt.clear()
        self.aviso.setText("")
        self._calcular()
        self.show()
        self.txt.setFocus()
        try:
            from src.hardware.cash_drawer import drawer_manager
            drawer_manager.set_authorized(True)
            drawer_manager.abrir(autorizada=True)
        except Exception:
            pass

    def cerrar(self):
        self.hide()

    def tecla(self, k):
        if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirmar()
            return True
        return False

    def _numero(self):
        texto = (self.txt.text() or "").replace("$", "").replace(" ", "").replace(",", ".")
        if not texto.strip():
            return 0.0
        try:
            return redondear_dinero(float(texto))
        except ValueError:
            return None

    def _calcular(self):
        recibido = self._numero()
        if recibido is None:
            self.lbl_vuelto_tit.setText("FALTA:")
            self.lbl_vuelto.setText("—")
            self.lbl_vuelto.setStyleSheet(
                "color: #EF4444; font-size: 36px; font-weight: 900; background: transparent; border: none;"
            )
            return
        vuelto = redondear_dinero(recibido - self._deuda)
        if vuelto < 0:
            self.lbl_vuelto_tit.setText("FALTA:")
            self.lbl_vuelto.setText(f"${abs(vuelto):,.2f}")
            self.lbl_vuelto.setStyleSheet(
                "color: #EF4444; font-size: 36px; font-weight: 900; background: transparent; border: none;"
            )
        else:
            self.lbl_vuelto_tit.setText("SU CAMBIO:")
            self.lbl_vuelto.setText(f"${vuelto:,.2f}")
            self.lbl_vuelto.setStyleSheet(
                "color: #10B981; font-size: 36px; font-weight: 900; background: transparent; border: none;"
            )

    def _confirmar(self):
        recibido = self._numero()
        if recibido is None:
            self.aviso.setText("Hay un importe que no es un número.")
            return
        if recibido + 0.001 < self._deuda:
            self.aviso.setText("Falta dinero.")
            return
        self.aviso.setText("")
        self.listo.emit(self._deuda)

    def _al_volver(self):
        self.cerrar()
        self.volver.emit()
