"""Diálogo para armar la fórmula de stock desde Costos y Promedios."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QRadioButton, QButtonGroup, QMessageBox,
)
from src.contabilidad.shared_globals import PAL
from src.base_de_datos.database import db_manager
from src.jefe.promedios.formula.motor import guardar, listar


class DialogoFormula(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fórmula de stock")
        self.setMinimumSize(680, 560)
        self.setStyleSheet(f"background: {PAL['bg']}; color: {PAL['text']}; font-size: 14px;")
        self._armar()
        self._pintar_guardadas()

    def _armar(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(10)

        titulo = QLabel("Fórmula de stock")
        titulo.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        lay.addWidget(titulo)
        ayuda = QLabel(
            "El cajón es el stock del pedido. Cada mercadería dice cuántas piezas usa de ese cajón. "
            "Ejemplo: 1 cajón = 12 maples y 4 productos. Vender un maple descuenta 1/12 del cajón."
        )
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet("color: #475569;")
        lay.addWidget(ayuda)

        fila = QHBoxLayout()
        fila.addWidget(self._etiqueta("Producto base"))
        self._base = QLineEdit()
        self._base.setPlaceholderText("Cajón de huevo")
        fila.addWidget(self._base, 1)
        fila.addWidget(self._etiqueta("Piezas del base"))
        self._piezas = QLineEdit("12")
        self._piezas.setFixedWidth(70)
        fila.addWidget(self._piezas)
        lay.addLayout(fila)

        modos = QHBoxLayout()
        self._por_producto = QRadioButton("Por producto")
        self._por_depto = QRadioButton("Por departamento")
        self._por_producto.setChecked(True)
        grupo = QButtonGroup(self)
        grupo.addButton(self._por_producto)
        grupo.addButton(self._por_depto)
        self._por_producto.toggled.connect(self._cambiar_modo)
        modos.addWidget(self._por_producto)
        modos.addWidget(self._por_depto)
        modos.addStretch()
        lay.addLayout(modos)

        self._fila_depto = QHBoxLayout()
        self._lbl_depto = self._etiqueta("Departamento")
        self._depto = QLineEdit()
        self._depto.setPlaceholderText("Huevo")
        self._lbl_usa = self._etiqueta("Piezas que usa cada venta")
        self._usa_depto = QLineEdit("1")
        self._usa_depto.setFixedWidth(70)
        self._fila_depto.addWidget(self._lbl_depto)
        self._fila_depto.addWidget(self._depto, 1)
        self._fila_depto.addWidget(self._lbl_usa)
        self._fila_depto.addWidget(self._usa_depto)
        lay.addLayout(self._fila_depto)

        self._tabla = QTableWidget(4, 2)
        self._tabla.setHorizontalHeaderLabels(["Mercadería", "Piezas que usa"])
        self._tabla.horizontalHeader().setStretchLastSection(False)
        self._tabla.horizontalHeader().setSectionResizeMode(0, self._tabla.horizontalHeader().ResizeMode.Stretch)
        self._tabla.setColumnWidth(1, 140)
        self._tabla.verticalHeader().setVisible(False)
        for r in range(4):
            self._tabla.setItem(r, 0, QTableWidgetItem(""))
            self._tabla.setItem(r, 1, QTableWidgetItem("1"))
        lay.addWidget(self._tabla, 1)

        acciones = QHBoxLayout()
        mas = QPushButton("＋ Línea")
        mas.clicked.connect(self._agregar)
        guardar_btn = QPushButton("Guardar fórmula")
        guardar_btn.clicked.connect(self._guardar)
        guardar_btn.setStyleSheet(
            "background: #0F766E; color: white; border-radius: 8px; padding: 8px 16px; font-weight: 800;"
        )
        mas.setStyleSheet(
            "background: #E2E8F0; color: #0F172A; border-radius: 8px; padding: 8px 16px; font-weight: 800;"
        )
        acciones.addWidget(mas)
        acciones.addStretch()
        acciones.addWidget(guardar_btn)
        lay.addLayout(acciones)

        self._guardadas = QLabel("")
        self._guardadas.setWordWrap(True)
        self._guardadas.setStyleSheet("color: #334155;")
        lay.addWidget(self._guardadas)
        self._cambiar_modo()

    def _etiqueta(self, texto):
        lbl = QLabel(texto)
        lbl.setStyleSheet("font-weight: 800; color: #0F172A;")
        return lbl

    def _cambiar_modo(self):
        por_producto = self._por_producto.isChecked()
        self._tabla.setVisible(por_producto)
        for w in (self._lbl_depto, self._depto, self._lbl_usa, self._usa_depto):
            w.setVisible(not por_producto)

    def _agregar(self):
        r = self._tabla.rowCount()
        self._tabla.insertRow(r)
        self._tabla.setItem(r, 0, QTableWidgetItem(""))
        self._tabla.setItem(r, 1, QTableWidgetItem("1"))

    def _lineas(self):
        if self._por_depto.isChecked():
            return [{"nombre": self._depto.text().strip(), "piezas": self._usa_depto.text().replace(",", ".")}]
        lineas = []
        for r in range(self._tabla.rowCount()):
            nombre = self._tabla.item(r, 0).text().strip() if self._tabla.item(r, 0) else ""
            piezas = self._tabla.item(r, 1).text().strip() if self._tabla.item(r, 1) else ""
            lineas.append({"nombre": nombre, "piezas": piezas.replace(",", ".")})
        return lineas

    def _guardar(self):
        try:
            piezas = float(self._piezas.text().replace(",", ".") or 0)
        except ValueError:
            piezas = 0
        if piezas <= 0 or not self._base.text().strip():
            QMessageBox.warning(self, "Fórmula", "Indicá el producto base y cuántas piezas trae.")
            return
        alcance = "departamento" if self._por_depto.isChecked() else "producto"
        try:
            n = guardar(
                db_manager,
                self._base.text().strip(),
                piezas,
                self._lineas(),
                alcance,
                self._depto.text().strip(),
            )
        except Exception as e:
            QMessageBox.warning(self, "Fórmula", f"No se pudo guardar.\n{e}")
            return
        if n <= 0:
            QMessageBox.warning(self, "Fórmula", "Agregá al menos una mercadería con las piezas que usa.")
            return
        self._pintar_guardadas()
        QMessageBox.information(
            self,
            "Fórmula",
            f"Quedó guardada. Al vender, el stock baja del cajón «{self._base.text().strip()}».",
        )

    def _pintar_guardadas(self):
        try:
            filas = listar(db_manager)
        except Exception:
            self._guardadas.setText("")
            return
        if not filas:
            self._guardadas.setText("Todavía no hay fórmulas guardadas.")
            return
        lineas = []
        for f in filas[:12]:
            base = f.get("base_nombre") or ""
            venta = f.get("nombre_venta") or f.get("clave") or ""
            try:
                usa = float(f.get("piezas_venta") or 0)
                total = float(f.get("piezas_base") or 0)
            except (TypeError, ValueError):
                usa, total = 0, 0
            modo = "departamento" if f.get("alcance") == "departamento" else "producto"
            lineas.append(f"{base}  ·  {venta} usa {usa:g} de {total:g}  ({modo})")
        extra = ""
        if len(filas) > 12:
            extra = f"\n… y {len(filas) - 12} más"
        self._guardadas.setText("Guardadas:\n" + "\n".join(lineas) + extra)
