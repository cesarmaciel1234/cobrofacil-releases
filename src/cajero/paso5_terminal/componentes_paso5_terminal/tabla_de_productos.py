from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QLabel,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)


class EsperaVenta(QWidget):
    """Se ve solo con el ticket vacío. No tapa el naranja de editar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TerminalEsperaVenta")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        kicker = QLabel("LISTO")
        kicker.setObjectName("TerminalEsperaKicker")
        kicker.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo = QLabel("Escaneá el código")
        titulo.setObjectName("TerminalEsperaTitulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("o escribí el producto y presioná Enter")
        sub.setObjectName("TerminalEsperaSub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(kicker)
        lay.addWidget(titulo)
        lay.addWidget(sub)


class TablaDeProductos(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TerminalTablaContainer")
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["ID", "DESCRIPCION PRODUCTO", "PRECIO", "CANT", "DES. TOTAL", "TOTAL"])
        self.tabla.setObjectName("TerminalTabla")
        self.tabla.setAlternatingRowColors(True)
        header = self.tabla.horizontalHeader()

        header.setMinimumSectionSize(100)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(58)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.espera = EsperaVenta(self.tabla.viewport())
        modelo = self.tabla.model()
        modelo.rowsInserted.connect(self._sync_espera)
        modelo.rowsRemoved.connect(self._sync_espera)
        modelo.modelReset.connect(self._sync_espera)

        layout_principal.addWidget(self.tabla)
        self._sync_espera()

    def get_tabla(self):
        """Devuelve el widget de tabla para poder conectarle eventos o el NavRowBorderOverlay desde afuera."""
        return self.tabla

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._colocar_espera()

    def _sync_espera(self, *_args):
        vacia = self.tabla.rowCount() == 0
        self.espera.setVisible(vacia)
        self.tabla.setProperty("vacia", "true" if vacia else "false")
        self.tabla.style().unpolish(self.tabla)
        self.tabla.style().polish(self.tabla)
        if vacia:
            self._colocar_espera()
            self.espera.raise_()

    def _colocar_espera(self):
        vp = self.tabla.viewport()
        if vp is None:
            return
        self.espera.setGeometry(0, 0, vp.width(), vp.height())
