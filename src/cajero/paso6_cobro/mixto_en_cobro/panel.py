from PyQt6.QtCore import Qt, QEvent, pyqtSignal
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
        self._cerrado = False
        self._hechos = set()
        self._marcas = {}
        self._valores = {
            "efectivo": 0.0, "tarjeta": 0.0, "mercadopago": 0.0, "qr": 0.0, "cliente": 0.0,
        }
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
        self.txt_cliente = self._campo("Cliente ($)", "#1D4ED8")
        for fila, (clave, rotulo, caja) in enumerate((
            ("efectivo", "Efectivo ($)", self.txt_efectivo),
            ("tarjeta", "Tarjeta ($)", self.txt_tarjeta),
            ("mercadopago", "Transferencia ($)", self.txt_mercadopago),
            ("qr", "QR ($)", self.txt_qr),
            ("cliente", "Cliente ($)", self.txt_cliente),
        )):
            lbl = QLabel(rotulo)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet(
                f"color: {caja.property('tono')}; font-size: 16px; font-weight: 800; "
                "background: transparent; border: none;"
            )
            marca = QLabel("")
            marca.setFixedWidth(28)
            marca.setAlignment(Qt.AlignmentFlag.AlignCenter)
            marca.setStyleSheet(
                "color: #047857; font-size: 26px; font-weight: 900; background: transparent; border: none;"
            )
            self._marcas[clave] = marca
            grid.addWidget(lbl, fila, 0)
            grid.addWidget(caja, fila, 1)
            grid.addWidget(marca, fila, 2)
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
        caja.installEventFilter(self)
        return caja

    def campos(self):
        return (self.txt_efectivo, self.txt_tarjeta, self.txt_mercadopago, self.txt_qr, self.txt_cliente)

    def campo_foco(self):
        activo = self.focusWidget()
        if activo in self.campos():
            return activo
        return self.txt_efectivo

    def vaciar(self):
        """Sin importes de la venta anterior. Volver o F12 no reutiliza el mixto."""
        self._silencio = True
        try:
            self._cerrado = False
            self._hechos.clear()
            self._ultimo = None
            for clave, caja in self._claves():
                caja.setReadOnly(False)
                caja.blockSignals(True)
                caja.clear()
                caja.blockSignals(False)
                marca = self._marcas.get(clave)
                if marca is not None:
                    marca.setText("")
            self._valores = {clave: 0.0 for clave, _caja in self._claves()}
            self.estado.setText("Falta cubrir")
            self.estado.setStyleSheet(
                "color: #E11D48; font-size: 20px; font-weight: 800; background: transparent; border: none;"
            )
        finally:
            self._silencio = False

    def mostrar(self, total):
        self.vaciar()
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

    def cerrar_reparto(self):
        """Enter ya mandó a cobrar: no se tocan los importes."""
        self._cerrado = True
        for _clave, caja in self._claves():
            caja.setReadOnly(True)

    def abrir_reparto(self):
        self._cerrado = False
        for clave, caja in self._claves():
            caja.setReadOnly(clave in self._hechos)

    def marcar_hecho(self, clave):
        if clave not in self._marcas:
            return
        self._hechos.add(clave)
        self._marcas[clave].setText("✓")
        caja = dict(self._claves()).get(clave)
        if caja is not None:
            caja.setReadOnly(True)

    def limpiar_hechos(self):
        self._hechos.clear()
        for clave, marca in self._marcas.items():
            marca.setText("")
            caja = dict(self._claves()).get(clave)
            if caja is not None and not self._cerrado:
                caja.setReadOnly(False)

    def cubre(self):
        suma = redondear_dinero(sum(self._valores.values()))
        total = redondear_dinero(self._total)
        if suma + 0.001 < total:
            return False
        extra = redondear_dinero(suma - total)
        if extra > 0.01 and redondear_dinero(self._valores.get("efectivo") or 0) <= 0.009:
            return False
        return True

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
            ("cliente", self.txt_cliente),
        )

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn and obj in self.campos():
            self._completar_falta(obj)
        return super().eventFilter(obj, event)

    def completar_cliente(self):
        """Un solo medio con plata y un resto: ese resto queda en el cliente."""
        self._completar_falta(self.txt_cliente)

    def _completar_falta(self, campo):
        """Si hay un solo medio cargado y este casillero está vacío, pone lo que falta."""
        if campo is None or campo.isReadOnly() or self._cerrado:
            return
        if self._numero(campo.text()) > 0.009:
            return
        clave_este = None
        for clave, caja in self._claves():
            if caja is campo:
                clave_este = clave
                break
        if clave_este is None:
            return
        otros = [clave for clave, valor in self._valores.items() if clave != clave_este and valor > 0.009]
        if len(otros) != 1:
            return
        falta = redondear_dinero(self._total - sum(self._valores.values()))
        if falta <= 0.009:
            return
        campo.blockSignals(True)
        campo.setText(f"{falta:.2f}")
        campo.blockSignals(False)
        campo.selectAll()
        self._recalcular()

    def _recalcular(self):
        if self._silencio:
            return
        self._valores = {clave: self._numero(campo.text()) for clave, campo in self._claves()}
        activos = [clave for clave, valor in self._valores.items() if valor > 0.009]
        if (
            not self._cerrado
            and len(activos) > 2
            and self._ultimo is not None
            and self._numero(self._ultimo.text()) > 0.009
        ):
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
            if redondear_dinero(self._valores.get("efectivo") or 0) > 0.009:
                self.estado.setText(f"Vuelto efectivo: ${diferencia:,.2f}")
                self.estado.setStyleSheet(
                    "color: #047857; font-size: 20px; font-weight: 800; background: transparent; border: none;"
                )
            else:
                self.estado.setText(f"Sobran ${diferencia:,.2f} en medios digitales")
                self.estado.setStyleSheet(
                    "color: #E11D48; font-size: 20px; font-weight: 800; background: transparent; border: none;"
                )
        else:
            self.estado.setText("Pago exacto")
            self.estado.setStyleSheet(
                "color: #1E3A8A; font-size: 20px; font-weight: 800; background: transparent; border: none;"
            )
        self.cambio.emit(self.valores())
