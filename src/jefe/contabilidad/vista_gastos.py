from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import datetime
from src.jefe.contabilidad.shared_globals import *

class VistaGastosMixin:
    def _build_tab_gastos(self):
        lay, _ = self._page()
        lay.addWidget(section_title("💸  Gastos Diarios"))

        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 16px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Fecha:"), 0, 0); self._gas_fecha = date_field(); fl.addWidget(self._gas_fecha, 0, 1)
        fl.addWidget(QLabel("Categoría:"), 0, 2)
        self._gas_cat = input_field(is_combo=True, items=CAT_GASTO); fl.addWidget(self._gas_cat, 0, 3)
        fl.addWidget(QLabel("Monto $:"), 1, 0)
        self._gas_monto = input_field("0.00"); fl.addWidget(self._gas_monto, 1, 1)
        fl.addWidget(QLabel("Descripción:"), 1, 2)
        self._gas_desc = input_field("Detalle del gasto..."); fl.addWidget(self._gas_desc, 1, 3)

        btn_add = btn_primary("➕  Registrar Gasto")
        btn_add.clicked.connect(self._add_gasto)
        fl.addWidget(btn_add, 2, 0, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_gas = build_table(["ID", "Fecha", "Categoría", "Descripción", "Monto", "Acción"])
        lay.addWidget(self._tbl_gas)
        lay.addStretch()

    def _load_gastos(self):
        if not self._db: return
        try:
            all_exp = self._db.get_expenses()
            period  = f"{self._año}-{self._mes:02d}"
            rows    = [r for r in (all_exp or []) if str(r[1] or "").startswith(period)]
            self._tbl_gas.setRowCount(0)
            for row in rows:
                r = self._tbl_gas.rowCount()
                self._tbl_gas.insertRow(r)
                vals = [str(row[0]), str(row[1]), str(row[2] or ""), str(row[4] or ""), f"$ {float(row[3] or 0):,.2f}"]
                for c, v in enumerate(vals):
                    self._tbl_gas.setItem(r, c, QTableWidgetItem(v))
                btn = btn_danger("🗑", "")
                btn.setFixedSize(36, 30)
                btn.clicked.connect(lambda _, rid=row[0]: self._del_gasto(rid))
                self._tbl_gas.setCellWidget(r, 5, btn)
        except Exception as e:
            logger.error(f"load_gastos: {e}")

    def _add_gasto(self):
        try:
            monto = float(self._gas_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            fecha = self._gas_fecha.date().toString("yyyy-MM-dd")
            self._db.add_expense(fecha, self._gas_cat.currentText(), monto,
                                 self._gas_desc.text(), "variable")
            self._gas_monto.clear(); self._gas_desc.clear()
            self._load_gastos()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _del_gasto(self, rid):
        if QMessageBox.question(self, "Eliminar", "¿Eliminar este gasto?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._db.delete_expense(rid)
            self._load_gastos()

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3 — PROVEEDORES (Deudas a proveedores)
    # ─────────────────────────────────────────────────────────────────────────
