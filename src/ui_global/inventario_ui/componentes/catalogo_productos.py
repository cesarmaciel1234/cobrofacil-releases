from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QPushButton, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QTreeWidget, QTreeWidgetItem, QSplitter,
    QComboBox, QCheckBox, QStackedWidget, QFileDialog, QGridLayout,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QColor, QFont, QBrush

# Removed db_manager import

class MotorBusquedaInventario(QThread):
    busqueda_terminada = pyqtSignal(list, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buscar = ""
        self.depto = None
        self._motor = None
        
    def setup(self, buscar, depto, motor):
        self.buscar = buscar
        self.depto = depto
        self._motor = motor
        
    def run(self):
        try:
            if not self._motor: return
            filas, _ = self._motor.obtener_productos(self.buscar, self.depto, limite=50000, offset=0)
            sin_stock = sum(1 for r in filas if (dict(r).get('stock') or 0.0) <= 0)
            self.busqueda_terminada.emit(filas, sin_stock)
        except Exception as e:
            print("Error MotorBusquedaInventario:", e)
            self.busqueda_terminada.emit([], 0)

class CatalogoProductos(QWidget):
    volver = pyqtSignal()

    HEADERS = ["", "Código", "Descripción del Producto", "Departamento", "IVA (%)",
               "Costo", "P. Venta", "C. Mayoreo", "P. Mayoreo", "Regla Promo", "Of. Relámpago", "Of. Promedio", "Existencia",
               "Inv. Mínimo", "Inv. Máximo", "Tipo de Venta"]

    def __init__(self, parent=None):
        super().__init__(parent)
        
        from src.utils.theme_manager import theme_manager
        self.DEPTO_COLORS = theme_manager.get_depto_colors()

        self._depto_color_map = {}
        self.all_rows = []
        self.loaded_count = 0
        
        # Iniciar Motores
        from src.motor_inventario.motor_catalogo import MotorCatalogo
        from src.motor_inventario.motor_importacion import MotorImportacion
        self.motor = MotorCatalogo()
        self.motor_imp = MotorImportacion()
        
        self.motor_busqueda = MotorBusquedaInventario(self)
        self.motor_busqueda.busqueda_terminada.connect(self._on_busqueda_terminada)
        
        self._setup_ui()
        self._cargar_deptos()
        self.cargar_datos()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(8)
        root.setSpacing(8)
        self.setObjectName("catalogoProductosMain")

        from src.config import config
        from src.shared.urgencia_stock_banner import UrgenciaStockBanner

        self._urgencia_banner = UrgenciaStockBanner(self)
        root.addWidget(self._urgencia_banner)

        # ── Barra de filtros ─────────────────────────────
        fb = QFrame(); fb.setFixedHeight(60)
        fb.setObjectName("catalogoToolbar")
        fl = QHBoxLayout(fb); fl.setContentsMargins(15, 6, 15, 6); fl.setSpacing(12)
        
        ico_search = QLabel("🔍")
        ico_search.setStyleSheet(" font-size: 16px; background: transparent;")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre, código o ID...")
        self.txt_buscar.setMinimumWidth(350)
        
        # Debounce timer para búsqueda rápida sin lag (aumentado para código de barras)
        from PyQt6.QtCore import QTimer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.cargar_datos)
        self.txt_buscar.textChanged.connect(lambda: self.search_timer.start(500))

        lbl_dep = QLabel("FILTRAR POR DEPARTAMENTO:")
        lbl_dep.setStyleSheet("font-weight:800;font-size:10px;letter-spacing:1px; background: transparent;")
        self.cmb_depto = QComboBox()
        self.cmb_depto.setMinimumWidth(200)
        self.cmb_depto.currentIndexChanged.connect(self.cargar_datos)

        fl.addWidget(ico_search)
        fl.addWidget(self.txt_buscar)
        fl.addSpacing(15)
        fl.addWidget(lbl_dep); fl.addWidget(self.cmb_depto)
        fl.addSpacing(20)

        self.chk_venta_sin_stock = QCheckBox("🚨 Urgencia: vender sin stock")
        self.chk_venta_sin_stock.setToolTip(
            "Solo para emergencias. El cajero podrá vender aunque no haya existencia "
            "y se mostrará una alerta parpadeante mientras esté activo."
        )
        self.chk_venta_sin_stock.setStyleSheet(
            "QCheckBox { font-weight: 800; color: #B91C1C; padding: 4px 8px; "
            "border: 1px solid #FECACA; border-radius: 6px; background: #FFF7ED; }"
            "QCheckBox::indicator { width: 18px; height: 18px; }"
        )
        self.chk_venta_sin_stock.setChecked(bool(config.get("opt_stock_negativo", False)))
        self.chk_venta_sin_stock.toggled.connect(self._toggle_venta_sin_stock)
        fl.addWidget(self.chk_venta_sin_stock)

        fl.addStretch()
        root.addWidget(fb)

        self._sync_urgencia_banner()

        # ── Tabla ────────────────────────────────────────
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(self.HEADERS))
        self.tabla.setHorizontalHeaderLabels(self.HEADERS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setAlternatingRowColors(False)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setShowGrid(False)
        self.tabla.setObjectName("catalogoTable")
        # 16 columnas: Check, Codigo, Desc(Stretch), Depto, IVA, Costo, Venta, C.Mayoreo, P.Mayoreo, Promo, Relampago, Promedio, Existencia, Min, Max, Tipo
        col_widths = [28, 80, -1, 100, 60, 75, 85, 90, 90, 110, 105, 105, 95, 85, 85, 90]
        hh = self.tabla.horizontalHeader()
        for i, w in enumerate(col_widths):
            if w == -1:
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Fixed)
                self.tabla.setColumnWidth(i, w)

        self.tabla.verticalHeader().setDefaultSectionSize(40)
        self.tabla.doubleClicked.connect(self._modificar_seleccionado)
        root.addWidget(self.tabla)

        # ── Footer ───────────────────────────────────────
        ft = QFrame(); ft.setFixedHeight(38)
        ft.setObjectName("catalogoFooter")
        fl2 = QHBoxLayout(ft); fl2.setContentsMargins(12, 0, 12, 0)
        self.lbl_total   = QLabel("0 productos")
        self.lbl_stock0  = QLabel("")
        self.lbl_sel     = QLabel("")
        for lbl in [self.lbl_total, self.lbl_stock0, self.lbl_sel]:
            lbl.setStyleSheet("font-size:11px; background: transparent;")
        fl2.addWidget(self.lbl_total)
        fl2.addSpacing(20); fl2.addWidget(self.lbl_stock0)
        fl2.addStretch();   fl2.addWidget(self.lbl_sel)
        root.addWidget(ft)

        self.tabla.itemSelectionChanged.connect(self._actualizar_sel)
        self.tabla.verticalScrollBar().valueChanged.connect(self._al_hacer_scroll)

    def _apply_catalogo_theme(self):
        from src.utils.theme_manager import theme_manager
        
        # Colors based on current theme
        is_dark = theme_manager.is_dark()
        bg = "#1E293B" if is_dark else "#FFFFFF"
        text = "#F8FAFC" if is_dark else "#0F172A"
        border = "#334155" if is_dark else "#E2E8F0"
        hover = "#334155" if is_dark else "#F1F5F9"
        sel_bg = "#EFF6FF" if is_dark else "#EFF6FF"
        sel_text = "#1E3A8A" if is_dark else "#1D4ED8"
        header_bg = "#0F172A" if is_dark else "#F8FAFC"
        header_text = "#94A3B8" if is_dark else "#64748B"
        main_bg = "#0F172A" if is_dark else "#F8FAFC"
        
        self.setStyleSheet(f"background-color: {main_bg};")
        
        if hasattr(self, "tabla"):
            self.tabla.setStyleSheet(f"""
                QTableWidget {{
                    background: {bg};
                    border: 1px solid {border};
                    border-radius: 12px;
                    gridline-color: transparent;
                    outline: none;
                }}
                QTableWidget::item {{
                    padding: 8px 10px;
                    color: {text};
                    border-bottom: 1px solid {hover};
                }}
                QTableWidget::item:hover {{
                    background-color: {hover};
                }}
                QTableWidget::item:selected {{
                    background-color: {sel_bg};
                    color: {sel_text};
                    border-bottom: 2px solid #3B82F6;
                }}
                QHeaderView::section {{
                    background-color: {header_bg};
                    color: {header_text};
                    font-weight: 900;
                    padding: 12px 8px;
                    border: none;
                    border-bottom: 2px solid {border};
                    font-size: 11px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
            """)
            
        if hasattr(self, "txt_buscar"):
            self.txt_buscar.setStyleSheet(f"""
                QLineEdit {{ background: {bg}; color: {text}; border: 1px solid {border}; 
                border-radius: 8px; padding: 10px 14px; font-size: 13px; }}
                QLineEdit:focus {{ border: 2px solid #3B82F6; }}
            """)
            
        if hasattr(self, "cmb_depto"):
            self.cmb_depto.setStyleSheet(f"""
                QComboBox {{ background: {bg}; color: {text}; border: 1px solid {border}; 
                border-radius: 8px; padding: 8px 12px; }}
                QComboBox:focus {{ border: 2px solid #3B82F6; }}
            """)

    def _sync_urgencia_banner(self):
        activo = bool(self.chk_venta_sin_stock.isChecked())
        self._urgencia_banner.set_active(activo)
        self.chk_venta_sin_stock.setStyleSheet(
            "QCheckBox { font-weight: 800; color: #B91C1C; padding: 4px 8px; "
            "border: 2px solid #DC2626; border-radius: 6px; background: #FEE2E2; }"
            "QCheckBox::indicator { width: 18px; height: 18px; }"
            if activo
            else "QCheckBox { font-weight: 800; color: #B91C1C; padding: 4px 8px; "
            "border: 1px solid #FECACA; border-radius: 6px; background: #FFF7ED; }"
            "QCheckBox::indicator { width: 18px; height: 18px; }"
        )

    def _toggle_venta_sin_stock(self, checked: bool):
        from src.config import config

        if checked:
            r = QMessageBox.warning(
                self,
                "Modo urgencia — vender sin stock",
                "Estás activando una excepción a las reglas de inventario.\n\n"
                "• El cajero podrá vender productos sin existencia.\n"
                "• Habrá una alerta PARPADEANTE en inventario y en el terminal.\n\n"
                "Desactivalo cuando termine la urgencia.",
                QMessageBox.Ok | QMessageBox.Cancel,
                QMessageBox.Cancel,
            )
            if r != QMessageBox.Ok:
                self.chk_venta_sin_stock.blockSignals(True)
                self.chk_venta_sin_stock.setChecked(False)
                self.chk_venta_sin_stock.blockSignals(False)
                self._sync_urgencia_banner()
                return

        config.set("opt_stock_negativo", bool(checked))
        self._sync_urgencia_banner()

    def showEvent(self, event):
        super().showEvent(event)
        from src.config import config

        self.chk_venta_sin_stock.blockSignals(True)
        self.chk_venta_sin_stock.setChecked(bool(config.get("opt_stock_negativo", False)))
        self.chk_venta_sin_stock.blockSignals(False)
        self._sync_urgencia_banner()

    def _cargar_deptos(self):
        self.cmb_depto.blockSignals(True)
        self.cmb_depto.clear()
        self.cmb_depto.addItem("— Todas las categorías —", None)
        try:
            from src.motor_inventario.motor_departamentos import MotorDepartamentos
            md = MotorDepartamentos()
            deps = md.obtener_categorias()
            for r in deps:
                dep = r['nombre']
                if dep and dep.upper() != "GENERAL":
                    self.cmb_depto.addItem(dep, dep)
        except: pass
        self.cmb_depto.blockSignals(False)

    def cargar_datos(self):
        buscar = self.txt_buscar.text().strip()
        depto  = self.cmb_depto.currentData()

        # Mostrar estado de carga
        self.lbl_total.setText("🔄 Buscando productos... Por favor espera.")
        self.lbl_stock0.setText("")
        self.tabla.setRowCount(0)
        
        # Iniciar búsqueda en background (Cerebro Asíncrono)
        self.motor_busqueda.setup(buscar, depto, self.motor)
        self.motor_busqueda.start()

    def _on_busqueda_terminada(self, filas, sin_stock):
        self.all_rows = filas
        self._depto_color_map = {}
        self.loaded_count = 0
        self.tabla.setRowCount(0)
        
        # Cargar la primera página
        self._cargar_siguiente_pagina()

        n = len(self.all_rows)
        self.lbl_total.setText(f"📦 {n} PRODUCTOS EN INVENTARIO")
        self.lbl_total.setStyleSheet(" font-weight: 800; background: transparent;")
        from src.utils.theme_manager import theme_manager
        color_agotado = theme_manager.get_color("stock_agotado")
        color_saludable = theme_manager.get_color("stock_saludable")
        self.lbl_stock0.setText(
            f"⚠️ Stock Crítico: {sin_stock}" if sin_stock else "✅ Stock Saludable"
        )
        self.lbl_stock0.setStyleSheet(
            f"color:{color_agotado if sin_stock else color_saludable}; font-size:11px; font-weight:bold; background: transparent;"
        )

    def _cargar_siguiente_pagina(self):
        if getattr(self, '_loading_page', False):
            return
        self._loading_page = True
        try:
            if self.loaded_count >= len(self.all_rows):
                return
                
            inicio = self.loaded_count
            fin = min(inicio + 100, len(self.all_rows))  # 100 filas por página (era 50)
            
            # ── Pre-calcular todo FUERA del bucle para máximo rendimiento ──
            from src.utils.theme_manager import theme_manager
            from src.config import config
            tax_default = float(config.get("tax_percentage", 21.0))
            
            # Colores pre-resueltos una sola vez
            c_texto      = QColor(theme_manager.get_color("texto_primario"))
            c_oferta     = QColor(theme_manager.get_color("oferta"))
            c_agotado    = QColor(theme_manager.get_color("stock_agotado"))
            c_bajo       = QColor(theme_manager.get_color("stock_bajo"))
            c_saludable  = QColor(theme_manager.get_color("stock_saludable"))
            c_tipo       = QColor(theme_manager.get_color("tipo_producto"))
            bg_agotado   = QColor(theme_manager.get_color("bg_stock_agotado"))
            bg_bajo      = QColor(theme_manager.get_color("bg_stock_bajo"))
            bg_impar     = theme_manager.get_color("bg_fila_impar")
            font_bold    = QFont("Segoe UI", 9, QFont.Bold)
            
            self.tabla.blockSignals(True)
            self.tabla.setRowCount(fin)
            
            for i in range(inicio, fin):
                r = self.all_rows[i]
                # Convertir a dict UNA sola vez por fila
                rd = dict(r) if not isinstance(r, dict) else r
                
                dep   = rd.get('departamento') or ''
                stock = float(rd.get('stock') or 0.0)
                uni   = (rd.get('unidad') or 'UN').upper()
                tipo  = "KILO" if uni == 'KG' else "UNIDAD"
                
                depto_iva = rd.get('depto_iva')
                depto_iva = float(depto_iva) if depto_iva is not None else tax_default

                dep_key = (dep or "GENERAL").upper()
                if dep_key not in self._depto_color_map:
                    idx = len(self._depto_color_map) % len(self.DEPTO_COLORS)
                    self._depto_color_map[dep_key] = self.DEPTO_COLORS[idx]
                base_hex = self._depto_color_map[dep_key]
                
                if i % 2 == 1 and base_hex == "#FFFFFF":
                    base_hex = bg_impar
                row_bg = QColor(base_hex)

                chk = QTableWidgetItem()
                chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                chk.setCheckState(Qt.Unchecked)
                chk.setBackground(row_bg)
                self.tabla.setItem(i, 0, chk)

                p_oferta    = float(rd.get('precio_oferta') or 0)
                c_oferta_r  = float(rd.get('cant_oferta') or 0)
                p_mayor     = float(rd.get('precio_mayoreo') or 0)
                c_mayor     = float(rd.get('cant_mayoreo') or 0)
                p_relamp    = float(rd.get('precio_oferta_relampago') or 0)
                p_prom      = float(rd.get('precio_oferta_promedio') or 0)
                
                vals = [
                    (str(rd.get('codigo') or '') or f"[{rd.get('id','')}]", Qt.AlignRight),
                    (rd.get('nombre') or '',  Qt.AlignLeft),
                    (dep,                     Qt.AlignLeft),
                    (f"{depto_iva:.1f}%",     Qt.AlignCenter),
                    (f"${float(rd.get('costo') or 0):.2f}",  Qt.AlignRight),
                    (f"${float(rd.get('precio') or 0):.2f}", Qt.AlignRight),
                    (f"{c_mayor:g}" if c_mayor > 0 else "-",         Qt.AlignCenter),
                    (f"${p_mayor:.2f}" if p_mayor > 0 else "-",      Qt.AlignRight),
                    (f"{c_oferta_r:g} x ${p_oferta:.2f}" if p_oferta else "-", Qt.AlignCenter),
                    (f"${p_relamp:.2f}" if p_relamp else "-",         Qt.AlignCenter),
                    (f"${p_prom:.2f}" if p_prom else "-",             Qt.AlignCenter),
                    (f"{stock:.2f}",           Qt.AlignRight),
                    (f"{float(rd.get('stock_minimo') or 0):.2f}", Qt.AlignCenter),
                    (f"{float(rd.get('stock_maximo') or 0):.2f}", Qt.AlignCenter),
                    (tipo,                     Qt.AlignCenter),
                ]

                for j, (v, align) in enumerate(vals, 1):
                    it = QTableWidgetItem(v)
                    it.setTextAlignment(Qt.AlignVCenter | align)
                    it.setBackground(row_bg)
                    it.setForeground(c_texto)

                    if j in (9, 10) and v != "-":
                        it.setForeground(c_oferta)
                        it.setFont(font_bold)

                    if j == 12:
                        if stock <= 0:
                            it.setForeground(c_agotado)
                            it.setBackground(bg_agotado)
                        elif stock < 5:
                            it.setForeground(c_bajo)
                            it.setBackground(bg_bajo)
                        else:
                            it.setForeground(c_saludable)

                    if j == 15:
                        it.setForeground(c_tipo)
                        it.setFont(font_bold)

                    self.tabla.setItem(i, j, it)
                    
            self.loaded_count = fin
        finally:
            self.tabla.blockSignals(False)
            self._loading_page = False


    def _al_hacer_scroll(self, value):
        bar = self.tabla.verticalScrollBar()
        if bar.maximum() > 0 and value >= bar.maximum() - 15:
            self._cargar_siguiente_pagina()

    def _actualizar_sel(self):
        sel = len(self.tabla.selectedItems()) // len(self.HEADERS)
        self.lbl_sel.setText(f"Seleccionados: {sel}" if sel else "")

    def _modificar_seleccionado(self, *args, **kwargs):
        row = self.tabla.currentRow()
        if row == -1:
            QMessageBox.information(self, "Selección", "Seleccioná un producto primero.")
            return
        item_id = self.tabla.item(row, 1)
        if not item_id:
            return
        id_p = item_id.text()
        # Usar el motor
        from src.motor_inventario.motor_catalogo import MotorCatalogo
        motor = MotorCatalogo()
        r = motor.obtener_producto_por_id(id_p)
        if not r: return
        def get_val(col, default=0.0):
            try: 
                return r[col] if r[col] is not None else default
            except: 
                return default

        datos = {
            'id': r['id'], 
            'codigo': r['codigo'] or '', 
            'nombre': r['nombre'] or '',
            'precio': r['precio'] if r['precio'] is not None else 0.0, 
            'precio_mayoreo': r['precio_mayoreo'] if r['precio_mayoreo'] is not None else 0.0,
            'cant_mayoreo': r['cant_mayoreo'] if r['cant_mayoreo'] is not None else 0.0,
            'cant_oferta': get_val('cant_oferta', 0.0), 
            'precio_oferta': get_val('precio_oferta', 0.0),
            'costo': r['costo'] if r['costo'] is not None else 0.0, 
            'stock': r['stock'] if r['stock'] is not None else 0.0,
            'stock_minimo': r['stock_minimo'] if r['stock_minimo'] is not None else 0.0, 
            'stock_maximo': r['stock_maximo'] if r['stock_maximo'] is not None else 0.0,
            'unidad': r['unidad'] or 'UN', 
            'es_pesable': r['es_pesable'] if r['es_pesable'] is not None else 0,
            'departamento': r['departamento'] or '', 
            'categoria': r['categoria'] or 'GENERAL'
        }
        from src.ui_global.inventario_ui.componentes.dialogo_producto import DialogoProducto
        dlg = DialogoProducto(datos, self)
        if qt_exec(dlg):
            d = dlg.get_data()
            from src.motor_inventario.motor_catalogo import MotorCatalogo
            motor = MotorCatalogo()
            ok, msg = motor.guardar_producto(d, is_new=False, prod_id=d['id'])
            if ok:
                self.cargar_datos()
                # Trigger cartelera
                try:
                    from src.central_red_global.network_engine import get_network_engine
                    e = get_network_engine()
                    if e: e.broadcast_message("PRECIOS_ACTUALIZADOS", {})
                except: pass
            else:
                QMessageBox.warning(self, "Error", f"No se pudo actualizar el producto.\n\nDetalle técnico:\n{msg}")

    def _exportar(self):
        from datetime import datetime
        nombre_def = f"productos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exportar productos", nombre_def,
            "Excel (*.xlsx);;Todos los archivos (*)")
        if not filepath: return
        
        # Inyectar trabajador en segundo plano
        class WorkerExport(QThread):
            finished = pyqtSignal(bool, str)
            def __init__(self, path):
                super().__init__()
                self.path = path
            def run(self):
                from src.admin.admin_importexport import exportar_excel
                ok, msg = exportar_excel(self.path)
                self.finished.emit(ok, msg)
                
        self._btn_sender = self.sender() # Identifica qué botón presiono
        if self._btn_sender:
            self._old_text = self._btn_sender.text()
            self._btn_sender.setText("⏳ CARGANDO...")
            self._btn_sender.setEnabled(False)
            
        self._worker_exp = WorkerExport(filepath)
        def on_fin(ok, msg):
            if self._btn_sender:
                self._btn_sender.setText(self._old_text)
                self._btn_sender.setEnabled(True)
            (QMessageBox.information if ok else QMessageBox.critical)(
                self, "Exportación" + (" exitosa" if ok else " fallida"), msg)
        self._worker_exp.finished.connect(on_fin)
        self._worker_exp.start()

    def _descargar_precarga(self):
        respuesta = QMessageBox.question(
            self, "Precarga desde la Nube",
            "¿Deseas descargar y sumar ~12,800 productos precargados desde la nube a tu base de datos?\n(Esto tomará un par de segundos)",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if respuesta != QMessageBox.Yes: return

        class WorkerPrecarga(QThread):
            finished = pyqtSignal(bool, str)
            def run(self):
                from src.motor_inventario.motor_importacion import MotorImportacion
                ok, msg = MotorImportacion().descargar_precarga()
                self.finished.emit(ok, msg)

        self._btn_sender_pre = self.sender()
        if self._btn_sender_pre:
            self._old_text_pre = self._btn_sender_pre.text()
            self._btn_sender_pre.setText("⏳ DESCARGANDO...")
            self._btn_sender_pre.setEnabled(False)

        self._worker_pre = WorkerPrecarga()
        def on_fin_pre(ok, msg):
            if self._btn_sender_pre:
                self._btn_sender_pre.setText(self._old_text_pre)
                self._btn_sender_pre.setEnabled(True)
            (QMessageBox.information if ok else QMessageBox.critical)(
                self, "Precarga Nube" + (" completada" if ok else " fallida"), msg)
            if ok:
                self.txt_buscar.clear()
                self.cargar_datos()

        self._worker_pre.finished.connect(on_fin_pre)
        self._worker_pre.start()

    def _unificar_duplicados(self):
        respuesta = QMessageBox.question(
            self, "Unificar Duplicados",
            "¿Deseas buscar y unificar automáticamente todos los productos repetidos (con el mismo código)?\n\nEl sistema acumulará el stock en el producto principal y eliminará las copias vacías o basura.\nEste proceso no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if respuesta != QMessageBox.Yes: return
        
        from src.motor_inventario.motor_catalogo import MotorCatalogo
        motor = MotorCatalogo()
        ok, msg = motor.unificar_duplicados()
        
        QMessageBox.information(self, "Unificación Completada", msg)
        self.txt_buscar.clear()
        self.cargar_datos()

    def _importar(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Importar productos", "",
            "Excel (*.xlsx *.xls);;Todos los archivos (*)")
        if not filepath: return

        class WorkerImport(QThread):
            finished = pyqtSignal(bool, str)
            def __init__(self, path):
                super().__init__()
                self.path = path
            def run(self):
                from src.admin.admin_importexport import importar_excel
                ok, msg = importar_excel(self.path)
                self.finished.emit(ok, msg)

        self._btn_sender_imp = self.sender()
        if self._btn_sender_imp:
            self._old_text_imp = self._btn_sender_imp.text()
            self._btn_sender_imp.setText("⏳ CARGANDO...")
            self._btn_sender_imp.setEnabled(False)

        self._worker_imp = WorkerImport(filepath)
        def on_fin_imp(ok, msg):
            if self._btn_sender_imp:
                self._btn_sender_imp.setText(self._old_text_imp)
                self._btn_sender_imp.setEnabled(True)
            (QMessageBox.information if ok else QMessageBox.critical)(
                self, "Importación" + (" completada" if ok else " fallida"), msg)
            if ok:
                self._cargar_deptos(); self.cargar_datos()
        self._worker_imp.finished.connect(on_fin_imp)
        self._worker_imp.start()

# ── Pantalla principal Inventario ─────────────────────────

