from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import datetime
from src.contabilidad.shared_globals import *

class VistaIngresosMixin:
    def _build_tab_ingresos(self):
        lay, _ = self._page()
        lay.addWidget(section_title("💰  Ingresos"))

        # Formulario
        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 16px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(12)

        fl.addWidget(QLabel("Fecha:"), 0, 0); self._ing_fecha = date_field(); fl.addWidget(self._ing_fecha, 0, 1)
        fl.addWidget(QLabel("Fuente:"), 0, 2)
        self._ing_fuente = input_field(is_combo=True, items=CAT_INGRESO); fl.addWidget(self._ing_fuente, 0, 3)
        fl.addWidget(QLabel("Monto $:"), 1, 0)
        self._ing_monto = input_field("0.00"); fl.addWidget(self._ing_monto, 1, 1)
        fl.addWidget(QLabel("Descripción:"), 1, 2)
        self._ing_desc = input_field("Concepto del ingreso..."); fl.addWidget(self._ing_desc, 1, 3)

        fl.addWidget(QLabel("Monto I.V.A.:"), 2, 0)
        self._ing_tax = input_field("0.00"); fl.addWidget(self._ing_tax, 2, 1)
        fl.addWidget(QLabel("Método Pago:"), 2, 2)
        self._ing_pago = input_field(is_combo=True, items=['Efectivo Caja', 'Transferencia', 'MercadoPago', 'Tarjeta', 'Otro']); fl.addWidget(self._ing_pago, 2, 3)
        fl.addWidget(QLabel("Nº Factura:"), 3, 0)
        self._ing_fac = input_field(""); fl.addWidget(self._ing_fac, 3, 1)

        btn_add = btn_primary("➕  Registrar Ingreso")
        btn_add.clicked.connect(self._add_ingreso)
        fl.addWidget(btn_add, 3, 2, 1, 2)

        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_ing = build_table(["ID", "Fecha", "Fuente", "Descripción", "Método", "Factura", "Monto", "Acción"])
        lay.addWidget(self._tbl_ing)
        lay.addStretch()

    def _load_ingresos(self):
        if not self._db: return
        try:
            rows = self._db.get_income(self._desde, self._hasta)
            self._tbl_ing.setRowCount(0)
            for row in (rows or []):
                r = self._tbl_ing.rowCount()
                self._tbl_ing.insertRow(r)
                metodo_pago = str(row[6] if len(row) > 6 and row[6] else "Efectivo Caja")
                nro_factura = str(row[7] if len(row) > 7 and row[7] else "")
                vals = [str(row[0]), str(row[1]), str(row[4] or ""), str(row[3] or ""), metodo_pago, nro_factura, f"$ {float(row[2] or 0):,.2f}"]
                for c, v in enumerate(vals):
                    self._tbl_ing.setItem(r, c, QTableWidgetItem(v))
                btn = btn_danger("🗑", "")
                btn.setFixedSize(36, 30)
                btn.clicked.connect(lambda _, rid=row[0]: self._del_ingreso(rid))
                self._tbl_ing.setCellWidget(r, 7, btn)
        except Exception as e:
            logger.error(f"load_ingresos: {e}")

    def _add_ingreso(self):
        try:
            monto = float(self._ing_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            tax = float(self._ing_tax.text().replace(",", ".") or "0")
            fecha = self._ing_fecha.date().toString("yyyy-MM-dd")
            self._db.add_income(fecha, monto, self._ing_desc.text(), self._ing_fuente.currentText(), tax_amount=tax, payment_method=self._ing_pago.currentText(), invoice_number=self._ing_fac.text())
            self._ing_monto.clear(); self._ing_desc.clear(); self._ing_tax.clear(); self._ing_fac.clear()
            self._load_ingresos()
        except Exception as e:
            QMessageBox.warning(self.window(), "Error", str(e))

    def _del_ingreso(self, rid):
        if QMessageBox.question(self.window(), "Eliminar", "¿Eliminar este ingreso?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._db.delete_income(rid)
            self._load_ingresos()

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2 — GASTOS
    # ─────────────────────────────────────────────────────────────────────────
