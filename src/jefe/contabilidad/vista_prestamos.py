from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import datetime
from src.jefe.contabilidad.shared_globals import *

class VistaPrestamosMixin:
    def _build_tab_prestamos(self):
        lay, _ = self._page()
        lay.addWidget(section_title("🏦  Préstamos y Cuotas"))

        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 16px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Entidad:"), 0, 0)
        self._pr_nombre = input_field("Banco o entidad..."); fl.addWidget(self._pr_nombre, 0, 1)
        fl.addWidget(QLabel("Categoría:"), 0, 2)
        self._pr_cat = input_field(is_combo=True, items=CAT_PREST); fl.addWidget(self._pr_cat, 0, 3)
        fl.addWidget(QLabel("Monto Total $:"), 1, 0)
        self._pr_total = input_field("0.00"); fl.addWidget(self._pr_total, 1, 1)
        fl.addWidget(QLabel("Capital $:"), 1, 2)
        self._pr_capital = input_field("0.00"); fl.addWidget(self._pr_capital, 1, 3)
        fl.addWidget(QLabel("Interés $:"), 2, 0)
        self._pr_interes = input_field("0.00"); fl.addWidget(self._pr_interes, 2, 1)
        fl.addWidget(QLabel("Cuotas:"), 2, 2)
        self._pr_cuotas = QSpinBox(); self._pr_cuotas.setRange(1, 360); self._pr_cuotas.setValue(12)
        self._pr_cuotas.setStyleSheet(f"background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                       " border-radius: 8px; padding: 9px; color: {PAL['text']};")
        fl.addWidget(self._pr_cuotas, 2, 3)
        fl.addWidget(QLabel("1er Vencimiento:"), 3, 0)
        self._pr_fecha = date_field(); fl.addWidget(self._pr_fecha, 3, 1)

        btn_add = btn_primary("➕  Registrar Préstamo")
        btn_add.clicked.connect(self._add_prestamo)
        fl.addWidget(btn_add, 3, 2, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        lay.addWidget(QLabel("  Cuotas Pendientes:"))
        self._tbl_prest = build_table(["Préstamo", "Cuota N°", "Monto", "Vencimiento", "Pagado", "Estado", "Pagar"])
        lay.addWidget(self._tbl_prest)
        lay.addStretch()

    def _load_prestamos(self):
        if not self._db: return
        try:
            cuotas = self._db.get_installments()
            self._tbl_prest.setRowCount(0)
            for row in (cuotas or []):
                r = self._tbl_prest.rowCount()
                self._tbl_prest.insertRow(r)
                monto  = float(row[3] or 0)
                pagado = float(row[7] if len(row) > 7 else 0)
                status = str(row[5] or "pending")
                estado_txt = {"pending": "⏳ Pendiente", "partial": "🔶 Parcial", "paid": "✅ Pagada"}.get(status, status)
                vals = [str(row[8] if len(row) > 8 else ""), str(row[2] or ""),
                        f"$ {monto:,.2f}", str(row[4] or ""), f"$ {pagado:,.2f}", estado_txt]
                for c, v in enumerate(vals):
                    self._tbl_prest.setItem(r, c, QTableWidgetItem(v))
                rest = monto - pagado
                btn = btn_primary("💳 Pagar")
                btn.setFixedSize(80, 30)
                btn.clicked.connect(lambda _, iid=row[0], rem=rest: self._pagar_cuota(iid, rem))
                self._tbl_prest.setCellWidget(r, 6, btn)
        except Exception as e:
            logger.error(f"load_prestamos: {e}")

    def _add_prestamo(self):
        try:
            total = float(self._pr_total.text().replace(",", ".") or "0")
            if total <= 0: raise ValueError("Monto inválido")
            cap  = float(self._pr_capital.text().replace(",", ".") or "0")
            inte = float(self._pr_interes.text().replace(",", ".") or "0")
            fecha = self._pr_fecha.date().toString("yyyy-MM-dd")
            self._db.add_loan(self._pr_nombre.text(), total, cap, inte,
                              self._pr_cat.currentText(), self._pr_cuotas.value(), fecha)
            self._pr_nombre.clear(); self._pr_total.clear()
            self._pr_capital.clear(); self._pr_interes.clear()
            self._load_prestamos()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _pagar_cuota(self, iid, restante):
        monto_str, ok = QInputDialog.getText(self, "Pagar Cuota",
                                              f"Monto a pagar (restante: $ {restante:,.2f}):",
                                              QLineEdit.Normal, f"{restante:.2f}")
        if ok and monto_str:
            try:
                self._db.pay_installment(iid, float(monto_str.replace(",", ".")))
                self._load_prestamos()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 5 — CHEQUES
    # ─────────────────────────────────────────────────────────────────────────
