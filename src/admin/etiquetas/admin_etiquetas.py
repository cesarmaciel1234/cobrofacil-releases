from src.utils.theme_manager import theme_manager
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit,
    QDialog, QFormLayout, QComboBox, QRadioButton, QFrame, QGridLayout,
    QCheckBox, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont, QBrush

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

from src.services.etiquetas.renderer import EtiquetaRenderer, abrir_archivo_pdf

class AdminEtiquetas(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.productos_impresos_etiquetas = set()
        self.productos_impresos_ofertas = set()
        self.productos_seleccionados = {}
        
        self.setup_ui()
        self.cargar_productos()
        self.actualizar_materia_prima_count()
        
        theme_manager.theme_changed.connect(self._apply_theme)
        QTimer.singleShot(50, self._apply_theme)

    def _create_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 15) if theme_manager.current_theme == "light" else QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        return shadow

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # --- HEADER PRINCIPAL ---
        header_layout = QHBoxLayout()
        self.btn_back = QPushButton("⬅ VOLVER", objectName="btnBack")
        self.btn_back.clicked.connect(self.request_dashboard.emit)
        self.btn_back.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(self.btn_back)
        
        self.header_title = QLabel("🏭 PLANTA DE IMPRESIÓN & ETIQUETADO")
        self.header_title.setStyleSheet("font-size: 24px; font-weight: 900; letter-spacing: 1px;")
        header_layout.addWidget(self.header_title)
        header_layout.addStretch()
        
        self.lbl_status = QLabel("🟢 MOTOR EN LÍNEA")
        self.lbl_status.setStyleSheet("font-weight: 900; border-radius: 8px; padding: 8px 16px; border: 1px solid #10B981; color: #10B981; background: rgba(16, 185, 129, 0.1);")
        header_layout.addWidget(self.lbl_status)
        
        main_layout.addLayout(header_layout)

        # --- HERO CARDS ---
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Card 1: Materia Prima
        self.card_materia, self.lbl_stat_materia = self._build_hero_card("📦 MATERIA PRIMA (INVENTARIO)", "Cargando catálogo...", "#3B82F6")
        cards_layout.addWidget(self.card_materia)
        
        # Card 2: Lote Activo
        self.card_lote, self.lbl_stat_lote = self._build_hero_card("⚡ HILO DE SELECCIÓN", "0 Productos", "#10B981")
        cards_layout.addWidget(self.card_lote)

        # Card 3: Configuración de Marca Comercial
        self.card_marca, self.lbl_stat_marca = self._build_hero_card("🏢 MARCA COMERCIAL", "MACIEL - CARNICERÍA", "#F59E0B")
        cards_layout.addWidget(self.card_marca)
        
        main_layout.addLayout(cards_layout)

        # --- CONTROL DE PARÁMETROS DE MARCA EN CALIENTE ---
        brand_layout = QHBoxLayout()
        
        self.lbl_r = QLabel("RUBRO COMERCIAL:"); self.lbl_r.setStyleSheet("font-weight: 900; font-size: 11px; letter-spacing: 1px;")
        self.txt_rubro = QLineEdit()
        self.txt_rubro.setPlaceholderText("RUBRO (Ej: CARNICERÍA)")
        self.txt_rubro.setText("CARNICERÍA")
        self.txt_rubro.setStyleSheet("font-weight: bold; font-size: 14px; padding: 8px;")
        self.txt_rubro.textChanged.connect(self.actualizar_marca_de_impresion)
        
        self.lbl_n = QLabel("NEGOCIO:"); self.lbl_n.setStyleSheet("font-weight: 900; font-size: 11px; letter-spacing: 1px;")
        self.txt_negocio = QLineEdit()
        self.txt_negocio.setPlaceholderText("NEGOCIO (Ej: MACIEL)")
        self.txt_negocio.setText("MACIEL")
        self.txt_negocio.setStyleSheet("font-weight: bold; font-size: 14px; padding: 8px;")
        self.txt_negocio.textChanged.connect(self.actualizar_marca_de_impresion)
        
        brand_layout.addWidget(self.lbl_r); brand_layout.addWidget(self.txt_rubro)
        brand_layout.addSpacing(15)
        brand_layout.addWidget(self.lbl_n); brand_layout.addWidget(self.txt_negocio)
        main_layout.addLayout(brand_layout)

        # --- FILTRO DEL FLUJO DE ENTRADA (Buscador) ---
        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 ESCANEA CÓDIGO O ESCRIBE NOMBRE DE PRODUCTO PARA FILTRAR EN TIEMPO REAL...")
        self.txt_search.setStyleSheet("font-size: 15px; padding: 14px; font-weight: bold; border-radius: 8px;")
        self.txt_search.textChanged.connect(self.cargar_productos)
        search_layout.addWidget(self.txt_search)
        main_layout.addLayout(search_layout)

        # --- TABLA DE PROCESAMIENTO ---
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
        self.btn_select_all.setStyleSheet("font-size: 14px; font-weight: bold; padding: 12px 24px; border-radius: 8px;")

        self.btn_print = QPushButton("🏭 LANZAR IMPRESIÓN GÓNDOLA (PDF)", objectName="btnPrint")
        self.btn_print.clicked.connect(self.generar_pdf)
        self.btn_print.setCursor(Qt.PointingHandCursor)
        self.btn_print.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #6366f1); color: white; font-size: 14px; font-weight: bold; padding: 12px 24px; border-radius: 8px; border: none;")
        
        btn_layout.addWidget(self.btn_select_all)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_print)
        main_layout.addLayout(btn_layout)

    def _build_hero_card(self, title, initial_val, accent_color):
        card = QFrame()
        card.setObjectName("HeroCard")
        card.setGraphicsEffect(self._create_shadow())
        
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(5)
        
        lbl_tit = QLabel(title)
        lbl_tit.setStyleSheet("font-size: 13px; font-weight: 700; opacity: 0.7;")
        
        lbl_val = QLabel(initial_val)
        lbl_val.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {accent_color}; letter-spacing: -0.5px;")
        lbl_val.setWordWrap(True)
        
        lay.addWidget(lbl_tit)
        lay.addWidget(lbl_val)
        lay.addStretch()
        
        return card, lbl_val

    def _apply_theme(self):
        is_dark = theme_manager.current_theme == "dark"
        card_bg = "#111827" if is_dark else "#FFFFFF"
        card_border = "#1F2937" if is_dark else "#E5E7EB"
        
        # Hero Cards Style
        hero_style = f"""
            QFrame#HeroCard {{
                background: {card_bg};
                border: 1px solid {card_border};
                border-radius: 12px;
            }}
        """
        self.card_materia.setStyleSheet(hero_style)
        self.card_lote.setStyleSheet(hero_style)
        self.card_marca.setStyleSheet(hero_style)

        # Update shadow color
        for card in [self.card_materia, self.card_lote, self.card_marca]:
            eff = card.graphicsEffect()
            if eff:
                eff.setColor(QColor(0, 0, 0, 80) if is_dark else QColor(0, 0, 0, 15))

        btn_bg = theme_manager.get_color("btn_bg")
        btn_text = theme_manager.get_color("btn_text")
        btn_border = theme_manager.get_color("btn_border")
        btn_hover = theme_manager.get_color("btn_hover")

        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: #EF4444; font-weight: bold; border: 1px solid #EF4444; border-radius: 6px; padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.1);
            }}
        """)
        
        self.btn_select_all.setStyleSheet(f"""
            QPushButton {{
                background: {btn_bg}; color: {btn_text}; border: 1px solid {btn_border}; font-weight: bold; border-radius: 8px; padding: 12px 24px; font-size: 14px;
            }}
            QPushButton:hover {{
                background: {btn_hover};
            }}
        """)

        # Volver a colorear la tabla tras un cambio de tema
        self.cargar_productos()

    def cargar_productos(self):
        txt = self.txt_search.text().strip()
        is_dark = theme_manager.current_theme == "dark"
        
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
            
            # Checkbox
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Checked if p_id_str in self.productos_seleccionados else Qt.Unchecked)
            
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
            
            # ID
            id_text = p_id_str + (" ✓" if is_printed else "")
            id_item = QTableWidgetItem(id_text)
            id_item.setFont(QFont("Consolas", 10, QFont.Bold))
            self.tabla.setItem(i, 1, id_item)
            
            # Nombre
            nom_text = str(p['nombre'])
            if is_printed:
                if is_ambos: nom_text = "🏷️🔥 [AMBOS] " + nom_text
                elif is_oferta: nom_text = "🔥 [OFERTA] " + nom_text
                else: nom_text = "🏷️ [ETIQUETA] " + nom_text
            nom_item = QTableWidgetItem(nom_text)
            nom_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            self.tabla.setItem(i, 2, nom_item)
            
            # Precio
            pr_item = QTableWidgetItem(f"${p['precio']:.2f}")
            pr_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            self.tabla.setItem(i, 3, pr_item)
            
            # Categoría
            cat = p['categoria'] if p['categoria'] else 'GENERAL'
            cat_item = QTableWidgetItem(str(cat).upper())
            self.tabla.setItem(i, 4, cat_item)
            
            self.tabla.item(i, 1).setData(Qt.UserRole, p_data_payload)
            
            # Smart Coloring using QBrush with semi-transparent colors
            if is_printed:
                if is_ambos:
                    bg_color = QColor(139, 92, 246, 30 if is_dark else 50) # Violeta
                    fg_color = QColor("#C4B5FD") if is_dark else QColor("#6D28D9")
                elif is_oferta:
                    bg_color = QColor(249, 115, 22, 30 if is_dark else 50) # Naranja
                    fg_color = QColor("#FDBA74") if is_dark else QColor("#C2410C")
                else:
                    bg_color = QColor(59, 130, 246, 30 if is_dark else 50) # Azul
                    fg_color = QColor("#93C5FD") if is_dark else QColor("#1D4ED8")
            else:
                bg_color = QColor(0, 0, 0, 0) # Transparente
                fg_color = QColor("#F8FAFC") if is_dark else QColor("#0F172A")
                
            for col in range(5):
                item = self.tabla.item(i, col)
                if item:
                    item.setBackground(QBrush(bg_color))
                    if col > 0: # No colorear el checkbox textualmente para evitar glitches
                        item.setForeground(QBrush(fg_color))
            
        self.tabla.blockSignals(False)
        self.actualizar_contador_seleccionados()

    def actualizar_materia_prima_count(self):
        try:
            res = db_manager.execute_query("SELECT COUNT(*) as cant FROM productos")
            count = res[0]['cant'] if res else 0
            self.lbl_stat_materia.setText(f"{count} Productos en catálogo")
        except Exception:
            self.lbl_stat_materia.setText("Error de Base de Datos")

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
        self.lbl_stat_lote.setText(f"{seleccionados} Productos en fila")

    def actualizar_marca_de_impresion(self):
        rubro = self.txt_rubro.text().strip().upper() or "CARNICERÍA"
        negocio = self.txt_negocio.text().strip().upper() or "MACIEL"
        self.lbl_stat_marca.setText(f"{negocio} - {rubro}")

    def seleccionar_todo(self):
        self.tabla.blockSignals(True)
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
                
        # Modern QDialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Configuración de Etiquetas de Góndola")
        dlg.setFixedSize(500, 480)
        
        is_dark = theme_manager.current_theme == "dark"
        dlg_bg = "#0F172A" if is_dark else "#FFFFFF"
        dlg_fg = "#F8FAFC" if is_dark else "#0F172A"
        dlg_brd = "#334155" if is_dark else "#E2E8F0"
        dlg_inp = "#1E293B" if is_dark else "#F8FAFC"
        
        dlg.setStyleSheet(f"""
            QDialog {{ background: {dlg_bg}; color: {dlg_fg}; font-family: 'Segoe UI'; font-size: 14px; }}
            QLabel {{ color: {dlg_fg}; }}
            QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #6366f1); color: white; font-weight: bold; padding: 12px; border-radius: 8px; border: none; font-size: 14px; }}
            QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #4f46e5); }}
            QLineEdit, QComboBox {{ padding: 10px; border: 1px solid {dlg_brd}; border-radius: 8px; background: {dlg_inp}; color: {dlg_fg}; }}
            QRadioButton, QCheckBox {{ spacing: 10px; font-weight: 500; color: {dlg_fg}; }}
            QRadioButton::indicator, QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid {dlg_brd}; border-radius: 9px; background: {dlg_inp}; }}
            QCheckBox::indicator {{ border-radius: 4px; }}
            QRadioButton::indicator:checked, QCheckBox::indicator:checked {{ background: #3B82F6; border-color: #3B82F6; }}
        """)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(15)
        
        lbl_tit = QLabel("🖨️ Formato de Etiquetas")
        lbl_tit.setStyleSheet("font-size: 18px; font-weight: 900; margin-bottom: 10px;")
        lay.addWidget(lbl_tit)
        
        form = QFormLayout()
        form.setSpacing(15)
        
        cmb_estilo = QComboBox()
        cmb_estilo.addItem("⚪ Estilo Minimalista (Limpio)", "minimalista")
        cmb_estilo.addItem("🔵 Estilo Clásico (Azul)", "clasico")
        cmb_estilo.addItem("⚡ Estilo Neón (Borde Moderno)", "neon")
        form.addRow("<b>Estilo Visual:</b>", cmb_estilo)
        lay.addLayout(form)
        
        lay.addWidget(QLabel("<b>Distribución de Página (Grilla A4):</b>"))
        lay_grid = QVBoxLayout()
        lay_grid.setSpacing(8)
        rb_3x7 = QRadioButton("Estándar: 21 etiquetas por hoja (3x7)")
        rb_3x7.setChecked(True)
        rb_3x10 = QRadioButton("Compacto: 30 etiquetas por hoja (3x10)")
        rb_4x10 = QRadioButton("Mini: 40 etiquetas por hoja (4x10)")
        lay_grid.addWidget(rb_3x7)
        lay_grid.addWidget(rb_3x10)
        lay_grid.addWidget(rb_4x10)
        lay.addLayout(lay_grid)
        
        lay.addWidget(QLabel("<b>Opciones de Contenido:</b>"))
        lay_opts = QVBoxLayout()
        lay_opts.setSpacing(8)
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
        
        lay.addStretch()
        btn_ok = QPushButton("🏭 Iniciar Imprenta y Generar PDF")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(dlg.accept)
        lay.addWidget(btn_ok)
        
        if dlg.exec_():
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
                
                abrir_archivo_pdf(pdf_path)

                for p in seleccionados:
                    p_id = str(p['id'])
                    if p.get('is_oferta'):
                        self.productos_impresos_ofertas.add(p_id)
                    else:
                        self.productos_impresos_etiquetas.add(p_id)
                        
                self.productos_seleccionados.clear()
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
