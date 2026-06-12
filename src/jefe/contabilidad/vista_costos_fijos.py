from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import datetime
from src.jefe.contabilidad.shared_globals import *

class VistaCostosFijosMixin:
    def _build_tab_costos_fijos(self):
        lay, _ = self._page()
        lay.addWidget(section_title("🔒  Costos Fijos Mensuales"))

        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 16px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Nombre:"), 0, 0)
        self._cf_nombre = input_field("Alquiler, Internet, etc..."); fl.addWidget(self._cf_nombre, 0, 1)
        fl.addWidget(QLabel("Categoría:"), 0, 2)
        self._cf_cat = input_field(is_combo=True, items=CAT_COSTO_F); fl.addWidget(self._cf_cat, 0, 3)
        fl.addWidget(QLabel("Monto $:"), 1, 0)
        self._cf_monto = input_field("0.00"); fl.addWidget(self._cf_monto, 1, 1)

        btn_add = btn_primary("➕  Agregar Costo Fijo")
        btn_add.clicked.connect(self._add_costo_fijo)
        fl.addWidget(btn_add, 1, 2, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_cf = build_table(["Nombre", "Categoría", "Monto Mensual", "Acción"])
        lay.addWidget(self._tbl_cf)

        # Total fijos
        self._lbl_cf_total = QLabel("Total mensual estimado: $ 0,00")
        self._lbl_cf_total.setStyleSheet(
            f"font-size: 14px; font-weight: 900; color: {PAL['danger']}; background: transparent; border: none;")
        lay.addWidget(self._lbl_cf_total)
        lay.addStretch()

    def _load_costos_fijos(self):
        if not self._db: return
        try:
            rows = self._db.get_fixed_costs()
            self._tbl_cf.setRowCount(0)
            total = 0.0
            for row in (rows or []):
                r = self._tbl_cf.rowCount()
                self._tbl_cf.insertRow(r)
                monto = float(row[2] or 0)
                total += monto
                vals = [str(row[1] or ""), str(row[3] or ""), f"$ {monto:,.2f}"]
                for c, v in enumerate(vals):
                    self._tbl_cf.setItem(r, c, QTableWidgetItem(v))
                btn = btn_danger("🗑", "")
                btn.setFixedSize(36, 30)
                btn.clicked.connect(lambda _, cid=row[0]: self._del_costo_fijo(cid))
                self._tbl_cf.setCellWidget(r, 3, btn)
            self._lbl_cf_total.setText(f"Total mensual estimado: $ {total:,.2f}")
        except Exception as e:
            logger.error(f"load_costos_fijos: {e}")

    def _add_costo_fijo(self):
        try:
            monto = float(self._cf_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            self._db.add_fixed_cost(self._cf_nombre.text(), monto, self._cf_cat.currentText())
            self._cf_nombre.clear(); self._cf_monto.clear()
            self._load_costos_fijos()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _del_costo_fijo(self, cid):
        if QMessageBox.question(self, "Eliminar", "¿Eliminar este costo fijo?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._db.delete_fixed_cost(cid)
            self._load_costos_fijos()

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 9 — HISTORIAL
    # ─────────────────────────────────────────────────────────────────────────
