from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QLineEdit, QVBoxLayout


class PanelMixtoCobro(QFrame):
    """Divide el pago en la misma pantalla. No es un cuadro aparte."""

    cambio = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = 0.0
        self._valores = {"efectivo": 0.0, "tarjeta": 0.0, "mercadopago": 0.0, "qr": 0.0}
        self.hide()
        self._armar()

    def _armar(self):
        self.setObjectName("PanelMixtoCobro")
        self.setStyleSheet(
            "QFrame#PanelMixtoCobro { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(10)

        titulo = QLabel("DIVISIÓN DE PAGOS")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet(
            "color: #1E3A8A; font-size: 16px; font-weight: 900; background: transparent; border: none;"
        )
        lay.addWidget(titulo)

        grid = QGridLayout()
        grid.setSpacing(10)
        self.txt_efectivo = self._campo("Efectivo ($)", "#10B981")
        self.txt_tarjeta = self._campo("Tarjeta ($)", "#F59E0B")
        self.txt_mercadopago = self._campo("Transferencia ($)", "#0EA5E9")
        self.txt_qr = self._campo("QR ($)", "#7C3AED")
        for fila, (rotulo, caja) in enumerate((
            ("Efectivo ($)", self.txt_efectivo),
            ("Tarjeta ($)", self.txt_tarjeta),
            ("Transferencia ($)", self.txt_mercadopago),
            ("QR ($)", self.txt_qr),
        )):
            lbl = QLabel(rotulo)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet(
                f"color: {caja.property('tono')}; font-size: 16px; font-weight: 800; "
                "background: transparent; border: none;"
            )
            grid.addWidget(lbl, fila, 0)
            grid.addWidget(caja, fila, 1)
        lay.addLayout(grid)

        self.estado = QLabel("Falta cubrir")
        self.estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado.setStyleSheet(
            "color: #E11D48; font-size: 20px; font-weight: 800; background: transparent; border: none;"
        )
        lay.addWidget(self.estado)

    def _campo(self, _nombre, color):
        caja = QLineEdit()
        caja.setProperty("tono", color)
        caja.setPlaceholderText("0.00")
        caja.setFixedHeight(52)
        caja.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caja.setStyleSheet(
            f"QLineEdit {{ background: #FFFFFF; border: 2px solid {color}; border-radius: 10px; "
            f"font-size: 22px; font-weight: 800; color: {color}; }}"
        )
        caja.textChanged.connect(self._recalcular)
        return caja

    def campos(self):
        return (self.txt_efectivo, self.txt_tarjeta, self.txt_mercadopago, self.txt_qr)

    def campo_foco(self):
        activo = self.focusWidget()
        if activo in self.campos():
            return activo
        return self.txt_efectivo

    def mostrar(self, total):
        self._total = float(total or 0)
        self._recalcular()
        self.show()
        self.txt_efectivo.setFocus()
        self.txt_efectivo.selectAll()

    def ocultar(self):
        self.hide()

    def fijar_total(self, total):
        self._total = float(total or 0)
        self._recalcular()

    def valores(self):
        return dict(self._valores)

    def cubre(self):
        suma = sum(self._valores.values())
        return suma + 0.01 >= self._total

    def _numero(self, texto):
        limpio = (texto or "").strip().replace("$", "").replace(",", ".")
        if not limpio:
            return 0.0
        try:
            return float(limpio)
        except ValueError:
            return 0.0

    def _recalcular(self):
        self._valores = {
            "efectivo": self._numero(self.txt_efectivo.text()),
            "tarjeta": self._numero(self.txt_tarjeta.text()),
            "mercadopago": self._numero(self.txt_mercadopago.text()),
            "qr": self._numero(self.txt_qr.text()),
        }
        diferencia = sum(self._valores.values()) - self._total
        if diferencia < -0.01:
            self.estado.setText(f"Falta cubrir: ${abs(diferencia):,.2f}")
            self.estado.setStyleSheet(
                "color: #E11D48; font-size: 20px; font-weight: 800; background: transparent; border: none;"
            )
        elif diferencia > 0.01:
            self.estado.setText(f"Vuelto efectivo: ${diferencia:,.2f}")
            self.estado.setStyleSheet(
                "color: #047857; font-size: 20px; font-weight: 800; background: transparent; border: none;"
            )
        else:
            self.estado.setText("Pago exacto")
            self.estado.setStyleSheet(
                "color: #1E3A8A; font-size: 20px; font-weight: 800; background: transparent; border: none;"
            )
        self.cambio.emit(self.valores())
