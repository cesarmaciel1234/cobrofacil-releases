"""Una línea bajo el escáner. Elige el módulo y la cantidad. Los productos van al remito."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QComboBox
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from src.contabilidad.shared_globals import PAL
from src.proveedor_global.frontend.formula.motores.consulta import al_elegir, modulos


class LineaBulto(QWidget):
    """Por bulto: un selector y la cantidad. Al elegir, carga los productos."""

    cargado = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = None
        self._ultimo = ""
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 4, 0, 0)
        raiz.setSpacing(4)
        fila = QHBoxLayout()
        fila.setSpacing(8)

        titulo = QLabel("Por bulto")
        titulo.setStyleSheet(f"color: {PAL['primary']}; font-weight: 800; font-size: 13px; background: transparent;")
        fila.addWidget(titulo)

        self.combo = QComboBox()
        self.combo.setFixedHeight(36)
        self.combo.addItem("Elegir", "")
        for nombre in modulos():
            self.combo.addItem(nombre, nombre)
        self.combo.setStyleSheet(
            "QComboBox { background: white; border: 1px solid #CBD5E1; border-radius: 6px;"
            " padding: 0 10px; color: #0F172A; font-size: 13px; font-weight: 700; }"
        )
        self.combo.currentIndexChanged.connect(self._calcular)
        fila.addWidget(self.combo, 1)

        self.cantidad = QLineEdit()
        self.cantidad.setFixedSize(72, 36)
        self.cantidad.setPlaceholderText("1")
        self.cantidad.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cantidad.setStyleSheet(
            "QLineEdit { background: white; border: 1.5px solid #93C5FD; border-radius: 6px;"
            " font-size: 14px; font-weight: 700; color: #1E3A8A; }"
        )
        self.cantidad.textChanged.connect(self._pedir)
        fila.addWidget(self.cantidad)

        self.precio = QLineEdit()
        self.precio.setFixedSize(128, 36)
        self.precio.setPlaceholderText("Precio bulto")
        self.precio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.precio.setStyleSheet(
            "QLineEdit { background: white; border: 1.5px solid #86EFAC; border-radius: 6px;"
            " font-size: 14px; font-weight: 700; color: #14532D; }"
        )
        self.precio.textChanged.connect(self._pedir)
        fila.addWidget(self.precio)
        raiz.addLayout(fila)

        self.nota = QLabel("Elegí el módulo, la cantidad y el precio de compra del bulto.")
        self.nota.setWordWrap(True)
        self.nota.setStyleSheet("color: #475569; font-size: 12px; background: transparent;")
        raiz.addWidget(self.nota)

        self._espera = QTimer(self)
        self._espera.setSingleShot(True)
        self._espera.timeout.connect(self._calcular)

    def recargar(self, db):
        self._db = db

    def _pedir(self):
        self._espera.start(280)

    def _bultos(self) -> float:
        texto = (self.cantidad.text() or "").strip().replace(",", ".")
        if not texto:
            return 1.0
        try:
            numero = float(texto)
        except ValueError:
            return 0.0
        return numero if numero > 0 else 0.0

    def _precio(self) -> float:
        from src.proveedor_global.backend.moneda import leer
        return leer(self.precio.text())

    def _calcular(self):
        modulo = self.combo.currentData()
        bultos = self._bultos()
        precio = self._precio()
        if not modulo or not self._db or bultos <= 0:
            return
        try:
            arma = al_elegir(self._db, str(modulo), bultos, precio) or {}
        except Exception:
            self.nota.setText("Ese módulo no pudo armar los productos.")
            return
        self.nota.setText(arma.get("nota") or "Sin productos de esa fórmula en el inventario.")
        productos = arma.get("productos") or []
        marca = f"{modulo}:{bultos}:{precio}:{len(productos)}"
        if marca == self._ultimo:
            return
        self._ultimo = marca
        self.cargado.emit({
            "origen": "consulta",
            "productos": productos,
            "bultos": bultos,
            "precio": precio,
            "monto": arma.get("monto") or 0,
            "modulo": str(modulo),
            "merma": arma.get("merma") or 0,
            "kilos_receta": arma.get("kilos_receta") or 0,
        })
