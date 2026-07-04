from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import datetime
from src.jefe.contabilidad.shared_globals import *

class VistaHistorialMixin:
    def _build_tab_historial(self):
        lay, _ = self._page()
        hdr = QHBoxLayout()
        hdr.addWidget(section_title("📜  Historial de Movimientos"))
        btn_exp = btn_ghost("⬇️ Exportar CSV")
        btn_exp.clicked.connect(self._export_historial)
        hdr.addStretch(); hdr.addWidget(btn_exp)
        lay.addLayout(hdr)

        self._tbl_hist = build_table(["Fecha", "Tipo", "Categoría", "Descripción", "Monto", "Estado"])
        lay.addWidget(self._tbl_hist)
        lay.addStretch()

    def _load_historial(self):
        if not self._db: return
        try:
            movs = self._db.get_all_movements(self._mes, self._año)
            self._tbl_hist.setRowCount(0)
            for row_data in (movs or []):
                r = self._tbl_hist.rowCount()
                self._tbl_hist.insertRow(r)
                fecha = str(row_data[0] or "")
                tipo  = str(row_data[1] or "")
                cat   = str(row_data[2] or "")
                desc  = str(row_data[3] or "")
                monto = float(row_data[4] or 0)
                estat = str(row_data[5] if len(row_data) > 5 else "")
                vals  = [fecha, tipo, cat, desc, f"$ {monto:,.2f}", estat]
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(v)
                    if tipo == "INGRESO":
                        it.setForeground(QColor(PAL["success"]))
                    elif tipo == "EGRESO":
                        it.setForeground(QColor(PAL["danger"]))
                    self._tbl_hist.setItem(r, c, it)
        except Exception as e:
            logger.error(f"load_historial: {e}")

    def _export_historial(self):
        try:
            import csv
            path, _ = QFileDialog.getSaveFileName(self, "Exportar Historial", "historial.csv",
                                                   "CSV (*.csv)")
            if not path: return
            movs = self._db.get_all_movements(self._mes, self._año)
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Fecha", "Tipo", "Categoría", "Descripción", "Monto", "Estado"])
                for row in (movs or []):
                    w.writerow([row[0], row[1], row[2], row[3], row[4],
                                row[5] if len(row) > 5 else ""])
            QMessageBox.information(self, "Exportado", f"Historial exportado:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 10 — REPORTES PDF
    
    # ─────────────────────────────────────────────────────────────────────────
    # TAB 11 — PROMEDIOS
    # ─────────────────────────────────────────────────────────────────────────
    # ================= ESTILOS =================

