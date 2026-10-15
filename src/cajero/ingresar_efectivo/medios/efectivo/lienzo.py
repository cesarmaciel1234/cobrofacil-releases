"""Pide el efectivo recibido. El abono es el de la ficha. No abre el cajón ni registra."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from src.utils.dinero import redondear_dinero


_QSS_OK = (
    "color: #047857; font-size: 28px; font-weight: 900; background: transparent; border: none;"
)
_QSS_MAL = (
    "color: #B91C1C; font-size: 28px; font-weight: 900; background: transparent; border: none;"
)
_QSS_BTN_OK = (
    "QPushButton { background: #10B981; color: #FFFFFF; font-size: 22px; font-weight: 900;"
    " border: none; border-radius: 14px; padding: 14px; }"
    "QPushButton:hover { background: #059669; }"
    "QPushButton:disabled { background: #CBD5E1; color: #64748B; }"
)
_QSS_BTN_VOLVER = (
    "QPushButton { background: #F1F5F9; color: #334155; font-size: 16px; font-weight: 800;"
    " border: 2px solid #CBD5E1; border-radius: 12px; padding: 10px 16px; }"
    "QPushButton:hover { background: #E2E8F0; }"
)


class LienzoEfectivo(QWidget):
    listo = pyqtSignal(float)
    volver = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._abono = 0.0
        self._cerrando = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 8)
        lay.setSpacing(10)

        self.lbl_abono = QLabel("Va a la cuenta: $0,00")
        self.lbl_abono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_abono.setStyleSheet(
            "color: #0F172A; font-size: 20px; font-weight: 900; background: #ECFDF5;"
            " border: 2px solid #A7F3D0; border-radius: 12px; padding: 10px;"
        )
        lay.addWidget(self.lbl_abono)

        self.lbl_tit = QLabel("¿Cuánto te dio en billetes?")
        self.lbl_tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_tit.setStyleSheet(
            "color: #334155; font-size: 18px; font-weight: 800; background: transparent; border: none;"
        )
        lay.addWidget(self.lbl_tit)

        self.txt = QLineEdit()
        self.txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt.setPlaceholderText("Escribí lo que te entregó")
        self.txt.setFixedHeight(76)
        self.txt.setStyleSheet(
            "QLineEdit { background: #FFFFFF; color: #0F172A; border: 3px solid #94A3B8;"
            " border-radius: 14px; font-size: 36px; font-weight: 900; }"
            "QLineEdit:focus { border-color: #2563EB; background: #F8FAFC; }"
        )
        self.txt.textChanged.connect(self._calcular)
        self.txt.returnPressed.connect(self._confirmar)
        lay.addWidget(self.txt)

        self.caja_dif = QFrame()
        self.caja_dif.setStyleSheet(
            "QFrame { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; }"
        )
        lay_dif = QVBoxLayout(self.caja_dif)
        lay_dif.setContentsMargins(12, 10, 12, 10)
        lay_dif.setSpacing(2)
        self.lbl_vuelto = QLabel("$0.00")
        self.lbl_vuelto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vuelto.setWordWrap(True)
        self.lbl_vuelto.setStyleSheet(_QSS_OK)
        lay_dif.addWidget(self.lbl_vuelto)
        lay.addWidget(self.caja_dif)

        self.btn_cobrar = QPushButton("COBRAR  ·  Enter")
        self.btn_cobrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cobrar.setFixedHeight(58)
        self.btn_cobrar.setStyleSheet(_QSS_BTN_OK)
        self.btn_cobrar.clicked.connect(self._confirmar)
        lay.addWidget(self.btn_cobrar)

        fila = QHBoxLayout()
        self.btn_volver = QPushButton("Volver  ·  Esc")
        self.btn_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_volver.setFixedHeight(44)
        self.btn_volver.setStyleSheet(_QSS_BTN_VOLVER)
        self.btn_volver.clicked.connect(self._al_volver)
        fila.addStretch()
        fila.addWidget(self.btn_volver)
        fila.addStretch()
        lay.addLayout(fila)

        self.aviso = QLabel("")
        self.aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aviso.setWordWrap(True)
        self.aviso.setStyleSheet(
            "color: #B91C1C; font-weight: 800; background: transparent; border: none;"
        )
        lay.addWidget(self.aviso)

    def arrancar(self, monto):
        self._abono = redondear_dinero(monto)
        self._cerrando = False
        self.lbl_abono.setText(f"Va a la cuenta: ${self._abono:,.2f}")
        self.txt.setText(f"{self._abono:.2f}".replace(".", ","))
        self.aviso.setText("")
        self._calcular()
        self.show()
        self.txt.setFocus()
        self.txt.selectAll()

    def cerrar(self):
        self.hide()

    def tecla(self, k):
        if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirmar()
            return True
        if k == Qt.Key.Key_Escape:
            self._al_volver()
            return True
        return False

    def _numero(self):
        texto = (self.txt.text() or "").replace("$", "").replace(" ", "").replace(",", ".")
        if not texto.strip():
            return None
        try:
            valor = redondear_dinero(float(texto))
        except ValueError:
            return None
        if valor < 0:
            return None
        return valor

    def _cubre(self):
        recibido = self._numero()
        if recibido is None:
            return False
        return recibido + 0.001 >= self._abono

    def _calcular(self):
        self.aviso.setText("")
        if not (self.txt.text() or "").strip():
            self._pintar_falta(self._abono)
            return
        recibido = self._numero()
        if recibido is None:
            self.lbl_vuelto.setText("Escribí solo el número, sin letras.")
            self.lbl_vuelto.setStyleSheet(_QSS_MAL)
            self.caja_dif.setStyleSheet(
                "QFrame { background: #FEF2F2; border: 1px solid #FECACA; border-radius: 12px; }"
            )
            self._listo_ui(False)
            return
        vuelto = redondear_dinero(recibido - self._abono)
        if vuelto < -0.001:
            self._pintar_falta(abs(vuelto))
            return
        if vuelto < 0.009:
            self.lbl_vuelto.setText("Justo. No hay vuelto.")
        else:
            self.lbl_vuelto.setText(f"Devolvé ${vuelto:,.2f}")
        self.lbl_vuelto.setStyleSheet(_QSS_OK)
        self.caja_dif.setStyleSheet(
            "QFrame { background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 12px; }"
        )
        self._listo_ui(True)

    def _pintar_falta(self, cuanto):
        self.lbl_vuelto.setText(f"Faltan ${cuanto:,.2f}. Pedí más billetes.")
        self.lbl_vuelto.setStyleSheet(_QSS_MAL)
        self.caja_dif.setStyleSheet(
            "QFrame { background: #FEF2F2; border: 1px solid #FECACA; border-radius: 12px; }"
        )
        self._listo_ui(False)

    def _listo_ui(self, listo):
        self.btn_cobrar.setEnabled(listo)
        if listo:
            self.btn_cobrar.setText("COBRAR  ·  Enter")
        else:
            self.btn_cobrar.setText("Todavía no se puede cobrar")

    def _confirmar(self):
        if self._cerrando:
            return
        if not self._cubre():
            self.aviso.setText("Tiene que alcanzar lo que va a la cuenta.")
            return
        self.aviso.setText("")
        self._cerrando = True
        self.listo.emit(self._abono)

    def _al_volver(self):
        self.cerrar()
        self.volver.emit()
