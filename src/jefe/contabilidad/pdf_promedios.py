from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def exportar_pdf_interno(tabla, proveedor, fecha, kilos_media, merma, precio, parent=None):
    from PyQt5.QtWidgets import QFileDialog, QMessageBox
    try:
        ruta, _ = QFileDialog.getSaveFileName(parent, "Guardar PDF Interno", "", "Archivo PDF (*.pdf)")
        if not ruta:
            return
        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"

        doc = SimpleDocTemplate(ruta, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Titulo
        elements.append(Paragraph("Análisis de Costo de Media Res", styles['h1']))
        elements.append(Spacer(1, 0.2*inch))

        # Datos de la media res
        kilos_utiles = kilos_media - merma
        costo_real_kg = (precio * kilos_media) / kilos_utiles if kilos_utiles > 0 else 0
        
        datos_media_res = [
            [Paragraph("<b>Proveedor:</b>", styles['Normal']), proveedor, Paragraph("<b>Fecha:</b>", styles['Normal']), fecha],
            [Paragraph("<b>Kilos Media Res:</b>", styles['Normal']), f"{kilos_media:,.2f} kg", Paragraph("<b>Precio Compra/kg:</b>", styles['Normal']), f"${precio:,.2f}"],
            [Paragraph("<b>Merma:</b>", styles['Normal']), f"{merma:,.2f} kg", Paragraph("<b>Costo Real/kg:</b>", styles['Normal']), f"${costo_real_kg:,.2f}"],
        ]
        tbl_media_res = Table(datos_media_res, colWidths=[1.2*inch, 1.8*inch, 1.4*inch, 1.6*inch])
        tbl_media_res.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(tbl_media_res)
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabla de cortes
        data = [["Descripción", "Kilos", "Costo $/kg", "% Gan.", "Precio/kg", "Oferta", "Venta total", "Ganancia"]]
        total_venta_final = 0
        total_ganancia_final = 0

        for r in range(tabla.rowCount()):
            row_data = [tabla.item(r, c).text() if tabla.item(r,c) else '' for c in range(8)]
            data.append(row_data)
            try:
                total_venta_final += float(row_data[6].replace(",", ""))
                total_ganancia_final += float(row_data[7].replace(",", ""))
            except (ValueError, TypeError):
                pass

        table = Table(data, colWidths=[1.4*inch, 0.6*inch, 0.9*inch, 0.6*inch, 0.9*inch, 0.8*inch, 0.9*inch, 0.9*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#6366F1")), # Primary color
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
            ('GRID', (0,0), (-1,-1), 1, colors.lightgrey)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Totales
        totales_data = [
            [Paragraph(f"<b>TOTAL VENTA:</b> ${total_venta_final:,.2f}", styles['Normal']),
             Paragraph(f"<b>GANANCIA NETA:</b> ${total_ganancia_final:,.2f}", styles['Normal'])]
        ]
        tbl_totales = Table(totales_data, colWidths=[3.5*inch, 3.5*inch])
        tbl_totales.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(tbl_totales)

        def footer(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 9)
            canvas.drawCentredString(A4[0]/2, 0.75 * inch, f"Página {doc.page} - PUNPRO ERP")
            canvas.restoreState()

        doc.build(elements, onFirstPage=footer, onLaterPages=footer)
        QMessageBox.information(parent, "Éxito", f"PDF guardado en:\\n{ruta}")
    except Exception as e:
        QMessageBox.warning(parent, "Error", f"Error al generar PDF:\\n{e}")

def exportar_pdf_clientes(tabla, proveedor, fecha, parent=None):
    from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog
    try:
        mensaje, ok = QInputDialog.getText(parent, "Mensaje para Clientes", "Ingrese un mensaje opcional para el encabezado (ej: Ofertas de la semana):")
        if not ok: return
        
        ruta, _ = QFileDialog.getSaveFileName(parent, "Guardar PDF Clientes", "", "Archivo PDF (*.pdf)")
        if not ruta:
            return
        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"

        c = canvas.Canvas(ruta, pagesize=A4)
        width, height = A4
        y = height - 40
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, y, f"PRECIOS DE VENTA - {proveedor.upper()}")
        y -= 25
        c.setFont("Helvetica", 10)
        c.drawString(40, y, f"Fecha de Actualización: {fecha}")
        y -= 25

        if mensaje:
            c.setFont("Helvetica-Oblique", 11)
            c.drawString(40, y, mensaje)
            y -= 25

        headers = ["Corte / Descripción", "Precio por Kg"]
        x_positions = [40, 300]
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#0F172A"))
        for h, x in zip(headers, x_positions):
            c.drawString(x, y, h)
        y -= 15
        
        c.setLineWidth(1)
        c.line(40, y+5, width-40, y+5)
        y -= 15

        c.setFont("Helvetica", 11)

        for r in range(tabla.rowCount()):
            if y < 60:
                c.showPage()
                y = height - 40
                c.setFont("Helvetica-Bold", 16)
                c.drawString(40, y, f"PRECIOS DE VENTA - {proveedor.upper()}")
                y -= 30
                c.setFont("Helvetica-Bold", 12)
                for h, x in zip(headers, x_positions):
                    c.drawString(x, y, h)
                y -= 15
                c.line(40, y+5, width-40, y+5)
                y -= 15
                c.setFont("Helvetica", 11)

            corte = tabla.item(r,0).text()
            
            # Priorizar oferta
            oferta_str = tabla.item(r,5).text().replace(',','').strip()
            precio_base = tabla.item(r,4).text().replace(',','').strip()
            precio = oferta_str if oferta_str else precio_base
            
            try:
                if float(precio) <= 0: continue
            except: continue

            c.drawString(x_positions[0], y, corte)
            c.drawString(x_positions[1], y, f"$ {precio}")
            y -= 20

        c.save()
        QMessageBox.information(parent, "Éxito", f"PDF para clientes guardado en:\\n{ruta}")
    except Exception as e:
        QMessageBox.warning(parent, "Error", f"Error al generar PDF de clientes:\\n{e}")
