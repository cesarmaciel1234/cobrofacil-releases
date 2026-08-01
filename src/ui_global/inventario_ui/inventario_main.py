# inventario_main.py - Pantalla principal del Inventario.
from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QPushButton, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QTreeWidget, QTreeWidgetItem, QSplitter,
    QComboBox, QCheckBox, QStackedWidget, QFileDialog, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QColor, QFont, QBrush
from src.config import config
from src.services.inventario_service import InventarioService

from src.ui_global.inventario_ui.componentes.dialogo_producto import DialogoProducto
from src.ui_global.inventario_ui.componentes.panel_departamentos import PanelDepartamentos
from src.ui_global.inventario_ui.componentes.panel_categorias import PanelCategorias
from src.ui_global.inventario_ui.componentes.catalogo_productos import CatalogoProductos

class Admin1Inventario(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.user_role = "admin" # Rol predeterminado
        self._setup_ui()
        self._apply_inventario_theme()
        self.aplicar_permisos_perfil()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_inventario_theme()
        self.aplicar_permisos_perfil()

    def aplicar_permisos_perfil(self, rol: str = None):
        """Bloquea o desbloquea los botones de la barra de herramientas según el rol.
        Si se pasa 'rol', usa ese en lugar de leer la sesion activa (util para carteleria sin login).
        """
        from src.services.session_service import SessionService
        if rol is not None:
            self.user_role = str(rol).lower()
        else:
            self.user_role = SessionService.obtener_rol_usuario()

        # Si es cajero, es de solo lectura
        es_lectura = (self.user_role == "cajero")

        self.btn_nuevo.setEnabled(not es_lectura)
        self.btn_modif.setEnabled(not es_lectura)
        self.btn_eliminar.setEnabled(not es_lectura)
        self.btn_importar.setEnabled(not es_lectura)
        self.btn_precarga.setEnabled(not es_lectura)
        self.btn_unificar.setEnabled(not es_lectura)
        self.btn_categorias.setEnabled(not es_lectura)
        self.btn_deptos.setEnabled(not es_lectura)

        # Informar también al catálogo para sus bloqueos internos
        if hasattr(self, "catalogo"):
            self.catalogo.aplicar_permisos_perfil(self.user_role)

    def _apply_inventario_theme(self):
        """Aplica el tema dinámicamente según el theme_manager."""
        if hasattr(self, "catalogo"):
            self.catalogo._apply_catalogo_theme()

    def _setup_ui(self):
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', sans-serif; }
            QPushButton {
                background-color: #F1F5F9; color: #1E293B; border: 1px solid #CBD5E1;
                border-radius: 8px; padding: 10px 18px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #E2E8F0; border-color: #94A3B8; }
            QPushButton#blue, QPushButton[objectName="blue"] {
                background-color: #2563EB; color: #FFFFFF; border: none;
            }
            QPushButton#blue:hover, QPushButton[objectName="blue"]:hover {
                background-color: #1D4ED8;
            }
            QPushButton#danger, QPushButton[objectName="danger"] {
                background-color: #DC2626; color: #FFFFFF; border: none;
            }
            QPushButton#danger:hover, QPushButton[objectName="danger"]:hover {
                background-color: #B91C1C;
            }
            QPushButton#gray, QPushButton[objectName="gray"] {
                background-color: #64748B; color: #FFFFFF; border: none;
            }
            QPushButton#gray:hover, QPushButton[objectName="gray"]:hover {
                background-color: #475569;
            }
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Cabecera
        hdr = QFrame()
        hdr.setObjectName("header")
        hdr.setFixedHeight(85)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(25, 0, 25, 0)
        
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
        hl.addWidget(tit)
        hl.addStretch()
        root.addWidget(hdr)

        # Barra de herramientas principal (Toolbar)
        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(70)
        self.toolbar.setObjectName("inventarioToolbar")
        tl = QHBoxLayout(self.toolbar)
        tl.setContentsMargins(25, 0, 25, 0)
        tl.setSpacing(12)
        
        self.btn_nuevo = QPushButton("➕ NUEVO PRODUCTO")
        self.btn_nuevo.clicked.connect(self._nuevo)
        
        self.btn_modif = QPushButton("✏️ MODIFICAR")
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
        
        self.btn_deptos = QPushButton("⚖️ DEP. IMPUESTOS")
        self.btn_deptos.clicked.connect(self._mostrar_departamentos)
        
        self.btn_catalogo = QPushButton("📰 CATÁLOGO PDF")
        self.btn_catalogo.setObjectName("blue")
        self.btn_catalogo.clicked.connect(self._dialogo_catalogo_pdf)
        
        for b in [
            self.btn_nuevo, self.btn_modif, self.btn_eliminar, self.btn_importar, 
            self.btn_exportar, self.btn_precarga, self.btn_unificar, 
            self.btn_categorias, self.btn_deptos, self.btn_catalogo
        ]:
            tl.addWidget(b)
            
        tl.addStretch()
        root.addWidget(self.toolbar)

        # Vista de paginas
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

        self.stack.addWidget(self.catalogo)         # Index 0
        self.stack.addWidget(self.panel_deptos)     # Index 1
        self.stack.addWidget(self.panel_categorias) # Index 2

        self.stack.setCurrentIndex(0)
        root.addWidget(self.stack)
        
        # Sincronización en Tiempo Real
        db_path = config.get("db_path", "")
        if db_path and db_path != "":
            self.sync_timer = QTimer(self)
            self.sync_timer.timeout.connect(self.sincronizacion_silenciosa)
            self.sync_timer.start(5000)

    def sincronizacion_silenciosa(self):
        if not self.isVisible(): 
            return
        if self.stack.currentIndex() != 0: 
            return
        if self.catalogo.filtros.txt_buscar.hasFocus(): 
            return
        
        bar = self.catalogo.tabla.verticalScrollBar()
        scroll_pos = bar.value() if bar else 0
        target_count = self.catalogo.tabla.loaded_count
        
        self.cargar_datos()
        
        # Mantener paginas cargadas al hacer scroll
        if target_count > 50:
            while self.catalogo.tabla.loaded_count < target_count and self.catalogo.tabla.loaded_count < len(self.catalogo.all_rows):
                self.catalogo.tabla.cargar_siguiente_pagina()
        
        if bar:
            bar.setValue(scroll_pos)

    def _mostrar_departamentos(self, *args, **kwargs):
        self.toolbar.setVisible(False)
        self.stack.setCurrentIndex(1)

    def _mostrar_categorias(self, *args, **kwargs):
        self.toolbar.setVisible(False)
        self.stack.setCurrentIndex(2)

    def _volver_catalogo(self):
        self.toolbar.setVisible(True)
        self.stack.setCurrentIndex(0)

    def _dialogo_catalogo_pdf(self):
        visible_rows = []
        checked_rows = []
        
        # Buscar filas visibles y tildadas
        for i in range(self.catalogo.tabla.rowCount()):
            if not self.catalogo.tabla.isRowHidden(i):
                item_chk = self.catalogo.tabla.item(i, 0)
                item_id = self.catalogo.tabla.item(i, 1)
                if not item_id:
                    continue
                id_p = item_id.text()
                
                # Buscar datos originales
                row_data = None
                for r in self.catalogo.all_rows:
                    if str(r.get('id')) == id_p:
                        row_data = r
                        break
                        
                if row_data:
                    visible_rows.append(row_data)
                    if item_chk and item_chk.checkState() == Qt.CheckState.Checked:
                        checked_rows.append(row_data)

        total_filtered = len(visible_rows)
        has_checked = len(checked_rows) > 0

        dlg = QDialog(self)
        dlg.setWindowTitle("Exportar Catálogo / Lista de Precios")
        dlg.setFixedSize(500, 420)
        dlg.setStyleSheet("""
            QDialog { background: white; font-family: 'Segoe UI'; font-size: 13px; }
            QPushButton { background-color: #3b82f6; color: white; font-weight: bold; padding: 10px; border-radius: 6px; border: none; font-size: 12px; }
            QLineEdit, QComboBox, QSpinBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; background: white; }
            QRadioButton { spacing: 8px; font-weight: bold; }
        """)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)
        
        lbl_tit = QLabel("📰 CREAR CATÁLOGO DE PRECIOS (PDF)")
        lbl_tit.setStyleSheet("font-size: 15px; font-weight: 900; letter-spacing: 0.5px;")
        lay.addWidget(lbl_tit)
        
        from PyQt6.QtWidgets import QFormLayout, QRadioButton, QSpinBox
        form = QFormLayout()
        form.setSpacing(10)
        
        txt_titulo = QLineEdit("CATÁLOGO DE PRODUCTOS")
        txt_titulo.setPlaceholderText("Título del catálogo...")
        txt_titulo.setMinimumWidth(260)
        
        txt_negocio = QLineEdit("MINI-SÚPER ELITE")
        try:
            nombre_neg = config.get("business_name", "")
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
                depto = p.get('departamento') or ''
                uni = p.get('unidad') or 'UN'
                
                lote_catalogo.append({
                    "id": str(p.get('id')),
                    "nombre": p.get('nombre'),
                    "precio": f"{p.get('precio', 0.0):.2f}" if p.get('precio') is not None else "0.00",
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
        if self.user_role == "cajero":
            QMessageBox.warning(self, "Acceso Denegado", "Tu perfil de cajero no tiene permiso para crear productos.")
            return

        dlg = DialogoProducto(parent=self)
        if qt_exec(dlg):
            d = dlg.get_data()
            is_new = not bool(d.get('id'))
            ok, msg = InventarioService.guardar_producto(d, es_nuevo=is_new, producto_id=d.get('id'))
            if ok:
                self.catalogo._cargar_deptos()
                self.catalogo.cargar_datos()
                try:
                    from src.central_red_global.network_engine import get_network_engine
                    e = get_network_engine()
                    if e: 
                        e.broadcast_message("PRECIOS_ACTUALIZADOS", {})
                except: 
                    pass
            else:
                QMessageBox.warning(self, "Error", f"No se pudo guardar.\n\nDetalle técnico:\n{msg}")

    def _borrar_desde_catalogo(self, *args, **kwargs):
        if self.user_role == "cajero":
            QMessageBox.warning(self, "Acceso Denegado", "Tu perfil de cajero no tiene permiso para eliminar productos.")
            return

        # 1. Obtener todas las filas seleccionadas por checkbox
        filas_a_borrar = []
        for i in range(self.catalogo.tabla.rowCount()):
            chk = self.catalogo.tabla.item(i, 0)
            if chk and chk.checkState() == Qt.CheckState.Checked:
                filas_a_borrar.append(i)
                
        # 2. Si no hay checkboxes marcados, usar las seleccionadas
        if not filas_a_borrar:
            for item in self.catalogo.tabla.selectedItems():
                if item.row() not in filas_a_borrar:
                    filas_a_borrar.append(item.row())
                
        if not filas_a_borrar:
            QMessageBox.information(self, "Aviso", "Seleccioná al menos un producto (usando las casillas o seleccionando filas) para eliminar.")
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
            
        if QMessageBox.question(self, "Confirmar Eliminación", mensaje, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            eliminados = 0
            for id_p in ids_a_borrar:
                resultado = InventarioService.borrar_producto(id_p)
                # borrar_producto puede retornar bool o (bool, str)
                ok = resultado[0] if isinstance(resultado, tuple) else bool(resultado)
                if ok:
                    eliminados += 1
                    
            if eliminados > 0:
                self.catalogo._cargar_deptos()
                self.catalogo.cargar_datos()
                if len(ids_a_borrar) > 1:
                    QMessageBox.information(self, "Éxito", f"Se eliminaron {eliminados} productos correctamente.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el/los producto(s) de la base de datos.")
