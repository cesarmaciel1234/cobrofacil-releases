from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import datetime
from src.contabilidad.shared_globals import *

class VistaReportesMixin:
    def _build_tab_reportes(self):
        lay, _ = self._page()
        lay.addWidget(section_title("📄  Reportes y Exportación"))

        cards_lay = QGridLayout()
        cards_lay.setSpacing(16)

        btns = [
            ("📊  Reporte Mensual PDF",    PAL["primary"],  self._gen_pdf_mensual),
            ("💸  Exportar Gastos CSV",    PAL["danger"],   self._export_gastos_excel),
            ("💰  Exportar Ingresos CSV",  PAL["success"],  self._export_ingresos_excel),
            ("🏦  Exportar Préstamos CSV", PAL["warning"],  self._export_prestamos_excel),
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
            shadow = QGraphicsDropShadowEffect(card)
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(0, 0, 0, 40))
            shadow.setOffset(0, 4)
            card.setGraphicsEffect(shadow)

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
            path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF",
                f"reporte_{self._mes:02d}_{self._año}.pdf", "PDF (*.pdf)")
            if not path: return

            stats = self._db.get_stats(self._mes, self._año)

            from src.creador_pdf_global.motor_pdf_reportes import generar_pdf_mensual_stats
            generar_pdf_mensual_stats(path, stats, self._mes, self._año, MESES[self._mes-1])

            QMessageBox.information(self.window(), "PDF Generado", f"Guardado en:\n{path}")
        except Exception as e:
            QMessageBox.critical(self.window(), "Error", str(e))


    def _export_excel_generic(self, rows, headers, sheet_title, filename):
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter

        path, _ = QFileDialog.getSaveFileName(self, "Exportar Excel", filename, "Excel (*.xlsx)")
        if not path: return
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_title

        # Estilos de encabezado
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="4F46E5") # Color primario TPV PRO
        align_center = Alignment(horizontal="center", vertical="center")

        # Escribir encabezados
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = align_center

        # Escribir filas
        for row_num, row_data in enumerate(rows or [], 2):
            for col_num, cell_value in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col_num, value=cell_value)
                # Si el encabezado dice "Monto", aplicamos formato de moneda
                if "Monto" in headers[col_num - 1]:
                    try:
                        cell.value = float(cell_value)
                        cell.number_format = '$#,##0.00'
                    except:
                        pass
        
        # Ajustar ancho de columnas
        for col_num, column_cells in enumerate(ws.columns, 1):
            max_length = 0
            column_letter = get_column_letter(col_num)
            for cell in column_cells:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column_letter].width = adjusted_width

        wb.save(path)
        QMessageBox.information(self.window(), "Exportado", f"Guardado en:\n{path}")

    def _export_gastos_excel(self):
        try:
            self._export_excel_generic(self._db.get_expenses(),
                                      ["ID", "Fecha", "Categoría", "Monto", "Descripción", "Tipo", "Monto I.V.A.", "Método Pago", "Nº Factura"],
                                      "Gastos",
                                      f"gastos_{self._año}.xlsx")
        except Exception as e: QMessageBox.critical(self.window(), "Error", str(e))

    def _export_ingresos_excel(self):
        try:
            self._export_excel_generic(self._db.get_income(self._desde, self._hasta),
                                      ["ID", "Fecha", "Monto", "Descripción", "Fuente", "Monto I.V.A.", "Método Pago", "Nº Factura"],
                                      "Ingresos",
                                      f"ingresos_{self._año}.xlsx")
        except Exception as e: QMessageBox.critical(self.window(), "Error", str(e))

    def _export_prestamos_excel(self):
        try:
            self._export_excel_generic(self._db.get_installments(),
                                      ["ID", "LoanID", "N°", "Monto", "Vencimiento", "Estado", "PaidDate"],
                                      "Préstamos",
                                      f"prestamos_{self._año}.xlsx")
        except Exception as e: QMessageBox.critical(self.window(), "Error", str(e))

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
            shutil.copy2(self._db.db_name, dest)
            QMessageBox.information(self.window(), "✅ Backup", f"Guardado en:\n{dest}")
        except Exception as e:
            QMessageBox.critical(self.window(), "Error", str(e))
