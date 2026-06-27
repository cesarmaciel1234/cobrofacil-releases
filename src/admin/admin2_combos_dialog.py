"""Editor de combos multi-artículo (cartelería espía)."""
import json
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QMessageBox, QHeaderView, QAbstractItemView,
)

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    db_manager = None

TIPOS = [
    ("combo_fijo", "Combo fijo (todos los artículos)"),
    ("combo_n", "Combo N (elegir N del listado)"),
    ("cantidad_grupo", "Cantidad grupo (X unidades del pool)"),
]


class AdminCombosDialog(QDialog):
    def __init__(self, productos_seleccionados=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Combos Cartelería / Espía")
        self.setMinimumSize(720, 520)
        self.productos_seleccionados = productos_seleccionados or []
        self._combo_id = None
        self._build_ui()
        self._cargar_tabla()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(
            "<b>Combos para pantalla espía</b> — al cumplir requisitos en caja, "
            "la cartelería anima el descuento."
        ))

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Tipo", "Precio combo"])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self._on_sel)
        lay.addWidget(self.tabla, 1)

        form = QVBoxLayout()
        row1 = QHBoxLayout()
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre del combo (ej. Combo Asado x4)")
        self.cmb_tipo = QComboBox()
        for k, lbl in TIPOS:
            self.cmb_tipo.addItem(lbl, k)
        row1.addWidget(QLabel("Nombre:"))
        row1.addWidget(self.txt_nombre, 2)
        row1.addWidget(QLabel("Tipo:"))
        row1.addWidget(self.cmb_tipo, 1)
        form.addLayout(row1)

        row2 = QHBoxLayout()
        self.sp_precio = QDoubleSpinBox()
        self.sp_precio.setRange(0, 99999999)
        self.sp_precio.setDecimals(2)
        self.sp_desc = QDoubleSpinBox()
        self.sp_desc.setRange(0, 100)
        self.sp_desc.setDecimals(1)
        self.sp_elegir = QSpinBox()
        self.sp_elegir.setRange(0, 99)
        self.sp_elegir.setToolTip("Para combo_n: cuántos artículos del pool. Para cantidad_grupo: unidades mínimas.")
        row2.addWidget(QLabel("Precio combo $:"))
        row2.addWidget(self.sp_precio)
        row2.addWidget(QLabel("O desc %:"))
        row2.addWidget(self.sp_desc)
        row2.addWidget(QLabel("N / Cant:"))
        row2.addWidget(self.sp_elegir)
        form.addLayout(row2)

        self.txt_req = QLineEdit()
        self.txt_req.setPlaceholderText(
            'Requisitos JSON: [{"id":"12","cant":1},{"id":"34","cant":2}]'
        )
        form.addWidget(QLabel("Artículos requeridos (JSON):"))
        form.addWidget(self.txt_req)

        btn_row = QHBoxLayout()
        self.btn_nuevo = QPushButton("Nuevo")
        self.btn_guardar = QPushButton("Guardar")
        self.btn_borrar = QPushButton("Eliminar")
        self.btn_desde_sel = QPushButton("Desde productos seleccionados")
        for b in (self.btn_nuevo, self.btn_guardar, self.btn_borrar, self.btn_desde_sel):
            btn_row.addWidget(b)
        form.addLayout(btn_row)
        lay.addLayout(form)

        self.btn_nuevo.clicked.connect(self._nuevo)
        self.btn_guardar.clicked.connect(self._guardar)
        self.btn_borrar.clicked.connect(self._borrar)
        self.btn_desde_sel.clicked.connect(self._desde_seleccion)

        if self.productos_seleccionados:
            self._desde_seleccion()

    def _cargar_tabla(self):
        self.tabla.setRowCount(0)
        if not db_manager:
            return
        try:
            rows = db_manager.execute_query(
                "SELECT id, nombre, tipo, precio_combo FROM combos_descuento ORDER BY orden, id"
            )
        except Exception:
            rows = []
        for r in rows or []:
            if isinstance(r, dict):
                rid, nom, tipo, prec = r.get("id"), r.get("nombre"), r.get("tipo"), r.get("precio_combo")
            else:
                rid, nom, tipo, prec = r[0], r[1], r[2], r[3]
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            for c, v in enumerate((rid, nom, tipo, prec)):
                self.tabla.setItem(row, c, QTableWidgetItem(str(v or "")))

    def _on_sel(self):
        rows = self.tabla.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        self._combo_id = self.tabla.item(row, 0).text()
        if not db_manager:
            return
        res = db_manager.execute_query(
            "SELECT nombre, tipo, precio_combo, descuento_pct, elegir_n, requisitos_json "
            "FROM combos_descuento WHERE id = ?",
            (self._combo_id,),
        )
        if not res:
            return
        p = res[0]
        if isinstance(p, dict):
            self.txt_nombre.setText(p.get("nombre") or "")
            idx = self.cmb_tipo.findData(p.get("tipo") or "combo_fijo")
            if idx >= 0:
                self.cmb_tipo.setCurrentIndex(idx)
            self.sp_precio.setValue(float(p.get("precio_combo") or 0))
            self.sp_desc.setValue(float(p.get("descuento_pct") or 0))
            self.sp_elegir.setValue(int(p.get("elegir_n") or 0))
            self.txt_req.setText(p.get("requisitos_json") or "[]")
        else:
            self.txt_nombre.setText(str(p[0] or ""))
            idx = self.cmb_tipo.findData(p[1] or "combo_fijo")
            if idx >= 0:
                self.cmb_tipo.setCurrentIndex(idx)
            self.sp_precio.setValue(float(p[2] or 0))
            self.sp_desc.setValue(float(p[3] or 0))
            self.sp_elegir.setValue(int(p[4] or 0))
            self.txt_req.setText(str(p[5] or "[]"))

    def _nuevo(self):
        self._combo_id = None
        self.txt_nombre.clear()
        self.cmb_tipo.setCurrentIndex(0)
        self.sp_precio.setValue(0)
        self.sp_desc.setValue(0)
        self.sp_elegir.setValue(0)
        self.txt_req.setText("[]")
        self.tabla.clearSelection()

    def _desde_seleccion(self):
        reqs = []
        for p in self.productos_seleccionados:
            pid = str(p.get("id") if isinstance(p, dict) else p)
            if pid:
                reqs.append({"id": pid, "cant": 1})
        if reqs:
            self.txt_req.setText(json.dumps(reqs, ensure_ascii=False))
            if not self.txt_nombre.text().strip():
                self.txt_nombre.setText(f"Combo {len(reqs)} artículos")
            if self.sp_elegir.value() == 0 and self.cmb_tipo.currentData() == "combo_n":
                self.sp_elegir.setValue(len(reqs))

    def _guardar(self):
        if not db_manager:
            QMessageBox.warning(self, "Error", "Base de datos no disponible.")
            return
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error", "Ingresá un nombre.")
            return
        try:
            reqs = json.loads(self.txt_req.text() or "[]")
            if not isinstance(reqs, list):
                raise ValueError("debe ser lista")
        except Exception as e:
            QMessageBox.warning(self, "JSON inválido", str(e))
            return
        tipo = self.cmb_tipo.currentData()
        precio = self.sp_precio.value()
        desc = self.sp_desc.value()
        elegir = self.sp_elegir.value()
        req_txt = json.dumps(reqs, ensure_ascii=False)
        try:
            if self._combo_id:
                db_manager.execute_query(
                    "UPDATE combos_descuento SET nombre=?, tipo=?, precio_combo=?, descuento_pct=?, "
                    "elegir_n=?, requisitos_json=?, activo=1 WHERE id=?",
                    (nombre, tipo, precio, desc, elegir, req_txt, self._combo_id),
                )
            else:
                db_manager.execute_query(
                    "INSERT INTO combos_descuento (nombre, tipo, precio_combo, descuento_pct, elegir_n, "
                    "requisitos_json, activo) VALUES (?, ?, ?, ?, ?, ?, 1)",
                    (nombre, tipo, precio, desc, elegir, req_txt),
                )
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))
            return
        self._cargar_tabla()
        QMessageBox.information(self, "OK", "Combo guardado.")

    def _borrar(self):
        if not self._combo_id or not db_manager:
            return
        if QMessageBox.question(self, "Confirmar", "¿Desactivar este combo?") != QMessageBox.Yes:
            return
        try:
            db_manager.execute_query(
                "UPDATE combos_descuento SET activo=0 WHERE id=?", (self._combo_id,)
            )
            self._nuevo()
            self._cargar_tabla()
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))
