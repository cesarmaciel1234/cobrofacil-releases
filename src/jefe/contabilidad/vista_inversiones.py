from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import datetime
from src.jefe.contabilidad.shared_globals import *

class VistaInversionesMixin:
    def _build_tab_inversiones(self):
        lay, _ = self._page()
        lay.addWidget(section_title("📈  Inversiones"))

        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 16px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Fecha:"), 0, 0); self._inv_fecha = date_field(); fl.addWidget(self._inv_fecha, 0, 1)
        fl.addWidget(QLabel("Descripción:"), 0, 2)
        self._inv_desc = input_field("Descripción de la inversión..."); fl.addWidget(self._inv_desc, 0, 3)
        fl.addWidget(QLabel("Monto $:"), 1, 0)
        self._inv_monto = input_field("0.00"); fl.addWidget(self._inv_monto, 1, 1)
        fl.addWidget(QLabel("Categoría:"), 1, 2)
        self._inv_cat = input_field(is_combo=True, items=CAT_INV); fl.addWidget(self._inv_cat, 1, 3)

        btn_add = btn_primary("➕  Registrar Inversión")
        btn_add.clicked.connect(self._add_inversion)
        fl.addWidget(btn_add, 2, 0, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_inv = build_table(["Fecha", "Descripción", "Categoría", "Monto", "Acción"])
        lay.addWidget(self._tbl_inv)
        lay.addStretch()

    def _load_inversiones(self):
        if not self._db: return
        try:
            rows = self._db.get_investments()
            self._tbl_inv.setRowCount(0)
            for row in (rows or []):
                r = self._tbl_inv.rowCount()
                self._tbl_inv.insertRow(r)
                vals = [str(row[1] or ""), str(row[2] or ""), str(row[4] or ""), f"$ {float(row[3] or 0):,.2f}"]
                for c, v in enumerate(vals):
                    self._tbl_inv.setItem(r, c, QTableWidgetItem(v))
                btn = btn_danger("🗑", "")
                btn.setFixedSize(36, 30)
                btn.clicked.connect(lambda _, iid=row[0]: self._del_inversion(iid))
                self._tbl_inv.setCellWidget(r, 4, btn)
        except Exception as e:
            logger.error(f"load_inversiones: {e}")

    def _add_inversion(self):
        try:
            monto = float(self._inv_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            fecha = self._inv_fecha.date().toString("yyyy-MM-dd")
            self._db.add_investment(fecha, self._inv_desc.text(), monto, self._inv_cat.currentText())
            self._inv_monto.clear(); self._inv_desc.clear()
            self._load_inversiones()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _del_inversion(self, iid):
        if QMessageBox.question(self, "Eliminar", "¿Eliminar esta inversión?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._db.delete_investment(iid)
            self._load_inversiones()

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 8 — COSTOS FIJOS
    # ─────────────────────────────────────────────────────────────────────────
