import os
import html
import shutil
from datetime import datetime
from PyQt5.QtGui import QTextDocument, QPageSize
from PyQt5.QtPrintSupport import QPrinter
import barcode
from barcode.writer import ImageWriter

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.graphics.barcode import code128
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.units import mm

def abrir_archivo_pdf(pdf_path):
    import sys
    import subprocess
    from src.logger import logger
    
    # Normalizar la ruta con las diagonales correctas de Windows (\)
    pdf_path = os.path.normpath(os.path.abspath(pdf_path))
    logger.info(f"🛰️ SOLICITUD DE APERTURA PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        logger.error(f"❌ ERROR: El archivo PDF no existe físicamente en el disco: {pdf_path}")
        return False
        
    try:
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl
        
        # 1. Intentar método nativo y robusto de PyQt5 (Fuerza GUI)
        try:
            url = QUrl.fromLocalFile(pdf_path)
            exito = QDesktopServices.openUrl(url)
            if exito:
                logger.info("✅ ÉXITO: PDF lanzado mediante QDesktopServices nativo.")
                return True
        except Exception as e:
            logger.warning(f"⚠️ Fallo QDesktopServices: {e}")
            
        if sys.platform == 'win32':
            # 2. Intentar abrir con el explorador nativo (os.startfile) como respaldo
            try:
                os.startfile(pdf_path)
                logger.info("✅ ÉXITO: PDF abierto con os.startfile nativo.")
                return True
            except Exception as e:
                logger.warning(f"⚠️ Fallo os.startfile: {e}")
                
            # 3. Intentar comando shell 'start' directo de Windows
            try:
                os.system(f'start "" "{pdf_path}"')
                logger.info("✅ ÉXITO: PDF lanzado mediante os.system('start').")
                return True
            except Exception as e:
                logger.warning(f"⚠️ Fallo os.system start: {e}")
                
            # 4. Intentar lanzar con subprocess Popen
            try:
                subprocess.Popen([pdf_path], shell=True)
                logger.info("✅ ÉXITO: PDF lanzado mediante subprocess.Popen.")
                return True
            except Exception as e:
                logger.error(f"❌ Fallo subprocess Popen: {e}")
        else:
            # macOS o Linux
            try:
                subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', pdf_path])
                logger.info("✅ ÉXITO: PDF abierto en entorno Unix.")
                return True
            except Exception as e:
                logger.error(f"❌ Fallo open/xdg-open en Unix: {e}")
    except Exception as g_ex:
        logger.error(f"❌ Fallo crítico global en abrir_archivo_pdf: {g_ex}")
    return False

class EtiquetaRenderer:
    def __init__(self):
        from src.utils.paths import get_base_path
        self.base_path = get_base_path()
        self.tmp_dir = os.path.join(self.base_path, "tmp_barcodes")
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def generar_pdf(self, productos, rubro="CARNICERÍA", negocio="MACIEL"):
        if not productos:
            raise Exception("No hay productos seleccionados.")

        html_content = self.generar_html(productos, rubro, negocio)

        doc = QTextDocument()
        doc.setHtml(html_content)

        # ── CARPETA CENTRALIZADA Y ARCHIVO CON TIMESTAMP PARA EVITAR BLOQUEOS ──
        base_dir = os.path.join(self.base_path, "Etiquetas_Impresas")
        os.makedirs(base_dir, exist_ok=True)
        
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        pdf_path = os.path.join(base_dir, f"Etiquetas_Gondola_{timestamp}.pdf")

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(pdf_path)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setResolution(600)
        # Margen estándar de 2mm para evitar cortes
        printer.setPageMargins(2, 2, 2, 2, QPrinter.Millimeter)

        doc.print_(printer)
        
        # ── LIBERACIÓN EXPLÍCITA DE MANEJADORES DE ARCHIVO ──
        del printer
        del doc
        
        self.limpiar_tmp()
        return pdf_path

    def generar_html(self, productos, rubro, negocio):
        fecha = datetime.now().strftime("%d/%m/%Y")
        html_doc = f"""
        <html>
        <head>
        <style>
        @page {{ size: A4; margin: 2mm; }}
        body {{ margin: 0; padding: 0; font-family: Arial; background: white; }}
        table.grid {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
        
        /* CONTENEDOR FIJO PARA EVITAR QUE SE ROMPA EL DISEÑO */
        td.label {{
            width: 69mm; 
            height: 48mm; 
            padding: 0; 
            border: 1px dashed #b8b8b8;
            vertical-align: top; 
            overflow: hidden;
            page-break-inside: avoid;
        }}

        /* CABECERA FIJA (15mm) */
        .header {{ 
            background: #082c63; 
            height: 15mm; 
            padding-left: 3mm; 
            padding-right: 3mm;
            padding-top: 1mm; 
            color: white;
            overflow: hidden;
        }}
        .super {{ 
            font-size: 9pt; 
            font-weight: bold; 
            height: 5mm;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .product {{ 
            font-size: 10pt; 
            font-weight: 900; 
            color: white; 
            text-transform: uppercase; 
            line-height: 1.1;
            height: 8mm;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }}

        /* CAJA DE PRECIO FIJA (20mm) */
        .price-box {{ 
            background: #f4511e; 
            height: 20mm; 
            text-align: center; 
            padding-top: 1mm; 
            overflow: hidden;
        }}
        .currency {{ color: white; font-size: 22pt; font-weight: bold; vertical-align: top; }}
        .price {{ color: white; font-size: 54pt; font-weight: 900; letter-spacing: -4px; line-height: 0.9; }}

        /* PIE FIJO (13mm) */
        .footer {{ 
            background: #082c63; 
            height: 13mm; 
            color: white;
            text-align: center;
            overflow: hidden;
        }}
        .barcode {{ width: 42mm; height: 9mm; margin-top: 0.5mm; }}
        .meta {{ 
            font-size: 6.5pt; 
            font-weight: bold; 
            color: white; 
            margin-top: 0.2mm;
            white-space: nowrap;
        }}
        </style>
        </head>
        <body>
        <table class="grid"><tr>
        """
        col = 0
        for p in productos:
            if col == 3:
                html_doc += "</tr><tr>"
                col = 0
            etiqueta = self.generar_etiqueta(p, fecha, rubro, negocio)
            html_doc += etiqueta
            col += 1

        while col < 3:
            html_doc += "<td></td>"
            col += 1

        html_doc += "</tr></table></body></html>"
        return html_doc

    def generar_etiqueta(self, producto, fecha, rubro, negocio):
        codigo_real = str(producto["id"]).strip()
        if not codigo_real: return ""
        
        # Sanitizamos solo el nombre de archivo, preservando el código real para el código de barras
        filename_seguro = "".join(c for c in codigo_real if c.isalnum() or c in "-_")
        if not filename_seguro: filename_seguro = "temp_code"
        
        barcode_url = self.generar_barcode(codigo_real, filename_seguro)
        
        try:
            precio_float = float(str(producto["precio"]).replace("$", "").replace(",", ""))
        except:
            precio_float = 0.0
            
        precio = f"{precio_float:.2f}"
        enteros = precio.split(".")[0]
        nombre = html.escape(str(producto["nombre"]).upper())

        try:
            unidad_val = producto["unidad"]
            if not unidad_val: unidad_val = "UN"
        except:
            unidad_val = "UN"

        # Ajuste automático de fuente para el precio
        p_font = "54pt"
        if len(enteros) >= 4: p_font = "46pt"
        if len(enteros) >= 5: p_font = "38pt"
        if len(enteros) >= 6: p_font = "30pt"

        # Ajuste para el nombre del negocio/rubro
        brand_text = f"🛒 {rubro.upper()} {negocio.upper()}"
        b_font = "9pt"
        if len(brand_text) > 25: b_font = "8pt"
        if len(brand_text) > 35: b_font = "7pt"

        return f"""
        <td class="label">
            <div class="header">
                <div class="super" style="font-size:{b_font};">{brand_text}</div>
                <div class="product">{nombre}</div>
            </div>
            <div class="price-box">
                <span class="currency">$</span>
                <span class="price" style="font-size:{p_font};">{enteros}</span>
            </div>
            <div class="footer">
                <img src="{barcode_url}" class="barcode">
                <div class="meta">
                    ${precio} /{str(unidad_val).upper()} &nbsp;&nbsp; • &nbsp;&nbsp; {fecha}
                </div>
            </div>
        </td>
        """

    def generar_barcode(self, codigo, filename_seguro=None):
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir, exist_ok=True)
            
        nombre_archivo = filename_seguro if filename_seguro else "".join(filter(str.isalnum, codigo))
        barcode_path = os.path.join(self.tmp_dir, nombre_archivo)
        CODE128 = barcode.get_barcode_class("code128")
        barcode_img = CODE128(codigo, writer=ImageWriter())
        filename = barcode_img.save(barcode_path, {
            "write_text": True, 
            "module_height": 2.5, 
            "module_width": 0.16,
            "quiet_zone": 0.5,
            "font_size": 5.5,
            "text_distance": 2.2
        })
        return "file:///" + os.path.abspath(filename).replace("\\", "/")

    def dibujar_flama(self, c, fx, fy, scale=1.0):
        # Dibuja una flama vectorial estilizada de alto impacto
        c.saveState()
        c.translate(fx, fy)
        c.scale(scale, scale)
        
        # Flama Externa (Rojo Fuego)
        c.setFillColor(HexColor("#ef4444"))
        p1 = c.beginPath()
        p1.moveTo(0, 0)
        p1.curveTo(-15, 10, -20, 30, -10, 45)
        p1.curveTo(-5, 55, 5, 60, 10, 70)
        p1.curveTo(15, 55, 25, 45, 20, 30)
        p1.curveTo(18, 15, 10, 5, 0, 0)
        p1.close()
        c.drawPath(p1, fill=1, stroke=0)
        
        # Flama Media (Naranja Brillante)
        c.setFillColor(HexColor("#f97316"))
        p2 = c.beginPath()
        p2.moveTo(0, 5)
        p2.curveTo(-10, 13, -12, 28, -6, 38)
        p2.curveTo(-2, 45, 4, 48, 7, 56)
        p2.curveTo(10, 48, 16, 38, 13, 28)
        p2.curveTo(11, 17, 7, 10, 0, 5)
        p2.close()
        c.drawPath(p2, fill=1, stroke=0)
        
        # Flama Interna (Amarillo Fuego)
        c.setFillColor(HexColor("#facc15"))
        p3 = c.beginPath()
        p3.moveTo(0, 12)
        p3.curveTo(-6, 18, -8, 26, -4, 32)
        p3.curveTo(-1, 38, 2, 40, 4, 46)
        p3.curveTo(6, 40, 10, 32, 8, 26)
        p3.curveTo(7, 20, 4, 16, 0, 12)
        p3.close()
        c.drawPath(p3, fill=1, stroke=0)
        
        c.restoreState()

    def generar_pdf_ofertas(self, lote_ofertas, rubro="CARNICERÍA", negocio="MACIEL"):
        """
        Genera un PDF masivo utilizando ReportLab. Soporta múltiples formatos por lote o individuales:
        - "a4_vertical" (1 por página)
        - "a5_horizontal" (2 por página)
        - "a6_grid" (4 por página)
        - "a8_grid" (8 por página)
        """
        # Intentar obtener de config.json para que sea dinámico y correcto
        try:
            from src.config import config as _cfg
            config_negocio = _cfg.get("business_name", "").upper().strip()
            config_rubro = _cfg.get("business_rubro", "").upper().strip()
            if config_negocio:
                negocio = config_negocio
            if config_rubro:
                rubro = config_rubro
        except:
            pass

        base_dir = os.path.join(self.base_path, "Carteles_Oferta")
        os.makedirs(base_dir, exist_ok=True)
        
        nombre_safe = "PRODUCTOS"
        if lote_ofertas and "nombre" in lote_ofertas[0]:
            nombre_safe = "".join([char if char.isalnum() else "_" for char in str(lote_ofertas[0]["nombre"])]).strip("_").upper()
            
        pdf_path = os.path.join(base_dir, f"Cartel_Oferta_{nombre_safe}.pdf")
        
        c = canvas.Canvas(pdf_path, pagesize=A4)
        PAGE_W, PAGE_H = A4

        # Agrupar las ofertas según su formato
        ofertas_por_formato = {
            "a4_vertical": [],
            "a5_horizontal": [],
            "a6_grid": [],
            "a8_grid": []
        }
        
        for oferta in lote_ofertas:
            fmt = oferta.get("formato")
            if not fmt:
                # Deducir
                if oferta.get("orientacion", "horizontal") == "horizontal":
                    fmt = "a5_horizontal"
                else:
                    fmt = "a4_vertical"
            
            if fmt in ofertas_por_formato:
                ofertas_por_formato[fmt].append(oferta)
            else:
                ofertas_por_formato["a5_horizontal"].append(oferta)

        # Rellenar cíclicamente para completar las hojas de etiquetas y no desperdiciar papel
        for fmt, cap in [("a5_horizontal", 2), ("a6_grid", 4), ("a8_grid", 8)]:
            lst = ofertas_por_formato[fmt]
            if lst:
                original_len = len(lst)
                while len(lst) % cap != 0:
                    copia = lst[len(lst) % original_len].copy()
                    lst.append(copia)

        # -------------------------------------------------------------
        # 1. RENDER FORMATO: A4 VERTICAL (1 por hoja)
        # -------------------------------------------------------------
        for oferta in ofertas_por_formato["a4_vertical"]:
            self.dibujar_oferta_vertical(c, oferta, 0, 0, PAGE_W, PAGE_H, rubro, negocio)
            c.showPage()

        # -------------------------------------------------------------
        # 2. RENDER FORMATO: A5 HORIZONTAL (2 por hoja)
        # -------------------------------------------------------------
        items_a5 = ofertas_por_formato["a5_horizontal"]
        for i in range(0, len(items_a5), 2):
            oferta1 = items_a5[i]
            oferta2 = items_a5[i + 1] if i + 1 < len(items_a5) else None
            
            mitad_h = PAGE_H / 2
            
            # Oferta Superior
            self.dibujar_oferta_horizontal(c, oferta1, 0, mitad_h, PAGE_W, mitad_h, rubro, negocio)
            
            # Oferta Inferior
            if oferta2:
                self.dibujar_oferta_horizontal(c, oferta2, 0, 0, PAGE_W, mitad_h, rubro, negocio)
                
            # Línea guía de corte central
            if oferta2:
                c.setDash(3, 3)
                c.setStrokeColor(HexColor("#cbd5e1"))
                c.setLineWidth(1)
                c.line(0, mitad_h, PAGE_W, mitad_h)
                c.setDash()
                
            c.showPage()

        # -------------------------------------------------------------
        # 3. RENDER FORMATO: A6 GRID (4 por hoja)
        # -------------------------------------------------------------
        items_a6 = ofertas_por_formato["a6_grid"]
        for i in range(0, len(items_a6), 4):
            chunk = items_a6[i:i+4]
            
            quad_w = PAGE_W / 2
            quad_h = PAGE_H / 2
            
            coordenadas = [
                (0, quad_h),       # Top-Left
                (quad_w, quad_h),  # Top-Right
                (0, 0),            # Bottom-Left
                (quad_w, 0)        # Bottom-Right
            ]
            
            for idx, oferta in enumerate(chunk):
                qx, qy = coordenadas[idx]
                
                c.saveState()
                c.translate(qx, qy)
                c.scale(0.5, 0.5)
                self.dibujar_oferta_vertical(c, oferta, 0, 0, PAGE_W, PAGE_H, rubro, negocio)
                c.restoreState()
                
            # Líneas guía de corte
            c.setDash(3, 3)
            c.setStrokeColor(HexColor("#cbd5e1"))
            c.setLineWidth(1)
            c.line(0, quad_h, PAGE_W, quad_h)  # Horizontal
            c.line(quad_w, 0, quad_w, PAGE_H)  # Vertical
            c.setDash()
            
            c.showPage()

        # -------------------------------------------------------------
        # 4. RENDER FORMATO: A8 GRID (8 por hoja)
        # -------------------------------------------------------------
        items_a8 = ofertas_por_formato["a8_grid"]
        for i in range(0, len(items_a8), 8):
            chunk = items_a8[i:i+8]
            
            cell_w = PAGE_W / 2
            cell_h = PAGE_H / 4
            
            coordenadas = [
                (0, cell_h * 3),       # Fila 4, Col 1
                (cell_w, cell_h * 3),  # Fila 4, Col 2
                (0, cell_h * 2),       # Fila 3, Col 1
                (cell_w, cell_h * 2),  # Fila 3, Col 2
                (0, cell_h),           # Fila 2, Col 1
                (cell_w, cell_h),      # Fila 2, Col 2
                (0, 0),                # Fila 1, Col 1
                (cell_w, 0)            # Fila 1, Col 2
            ]
            
            for idx, oferta in enumerate(chunk):
                cx, cy = coordenadas[idx]
                
                c.saveState()
                c.translate(cx, cy)
                c.scale(0.5, 0.5)
                self.dibujar_oferta_horizontal(c, oferta, 0, 0, PAGE_W, PAGE_H / 2, rubro, negocio)
                c.restoreState()
                
            # Líneas guía de corte
            c.setDash(3, 3)
            c.setStrokeColor(HexColor("#cbd5e1"))
            c.setLineWidth(1)
            c.line(cell_w, 0, cell_w, PAGE_H)  # Vertical central
            c.line(0, cell_h, PAGE_W, cell_h)  # Horizontal 1
            c.line(0, cell_h * 2, PAGE_W, cell_h * 2)  # Horizontal 2
            c.line(0, cell_h * 3, PAGE_W, cell_h * 3)  # Horizontal 3
            c.setDash()
            
            c.showPage()

        c.save()
        self.limpiar_tmp()
        return pdf_path

    # =========================================================
    # OFERTA VERTICAL A4 COMPLETA (REPORTLAB)
    # =========================================================
    def dibujar_oferta_vertical(self, c, oferta, x, y, w, h, rubro, negocio):
        # Paleta de colores Premium de Alto Impacto
        rojo_accent = HexColor("#ef4444")
        naranja_accent = HexColor("#ea580c")
        amarillo_accent = HexColor("#facc15")
        gris_oscuro = HexColor("#0f172a")
        gris_medio = HexColor("#475569")
        gris_borde = HexColor("#cbd5e1")

        # Fondo blanco
        c.setFillColor(white)
        c.rect(x, y, w, h, fill=1, stroke=0)

        # Doble borde elegante "FUEGO" de alto impacto
        c.setStrokeColor(naranja_accent)
        c.setLineWidth(3)
        c.roundRect(x + 20, y + 20, w - 40, h - 40, 16, fill=0, stroke=1)
        
        c.setStrokeColor(amarillo_accent)
        c.setLineWidth(1.5)
        c.roundRect(x + 24, y + 24, w - 48, h - 48, 14, fill=0, stroke=1)

        # Header Badge (Píldora Roja de Oferta con borde amarillo brillante)
        c.setFillColor(rojo_accent)
        c.setStrokeColor(amarillo_accent)
        c.setLineWidth(1.5)
        c.roundRect(x + (w - 280)/2, y + h - 75, 280, 40, 20, fill=1, stroke=1)
        
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 18)
        # Asegurar un texto llamativo
        texto_promo = str(oferta["tipo_promo"]).upper().strip()
        if not texto_promo:
            texto_promo = "¡SUPER OFERTA!"
        c.drawCentredString(x + w / 2, y + h - 63, texto_promo)

        # Dibujar dos hermosas flamas a los lados del Header Badge
        self.dibujar_flama(c, x + (w - 280)/2 - 25, y + h - 73, scale=0.7)
        self.dibujar_flama(c, x + (w + 280)/2 + 5, y + h - 73, scale=0.7)

        # Nombre del Negocio / Rubro
        c.setFillColor(gris_medio)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(x + w / 2, y + h - 110, f"{rubro} • {negocio}".upper())

        # Línea divisoria sutil
        c.setStrokeColor(gris_borde)
        c.setLineWidth(1)
        c.line(x + 60, y + h - 130, x + w - 60, y + h - 130)

        # Nombre del Producto
        nombre = str(oferta["nombre"]).strip().upper()
        c.setFillColor(gris_oscuro)

        # Envoltura en 2 líneas
        palabras = nombre.split()
        linea1 = []
        linea2 = []
        limite_caracteres = 15
        
        for p in palabras:
            if len(" ".join(linea1 + [p])) <= limite_caracteres:
                linea1.append(p)
            else:
                linea2.append(p)
                
        txt_linea1 = " ".join(linea1)
        txt_linea2 = " ".join(linea2)

        if txt_linea2:
            c.setFont("Helvetica-Bold", 32)
            c.drawCentredString(x + w / 2, y + h - 190, txt_linea1)
            c.drawCentredString(x + w / 2, y + h - 235, txt_linea2)
            y_precio_base = y + h / 2 - 20
        else:
            c.setFont("Helvetica-Bold", 38)
            c.drawCentredString(x + w / 2, y + h - 200, txt_linea1)
            y_precio_base = y + h / 2 - 10

        # Precio de Lista (Tachado)
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(gris_medio)
        p_reg_txt = f"ANTES PRECIO RAYADO: ${oferta['precio_regular']}"
        w_reg = stringWidth(p_reg_txt, "Helvetica-Bold", 16)
        c.drawCentredString(x + w / 2, y_precio_base + 110, p_reg_txt)
        
        # Línea de tachado roja gruesa sobre el precio regular
        c.setStrokeColor(rojo_accent)
        c.setLineWidth(2.5)
        c.line(x + (w - w_reg)/2, y_precio_base + 115, x + (w + w_reg)/2, y_precio_base + 115)

        # Precio de Oferta Gigante
        precio_of = str(oferta["precio_oferta"])
        if "." in precio_of:
            partes = precio_of.split(".")
            entero = partes[0]
            centavo = partes[1]
        else:
            entero = precio_of
            centavo = "00"

        font_size_price = 140
        font_size_symbol = 60

        c.setFont("Helvetica-Bold", font_size_price)
        ancho_entero = stringWidth(entero, "Helvetica-Bold", font_size_price)
        ancho_simbolo = stringWidth("$ ", "Helvetica-Bold", font_size_symbol)
        ancho_centavos = stringWidth(f".{centavo}", "Helvetica-Bold", font_size_symbol)

        ancho_total = ancho_simbolo + ancho_entero + ancho_centavos
        start_px = x + (w - ancho_total) / 2

        # Dibujar una flama espectacular a la izquierda del precio
        self.dibujar_flama(c, start_px - 45, y_precio_base - 35, scale=0.9)

        # Dibujar símbolo pesos ($)
        c.setFont("Helvetica-Bold", font_size_symbol)
        c.setFillColor(gris_medio)
        c.drawString(start_px, y_precio_base - 10, "$")

        # Dibujar enteros
        c.setFont("Helvetica-Bold", font_size_price)
        c.setFillColor(rojo_accent)
        c.drawString(start_px + ancho_simbolo, y_precio_base - 40, entero)

        # Dibujar centavos
        c.setFont("Helvetica-Bold", font_size_symbol)
        c.setFillColor(rojo_accent)
        c.drawString(start_px + ancho_simbolo + ancho_entero, y_precio_base - 10, f".{centavo}")

        # Condición de Venta (Detalle Promoción)
        condicion = str(oferta.get("condicion_venta", "")).strip().upper()
        if condicion:
            # Fondo amarillo de atención para que resalte
            c.setFillColor(HexColor("#fef3c7")) # Warm yellow
            c.setStrokeColor(naranja_accent)
            c.setLineWidth(1)
            c.roundRect(x + (w - 320)/2, y_precio_base - 110, 320, 35, 8, fill=1, stroke=1)
            
            c.setFillColor(HexColor("#9a3412")) # Orange-brown
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(x + w / 2, y_precio_base - 98, condicion)

        # Footer Barra Oscura Elegante
        c.setFillColor(gris_oscuro)
        c.roundRect(x + 20, y + 20, w - 40, 60, 12, fill=1, stroke=0)

        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 10)
        fecha = datetime.now().strftime("%d/%m/%Y")
        c.drawString(x + 40, y + 45, f"PLU: {oferta['id']}")
        c.setFont("Helvetica", 9)
        c.drawString(x + 40, y + 32, f"Válido desde: {fecha}")

        # Barcode vectorial a la derecha
        barcode = code128.Code128(str(oferta["id"]), barHeight=10 * mm, barWidth=0.35)
        barcode_width = barcode.width
        barcode.drawOn(c, x + w - barcode_width - 40, y + 27)

    # =========================================================
    # OFERTA HORIZONTAL MEDIA HOJA (REPORTLAB)
    # =========================================================
    def dibujar_oferta_horizontal(self, c, oferta, x, y, w, h, rubro, negocio):
        rojo_accent = HexColor("#ef4444")
        naranja_accent = HexColor("#ea580c")
        amarillo_accent = HexColor("#facc15")
        gris_oscuro = HexColor("#0f172a")
        gris_medio = HexColor("#475569")

        # Fondo
        c.setFillColor(white)
        c.rect(x, y, w, h, fill=1, stroke=0)

        # Borde elegante "FUEGO" de alto impacto
        c.setStrokeColor(naranja_accent)
        c.setLineWidth(2.5)
        c.roundRect(x + 15, y + 15, w - 30, h - 30, 12, fill=0, stroke=1)
        
        c.setStrokeColor(amarillo_accent)
        c.setLineWidth(1)
        c.roundRect(x + 18, y + 18, w - 36, h - 36, 10, fill=0, stroke=1)

        # Header Badge (Píldora Roja de Oferta con borde amarillo)
        c.setFillColor(rojo_accent)
        c.setStrokeColor(amarillo_accent)
        c.setLineWidth(1)
        c.roundRect(x + 30, y + h - 55, 180, 25, 12, fill=1, stroke=1)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 12)
        
        texto_promo = str(oferta["tipo_promo"]).upper().strip()
        if not texto_promo:
            texto_promo = "¡SUPER OFERTA!"
        c.drawCentredString(x + 120, y + h - 48, texto_promo)

        # Dibujar dos hermosas flamas a los lados del Header Badge
        self.dibujar_flama(c, x + 15, y + h - 53, scale=0.4)
        self.dibujar_flama(c, x + 215, y + h - 53, scale=0.4)

        # Nombre del Negocio / Rubro
        c.setFillColor(gris_medio)
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(x + w - 35, y + h - 48, f"{rubro} • {negocio}".upper())

        # Separador sutil
        c.setStrokeColor(HexColor("#e2e8f0"))
        c.setLineWidth(1)
        c.line(x + 30, y + h - 68, x + w - 30, y + h - 68)

        # Nombre del Producto (Columna Izquierda)
        nombre = str(oferta["nombre"]).strip().upper()
        c.setFillColor(gris_oscuro)

        palabras = nombre.split()
        linea1 = []
        linea2 = []
        limite = 15
        for p in palabras:
            if len(" ".join(linea1 + [p])) <= limite:
                linea1.append(p)
            else:
                linea2.append(p)
        txt_l1 = " ".join(linea1)
        txt_l2 = " ".join(linea2)

        c.setFont("Helvetica-Bold", 24)
        if txt_l2:
            c.drawString(x + 35, y + h / 2 + 10, txt_l1)
            c.drawString(x + 35, y + h / 2 - 20, txt_l2)
        else:
            c.drawString(x + 35, y + h / 2, txt_l1)

        # Precio de Lista (Tachado)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(gris_medio)
        p_reg_txt = f"ANTES PRECIO RAYADO: ${oferta['precio_regular']}"
        c.drawString(x + 35, y + h / 2 - 55, p_reg_txt)
        w_reg = stringWidth(p_reg_txt, "Helvetica-Bold", 12)
        c.setStrokeColor(rojo_accent)
        c.setLineWidth(1.5)
        c.line(x + 35, y + h / 2 - 51, x + 35 + w_reg, y + h / 2 - 51)

        # Condición de Venta
        condicion = str(oferta.get("condicion_venta", "")).strip().upper()
        if condicion:
            # Fondo amarillo de atención para que resalte
            c.setFillColor(HexColor("#fef3c7"))
            c.setStrokeColor(naranja_accent)
            c.setLineWidth(0.8)
            c.roundRect(x + 35, y + h / 2 - 95, 230, 25, 6, fill=1, stroke=1)
            
            c.setFillColor(HexColor("#9a3412"))
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x + 45, y + h / 2 - 87, condicion)

        # Precio de Oferta Gigante (Columna Derecha)
        precio_of = str(oferta["precio_oferta"])
        if "." in precio_of:
            partes = precio_of.split(".")
            entero = partes[0]
            centavo = partes[1]
        else:
            entero = precio_of
            centavo = "00"

        font_size_price = 85
        font_size_symbol = 36

        c.setFont("Helvetica-Bold", font_size_price)
        ancho_entero = stringWidth(entero, "Helvetica-Bold", font_size_price)
        ancho_simbolo = stringWidth("$ ", "Helvetica-Bold", font_size_symbol)
        ancho_centavos = stringWidth(f".{centavo}", "Helvetica-Bold", font_size_symbol)

        ancho_total = ancho_simbolo + ancho_entero + ancho_centavos
        centro_derecho = x + w - (w/2 - 20)/2 - 20
        start_px = centro_derecho - ancho_total / 2

        y_precio_base = y + h / 2 - 25

        # Dibujar una flama espectacular a la izquierda del precio
        self.dibujar_flama(c, start_px - 28, y_precio_base - 5, scale=0.55)

        # Símbolo
        c.setFont("Helvetica-Bold", font_size_symbol)
        c.setFillColor(gris_medio)
        c.drawString(start_px, y_precio_base + 15, "$")

        # Entero
        c.setFont("Helvetica-Bold", font_size_price)
        c.setFillColor(rojo_accent)
        c.drawString(start_px + ancho_simbolo, y_precio_base - 10, entero)

        # Centavo
        c.setFont("Helvetica-Bold", font_size_symbol)
        c.setFillColor(rojo_accent)
        c.drawString(start_px + ancho_simbolo + ancho_entero, y_precio_base + 15, f".{centavo}")

        # Footer
        c.setFillColor(gris_oscuro)
        c.roundRect(x + 20, y + 20, w - 40, 38, 8, fill=1, stroke=0)

        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 8.5)
        fecha = datetime.now().strftime("%d/%m/%Y")
        c.drawString(x + 35, y + 33, f"PLU: {oferta['id']}  |  Válido desde: {fecha}")

        # Barcode
        barcode = code128.Code128(str(oferta["id"]), barHeight=6 * mm, barWidth=0.3)
        barcode_width = barcode.width
        barcode.drawOn(c, x + w - barcode_width - 35, y + 25)

    def generar_pdf_folleto_ofertas(self, lote_ofertas, titulo_folleto="FOLLETO DE OFERTAS", negocio="TPV PRO", diseno_tipo="grilla"):
        """
        Genera un folleto publicitario/catálogo en PDF en tamaño A4 con las ofertas especificadas.
        Sostiene dos diseños: 'grilla' (6 productos por página con tarjetas visuales) o 'lista' (tabla compacta elegante).
        """
        base_dir = os.path.join(self.base_path, "Folletos_Oferta")
        os.makedirs(base_dir, exist_ok=True)
        pdf_path = os.path.join(base_dir, "Folleto_Ofertas.pdf")
        
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(pdf_path)
        printer.setResolution(300)
        printer.setFullPage(True)
        printer.setPageMargins(10, 10, 10, 10, QPrinter.Millimeter)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setOrientation(QPrinter.Portrait)

        doc = QTextDocument()
        from PyQt5.QtCore import QSizeF
        doc.setPageSize(QSizeF(printer.pageRect().size()))
        doc.setDocumentMargin(0)
        fecha = datetime.now().strftime("%d/%m/%Y")
        
        html_pages = []
        
        if diseno_tipo == "grilla":
            # Agrupar ofertas de 6 en 6 para paginado
            items_per_page = 6
            chunks = [lote_ofertas[i:i + items_per_page] for i in range(0, len(lote_ofertas), items_per_page)]
            
            for chunk_idx, chunk in enumerate(chunks):
                is_last_page = (chunk_idx == len(chunks) - 1)
                page_break = "page-break-after: always;" if not is_last_page else ""
                
                # Armar filas de la grilla (de a 2 columnas)
                rows_html = ""
                for row_idx in range(0, len(chunk), 2):
                    row_items = chunk[row_idx:row_idx + 2]
                    
                    cols_html = ""
                    for item in row_items:
                        nombre = html.escape(str(item["nombre"]).upper())
                        precio_reg = str(item["precio_regular"])
                        precio_of = str(item["precio_oferta"])
                        cond_v = html.escape(str(item.get("condicion_venta", "")).upper())
                        
                        entero = precio_of.split('.')[0]
                        centavos = '.' + precio_of.split('.')[1] if '.' in precio_of else '.00'
                        
                        cond_badge_html = f"""
                        <div style="font-size: 9pt; font-weight: 800; color: #b45309; background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 5px; margin-top: 8px; text-transform: uppercase;">
                            {cond_v}
                        </div>
                        """ if cond_v else ""

                        cols_html += f"""
                        <td style="width: 50%; padding: 8px; vertical-align: top;">
                            <div style="border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff; padding: 16px; text-align: center; font-family: Arial; min-height: 60mm; box-sizing: border-box;">
                                <div style="background: #fee2e2; color: #ef4444; border: 1px solid #fecaca; font-weight: 800; font-size: 8.5pt; padding: 4px 12px; border-radius: 9999px; display: inline-block; margin-bottom: 8px; letter-spacing: 0.5px;">🔥 SÚPER OFERTA</div>
                                <div style="font-size: 11pt; font-weight: bold; color: #0f172a; height: 10mm; overflow: hidden; margin-bottom: 6px; line-height: 1.3; text-transform: uppercase;">
                                    {nombre}
                                </div>
                                <div style="font-size: 9.5pt; color: #64748b; margin-bottom: 4px; font-weight: bold;">
                                    Precio de Lista: <span style="text-decoration: line-through; color: #ef4444;">${precio_reg}</span>
                                </div>
                                <div style="color: #ef4444; margin-top: 2px;">
                                    <span style="font-size: 15pt; font-weight: bold; vertical-align: top;">$</span>
                                    <span style="font-size: 28pt; font-weight: 900; letter-spacing: -1.5px; line-height: 0.9;">{entero}</span>
                                    <span style="font-size: 14pt; font-weight: bold;">{centavos}</span>
                                </div>
                                {cond_badge_html}
                            </div>
                        </td>
                        """
                    # Si la fila tiene solo 1 producto, rellenar el otro con una celda vacía estética
                    if len(row_items) == 1:
                        cols_html += '<td style="width: 50%; padding: 8px;"></td>'
                        
                    rows_html += f"<tr>{cols_html}</tr>"
                
                page_html = f"""
                <div style="width: 100%; height: 98%; box-sizing: border-box; overflow: hidden; {page_break} font-family: Arial; padding: 10px; background: #f8fafc;">
                    <!-- HEADER DEL FOLLETO -->
                    <table style="width: 100%; background: #0f172a; border-radius: 12px; margin-bottom: 12px; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 20px; text-align: center;">
                                <div style="font-size: 22pt; font-weight: 900; color: white; letter-spacing: 3px; text-transform: uppercase; font-family: Arial;">
                                    {titulo_folleto}
                                </div>
                                <div style="font-size: 11pt; color: #38bdf8; font-weight: bold; margin-top: 6px; letter-spacing: 1px; text-transform: uppercase;">
                                    🛍️ {negocio.upper()} &bull; Ofertas Especiales al {fecha}
                                </div>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- CUADRÍCULA -->
                    <table style="width: 100%; border-collapse: collapse;">
                        {rows_html}
                    </table>
                    
                    <!-- FOOTER DEL FOLLETO -->
                    <div style="text-align: center; color: #64748b; font-size: 9pt; font-weight: bold; margin-top: 15px; border-top: 1px solid #e2e8f0; padding-top: 10px; letter-spacing: 2px;">
                        ¡APROVECHA NUESTRAS MEJORES OFERTAS! &bull; PÁGINA {chunk_idx + 1} DE {len(chunks)}
                    </div>
                </div>
                """
                html_pages.append(page_html)
                
        else: # Diseño "lista" (Tabla de promociones compacta)
            items_per_page = 14
            chunks = [lote_ofertas[i:i + items_per_page] for i in range(0, len(lote_ofertas), items_per_page)]
            
            for chunk_idx, chunk in enumerate(chunks):
                is_last_page = (chunk_idx == len(chunks) - 1)
                page_break = "page-break-after: always;" if not is_last_page else ""
                
                rows_html = ""
                for idx, item in enumerate(chunk):
                    bg_row = "#f8fafc" if idx % 2 == 1 else "#ffffff"
                    nombre = html.escape(str(item["nombre"]).upper())
                    precio_reg = str(item["precio_regular"])
                    precio_of = str(item["precio_oferta"])
                    cond_v = html.escape(str(item.get("condicion_venta", "")).upper())
                    
                    cond_td_html = f"""
                    <span style="background: #fffbeb; padding: 4px 12px; border-radius: 9999px; border: 1px solid #fde68a; color: #b45309; text-transform: uppercase;">
                        {cond_v}
                    </span>
                    """ if cond_v else ""

                    rows_html += f"""
                    <tr style="background: {bg_row};">
                        <td style="padding: 12px 10px; font-weight: bold; font-size: 11pt; color: #0f172a; border-bottom: 1px solid #e2e8f0;">
                            {nombre}
                        </td>
                        <td style="padding: 12px 10px; font-size: 11pt; color: #64748b; text-decoration: line-through; text-align: center; border-bottom: 1px solid #e2e8f0; font-weight: bold;">
                            ${precio_reg}
                        </td>
                        <td style="padding: 12px 10px; font-weight: 900; font-size: 13pt; color: #ef4444; text-align: center; border-bottom: 1px solid #e2e8f0;">
                            ${precio_of}
                        </td>
                        <td style="padding: 12px 10px; font-weight: bold; font-size: 9.5pt; color: #0f172a; text-align: center; border-bottom: 1px solid #e2e8f0;">
                            {cond_td_html}
                        </td>
                    </tr>
                    """
                
                page_html = f"""
                <div style="width: 100%; height: 98%; box-sizing: border-box; overflow: hidden; {page_break} font-family: Arial; padding: 10px; background: #ffffff;">
                    <!-- HEADER DEL FOLLETO -->
                    <table style="width: 100%; background: #0f172a; border-radius: 12px; margin-bottom: 15px; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 20px; text-align: center;">
                                <div style="font-size: 20pt; font-weight: 900; color: white; letter-spacing: 3px; text-transform: uppercase;">
                                    {titulo_folleto}
                                </div>
                                <div style="font-size: 11pt; color: #38bdf8; font-weight: bold; margin-top: 6px; text-transform: uppercase;">
                                    🛍️ Catálogo de Precios Especiales &bull; {negocio.upper()} &bull; {fecha}
                                </div>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- TABLA -->
                    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                        <thead>
                            <tr style="background: #1e293b; color: white;">
                                <th style="padding: 12px 10px; text-align: left; font-size: 10pt; font-weight: 800; background: #1e293b; color: white; border-top-left-radius: 8px; border-bottom-left-radius: 8px;">PRODUCTO / DESCRIPCIÓN</th>
                                <th style="padding: 12px 10px; text-align: center; font-size: 10pt; font-weight: 800; background: #1e293b; color: white; width: 150px;">PRECIO DE LISTA</th>
                                <th style="padding: 12px 10px; text-align: center; font-size: 10pt; font-weight: 800; background: #1e293b; color: white; width: 120px;">🔥 OFERTA</th>
                                <th style="padding: 12px 10px; text-align: center; font-size: 10pt; font-weight: 800; background: #1e293b; color: white; width: 220px; border-top-right-radius: 8px; border-bottom-right-radius: 8px;">DETALLE DE PROMOCIÓN</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                    
                    <!-- FOOTER -->
                    <div style="text-align: center; color: #64748b; font-size: 9pt; font-weight: bold; margin-top: 25px; border-top: 1px solid #e2e8f0; padding-top: 10px; letter-spacing: 1.5px;">
                        ¡COMPRA INTELIGENTE, AHORRA SIEMPRE! &bull; PÁGINA {chunk_idx + 1} DE {len(chunks)}
                    </div>
                </div>
                """
                html_pages.append(page_html)

        full_html = f"""
        <html>
        <head><style>body {{ margin:0; padding:0; background:white; }}</style></head>
        <body>{''.join(html_pages)}</body>
        </html>
        """
        
        doc.setHtml(full_html)
        doc.print_(printer)
        
        del printer
        del doc
        self.limpiar_tmp()
        return pdf_path

    def generar_pdf_gondola_personalizado(self, productos, rubro="CARNICERÍA", negocio="MACIEL", grilla_tipo="3x7", mostrar_barcode=True, mostrar_marca=True, mostrar_fecha=True, estilo_tipo="clasico"):
        """
        Genera un PDF con etiquetas de góndola en A4 utilizando una grilla personalizada:
        - '3x7' (21 etiquetas por página, 70x42mm)
        - '3x10' (30 etiquetas por página, 70x29mm)
        - '4x10' (40 etiquetas por página, 52x29mm)
        Admite estilos: 'clasico', 'minimalista', 'neon'.
        """
        base_dir = os.path.join(self.base_path, "Etiquetas_Impresas")
        os.makedirs(base_dir, exist_ok=True)
        
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        pdf_path = os.path.join(base_dir, f"Etiquetas_Personalizadas_{timestamp}.pdf")
        
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(pdf_path)
        printer.setResolution(300)
        printer.setFullPage(True)
        printer.setPageMargins(5, 5, 5, 5, QPrinter.Millimeter)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setOrientation(QPrinter.Portrait)

        doc = QTextDocument()
        doc.setDefaultStyleSheet("body { background-color: #ffffff; color: #000000; }")
        from PyQt5.QtCore import QSizeF
        doc.setPageSize(QSizeF(printer.pageRect().size()))
        doc.setDocumentMargin(0)
        fecha = datetime.now().strftime("%d/%m/%Y")
        
        # Determinar dimensiones de la grilla
        if grilla_tipo == "3x7":
            cols = 3; rows = 7; cell_w = "33.3%"; cell_h = "40.5mm"
        elif grilla_tipo == "3x10":
            cols = 3; rows = 10; cell_w = "33.3%"; cell_h = "28.1mm"
        elif grilla_tipo == "4x10":
            cols = 4; rows = 10; cell_w = "25%"; cell_h = "28.1mm"
        else:
            cols = 3; rows = 7; cell_w = "33.3%"; cell_h = "40.5mm"
            
        items_per_page = cols * rows
        chunks = [productos[i:i + items_per_page] for i in range(0, len(productos), items_per_page)]
        
        html_pages = []
        for chunk_idx, chunk in enumerate(chunks):
            is_last_page = (chunk_idx == len(chunks) - 1)
            page_break = "page-break-after: always;" if not is_last_page else ""
            
            grid_html = '<table style="width:100%; height:99%; border-collapse:separate; border-spacing:6px; table-layout:fixed; background-color:#ffffff;">'
            for r in range(rows):
                grid_html += '<tr>'
                for c_idx in range(cols):
                    item_idx = r * cols + c_idx
                    if item_idx < len(chunk):
                        p = chunk[item_idx]
                        codigo_real = str(p['id']).strip()
                        barcode_img_url = ""
                        if mostrar_barcode and codigo_real:
                            filename_seguro = "".join(c for c in codigo_real if c.isalnum() or c in "-_")
                            if not filename_seguro: filename_seguro = "temp_code"
                            barcode_img_url = self.generar_barcode(codigo_real, filename_seguro)
                        
                        nombre = html.escape(str(p['nombre']).upper())
                        precio = f"{float(p['precio']):.2f}"
                        unidad = html.escape(str(p.get('unidad', 'UN')).upper())
                        
                        is_oferta = p.get("is_oferta", False)
                        
                        # Generar condición de promoción si existe cant_oferta
                        condicion = ""
                        if is_oferta:
                            cant_of = float(p.get("cant_oferta") or 0)
                            tipo_u = str(p.get("tipo_unidad_oferta") or "Unidades").lower()
                            if cant_of > 0:
                                if tipo_u == "kilos" or p.get("unidad", "").upper() == "KG":
                                    condicion = f"DESDE {cant_of:g} KG"
                                else:
                                    condicion = f"LLEVANDO {int(cant_of)} UN"
                                    
                        condicion_html = ""
                        if condicion:
                            bc_margin = "1px" if grilla_tipo == "3x7" else "0px"
                            condicion_html = f'<div style="text-align:center; font-size:7pt; font-weight:bold; color:#dc2626; margin-top:{bc_margin}; background:#fee2e2; border-radius:3px; padding:1px 0; max-height:4mm; overflow:hidden; line-height:1;">{condicion}</div>'

                        # Definir bordes y estilos de la celda TD directamente
                        if is_oferta:
                            bg_color = "#fffaf5" if estilo_tipo == "minimalista" else "#ffffff"
                            if estilo_tipo == "neon":
                                border_style = "2px solid #ea580c; border-radius: 8px;"
                            elif estilo_tipo == "minimalista":
                                border_style = "1px solid #fdba74; border-radius: 4px;"
                            else: # clasico
                                border_style = "1px solid #ea580c;"
                        else:
                            bg_color = "#ffffff"
                            if estilo_tipo == "neon":
                                border_style = "2px solid #2563eb; border-radius: 8px;"
                            elif estilo_tipo == "minimalista":
                                border_style = "1px solid #cbd5e1; border-radius: 4px;"
                            else: # clasico
                                border_style = "1px solid #94a3b8;"
                            
                        # Encabezado comercial de la tarjeta
                        brand_header = ""
                        if mostrar_marca:
                            if is_oferta:
                                brand_text = f"🔥 OFERTA: {rubro} - {negocio}"
                                if estilo_tipo == "clasico":
                                    brand_header = f'<div style="background:#ea580c; color:white; font-size:6.5pt; font-weight:bold; height:5mm; line-height:5mm; overflow:hidden; text-align:center; white-space:nowrap; text-overflow:ellipsis;">{brand_text}</div>'
                                elif estilo_tipo == "neon":
                                    brand_header = f'<div style="background:#dc2626; color:white; font-size:7pt; font-weight:bold; height:5.5mm; line-height:5.5mm; border-top-left-radius:6px; border-top-right-radius:6px; overflow:hidden; text-align:center; white-space:nowrap; text-overflow:ellipsis;">{brand_text}</div>'
                                else: # minimalista
                                    brand_header = f'<div style="color:#ea580c; font-size:6.5pt; font-weight:bold; height:4.5mm; line-height:4.5mm; border-bottom:1px solid #ffedd5; overflow:hidden; text-align:center; white-space:nowrap; text-overflow:ellipsis;">{brand_text}</div>'
                            else:
                                brand_text = f"🛒 {rubro} - {negocio}"
                                if estilo_tipo == "clasico":
                                    brand_header = f'<div style="background:#082c63; color:white; font-size:6.5pt; font-weight:bold; height:5mm; line-height:5mm; overflow:hidden; text-align:center; white-space:nowrap; text-overflow:ellipsis;">{brand_text}</div>'
                                elif estilo_tipo == "neon":
                                    brand_header = f'<div style="background:#1e3a8a; color:white; font-size:7pt; font-weight:bold; height:5.5mm; line-height:5.5mm; border-top-left-radius:6px; border-top-right-radius:6px; overflow:hidden; text-align:center; white-space:nowrap; text-overflow:ellipsis;">{brand_text}</div>'
                                else: # minimalista
                                    brand_header = f'<div style="color:#64748b; font-size:6.5pt; font-weight:bold; height:4.5mm; line-height:4.5mm; border-bottom:1px solid #f1f5f9; overflow:hidden; text-align:center; white-space:nowrap; text-overflow:ellipsis;">{brand_text}</div>'
                        
                        # Imagen del código de barras
                        barcode_html = ""
                        if mostrar_barcode and barcode_img_url:
                            bc_h = "7.5mm" if grilla_tipo == "3x7" else "5.5mm"
                            barcode_html = f'<div style="text-align:center; margin-top:2px;"><img src="{barcode_img_url}" style="height:{bc_h}; width:88%;"></div>'
                            
                        meta_html = ""
                        if is_oferta and p.get("precio_regular"):
                            try:
                                p_reg_val = float(p.get("precio_regular"))
                                meta_html = f'<div style="font-size:6.5pt; color:#475569; text-align:center; margin-top:2px; font-weight:bold;">PLU: {p["id"]} &bull; Antes: <span style="text-decoration: line-through; color: #ef4444; font-weight:normal;">${p_reg_val:.2f}</span></div>'
                            except Exception:
                                pass
                        
                        if not meta_html and mostrar_fecha:
                            meta_html = f'<div style="font-size:5.5pt; color:#64748b; text-align:center; margin-top:2px;">PLU:{p["id"]} &bull; {fecha}</div>'
                        
                        # Tamaño de fuente del precio adaptativo
                        price_font = "26pt" if grilla_tipo == "3x7" else "18pt"
                        if len(precio.split('.')[0]) >= 4:
                            price_font = "20pt" if grilla_tipo == "3x7" else "14pt"
                        
                        if is_oferta:
                            price_color = "#dc2626"
                        else:
                            if estilo_tipo == "clasico":
                                price_color = "#1e3a8a" # Navy Blue for standard
                            elif estilo_tipo == "neon":
                                price_color = "#2563eb" # Royal Blue
                            else: # minimalista
                                price_color = "#1e293b" # Slate
                        
                        # Altura máxima del nombre
                        name_h = "8mm" if grilla_tipo == "3x7" else "6mm"
                        name_font = "8.5pt" if grilla_tipo == "3x7" else "7.5pt"
                        
                        display_nombre = f"🔥 {nombre}" if is_oferta else nombre
                        
                        grid_html += f"""
                        <td style="width:{cell_w}; height:{cell_h}; border:{border_style} background-color:{bg_color}; vertical-align:top; padding:0; box-sizing:border-box;">
                            {brand_header}
                            <div style="padding: 4px; box-sizing:border-box;">
                                <!-- Nombre de Producto -->
                                <div style="font-size:{name_font}; font-weight:bold; color:#0f172a; height:{name_h}; overflow:hidden; line-height:1.2; text-transform:uppercase; text-align:center; margin-top:2px;">
                                    {display_nombre}
                                </div>
                                <!-- Precio de Venta -->
                                <div style="text-align:center; color:{price_color}; margin-top:2px;">
                                    <span style="font-size:10pt; font-weight:bold; vertical-align:top;">$</span>
                                    <span style="font-size:{price_font}; font-weight:900; letter-spacing:-1px; line-height:0.9;">{precio.split('.')[0]}</span>
                                    <span style="font-size:10pt; font-weight:bold;">.{precio.split('.')[1]}</span>
                                    <span style="font-size:6.5pt; color:#64748b; font-weight:bold;">/{unidad}</span>
                                </div>
                                {condicion_html}
                                {barcode_html}
                                {meta_html}
                            </div>
                        </td>
                        """
                    else:
                        grid_html += f'<td style="width:{cell_w}; height:{cell_h}; border:none; background:transparent;"></td>'
                grid_html += '</tr>'
            grid_html += '</table>'
            
            page_html = f"""
            <div style="width:100%; height:99%; box-sizing:border-box; overflow:hidden; {page_break} background-color:#ffffff; padding:5px;">
                {grid_html}
            </div>
            """
            html_pages.append(page_html)
            
        full_html = f"""
        <html>
        <head>
        <style>
        body {{ margin:0; padding:0; background-color:#ffffff; color:#000000; }}
        table {{ background-color:#ffffff; }}
        td {{ background-color:#ffffff; }}
        </style>
        </head>
        <body>{''.join(html_pages)}</body>
        </html>
        """
        
        doc.setHtml(full_html)
        doc.print_(printer)
        
        del printer
        del doc
        self.limpiar_tmp()
        return pdf_path

    def limpiar_tmp(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
