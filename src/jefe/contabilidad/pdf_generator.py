import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class PDFReportGenerator:
    def __init__(self, db, month, year, output_dir=None):
        self.db = db
        self.month = month
        self.year = year
        self.period = f"{year}-{month:02d}"
        
        # Output folder
        if output_dir:
            self.folder_path = output_dir
        else:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            self.folder_path = os.path.join(desktop, "Reportes PunPro")
            os.makedirs(self.folder_path, exist_ok=True)
        
        self.styles = getSampleStyleSheet()
        self.title_style = self.styles['Heading1']
        self.title_style.alignment = 1 # Center
        self.subtitle_style = self.styles['Heading2']
        self.normal_style = self.styles['Normal']
        
    def generate_libro(self):
        filename = os.path.join(self.folder_path, f"Libro_Contable_{self.period}.pdf")
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elements = []
        
        elements.append(Paragraph(f"Libro Contable Completo - {self.period}", self.title_style))
        elements.append(Spacer(1, 20))
        
        # 1. Ingresos
        elements.append(Paragraph("1. Ingresos", self.subtitle_style))
        ingresos = self.db.get_income(self.month, self.year)
        data = [["Fecha", "Detalle", "Monto"]]
        total_ing = 0
        for i in ingresos:
            # Acceso robusto compatible con sqlite3.Row
            data.append([str(i['date']), str(i['source'] or ""), f"${i['amount']:,.2f}"])
            total_ing += i['amount']
        data.append(["TOTAL", "", f"${total_ing:,.2f}"])
        t = Table(data, colWidths=[100, 300, 100])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('GRID', (0,0), (-1,-1), 1, colors.black)]))
        elements.append(t)
        elements.append(Spacer(1, 20))
        
        # 2. Compras a Proveedores
        elements.append(Paragraph("2. Compras a Proveedores", self.subtitle_style))
        expenses = [e for e in self.db.get_expenses() if e[1].startswith(self.period) and e[2] == "Carne / Proveedores"]
        debts = [d for d in self.db.get_general_debts() if d[4].startswith(self.period) and d[2] == "Proveedor"]
        data = [["Fecha", "Proveedor", "Mercadería", "Monto", "Estado"]]
        total_prov = 0
        for e in expenses:
            data.append([str(e[1]), self._extract_prov(str(e[4] or "")), self._extract_merc(str(e[4] or "")), f"${e[3]:,.2f}", "Pagado"])
            total_prov += e[3]
        for d in debts:
            data.append([str(d[4]), self._extract_prov(str(d[1] or "")), self._extract_merc(str(d[1] or "")), f"${d[3]:,.2f}", "Deuda"])
            total_prov += d[3]
        data.append(["TOTAL", "", "", f"${total_prov:,.2f}", ""])
        t = Table(data, colWidths=[80, 120, 160, 80, 80])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('GRID', (0,0), (-1,-1), 1, colors.black)]))
        elements.append(t)
        elements.append(Spacer(1, 20))
        
        # 3. Gastos Varios
        elements.append(Paragraph("3. Gastos Varios", self.subtitle_style))
        gastos = [e for e in self.db.get_expenses() if e[1].startswith(self.period) and e[2] != "Carne / Proveedores"]
        data = [["Fecha", "Categoría", "Detalle", "Monto"]]
        total_gastos = 0
        for g in gastos:
            data.append([str(g[1]), str(g[2] or ""), str(g[4] or ""), f"${g[3]:,.2f}"])
            total_gastos += g[3]
        data.append(["TOTAL", "", "", f"${total_gastos:,.2f}"])
        t = Table(data, colWidths=[80, 120, 200, 100])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('GRID', (0,0), (-1,-1), 1, colors.black)]))
        elements.append(t)
        elements.append(Spacer(1, 20))
        
        # Build document
        doc.build(elements)
        return filename

    def generate_jefe(self):
        filename = os.path.join(self.folder_path, f"Reporte_Jefe_{self.period}.pdf")
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elements = []
        
        elements.append(Paragraph(f"Reporte Gerencial (Jefe) - {self.period}", self.title_style))
        elements.append(Spacer(1, 20))
        
        # Balance Summary
        elements.append(Paragraph("Resumen Financiero", self.subtitle_style))
        
        ingresos = sum(i[2] for i in self.db.get_income(self.month, self.year))
        gastos_todos = sum(e[3] for e in self.db.get_expenses() if e[1].startswith(self.period))
        costos_fijos = sum(c[2] for c in self.db.get_fixed_costs())
        
        data = [
            ["Concepto", "Monto"],
            ["Total Ingresos (Caja)", f"${ingresos:,.2f}"],
            ["Total Gastos Operativos (Caja)", f"${gastos_todos:,.2f}"],
            ["Total Costos Fijos Mensuales", f"${costos_fijos:,.2f}"],
            ["BALANCE BRUTO (Caja)", f"${ingresos - gastos_todos:,.2f}"]
        ]
        
        t = Table(data, colWidths=[300, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue), 
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), 
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))
        
        # Retiros
        elements.append(Paragraph("Retiros", self.subtitle_style))
        retiros = [e for e in self.db.get_expenses() if e[1].startswith(self.period) and e[4] and "retiro" in e[4].lower()]
        data = [["Fecha", "Detalle", "Monto"]]
        total_ret = 0
        for r in retiros:
            data.append([str(r[1]), str(r[4] or ""), f"${r[3]:,.2f}"])
            total_ret += r[3]
        if not retiros:
            data.append(["-", "Sin retiros registrados", "$0.00"])
        data.append(["TOTAL RETIROS", "", f"${total_ret:,.2f}"])
        t = Table(data, colWidths=[100, 250, 100])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.darkred), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('GRID', (0,0), (-1,-1), 1, colors.black)]))
        elements.append(t)
        
        doc.build(elements)
        return filename

    def _extract_prov(self, desc):
        lines = desc.split('\n')
        if lines and lines[0].startswith("Proveedor: "):
            return lines[0].replace("Proveedor: ", "")
        return "Desconocido"
        
    def _extract_merc(self, desc):
        lines = desc.split('\n')
        if len(lines) > 1 and lines[1].startswith("Mercadería: "):
            return lines[1].replace("Mercadería: ", "")
        return "General"
