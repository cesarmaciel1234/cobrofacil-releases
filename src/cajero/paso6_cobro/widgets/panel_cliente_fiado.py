"""Panel reutilizable: selector de cliente para fiado (venta nueva o abono F6)."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit
from PyQt6.QtCore import Qt


class PanelClienteFiado(QWidget):
    """
    modo='venta'  → crédito disponible (paso6 / Fiado Express)
    modo='abono'  → deuda actual + monto editable (F6 ingreso)
    """

    def __init__(self, modo: str = "abono", theme: str = "light", parent=None):
        super().__init__(parent)
        self.modo = modo
        self.theme = theme
        self._deuda_actual = 0.0
        self._monto_fijo = 0.0
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        dark = self.theme == "dark"
        lbl_color = "#94A3B8" if dark else "#334155"
        info_color = "#34D399" if self.modo == "venta" else "#DC2626"
        if dark and self.modo == "abono":
            info_color = "#F87171"

        self.lbl_cliente = QLabel("CLIENTE:")
        self.lbl_cliente.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {lbl_color}; border: none; background: transparent;"
        )
        lay.addWidget(self.lbl_cliente)

        self.cmb = QComboBox()
        if dark:
            self.cmb.setStyleSheet("""
                QComboBox {
                    background: #1E293B; color: #F8FAFC; border: 1px solid #475569;
                    border-radius: 10px; padding: 10px 14px; font-size: 16px; font-weight: 700;
                }
                QComboBox QAbstractItemView {
                    background: #1E293B; color: #F8FAFC; selection-background-color: #3B82F6;
                }
            """)
        else:
            self.cmb.setStyleSheet(
                "QComboBox { font-size: 16px; padding: 8px; border: 1px solid #cbd5e1; "
                "border-radius: 8px; background: white; }"
            )
        self.cmb.currentIndexChanged.connect(self._on_cliente_changed)
        lay.addWidget(self.cmb)

        self.lbl_info = QLabel("")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_info.setStyleSheet(
            f"font-size: {'14' if dark else '16'}px; color: {info_color}; "
            "font-weight: bold; border: none; background: transparent;"
        )
        lay.addWidget(self.lbl_info)

        self.txt_monto = None
        if self.modo == "abono":
            lbl_m = QLabel("Monto a Abonar ($):")
            lbl_m.setStyleSheet(
                f"font-size: 13px; color: {lbl_color}; font-weight: bold; border: none; background: transparent;"
            )
            lay.addWidget(lbl_m)
            self.txt_monto = QLineEdit()
            self.txt_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.txt_monto.setStyleSheet("""
                QLineEdit {
                    font-size: 36px; font-weight: 900; color: #059669;
                    border: 2px solid #cbd5e1; border-radius: 10px;
                    padding: 8px; background: white;
                }
                QLineEdit:focus { border-color: #10B981; }
            """)
            lay.addWidget(self.txt_monto)

    def cargar_clientes_venta(self, lista_clientes: list):
        """Todos los clientes con límite de crédito (cobro F12)."""
        self.cmb.clear()
        if not lista_clientes:
            self.cmb.addItem("— Sin clientes registrados —", userData=None)
            self.cmb.setEnabled(False)
            self.lbl_info.setText("")
            return
        self.cmb.setEnabled(True)
        for c in lista_clientes:
            disp = float(c["limite_credito"]) - float(c["deuda_actual"])
            self.cmb.addItem(f"{c['nombre']}  (Disp: ${disp:,.0f})", userData=c)
        self._on_cliente_changed(0)

    def cargar_clientes_abono(self):
        """Solo clientes con deuda (F6 abono)."""
        from src.repositories.cliente_repository import ClienteRepository

        self.cmb.clear()
        res = ClienteRepository.obtener_clientes_con_deuda()
        if res:
            for r in res:
                self.cmb.addItem(r["nombre"], userData=r)
            self.cmb.setCurrentIndex(0)
            self._on_cliente_changed(0)
        else:
            self.cmb.addItem("No hay deudores", userData=None)
            self.lbl_info.setText("Nadie tiene deuda activa")

    def set_monto_fijo(self, monto: float):
        self._monto_fijo = float(monto)

    def _on_cliente_changed(self, idx: int):
        data = self.cmb.itemData(idx)
        if not data:
            self.lbl_info.setText("")
            self._deuda_actual = 0.0
            return
        if self.modo == "venta":
            disp = float(data["limite_credito"]) - float(data["deuda_actual"])
            self.lbl_info.setText(f"Crédito disponible: ${disp:,.2f}")
        else:
            self._deuda_actual = float(data["deuda_actual"])
            self.lbl_info.setText(f"Deuda Actual: ${self._deuda_actual:,.2f}")
            if self.txt_monto is not None:
                self.txt_monto.setText(f"{self._deuda_actual:.2f}")

    def cliente_actual(self):
        return self.cmb.currentData()

    def deuda_actual(self) -> float:
        return self._deuda_actual

    def monto(self) -> float:
        if self.modo == "venta":
            return self._monto_fijo
        if self.txt_monto is None:
            return 0.0
        return float(self.txt_monto.text().strip() or 0)

    def validar(self) -> tuple[bool, str]:
        data = self.cliente_actual()
        if not data:
            if self.modo == "venta":
                return False, "Registre clientes en Admin antes de fiar."
            return False, "⚠️ Ningún cliente seleccionado"
        monto = self.monto()
        if self.modo == "venta":
            disp = float(data["limite_credito"]) - float(data["deuda_actual"])
            if monto > disp + 0.01:
                return False, f"Excede el crédito disponible (${disp:,.2f})."
            return True, ""
        if monto <= 0:
            return False, "⚠️ Ingresa un abono mayor a 0"
        if monto > self._deuda_actual + 0.01:
            return False, "⚠️ El abono no puede superar la deuda"
        return True, ""

    def focus_monto(self):
        if self.txt_monto is not None:
            self.txt_monto.setFocus()
            self.txt_monto.selectAll()
