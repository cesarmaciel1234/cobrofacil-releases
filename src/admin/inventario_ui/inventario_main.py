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

# Removed database direct import


from src.admin.inventario_ui.componentes.dialogo_producto import DialogoProducto
from src.admin.inventario_ui.componentes.panel_departamentos import PanelDepartamentos
from src.admin.inventario_ui.componentes.panel_categorias import PanelCategorias
from src.admin.inventario_ui.componentes.catalogo_productos import CatalogoProductos

class Admin1Inventario(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._apply_inventario_theme()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_inventario_theme()

    def _apply_inventario_theme(self):
        """El tema global se aplica automáticamente; ya no forzamos el modo claro."""
        pass

    def _setup_ui(self):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # Header Elite Blue (Cajero Style unificado sin recuadro blanco)
        hdr = QFrame(); hdr.setObjectName("header"); hdr.setFixedHeight(85)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(25,0,25,0)
        
        btn_back = QPushButton("🔙 VOLVER AL PANEL")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                border-radius: 10px;
                padding: 10px 25px; border: 1px solid #CBD5E1; font-size: 11px; letter-spacing: 1px;
            }
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)
        hl.addWidget(btn_back)
        
        hl.addSpacing(20)
        tit = QLabel("📦 GESTIÓN DE INVENTARIO <span style='color:#64748B;'>2026</span>")
        tit.setObjectName("titulo")
        tit.setStyleSheet("background: transparent;")
        hl.addWidget(tit); hl.addStretch()
        root.addWidget(hdr)

        # Toolbar superior
        self.toolbar = QFrame(); self.toolbar.setFixedHeight(70)
        self.toolbar.setObjectName("inventarioToolbar")
        tl = QHBoxLayout(self.toolbar); tl.setContentsMargins(25,0,25,0); tl.setSpacing(12)
        self.btn_nuevo    = QPushButton("➕ NUEVO PRODUCTO")
        self.btn_nuevo.clicked.connect(self._nuevo)
        self.btn_modif    = QPushButton("✏️ MODIFICAR")
        self.btn_modif.clicked.connect(lambda: self.catalogo._modificar_seleccionado())
        self.btn_eliminar = QPushButton("🗑️ ELIMINAR")
        self.btn_eliminar.setObjectName("danger")
        self.btn_eliminar.clicked.connect(self._borrar_desde_catalogo)
        
        self.btn_importar = QPushButton("📥 IMPORTAR EXCEL")
        self.btn_importar.clicked.connect(lambda: self.catalogo._importar())
        self.btn_exportar = QPushButton("📤 EXPORTAR EXCEL")
        self.btn_exportar.clicked.connect(lambda: self.catalogo._exportar())
        self.btn_precarga = QPushButton("📦 PRECARGA NUBE")
        self.btn_precarga.clicked.connect(lambda: self.catalogo._descargar_precarga())
        self.btn_unificar = QPushButton("🧹 UNIFICAR DUPLICADOS")
        self.btn_unificar.setObjectName("blue")
        self.btn_unificar.clicked.connect(lambda: self.catalogo._unificar_duplicados())
        
        self.btn_categorias = QPushButton("📁 DEPARTAMENTOS")
        self.btn_categorias.clicked.connect(self._mostrar_categorias)
        
        self.btn_deptos   = QPushButton("⚖️ DEP. IMPUESTOS")
        self.btn_deptos.clicked.connect(self._mostrar_departamentos)
        
        self.btn_catalogo = QPushButton("📰 CATÁLOGO PDF")
        self.btn_catalogo.setObjectName("blue")
        self.btn_catalogo.clicked.connect(self._dialogo_catalogo_pdf)
        
        for b in [self.btn_nuevo, self.btn_modif, self.btn_eliminar, self.btn_importar, self.btn_exportar, self.btn_precarga, self.btn_unificar, self.btn_categorias, self.btn_deptos, self.btn_catalogo]:
            tl.addWidget(b)
        tl.addStretch()
        root.addWidget(self.toolbar)

        self.stack = QStackedWidget()

        self.catalogo = CatalogoProductos()

        self.panel_deptos = PanelDepartamentos()
        self.panel_deptos.volver.connect(self._volver_catalogo)
        self.panel_deptos.departamentos_cambiados.connect(self.catalogo._cargar_deptos)
        self.panel_deptos.departamentos_cambiados.connect(self.catalogo.cargar_datos)

        self.panel_categorias = PanelCategorias()
        self.panel_categorias.volver.connect(self._volver_catalogo)
        self.panel_categorias.categorias_cambiadas.connect(self.catalogo._cargar_deptos)
        self.panel_categorias.categorias_cambiadas.connect(self.catalogo.cargar_datos)

        self.stack.addWidget(self.catalogo)         # 0
        self.stack.addWidget(self.panel_deptos)     # 1
        self.stack.addWidget(self.panel_categorias) # 2

        self.stack.setCurrentIndex(0)
        root.addWidget(self.stack)
        
        # Sincronización en Tiempo Real (Solo para Modo Espectador / Red)
        from src.config import config
        from PyQt6.QtCore import QTimer
        db_path = config.get("db_path", "")
        if db_path and db_path != "":
            self.sync_timer = QTimer(self)
            self.sync_timer.timeout.connect(self.sincronizacion_silenciosa)
            self.sync_timer.start(5000) # Cada 5 segundos

    def sincronizacion_silenciosa(self):
        if not self.isVisible(): return
        if self.stack.currentIndex() != 0: return
        if self.catalogo.txt_buscar.hasFocus(): return
        
        bar = self.catalogo.tabla.verticalScrollBar()
        scroll_pos = bar.value() if bar else 0
        target_count = self.catalogo.loaded_count # Cuántos registros ya cargó el usuario con scroll
        
        self.cargar_datos()
        
        # Forzar recarga de las páginas que ya tenía scrolleadas
        if target_count > 50:
            while self.catalogo.loaded_count < target_count and self.catalogo.loaded_count < len(self.catalogo.all_rows):
                self.catalogo._cargar_siguiente_pagina()
        
        if bar:
            bar.setValue(scroll_pos)

    def _mostrar_departamentos(self, *args, **kwargs):
        self.toolbar.setVisible(False) # Elimina los botones duplicados de la vista principal
        self.stack.setCurrentIndex(1)

    def _mostrar_categorias(self, *args, **kwargs):
        self.toolbar.setVisible(False)
        self.stack.setCurrentIndex(2)

    def _volver_catalogo(self):
        self.toolbar.setVisible(True)  # Restaura la botonera al regresar
        self.stack.setCurrentIndex(0)

    def _dialogo_catalogo_pdf(self):
        visible_rows = []
        checked_rows = []
        for i in range(self.catalogo.tabla.rowCount()):
            if not self.catalogo.tabla.isRowHidden(i):
                it = self.catalogo.tabla.item(i, 0)
                id_p = self.catalogo.tabla.item(i, 1).text()
                
                # Find the row data
                row_data = None
                for r in self.catalogo.all_rows:
                    if str(r['id']) == id_p:
                        row_data = r
                        break
                        
                if row_data:
                    visible_rows.append(row_data)
                    if it and it.checkState() == Qt.Checked:
                        checked_rows.append(row_data)

        total_filtered = len(visible_rows)
        has_checked = len(checked_rows) > 0

        dlg = QDialog(self)
        dlg.setWindowTitle("Exportar Catálogo / Lista de Precios")
        dlg.setFixedSize(500, 420)
        dlg.setStyleSheet("""
            QDialog { background: white;  font-family: 'Segoe UI'; font-size: 13px; }
            QPushButton {  background-color: #3b82f6; color: white; font-weight: bold; padding: 10px; border-radius: 6px; border: none; font-size: 12px; }
            QPushButton:hover {  }
            QLineEdit, QComboBox, QSpinBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px;  background: white; }
            QRadioButton { spacing: 8px; font-weight: bold; }
        """)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)
        
        lbl_tit = QLabel("📰 CREAR CATÁLOGO DE PRECIOS (PDF)")
        lbl_tit.setStyleSheet(" font-size: 15px; font-weight: 900; letter-spacing: 0.5px;")
        lay.addWidget(lbl_tit)
        
        from PyQt6.QtWidgets import QFormLayout, QRadioButton, QSpinBox
        form = QFormLayout()
        form.setSpacing(10)
        
        txt_titulo = QLineEdit("CATÁLOGO DE PRODUCTOS")
        txt_titulo.setPlaceholderText("Título del catálogo...")
        txt_titulo.setMinimumWidth(260)
        
        txt_negocio = QLineEdit("MINI-SÚPER ELITE")
        try:
            from src.config import config as _cfg
            nombre_neg = _cfg.get("business_name", "")
            if nombre_neg:
                txt_negocio.setText(nombre_neg.upper())
        except:
            pass
            
        cmb_diseno = QComboBox()
        cmb_diseno.addItem("📋 Lista Compacta (Tabla formal)", "lista")
        cmb_diseno.addItem("🖼️ Folleto Gráfico (Tarjetas de producto)", "grilla")
        
        form.addRow("<b>Título Principal:</b>", txt_titulo)
        form.addRow("<b>Nombre del Negocio:</b>", txt_negocio)
        form.addRow("<b>Diseño del PDF:</b>", cmb_diseno)
        lay.addLayout(form)
        
        lay.addWidget(QLabel("<b>¿Qué productos incluir?</b>"))
        lay_inc = QVBoxLayout()
        rb_all = QRadioButton(f"Los {total_filtered} productos que estoy viendo ahora")
        rb_all.setChecked(True)
        
        rb_sel = QRadioButton(f"Solo los marcados [🗹] ({len(checked_rows)} seleccionados)")
        rb_sel.setEnabled(has_checked)
        if has_checked:
            rb_sel.setChecked(True)
            
        lay_inc.addWidget(rb_all)
        lay_inc.addWidget(rb_sel)
        lay.addLayout(lay_inc)
        
        lay_limite = QHBoxLayout()
        lay_limite.addWidget(QLabel("<b>Limitar a los primeros:</b>"))
        spin_limite = QSpinBox()
        spin_limite.setRange(1, 100000)
        spin_limite.setValue(total_filtered if total_filtered > 0 else 1)
        spin_limite.setSuffix(" productos")
        lay_limite.addWidget(spin_limite)
        lay_limite.addStretch()
        lay.addLayout(lay_limite)
        
        # Conectar cambios de radio button a spinbox
        def _update_spin():
            if rb_sel.isChecked():
                spin_limite.setValue(len(checked_rows) if len(checked_rows) > 0 else 1)
            else:
                spin_limite.setValue(total_filtered if total_filtered > 0 else 1)
        rb_all.toggled.connect(_update_spin)
        rb_sel.toggled.connect(_update_spin)
        
        btn_ok = QPushButton("✔ Generar PDF y Abrir")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(dlg.accept)
        lay.addSpacing(10)
        lay.addWidget(btn_ok)
        
        if qt_exec(dlg):
            if rb_sel.isChecked():
                productos_a_procesar = checked_rows
            else:
                productos_a_procesar = visible_rows
                
            limite = spin_limite.value()
            productos_a_procesar = productos_a_procesar[:limite]
                
            if not productos_a_procesar:
                QMessageBox.warning(self, "Aviso", "No hay productos para exportar.")
                return
                
            lote_catalogo = []
            for p in productos_a_procesar:
                # sqlite3.Row does not have .get() method, use bracket notation
                depto = p['departamento'] if 'departamento' in p.keys() and p['departamento'] is not None else ''
                uni = p['unidad'] if 'unidad' in p.keys() and p['unidad'] is not None else 'UN'
                
                lote_catalogo.append({
                    "id": str(p['id']),
                    "nombre": p['nombre'],
                    "precio": f"{p['precio']:.2f}" if p['precio'] is not None else "0.00",
                    "departamento": depto,
                    "unidad": uni
                })
                
            try:
                from src.creador_pdf_global.motor_pdf import EtiquetaRenderer, abrir_archivo_pdf
                ren = EtiquetaRenderer()
                pdf_path = ren.generar_pdf_catalogo_inventario(
                    lote_productos=lote_catalogo,
                    titulo_folleto=txt_titulo.text().strip(),
                    negocio=txt_negocio.text().strip(),
                    diseno_tipo=cmb_diseno.currentData()
                )
                abrir_archivo_pdf(pdf_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Fallo al generar catálogo PDF: {e}")

    def cargar_datos(self):
        self.catalogo._cargar_deptos()
        self.catalogo.cargar_datos()

    def _nuevo(self, *args, **kwargs):
        dlg = DialogoProducto(parent=self)
        if qt_exec(dlg):
            d = dlg.get_data()
            from src.motor_inventario.motor_catalogo import MotorCatalogo
            ok, msg = MotorCatalogo().guardar_producto(d, is_new=True)
            if ok:
                self.catalogo._cargar_deptos(); self.catalogo.cargar_datos()
                try:
                    from src.central_red_global.network_engine import get_network_engine
                    e = get_network_engine()
                    if e: e.broadcast_message("PRECIOS_ACTUALIZADOS", {})
                except: pass
            else:
                QMessageBox.warning(self,"Error","No se pudo guardar.")

    def _borrar_desde_catalogo(self, *args, **kwargs):
        # 1. Obtener todas las filas seleccionadas por checkbox
        filas_a_borrar = []
        for i in range(self.catalogo.tabla.rowCount()):
            chk = self.catalogo.tabla.item(i, 0)
            if chk and chk.checkState() == Qt.Checked:
                filas_a_borrar.append(i)
                
        # 2. Si no hay checkboxes marcados, usar las filas seleccionadas (multiselección)
        if not filas_a_borrar:
            for item in self.catalogo.tabla.selectedItems():
                if item.row() not in filas_a_borrar:
                    filas_a_borrar.append(item.row())
                
        if not filas_a_borrar:
            QMessageBox.information(self, "Aviso", "Seleccioná al menos un producto (usando las casillas) para eliminar.")
            return
            
        nombres = []
        ids_a_borrar = []
        for row in filas_a_borrar:
            item_id = self.catalogo.tabla.item(row, 1)
            item_nom = self.catalogo.tabla.item(row, 2)
            if item_id and item_nom:
                ids_a_borrar.append(item_id.text())
                nombres.append(item_nom.text())
                
        if not ids_a_borrar:
            return
            
        mensaje = f"¿Estás seguro de eliminar {len(ids_a_borrar)} producto(s)?"
        if len(ids_a_borrar) == 1:
            mensaje = f"¿Borrar producto: {nombres[0]}?"
            
        if QMessageBox.question(self, "Confirmar Eliminación", mensaje, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            eliminados = 0
            from src.motor_inventario.motor_catalogo import MotorCatalogo
            motor = MotorCatalogo()
            for id_p in ids_a_borrar:
                # Borrar usando el motor
                ok, _ = motor.borrar_producto(id_p)
                if ok:
                    eliminados += 1
                    
            if eliminados > 0:
                self.catalogo._cargar_deptos()
                self.catalogo.cargar_datos()
                if len(ids_a_borrar) > 1:
                    QMessageBox.information(self, "Éxito", f"Se eliminaron {eliminados} productos correctamente.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el/los producto(s) de la base de datos.")
