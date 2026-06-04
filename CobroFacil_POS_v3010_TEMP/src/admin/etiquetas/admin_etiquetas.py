import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit,
    QDialog, QFormLayout, QComboBox, QRadioButton, QFrame, QGridLayout,
    QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

from src.services.etiquetas.renderer import EtiquetaRenderer, abrir_archivo_pdf

class AdminEtiquetas(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.productos_impresos_etiquetas = set() # Productos impresos como etiqueta normal (AZUL)
        self.productos_impresos_ofertas = set()   # Productos impresos como oferta (NARANJA)
        self.productos_seleccionados = {}         # Caché de productos seleccionados en memoria: {id_str: p_data}
        self.setup_ui()
        self.cargar_productos()
        self.actualizar_materia_prima_count()

    def setup_ui(self):
        # Sleek light industrial theme matching the global TPV application
        self.setStyleSheet("""
            QWidget { 
                background-color: #f8fafc; 
                color: #1e293b; 
                font-family: 'Segoe UI', 'Outfit', sans-serif; 
                font-size: 13px; 
            }
            QLabel {
                background: transparent;
            }
            QFrame#topDeck {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 16px;
            }
            QTableWidget { 
                background-color: white; 
                color: #1e293b; 
                gridline-color: #e2e8f0; 
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                font-size: 14px; 
                selection-background-color: #f1f5f9; 
                selection-color: #0f172a;
            }
            QHeaderView::section { 
                background-color: #f8fafc; 
                color: #475569; 
                border: 1px solid #cbd5e1;
                padding: 10px; 
                font-weight: bold;
                font-size: 12px;
                text-transform: uppercase;
            }
            QLineEdit {
                background: white; 
                border: 1px solid #cbd5e1; 
                border-radius: 8px; 
                color: #1e293b; 
                padding: 12px; 
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
            QPushButton {
                background-color: white; 
                color: #1e3a8a; 
                padding: 12px 24px; 
                font-weight: 900; 
                border-radius: 8px; 
                border: 1px solid #cbd5e1;
                letter-spacing: 0.5px;
            }
            QPushButton:hover { 
                background-color: #f1f5f9; 
                color: #3b82f6;
            }
            QPushButton#btnBack { 
                background-color: white; 
                border: 1px solid #ef4444; 
                color: #ef4444; 
                font-weight: 800;
            }
            QPushButton#btnBack:hover {
                background-color: #fef2f2;
                color: #ef4444;
            }
            QPushButton#btnPrint { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #6366f1);
                color: white; 
                font-size: 14px; 
                border: none;
            }
            QPushButton#btnPrint:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #4f46e5);
            }
            QPushButton#btnPrintOfertas { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ea580c, stop:1 #f97316);
                color: white; 
                font-size: 14px; 
                border: none;
            }
            QPushButton#btnPrintOfertas:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c2410c, stop:1 #ea580c);
            }
            QPushButton#btnSelectOfertas { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f59e0b, stop:1 #ea580c);
                color: white; 
                font-size: 14px; 
                border: none;
            }
            QPushButton#btnSelectOfertas:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #d05206);
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # --- HEADER PRINCIPAL ---
        header_layout = QHBoxLayout()
        btn_back = QPushButton("⬅ VOLVER", objectName="btnBack")
        btn_back.clicked.connect(self.request_dashboard.emit)
        btn_back.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(btn_back)
        
        header_title = QLabel("🏭 PLANTA DE IMPRESIÓN & ETIQUETADO ELITE")
        header_title.setStyleSheet("font-size: 24px; font-weight: 900; color: #0f172a; letter-spacing: 1px;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        
        # Indicador de estado del motor en línea
        lbl_status = QLabel("🟢 MOTOR EN LÍNEA")
        lbl_status.setStyleSheet("background-color: #ecfdf5; color: #10b981; font-weight: 900; border-radius: 8px; padding: 8px 16px; border: 1px solid #a7f3d0;")
        header_layout.addWidget(lbl_status)
        
        main_layout.addLayout(header_layout)

        # --- TOP STATS DECK: LA MATERIA PRIMA (INVENTARIO) ---
        self.top_deck = QFrame(objectName="topDeck")
        deck_lay = QGridLayout(self.top_deck)
        deck_lay.setContentsMargins(20, 20, 20, 20)
        deck_lay.setSpacing(20)
        
        # Card 1: Materia Prima
        self.lbl_stat_materia = QLabel("📦 MATERIA PRIMA (INVENTARIO)<br><b>Cargando catálogo...</b>")
        self.lbl_stat_materia.setTextFormat(Qt.RichText)
        self.lbl_stat_materia.setStyleSheet("font-size: 14px; color: #475569; line-height: 1.4;")
        deck_lay.addWidget(self.lbl_stat_materia, 0, 0)
        
        # Card 2: Lote Activo
        self.lbl_stat_lote = QLabel("⚡ HILO DE SELECCIÓN DE IMPRESIÓN<br><span style='color:#3b82f6; font-size:18px; font-weight:900;'>0 Productos</span>")
        self.lbl_stat_lote.setTextFormat(Qt.RichText)
        self.lbl_stat_lote.setStyleSheet("font-size: 14px; color: #475569; line-height: 1.4;")
        deck_lay.addWidget(self.lbl_stat_lote, 0, 1)

        # Card 3: Configuración de Marca Comercial
        self.lbl_stat_marca = QLabel("🏢 MARCA REGISTRADA COMERCIAL<br><span style='color:#a855f7; font-size:16px; font-weight:900;'>MACIEL - CARNICERÍA</span>")
        self.lbl_stat_marca.setTextFormat(Qt.RichText)
        self.lbl_stat_marca.setStyleSheet("font-size: 14px; color: #475569; line-height: 1.4;")
        deck_lay.addWidget(self.lbl_stat_marca, 0, 2)
        
        main_layout.addWidget(self.top_deck)

        # --- CONTROL DE PARÁMETROS DE MARCA EN CALIENTE ---
        brand_layout = QHBoxLayout()
        
        lbl_r = QLabel("RUBRO COMERCIAL:"); lbl_r.setStyleSheet("font-weight: 900; font-size: 11px; color: #64748b; letter-spacing: 1px;")
        self.txt_rubro = QLineEdit()
        self.txt_rubro.setPlaceholderText("RUBRO (Ej: CARNICERÍA)")
        self.txt_rubro.setText("CARNICERÍA")
        self.txt_rubro.setStyleSheet("font-weight: bold; color: #a855f7; font-size: 14px; border: 1px solid #cbd5e1;")
        self.txt_rubro.textChanged.connect(self.actualizar_marca_de_impresion)
        
        lbl_n = QLabel("NEGOCIO:"); lbl_n.setStyleSheet("font-weight: 900; font-size: 11px; color: #64748b; letter-spacing: 1px;")
        self.txt_negocio = QLineEdit()
        self.txt_negocio.setPlaceholderText("NEGOCIO (Ej: MACIEL)")
        self.txt_negocio.setText("MACIEL")
        self.txt_negocio.setStyleSheet("font-weight: bold; color: #3b82f6; font-size: 14px; border: 1px solid #cbd5e1;")
        self.txt_negocio.textChanged.connect(self.actualizar_marca_de_impresion)
        
        brand_layout.addWidget(lbl_r); brand_layout.addWidget(self.txt_rubro)
        brand_layout.addSpacing(15)
        brand_layout.addWidget(lbl_n); brand_layout.addWidget(self.txt_negocio)
        main_layout.addLayout(brand_layout)

        # --- FILTRO DEL FLUJO DE ENTRADA (Buscador) ---
        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 ESCANEA CÓDIGO O ESCRIBE NOMBRE DE PRODUCTO PARA FILTRAR EN TIEMPO REAL...")
        self.txt_search.setStyleSheet("font-size: 15px; padding: 14px; font-weight: bold; border-color: #cbd5e1;")
        self.txt_search.textChanged.connect(self.cargar_productos)
        search_layout.addWidget(self.txt_search)
        main_layout.addLayout(search_layout)

        # --- TABLA DE PROCESAMIENTO (LA MATERIA PRIMA AL NATURAL) ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["PROCESAR", "ID / PLU", "DESCRIPCIÓN DEL PRODUCTO", "PRECIO DE VENTA", "CATEGORÍA"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.itemChanged.connect(self.actualizar_contador_seleccionados)
        main_layout.addWidget(self.tabla)
        
        # --- PANEL DE ACCIÓN Y LANZAMIENTO INDUSTRIAL ---
        btn_layout = QHBoxLayout()
        self.btn_select_all = QPushButton("☑️ SELECCIÓN TOTAL")
        self.btn_select_all.clicked.connect(self.seleccionar_todo)
        self.btn_select_all.setCursor(Qt.PointingHandCursor)

        self.btn_print = QPushButton("🏭 LANZAR IMPRESIÓN GÓNDOLA (PDF)", objectName="btnPrint")
        self.btn_print.clicked.connect(self.generar_pdf)
        self.btn_print.setCursor(Qt.PointingHandCursor)
        
        btn_layout.addWidget(self.btn_select_all)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_print)
        main_layout.addLayout(btn_layout)

    def cargar_productos(self):
        txt = self.txt_search.text().strip()
        
        # Bloquear señales temporalmente para que no se dispare el conteo dinámico durante la carga
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(0)
        
        query = "SELECT id, nombre, precio, categoria, unidad, cant_oferta, precio_oferta, tipo_unidad_oferta FROM productos"
        params = []
        if txt:
            query += " WHERE id LIKE ? OR nombre LIKE ? OR codigo LIKE ?"
            params = [f"%{txt}%", f"%{txt}%", f"%{txt}%"]
            
        prods = db_manager.execute_query(query, tuple(params))
        for i, p in enumerate(prods or []):
            self.tabla.insertRow(i)
            
            p_id_str = str(p['id'])
            is_etiqueta = p_id_str in self.productos_impresos_etiquetas
            is_oferta = p_id_str in self.productos_impresos_ofertas
            is_printed = is_etiqueta or is_oferta
            is_ambos = is_etiqueta and is_oferta
            
            # Checkbox estilizado (solo habilitado si no ha sido impreso)
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            if p_id_str in self.productos_seleccionados:
                chk.setCheckState(Qt.Checked)
            else:
                chk.setCheckState(Qt.Unchecked)
            
            p_data_payload = {
                "id": p["id"],
                "nombre": p["nombre"],
                "precio": p["precio"],
                "categoria": p["categoria"],
                "unidad": p["unidad"] or 'UN',
                "cant_oferta": p["cant_oferta"],
                "precio_oferta": p["precio_oferta"],
                "tipo_unidad_oferta": p["tipo_unidad_oferta"] if 'tipo_unidad_oferta' in p.keys() else "Unidades"
            }
            chk.setData(Qt.UserRole, p_data_payload)
            self.tabla.setItem(i, 0, chk)
            
            id_text = p_id_str
            if is_printed:
                id_text += " ✓"
            id_item = QTableWidgetItem(id_text)
            id_item.setForeground(QColor("#64748b"))
            id_item.setFont(QFont("Consolas", 10, QFont.Bold))
            self.tabla.setItem(i, 1, id_item)
            
            nom_text = str(p['nombre'])
            if is_printed:
                if is_ambos:
                    nom_text = "🏷️🔥 [AMBOS] " + nom_text
                elif is_oferta:
                    nom_text = "🔥 [OFERTA] " + nom_text
                else:
                    nom_text = "🏷️ [ETIQUETA] " + nom_text
            
            nom_item = QTableWidgetItem(nom_text)
            nom_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            if is_printed:
                if is_ambos:
                    nom_item.setForeground(QColor("#6d28d9")) # Violeta imperial elegante
                elif is_oferta:
                    nom_item.setForeground(QColor("#c2410c")) # Naranja óxido elegante
                else:
                    nom_item.setForeground(QColor("#0369a1")) # Azul acero elegante
            else:
                nom_item.setForeground(QColor("#1e293b"))
            self.tabla.setItem(i, 2, nom_item)
            
            pr_item = QTableWidgetItem(f"${p['precio']:.2f}")
            if is_printed:
                if is_ambos:
                    pr_item.setForeground(QColor("#7c3aed"))
                elif is_oferta:
                    pr_item.setForeground(QColor("#ea580c"))
                else:
                    pr_item.setForeground(QColor("#0284c7"))
            else:
                pr_item.setForeground(QColor("#10b981"))
            pr_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            self.tabla.setItem(i, 3, pr_item)
            
            cat = p['categoria'] if p['categoria'] else 'GENERAL'
            cat_item = QTableWidgetItem(str(cat).upper())
            if is_printed:
                if is_ambos:
                    cat_item.setForeground(QColor("#8b5cf6"))
                elif is_oferta:
                    cat_item.setForeground(QColor("#f97316"))
                else:
                    cat_item.setForeground(QColor("#3b82f6"))
            else:
                cat_item.setForeground(QColor("#3b82f6"))
            self.tabla.setItem(i, 4, cat_item)
            
            # Guardamos los datos completos del producto en el rol personalizado para usarlo de forma robusta
            self.tabla.item(i, 1).setData(Qt.UserRole, {
                "id": p["id"],
                "nombre": p["nombre"],
                "precio": p["precio"],
                "categoria": p["categoria"],
                "unidad": p["unidad"] or 'UN',
                "cant_oferta": p["cant_oferta"],
                "precio_oferta": p["precio_oferta"],
                "tipo_unidad_oferta": p["tipo_unidad_oferta"] if 'tipo_unidad_oferta' in p.keys() else "Unidades"
            })
            
            # Resaltado inteligente: Lavanda para ambos, Naranja para oferta, Azul para etiqueta
            if is_printed:
                if is_ambos:
                    bg_color = QColor("#f3e8ff") # Tonalidad HSL suave lavanda
                elif is_oferta:
                    bg_color = QColor("#ffedd5") # Tonalidad HSL suave naranja
                else:
                    bg_color = QColor("#e0f2fe") # Tonalidad HSL suave celeste
                for col in range(5):
                    self.tabla.item(i, col).setBackground(bg_color)
            
        self.tabla.blockSignals(False)
        self.actualizar_contador_seleccionados()

    def actualizar_materia_prima_count(self):
        try:
            res = db_manager.execute_query("SELECT COUNT(*) as cant FROM productos")
            count = res[0]['cant'] if res else 0
            self.lbl_stat_materia.setText(
                f"📦 MATERIA PRIMA (INVENTARIO)<br>"
                f"<span style='color:#10b981; font-size:18px; font-weight:900;'>{count} Productos</span>"
            )
        except Exception:
            self.lbl_stat_materia.setText("📦 MATERIA PRIMA (INVENTARIO)<br><span style='color:#ef4444;'>Error de Base de Datos</span>")

    def actualizar_contador_seleccionados(self, item=None):
        if item is not None and item.column() == 0:
            p_data = item.data(Qt.UserRole)
            if isinstance(p_data, dict):
                p_id_str = str(p_data["id"])
                if item.checkState() == Qt.Checked:
                    self.productos_seleccionados[p_id_str] = p_data
                else:
                    self.productos_seleccionados.pop(p_id_str, None)
                
        seleccionados = len(self.productos_seleccionados)
        self.lbl_stat_lote.setText(
            f"⚡ HILO DE SELECCIÓN DE IMPRESIÓN<br>"
            f"<span style='color:#3b82f6; font-size:18px; font-weight:900;'>{seleccionados} Selección</span>"
        )

    def actualizar_marca_de_impresion(self):
        rubro = self.txt_rubro.text().strip().upper() or "CARNICERÍA"
        negocio = self.txt_negocio.text().strip().upper() or "MACIEL"
        self.lbl_stat_marca.setText(
            f"🏢 MARCA REGISTRADA COMERCIAL<br>"
            f"<span style='color:#a855f7; font-size:16px; font-weight:900;'>{negocio} - {rubro}</span>"
        )

    def seleccionar_todo(self):
        self.tabla.blockSignals(True)
        # Toggle inteligente: si todos los visibles ya están seleccionados, deseleccionamos todos los visibles.
        # De lo contrario, seleccionamos todos los visibles.
        all_checked = True
        for i in range(self.tabla.rowCount()):
            item = self.tabla.item(i, 0)
            if item and item.checkState() != Qt.Checked:
                all_checked = False
                break
                
        target_state = Qt.Unchecked if all_checked else Qt.Checked
        
        for i in range(self.tabla.rowCount()):
            item = self.tabla.item(i, 0)
            if item:
                item.setCheckState(target_state)
                p_data = item.data(Qt.UserRole)
                if isinstance(p_data, dict):
                    p_id_str = str(p_data["id"])
                    if target_state == Qt.Checked:
                        self.productos_seleccionados[p_id_str] = p_data
                    else:
                        self.productos_seleccionados.pop(p_id_str, None)
        self.tabla.blockSignals(False)
        self.actualizar_contador_seleccionados()

    def generar_pdf(self):
        rubro = self.txt_rubro.text().strip() or "CARNICERÍA"
        negocio = self.txt_negocio.text().strip() or "MACIEL"

        if not self.productos_seleccionados:
            QMessageBox.warning(self, "Aviso", "Selecciona al menos un producto de la materia prima para imprimir.")
            return

        # LÍMITE INDUSTRIAL DE SEGURIDAD CONTRA TRABAS
        LIMIT_MAX = 1000
        if len(self.productos_seleccionados) > LIMIT_MAX:
            QMessageBox.warning(
                self, 
                "Límite de Impresión Excedido", 
                f"⚠️ Lote de Impresión Demasiado Grande\n\n"
                f"Para garantizar un procesamiento instantáneo en Windows y evitar congelamientos de la cola de impresión, "
                f"el límite de seguridad configurado es de {LIMIT_MAX} etiquetas por lote.\n\n"
                f"Seleccionaste: {len(self.productos_seleccionados)} etiquetas.\n"
                f"Por favor, reduce la selección e imprime en lotes más pequeños."
            )
            return

        seleccionados = []
        for p_data in self.productos_seleccionados.values():
            p_id = str(p_data["id"])
            cant_of = float(p_data.get("cant_oferta") or 0)
            precio_of = float(p_data.get("precio_oferta") or 0)
            is_db_oferta = (cant_of > 0 and precio_of > 0)
            is_oferta = is_db_oferta or (p_id in self.productos_impresos_ofertas)
            precio_final = precio_of if (is_db_oferta and precio_of > 0) else p_data["precio"]
            
            seleccionados.append({
                "id": p_id,
                "nombre": p_data["nombre"],
                "precio": str(precio_final),
                "precio_regular": str(p_data["precio"]),
                "categoria": p_data["categoria"] or "GENERAL",
                "unidad": p_data["unidad"] or "UN",
                "is_oferta": is_oferta,
                "cant_oferta": cant_of,
                "precio_oferta": precio_of,
                "tipo_unidad_oferta": p_data.get("tipo_unidad_oferta") or "Unidades"
            })
                
        # Diálogo para configurar el formato del PDF de etiquetas de góndola
        dlg = QDialog(self)
        dlg.setWindowTitle("Configuración de Etiquetas de Góndola")
        dlg.setFixedSize(480, 420)
        dlg.setStyleSheet("""
            QDialog { background: white; color: #0f172a; font-family: 'Segoe UI'; font-size: 13px; }
            QPushButton { background: #3b82f6; color: white; font-weight: bold; padding: 10px; border-radius: 6px; border: none; font-size: 12px; }
            QPushButton:hover { background: #2563eb; }
            QLineEdit, QComboBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; color: #1e293b; background: white; }
            QRadioButton, QCheckBox { spacing: 8px; font-weight: bold; }
        """)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)
        
        lbl_tit = QLabel("🖨️ CONFIGURAR FORMATO DE ETIQUETAS")
        lbl_tit.setStyleSheet("color: #1e3a8a; font-size: 15px; font-weight: 900; letter-spacing: 0.5px;")
        lay.addWidget(lbl_tit)
        
        # Formulario de estilos
        form = QFormLayout()
        form.setSpacing(10)
        
        cmb_estilo = QComboBox()
        cmb_estilo.addItem("⚪ Estilo Minimalista (Limpio)", "minimalista")
        cmb_estilo.addItem("🔵 Estilo Clásico (Azul)", "clasico")
        cmb_estilo.addItem("⚡ Estilo Neón (Borde Moderno)", "neon")
        
        form.addRow("<b>Estilo Visual:</b>", cmb_estilo)
        lay.addLayout(form)
        
        # Opciones de Distribución (Grilla)
        lay.addWidget(QLabel("<b>Distribución de Página (Grilla A4):</b>"))
        lay_grid = QVBoxLayout()
        rb_3x7 = QRadioButton("Estándar: 21 etiquetas por hoja (3x7 - 70x42mm)")
        rb_3x7.setChecked(True)
        rb_3x10 = QRadioButton("Compacto: 30 etiquetas por hoja (3x10 - 70x29mm)")
        rb_4x10 = QRadioButton("Mini: 40 etiquetas por hoja (4x10 - 52x29mm)")
        
        lay_grid.addWidget(rb_3x7)
        lay_grid.addWidget(rb_3x10)
        lay_grid.addWidget(rb_4x10)
        lay.addLayout(lay_grid)
        
        # Checkboxes de visibilidad
        lay.addWidget(QLabel("<b>Opciones de Contenido:</b>"))
        lay_opts = QVBoxLayout()
        chk_barcode = QCheckBox("Mostrar Código de Barras")
        chk_barcode.setChecked(True)
        chk_marca = QCheckBox("Mostrar Nombre de Negocio / Rubro")
        chk_marca.setChecked(True)
        chk_fecha = QCheckBox("Mostrar Fecha de Impresión y PLU")
        chk_fecha.setChecked(True)
        
        lay_opts.addWidget(chk_barcode)
        lay_opts.addWidget(chk_marca)
        lay_opts.addWidget(chk_fecha)
        lay.addLayout(lay_opts)
        
        btn_ok = QPushButton("🏭 Iniciar Imprenta y Generar PDF")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(dlg.accept)
        lay.addSpacing(10)
        lay.addWidget(btn_ok)
        
        if dlg.exec_():
            # Determinar tipo de grilla
            grilla = "3x7"
            if rb_3x10.isChecked(): grilla = "3x10"
            elif rb_4x10.isChecked(): grilla = "4x10"
            
            try:
                renderer = EtiquetaRenderer()
                pdf_path = renderer.generar_pdf_gondola_personalizado(
                    productos=seleccionados,
                    rubro=rubro,
                    negocio=negocio,
                    grilla_tipo=grilla,
                    mostrar_barcode=chk_barcode.isChecked(),
                    mostrar_marca=chk_marca.isChecked(),
                    mostrar_fecha=chk_fecha.isChecked(),
                    estilo_tipo=cmb_estilo.currentData()
                )
                
                # Abrir el PDF automáticamente de manera robusta
                abrir_archivo_pdf(pdf_path)

                # Registrar como impresos
                for p in seleccionados:
                    p_id = str(p['id'])
                    if p.get('is_oferta'):
                        self.productos_impresos_ofertas.add(p_id)
                    else:
                        self.productos_impresos_etiquetas.add(p_id)
                        
                # Vaciar la lista de seleccionados tras imprimir exitosamente
                self.productos_seleccionados.clear()
                    
                # Recargar al instante para resaltar
                self.cargar_productos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo generar el PDF: {str(e)}")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = AdminEtiquetas()
    window.show()
    sys.exit(app.exec_())
