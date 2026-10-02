from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import datetime
from src.contabilidad.shared_globals import *

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
        
        fl.addWidget(QLabel("Monto I.V.A.:"), 2, 0)
        self._gas_tax = input_field("0.00"); fl.addWidget(self._gas_tax, 2, 1)
        fl.addWidget(QLabel("Método Pago:"), 2, 2)
        self._gas_pago = input_field(is_combo=True, items=['Efectivo Caja', 'Transferencia', 'MercadoPago', 'Tarjeta', 'Otro']); fl.addWidget(self._gas_pago, 2, 3)
        fl.addWidget(QLabel("Nº Factura:"), 3, 0)
        self._gas_fac = input_field(""); fl.addWidget(self._gas_fac, 3, 1)

        btn_add = btn_primary("➕  Registrar Gasto")
        btn_add.clicked.connect(self._add_gasto)
        fl.addWidget(btn_add, 3, 2, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_gas = build_table(["ID", "Fecha", "Categoría", "Descripción", "Método", "Factura", "Monto", "Acción"])
        lay.addWidget(self._tbl_gas)
        lay.addStretch()

    def _load_gastos(self):
        if not self._db: return
        try:
            all_exp = self._db.get_expenses()
            desde = self._desde
            hasta = self._hasta
            rows = []
            for r in (all_exp or []):
                fecha_str = str(r[1] or "")
                if desde and hasta:
                    if not (desde <= fecha_str <= hasta):
                        continue
                if str(r[5] or "") == 'tesoreria': continue
                rows.append(r)
            self._tbl_gas.setRowCount(0)
            for row in rows:
                r = self._tbl_gas.rowCount()
                self._tbl_gas.insertRow(r)
                metodo_pago = str(row[7] if len(row) > 7 and row[7] else "Efectivo Caja")
                nro_factura = str(row[8] if len(row) > 8 and row[8] else "")
                vals = [str(row[0]), str(row[1]), str(row[2] or ""), str(row[4] or ""), metodo_pago, nro_factura, f"$ {float(row[3] or 0):,.2f}"]
                for c, v in enumerate(vals):
                    self._tbl_gas.setItem(r, c, QTableWidgetItem(v))
                btn = btn_danger("🗑", "")
                btn.setFixedSize(36, 30)
                btn.clicked.connect(lambda _, rid=row[0]: self._del_gasto(rid))
                self._tbl_gas.setCellWidget(r, 7, btn)
        except Exception as e:
            logger.error(f"load_gastos: {e}")

    def _add_gasto(self):
        try:
            monto = float(self._gas_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            tax = float(self._gas_tax.text().replace(",", ".") or "0")
            fecha = self._gas_fecha.date().toString("yyyy-MM-dd")
            self._db.add_expense(fecha, self._gas_cat.currentText(), monto,
                                 self._gas_desc.text(), "variable", tax_amount=tax,
                                 payment_method=self._gas_pago.currentText(), invoice_number=self._gas_fac.text())
            self._gas_monto.clear(); self._gas_desc.clear(); self._gas_tax.clear(); self._gas_fac.clear()
            self._load_gastos()
        except Exception as e:
            QMessageBox.warning(self.window(), "Error", str(e))

    def _del_gasto(self, rid):
        if QMessageBox.question(self.window(), "Eliminar", "¿Eliminar este gasto?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._db.delete_expense(rid)
            self._load_gastos()

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3 — PROVEEDORES (Deudas a proveedores)
    # ─────────────────────────────────────────────────────────────────────────
