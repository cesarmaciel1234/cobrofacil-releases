from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import datetime
from src.jefe.contabilidad.shared_globals import *

class VistaTarjetasMixin:
    def _build_tab_tarjetas(self):
        lay, _ = self._page()
        lay.addWidget(section_title("💳  Tarjetas y Deudas Generales"))

        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 16px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Nombre:"), 0, 0)
        self._td_nombre = input_field("Descripción de la deuda..."); fl.addWidget(self._td_nombre, 0, 1)
        fl.addWidget(QLabel("Categoría:"), 0, 2)
        self._td_cat = input_field(is_combo=True, items=["Tarjeta", "Impuesto", "Servicio", "Personal", "Otros"])
        fl.addWidget(self._td_cat, 0, 3)
        fl.addWidget(QLabel("Monto $:"), 1, 0)
        self._td_monto = input_field("0.00"); fl.addWidget(self._td_monto, 1, 1)
        fl.addWidget(QLabel("Vencimiento:"), 1, 2)
        self._td_fecha = date_field(); fl.addWidget(self._td_fecha, 1, 3)

        btn_add = btn_primary("➕  Registrar Deuda")
        btn_add.clicked.connect(self._add_deuda)
        fl.addWidget(btn_add, 2, 0, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_td = build_table(["Nombre", "Categoría", "Monto", "Pagado", "Restante", "Vencimiento", "Estado", "Pagar"])
        lay.addWidget(self._tbl_td)
        lay.addStretch()

    def _load_tarjetas(self):
        if not self._db: return
        try:
            rows = [r for r in (self._db.get_general_debts() or [])
                    if str(r[2] or "") != "Proveedor"]
            self._tbl_td.setRowCount(0)
            for row in rows:
                r = self._tbl_td.rowCount()
                self._tbl_td.insertRow(r)
                monto  = float(row[3] or 0)
                pagado = float(row[6] if len(row) > 6 else 0)
                rest   = monto - pagado
                status = str(row[5] or "pending")
                estado_txt = {"pending": "⏳ Pendiente", "partial": "🔶 Parcial", "paid": "✅ Pagado"}.get(status, status)
                vals = [str(row[1] or ""), str(row[2] or ""),
                        f"$ {monto:,.2f}", f"$ {pagado:,.2f}", f"$ {rest:,.2f}",
                        str(row[4] or ""), estado_txt]
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(v)
                    if c == 6 and status == "pending":
                        it.setForeground(QColor(PAL["danger"]))
                    self._tbl_td.setItem(r, c, it)
                btn = btn_primary("💳 Pagar")
                btn.setFixedSize(80, 30)
                btn.clicked.connect(lambda _, did=row[0], rem=rest: self._pagar_deuda(did, rem))
                self._tbl_td.setCellWidget(r, 7, btn)
        except Exception as e:
            logger.error(f"load_tarjetas: {e}")

    def _add_deuda(self):
        try:
            monto = float(self._td_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            fecha = self._td_fecha.date().toString("yyyy-MM-dd")
            self._db.add_general_debt(self._td_nombre.text(), self._td_cat.currentText(), monto, fecha)
            self._td_nombre.clear(); self._td_monto.clear()
            self._load_tarjetas()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _pagar_deuda(self, did, restante):
        monto_str, ok = QInputDialog.getText(self, "Pagar Deuda",
                                              f"Monto a pagar (restante: $ {restante:,.2f}):",
                                              QLineEdit.Normal, f"{restante:.2f}")
        if ok and monto_str:
            try:
                self._db.pay_general_debt(did, float(monto_str.replace(",", ".")))
                self._load_tarjetas()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 7 — INVERSIONES
    # ─────────────────────────────────────────────────────────────────────────
