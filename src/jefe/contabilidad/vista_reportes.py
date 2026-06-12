from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import datetime
from src.jefe.contabilidad.shared_globals import *

class VistaReportesMixin:
    def _build_tab_reportes(self):
        lay, _ = self._page()
        lay.addWidget(section_title("📄  Reportes y Exportación"))

        cards_lay = QGridLayout()
        cards_lay.setSpacing(16)

        btns = [
            ("📊  Reporte Mensual PDF",    PAL["primary"],  self._gen_pdf_mensual),
            ("💸  Exportar Gastos CSV",    PAL["danger"],   self._export_gastos_csv),
            ("💰  Exportar Ingresos CSV",  PAL["success"],  self._export_ingresos_csv),
            ("🏦  Exportar Préstamos CSV", PAL["warning"],  self._export_prestamos_csv),
        ]

        for i, (txt, color, fn) in enumerate(btns):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {PAL['surface']};
                    border: 1px solid {PAL['border']};
                    border-top: 4px solid {color};
                    border-radius: 16px;
                }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(24, 24, 24, 24)
            lbl = QLabel(txt)
            lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {PAL['text']};"
                              " background: transparent; border: none;")
            cl.addWidget(lbl)
            b = btn_primary("Generar")
            b.clicked.connect(fn)
            cl.addWidget(b)
            cards_lay.addWidget(card, i // 2, i % 2)

        lay.addLayout(cards_lay)
        lay.addStretch()

    def _gen_pdf_mensual(self):
        try:
            from reportlab.pdfgen import canvas as pdf_canvas
            from reportlab.lib.pagesizes import A4

            path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF",
                f"reporte_{self._mes:02d}_{self._año}.pdf", "PDF (*.pdf)")
            if not path: return

            stats = self._db.get_stats(self._mes, self._año)
            c = pdf_canvas.Canvas(path, pagesize=A4)
            w_pg, h_pg = A4

            c.setFont("Helvetica-Bold", 18)
            c.drawString(50, h_pg - 60, f"Reporte Contable — {MESES[self._mes-1]} {self._año}")
            c.setFont("Helvetica", 12)
            y = h_pg - 100
            for key, val in [
                ("Ingresos Totales", f"$ {stats['total_income']:,.2f}"),
                ("Gastos Totales",   f"$ {stats['total_expenses']:,.2f}"),
                ("Saldo Neto",       f"$ {stats['balance']:,.2f}"),
            ]:
                c.drawString(50, y, f"{key}: {val}"); y -= 24

            c.save()
            QMessageBox.information(self, "PDF Generado", f"Guardado en:\n{path}")
        except ImportError:
            QMessageBox.warning(self, "Faltan librerías",
                               "Instalar: pip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _export_csv_generic(self, rows, headers, filename):
        import csv
        path, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", filename, "CSV (*.csv)")
        if not path: return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(headers)
            for r in (rows or []):
                w.writerow(list(r))
        QMessageBox.information(self, "Exportado", f"Guardado en:\n{path}")

    def _export_gastos_csv(self):
        try:
            self._export_csv_generic(self._db.get_expenses(),
                                      ["ID", "Fecha", "Categoría", "Monto", "Descripción", "Tipo"],
                                      f"gastos_{self._mes:02d}_{self._año}.csv")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _export_ingresos_csv(self):
        try:
            self._export_csv_generic(self._db.get_income(self._mes, self._año),
                                      ["ID", "Fecha", "Descripción", "Fuente", "Monto"],
                                      f"ingresos_{self._mes:02d}_{self._año}.csv")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _export_prestamos_csv(self):
        try:
            self._export_csv_generic(self._db.get_installments(),
                                      ["ID", "LoanID", "N°", "Monto", "Vencimiento", "Estado", "PaidDate"],
                                      f"prestamos_{self._año}.csv")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # BACKUP
    # ─────────────────────────────────────────────────────────────────────────
    def _do_backup(self):
        if not self._db: return
        try:
            import shutil
            dest, _ = QFileDialog.getSaveFileName(
                self, "Guardar Backup",
                f"backup_contabilidad_{datetime.date.today().strftime('%Y-%m-%d')}.db",
                "SQLite (*.db)")
            if not dest: return
            shutil.copy2(DB_PATH, dest)
            QMessageBox.information(self, "✅ Backup", f"Guardado en:\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
