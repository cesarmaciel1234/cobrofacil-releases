from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QLineEdit, QVBoxLayout

from src.utils.dinero import redondear_dinero


class PanelMixtoCobro(QFrame):
    """Divide el pago en la misma pantalla. No es un cuadro aparte."""

    cambio = pyqtSignal(object)
    aviso = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = 0.0
        self._ultimo = None
        self._silencio = False
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
        caja.textChanged.connect(lambda _texto, campo=caja: self._marcar(campo))
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
        suma = redondear_dinero(sum(self._valores.values()))
        return suma + 0.001 >= redondear_dinero(self._total)

    def _numero(self, texto):
        limpio = (texto or "").strip().replace("$", "").replace(",", ".")
        if not limpio:
            return 0.0
        try:
            return redondear_dinero(limpio)
        except ValueError:
            return 0.0

    def _marcar(self, campo):
        self._ultimo = campo
        self._recalcular()

    def _claves(self):
        return (
            ("efectivo", self.txt_efectivo),
            ("tarjeta", self.txt_tarjeta),
            ("mercadopago", self.txt_mercadopago),
            ("qr", self.txt_qr),
        )

    def _recalcular(self):
        if self._silencio:
            return
        self._valores = {clave: self._numero(campo.text()) for clave, campo in self._claves()}
        activos = [clave for clave, valor in self._valores.items() if valor > 0.009]
        if len(activos) > 2 and self._ultimo is not None and self._numero(self._ultimo.text()) > 0.009:
            self._silencio = True
            self._ultimo.blockSignals(True)
            self._ultimo.clear()
            self._ultimo.blockSignals(False)
            self._silencio = False
            self.aviso.emit("El pago mixto admite solo dos medios.")
            self._valores = {clave: self._numero(campo.text()) for clave, campo in self._claves()}
        diferencia = redondear_dinero(sum(self._valores.values()) - self._total)
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
