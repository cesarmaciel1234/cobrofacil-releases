from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import datetime
from src.jefe.contabilidad.shared_globals import *

class VistaChequesMixin:
    def _build_tab_cheques(self):
        lay, _ = self._page()
        lay.addWidget(section_title("📋  Cheques Emitidos"))

        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 16px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Banco:"), 0, 0)
        self._chq_banco = input_field("Nombre del banco..."); fl.addWidget(self._chq_banco, 0, 1)
        fl.addWidget(QLabel("N° Cheque:"), 0, 2)
        self._chq_numero = input_field("Número..."); fl.addWidget(self._chq_numero, 0, 3)
        fl.addWidget(QLabel("Beneficiario:"), 1, 0)
        self._chq_benef = input_field("A nombre de..."); fl.addWidget(self._chq_benef, 1, 1)
        fl.addWidget(QLabel("Monto $:"), 1, 2)
        self._chq_monto = input_field("0.00"); fl.addWidget(self._chq_monto, 1, 3)
        fl.addWidget(QLabel("Vencimiento:"), 2, 0)
        self._chq_fecha = date_field(); fl.addWidget(self._chq_fecha, 2, 1)

        btn_add = btn_primary("➕  Registrar Cheque")
        btn_add.clicked.connect(self._add_cheque)
        fl.addWidget(btn_add, 2, 2, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_chq = build_table(["Banco", "N° Cheque", "Beneficiario", "Monto", "Vencimiento", "Estado", "Pagar"])
        lay.addWidget(self._tbl_chq)
        lay.addStretch()

    def _load_cheques(self):
        if not self._db: return
        try:
            rows = self._db.get_checks()
            self._tbl_chq.setRowCount(0)
            for row in (rows or []):
                r = self._tbl_chq.rowCount()
                self._tbl_chq.insertRow(r)
                monto  = float(row[3] or 0)
                pagado = float(row[7] if len(row) > 7 else 0)
                rest   = monto - pagado
                status = str(row[6] or "pending")
                estado_txt = {"pending": "⏳ Pendiente", "partial": "🔶 Parcial", "paid": "✅ Cobrado"}.get(status, status)
                vals = [str(row[1] or ""), str(row[2] or ""), str(row[5] or ""),
                        f"$ {monto:,.2f}", str(row[4] or ""), estado_txt]
                for c, v in enumerate(vals):
                    self._tbl_chq.setItem(r, c, QTableWidgetItem(v))
                btn = btn_primary("💳 Pagar")
                btn.setFixedSize(80, 30)
                btn.clicked.connect(lambda _, cid=row[0], rem=rest: self._pagar_cheque(cid, rem))
                self._tbl_chq.setCellWidget(r, 6, btn)
        except Exception as e:
            logger.error(f"load_cheques: {e}")

    def _add_cheque(self):
        try:
            monto = float(self._chq_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            fecha = self._chq_fecha.date().toString("yyyy-MM-dd")
            self._db.add_check(self._chq_banco.text(), self._chq_numero.text(),
                               monto, fecha, self._chq_benef.text())
            for w in [self._chq_banco, self._chq_numero, self._chq_benef, self._chq_monto]:
                w.clear()
            self._load_cheques()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _pagar_cheque(self, cid, restante):
        monto_str, ok = QInputDialog.getText(self, "Pagar Cheque",
                                              f"Monto a pagar (restante: $ {restante:,.2f}):",
                                              QLineEdit.Normal, f"{restante:.2f}")
        if ok and monto_str:
            try:
                self._db.pay_check(cid, float(monto_str.replace(",", ".")))
                self._load_cheques()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 6 — TARJETAS / DEUDAS GENERALES
    # ─────────────────────────────────────────────────────────────────────────
