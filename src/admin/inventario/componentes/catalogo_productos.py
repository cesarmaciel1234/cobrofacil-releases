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

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager


class CatalogoProductos(QWidget):
    volver = pyqtSignal()

    HEADERS = ["", "Código", "Descripción del Producto", "Departamento", "IVA (%)",
               "Costo", "P. Venta", "Regla Promo", "Of. Relámpago", "Of. Promedio", "Existencia",
               "Inv. Mínimo", "Inv. Máximo", "Tipo de Venta"]

    DEPTO_COLORS = [
        "#FFFFFF", "#F8FAFC", "#F0F9FF", "#ECFDF5",
        "#FFFBEB", "#FFF1F2", "#F5F3FF", "#FDF4FF",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._depto_color_map = {}
        self.all_rows = []
        self.loaded_count = 0
        self._setup_ui()
        self._cargar_deptos()
        self.cargar_datos()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(8)
        self.setStyleSheet("background-color: #F8FAFC;")

        from src.config import config
        from src.shared.urgencia_stock_banner import UrgenciaStockBanner

        self._urgencia_banner = UrgenciaStockBanner(self)
        root.addWidget(self._urgencia_banner)

        # ── Barra de filtros ─────────────────────────────
        fb = QFrame(); fb.setFixedHeight(60)
        fb.setStyleSheet("QFrame { background: #FFFFFF; border-bottom: 1px solid #E2E8F0; }")
        fl = QHBoxLayout(fb); fl.setContentsMargins(15, 6, 15, 6); fl.setSpacing(12)
        
        ico_search = QLabel("🔍")
        ico_search.setStyleSheet(" font-size: 16px; background: transparent;")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre, código o ID...")
        self.txt_buscar.setMinimumWidth(350)
        
        # Debounce timer para búsqueda rápida sin lag
        from PyQt6.QtCore import QTimer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.cargar_datos)
        self.txt_buscar.textChanged.connect(lambda: self.search_timer.start(300))

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
        self.tabla.setStyleSheet("""
            QTableWidget {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                gridline-color: transparent;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px 10px;
                color: #0F172A;
                border-bottom: 1px solid #F1F5F9;
            }
            QTableWidget::item:hover {
                background-color: #F1F5F9;
            }
            QTableWidget::item:selected {
                background-color: #EFF6FF;
                color: #1D4ED8;
                border-bottom: 2px solid #3B82F6;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #64748B;
                font-weight: 900;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """)
        # Agregamos el ancho de "Regla Promo" (110) para tener 14 columnas
        col_widths = [28, 100, -1, 130, 70, 80, 80, 110, 95, 95, 80, 80, 80, 90]
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
        ft.setStyleSheet("QFrame { background: #FFFFFF; border-top: 1px solid #E2E8F0; }")
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
        """Mantiene tabla y filtros en modo claro aunque theme_manager reaplique estilos."""
        self.setStyleSheet("background-color: #F8FAFC;")
        if hasattr(self, "tabla"):
            self.tabla.setStyleSheet("""
                QTableWidget {
                    background: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 12px;
                    gridline-color: transparent;
                    outline: none;
                }
                QTableWidget::item {
                    padding: 8px 10px;
                    color: #0F172A;
                    border-bottom: 1px solid #F1F5F9;
                }
                QTableWidget::item:hover {
                    background-color: #F1F5F9;
                }
                QTableWidget::item:selected {
                    background-color: #EFF6FF;
                    color: #1D4ED8;
                    border-bottom: 2px solid #3B82F6;
                }
                QHeaderView::section {
                    background-color: #F8FAFC;
                    color: #64748B;
                    font-weight: 900;
                    padding: 12px 8px;
                    border: none;
                    border-bottom: 2px solid #E2E8F0;
                    font-size: 11px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
            """)
        if hasattr(self, "txt_buscar"):
            self.txt_buscar.setStyleSheet(
                "QLineEdit { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; "
                "border-radius: 8px; padding: 10px 14px; font-size: 13px; }"
                "QLineEdit:focus { border: 2px solid #3B82F6; }"
            )
        if hasattr(self, "cmb_depto"):
            self.cmb_depto.setStyleSheet(
                "QComboBox { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; "
                "border-radius: 8px; padding: 8px 12px; }"
                "QComboBox:focus { border: 2px solid #3B82F6; }"
            )

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
            db_manager.execute_non_query("CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL)")
            db_manager.execute_non_query("INSERT OR IGNORE INTO categorias (nombre) SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL AND categoria != ''")
            
            deps = db_manager.execute_query(
                "SELECT nombre FROM categorias ORDER BY nombre"
            ) or []
            for r in deps:
                dep = r['nombre']
                if dep and dep.upper() != "GENERAL":
                    self.cmb_depto.addItem(dep, dep)
        except: pass
        self.cmb_depto.blockSignals(False)

    def cargar_datos(self):
        buscar = self.txt_buscar.text().strip()
        depto  = self.cmb_depto.currentData()

        q = "SELECT p.*, d.iva AS depto_iva FROM productos p LEFT JOIN departamentos d ON UPPER(p.departamento) = UPPER(d.nombre) WHERE 1=1"
        p = []
        if buscar:
            q += " AND (p.nombre LIKE ? OR CAST(p.id AS TEXT) LIKE ? OR COALESCE(p.codigo,'') LIKE ?)"
            p += [f"%{buscar}%"] * 3
        if depto:
            q += " AND UPPER(p.departamento)=UPPER(?)"
            p.append(depto)
        q += " ORDER BY p.departamento, p.nombre"
        # q += " LIMIT 5000"  # Removido para permitir carga completa con paginación diferida

        self.all_rows = db_manager.execute_query(q, tuple(p)) or []
        self._depto_color_map = {}
        self.loaded_count = 0
        self.tabla.setRowCount(0)
        
        # Cargar la primera página
        self._cargar_siguiente_pagina()

        # Calcular stock crítico de forma rápida de la memoria sin trabar la UI
        sin_stock = sum(1 for r in self.all_rows if (r['stock'] or 0.0) <= 0)

        n = len(self.all_rows)
        self.lbl_total.setText(f"📦 {n} PRODUCTOS EN INVENTARIO")
        self.lbl_total.setStyleSheet(" font-weight: 800; background: transparent;")
        self.lbl_stock0.setText(
            f"⚠️ Stock Crítico: {sin_stock}" if sin_stock else "✅ Stock Saludable"
        )
        self.lbl_stock0.setStyleSheet(
            f"color:{'#ef4444' if sin_stock else '#10b981'}; font-size:11px; font-weight:bold; background: transparent;"
        )

    def _cargar_siguiente_pagina(self):
        if getattr(self, '_loading_page', False):
            return
        self._loading_page = True
        try:
            if self.loaded_count >= len(self.all_rows):
                return
                
            inicio = self.loaded_count
            fin = min(inicio + 50, len(self.all_rows))
            
            self.tabla.blockSignals(True)
            self.tabla.setRowCount(fin)
            
            for i in range(inicio, fin):
                r = self.all_rows[i]
                dep   = r['departamento'] or ''
                stock = r['stock'] or 0.0
                uni   = (r['unidad'] or 'UN').upper()
                tipo  = "KILO" if uni == 'KG' else "UNIDAD"
                
                depto_iva = None
                try:
                    depto_iva = r['depto_iva']
                except (IndexError, KeyError, TypeError):
                    pass
                    
                if depto_iva is None:
                    from src.config import config
                    depto_iva = float(config.get("tax_percentage", 21.0))
                else:
                    depto_iva = float(depto_iva)

                dep_key = (dep or "GENERAL").upper()
                if dep_key not in self._depto_color_map:
                    idx = len(self._depto_color_map) % len(self.DEPTO_COLORS)
                    self._depto_color_map[dep_key] = self.DEPTO_COLORS[idx]
                base_hex = self._depto_color_map[dep_key]
                if i % 2 == 1 and base_hex == "#FFFFFF":
                    base_hex = "#F8FAFC"
                row_bg = QColor(base_hex)
                chk = QTableWidgetItem()
                chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                chk.setCheckState(Qt.Unchecked)
                chk.setBackground(row_bg)
                self.tabla.setItem(i, 0, chk)

                vals = [
                    (str(r['id']),       Qt.AlignRight),
                    (r['nombre'] or '',  Qt.AlignLeft),
                    (dep,                Qt.AlignLeft),
                    (f"{depto_iva:.1f}%", Qt.AlignCenter),
                    (f"${r['costo']:.2f}", Qt.AlignRight),
                    (f"${r['precio']:.2f}", Qt.AlignRight),
                    (f"{r['cant_oferta']:g} x ${r['precio_oferta']:.2f}" if dict(r).get('precio_oferta') else "-", Qt.AlignCenter),
                    (f"${r['precio_oferta_relampago']:.2f}" if dict(r).get('precio_oferta_relampago') else "-", Qt.AlignCenter),
                    (f"${r['precio_oferta_promedio']:.2f}" if dict(r).get('precio_oferta_promedio') else "-", Qt.AlignCenter),
                    (f"{stock:.2f}",     Qt.AlignRight),
                    (f"{r['stock_minimo'] or 0:.2f}", Qt.AlignCenter),
                    (f"{r['stock_maximo'] or 0:.2f}", Qt.AlignCenter),
                    (tipo,               Qt.AlignCenter),
                ]

                for j, (v, align) in enumerate(vals, 1):
                    it = QTableWidgetItem(v)
                    it.setTextAlignment(Qt.AlignVCenter | align)
                    it.setBackground(row_bg)
                    it.setForeground(QColor("#0F172A"))

                    if j == 7 or j == 8:  # Resaltar si hay oferta
                        if v != "-":
                            it.setForeground(QColor("#EA580C"))
                            it.setFont(QFont("Segoe UI", 9, QFont.Bold))

                    if j == 9: # Stock
                        if stock <= 0:
                            it.setForeground(QColor("#DC2626"))
                            it.setBackground(QColor("#FEF2F2"))
                        elif stock < 5:
                            it.setForeground(QColor("#D97706"))
                            it.setBackground(QColor("#FFFBEB"))
                        else:
                            it.setForeground(QColor("#059669"))

                    if j == 12: # Tipo
                        it.setForeground(QColor("#2563EB"))
                        it.setFont(QFont("Segoe UI", 9, QFont.Bold))

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
        rows = db_manager.execute_query("SELECT * FROM productos WHERE id=?", (id_p,)) or []
        if not rows: 
            return
        r = rows[0]
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
        from src.admin.inventario.componentes.dialogo_producto import DialogoProducto
        dlg = DialogoProducto(datos, self)
        if qt_exec(dlg):
            d = dlg.get_data()
            ok = db_manager.execute_non_query(
                "UPDATE productos SET codigo=?,nombre=?,precio=?,precio_mayoreo=?,cant_oferta=?,precio_oferta=?,costo=?,stock=?,"
                "stock_minimo=?,stock_maximo=?,unidad=?,es_pesable=?,departamento=?,categoria=? WHERE id=?",
                (d['codigo'], d['nombre'], d['precio'], d['precio_mayoreo'], d['cant_oferta'], d['precio_oferta'], d['costo'], d['stock'],
                 d['stock_minimo'], d['stock_maximo'], d['unidad'], d['es_pesable'], d['departamento'], d['categoria'], d['id']))
            if ok:
                self._cargar_deptos()
                self.cargar_datos()
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar el producto. Verifique los campos ingresados o si el código ya existe.")

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
                import urllib.request
                import json
                
                url = "https://firebasestorage.googleapis.com/v0/b/cajafacil-pro-updates.firebasestorage.app/o/inventario_precargado.json?alt=media"
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=15) as response:
                        data = json.loads(response.read().decode('utf-8'))
                        
                    if not data:
                        self.finished.emit(False, "El archivo JSON está vacío.")
                        return
                    
                    # Load existing barcodes to prevent duplicates
                    existing_res = db_manager.execute_query("SELECT codigo FROM productos WHERE codigo IS NOT NULL AND codigo != ''")
                    existing_codes = set(str(row['codigo']).strip() for row in (existing_res or []))
                    
                    # Preparar lista para inserción masiva
                    values = []
                    for item in data:
                        codigo = str(dict(item).get("codigo", "") or "").strip()
                        nombre = str(dict(item).get("descripcion", "") or "").strip()
                        if not codigo or not nombre:
                            continue
                        if codigo in existing_codes:
                            continue # Skip items we already have!
                            
                        values.append((
                            codigo,
                            nombre,
                            float(dict(item).get("precio_venta") or 0.0),
                            float(dict(item).get("precio_costo") or 0.0),
                            float(dict(item).get("precio_mayoreo") or 0.0),
                            str(dict(item).get("departamento", "GENERAL") or "GENERAL"),
                            float(dict(item).get("stock") or 0.0),
                            float(dict(item).get("stock_minimo") or 0.0),
                            float(dict(item).get("stock_maximo") or 0.0),
                            1 if str(dict(item).get("tipo_venta", "")).strip().lower() in ("granel", "a granel") else 0
                        ))
                        # Add to existing so we don't insert duplicate barcodes from the JSON itself
                        existing_codes.add(codigo)
                    
                    if not values:
                        self.finished.emit(True, "Tu inventario ya está actualizado. No se encontraron productos nuevos en la nube.")
                        return

                    # Inserción masiva usando executemany con sintaxis compatible
                    insert_keyword = "INSERT IGNORE INTO" if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb" else "INSERT OR IGNORE INTO"
                    query = f"""
                        {insert_keyword} productos (
                            codigo, nombre, precio, costo, precio_mayoreo,
                            departamento, stock, stock_minimo, stock_maximo, es_pesable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    db_manager.execute_many(query, values)
                    self.finished.emit(True, f"Se insertaron {len(values)} productos nuevos exitosamente.")
                except Exception as e:
                    self.finished.emit(False, str(e))

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
        
        from src.utils.db import db_manager
        
        # 1. Obtener todos los productos
        res = db_manager.execute_query("SELECT id, codigo, nombre, precio, stock FROM productos WHERE codigo IS NOT NULL AND codigo != ''")
        if not res: return
        
        # 2. Agrupar por código
        por_codigo = {}
        for p in res:
            cod = str(p['codigo']).strip()
            if not cod: continue
            if cod not in por_codigo:
                por_codigo[cod] = []
            por_codigo[cod].append(p)
            
        unificados = 0
        eliminados = 0
        
        for cod, lista in por_codigo.items():
            if len(lista) > 1:
                # Elegir el principal (el que tenga mayor precio, luego mayor stock)
                lista.sort(key=lambda x: (float(x['precio'] or 0), float(x['stock'] or 0)), reverse=True)
                principal = lista[0]
                clones = lista[1:]
                
                stock_acumulado = float(principal['stock'] or 0)
                ids_a_borrar = []
                for clon in clones:
                    stock_acumulado += float(clon['stock'] or 0)
                    ids_a_borrar.append(clon['id'])
                    
                if ids_a_borrar:
                    # Actualizar stock del principal
                    db_manager.execute_query("UPDATE productos SET stock = ? WHERE id = ?", (stock_acumulado, principal['id']))
                    # Actualizar referencias en detalles_ventas (por si acaso usaban el ID del clon)
                    for cid in ids_a_borrar:
                        db_manager.execute_query("UPDATE detalles_ventas SET id_producto = ? WHERE id_producto = ?", (str(principal['id']), str(cid)))
                        db_manager.execute_query("DELETE FROM productos WHERE id = ?", (cid,))
                        eliminados += 1
                unificados += 1
                
        QMessageBox.information(self, "Unificación Completada", f"Se unificaron {unificados} códigos distintos.\nSe eliminaron {eliminados} productos duplicados (clones) de la base de datos.")
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
