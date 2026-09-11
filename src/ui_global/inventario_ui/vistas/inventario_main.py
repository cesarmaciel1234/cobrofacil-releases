# inventario_main.py - Pantalla principal del Inventario.
from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QPushButton, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QTreeWidget, QTreeWidgetItem, QSplitter,
    QComboBox, QCheckBox, QStackedWidget, QFileDialog, QGridLayout,
    QScrollArea, QListWidget, QListWidgetItem,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QColor, QFont, QBrush
from src.config import config
from src.services.inventario_service import InventarioService

from src.ui_global.inventario_ui.moleculas.dialogo_producto import DialogoProducto
from src.ui_global.inventario_ui.moleculas.panel_departamentos import PanelDepartamentos
from src.ui_global.inventario_ui.moleculas.panel_categorias import PanelCategorias
from src.ui_global.inventario_ui.paneles.catalogo_productos import CatalogoProductos

_QSS_INVENTARIO = """
QWidget#AdminInventario {
    background: #F8FAFC;
    font-family: 'Segoe UI', sans-serif;
    color: #0F172A;
}
QWidget#AdminInventario QStackedWidget { background: #F1F5F9; border: none; }
QWidget#AdminInventario QLabel { color: #0F172A; }
QWidget#AdminInventario QPushButton {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 700;
    font-size: 13px;
}
QWidget#AdminInventario QPushButton:hover {
    background-color: #EFF6FF;
    border-color: #60A5FA;
    color: #1E3A8A;
}
QWidget#AdminInventario QPushButton#blue {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
}
QWidget#AdminInventario QPushButton#blue:hover { background-color: #1D4ED8; color: #FFFFFF; }
QWidget#AdminInventario QPushButton#danger {
    background-color: #DC2626;
    color: #FFFFFF;
    border: none;
}
QWidget#AdminInventario QPushButton#danger:hover { background-color: #B91C1C; color: #FFFFFF; }
QWidget#AdminInventario QPushButton#btnInvBack {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 700;
}
"""


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
        # Preservar el rol que ya fue asignado (puede venir forzado desde carteleria)
        self.aplicar_permisos_perfil(self.user_role)

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
        if hasattr(self, "catalogo") and self.catalogo:
            self.catalogo.aplicar_permisos_perfil(self.user_role)
        for c in getattr(self, "_excel_cards", []):
            c.setEnabled((not es_lectura) or c.codigo == "exportar")

    def _apply_inventario_theme(self):
        self.setObjectName("AdminInventario")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(_QSS_INVENTARIO)
        if hasattr(self, "catalogo") and self.catalogo:
            self.catalogo._apply_catalogo_theme(forzar_claro=True)

    def _setup_ui(self):
        self.setObjectName("AdminInventario")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(_QSS_INVENTARIO)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        hdr = QFrame()
        hdr.setObjectName("header")
        hdr.setFixedHeight(72)
        hdr.setStyleSheet("QFrame#header { background: #FFFFFF; border-bottom: 1px solid #E2E8F0; }")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(24, 0, 24, 0)
        self.btn_back = QPushButton("← Panel admin")
        self.btn_back.setObjectName("btnInvBack")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.clicked.connect(self._on_back)
        hl.addWidget(self.btn_back)
        hl.addSpacing(16)
        col_t = QVBoxLayout()
        col_t.setSpacing(0)
        self.lbl_titulo = QLabel("Inventario")
        self.lbl_titulo.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A; background: transparent;")
        self.lbl_sub = QLabel("Catálogo, Excel y rubros")
        self.lbl_sub.setStyleSheet("font-size: 12px; color: #64748B; background: transparent;")
        col_t.addWidget(self.lbl_titulo)
        col_t.addWidget(self.lbl_sub)
        hl.addLayout(col_t)
        hl.addStretch()
        root.addWidget(hdr)

        self.stack = QStackedWidget()
        self.catalogo = None
        self.panel_deptos = None
        self.panel_categorias = None
        self.pagina_catalogo = None
        self._idx = {"hub": 0}

        self.stack.addWidget(self._armar_hub())
        root.addWidget(self.stack)

        self.toolbar = QFrame()
        self.toolbar.hide()
        self.btn_nuevo = QPushButton("➕ NUEVO PRODUCTO")
        self.btn_nuevo.clicked.connect(self._nuevo)
        self.btn_modif = QPushButton("✏️ MODIFICAR")
        self.btn_modif.clicked.connect(self._modificar_sel)
        self.btn_eliminar = QPushButton("🗑️ ELIMINAR")
        self.btn_eliminar.setObjectName("danger")
        self.btn_eliminar.clicked.connect(self._borrar_desde_catalogo)
        self.btn_importar = QPushButton("📥 IMPORTAR EXCEL")
        self.btn_exportar = QPushButton("📤 EXPORTAR EXCEL")
        self.btn_precarga = QPushButton("📦 PRECARGA NUBE")
        self.btn_unificar = QPushButton("🧹 UNIFICAR DUPLICADOS")
        self.btn_unificar.setObjectName("blue")
        self.btn_categorias = QPushButton("📁 DEPARTAMENTOS")
        self.btn_deptos = QPushButton("⚖️ DEP. IMPUESTOS")
        self.btn_catalogo = QPushButton("📰 CATÁLOGO PDF")
        self.btn_catalogo.setObjectName("blue")
        self.btn_catalogo.clicked.connect(self._dialogo_catalogo_pdf)

        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.sincronizacion_silenciosa)
        self.sync_timer.start(90000)

    def _armar_hub(self):
        from src.motor_descuentos.compartido import TarjetaModulo
        page = QWidget()
        page.setStyleSheet("background: #F1F5F9;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F1F5F9; border: none; }")
        wrap = QWidget()
        wrap.setStyleSheet("background: #F1F5F9;")
        grid = QGridLayout(wrap)
        grid.setContentsMargins(28, 28, 28, 28)
        grid.setSpacing(18)
        cards = (
            ("catalogo", "📦", "Catálogo", "Alta, baja y precios. Acá se trabaja el producto."),
            ("excel", "📑", "Excel y nube", "Importar, exportar, precarga y unificar duplicados."),
            ("deptos", "📁", "Departamentos", "Rubros del catálogo."),
            ("iva", "⚖️", "IVA por departamento", "Impuesto de cada rubro."),
            ("pdf", "📰", "Catálogo PDF", "Para enviar a clientes: fotos, precio y WhatsApp."),
        )
        for i, (cod, ico, tit, sub) in enumerate(cards):
            card = TarjetaModulo(cod, ico, tit, sub)
            card.clicked.connect(lambda c=cod: self._abrir_modulo(c))
            grid.addWidget(card, i // 3, i % 3)
        grid.setRowStretch(2, 1)
        scroll.setWidget(wrap)
        lay.addWidget(scroll, 1)
        return page

    def _on_back(self):
        if self.stack.currentIndex() == 0:
            self.request_dashboard.emit()
        else:
            self.stack.setCurrentIndex(0)
            self.lbl_titulo.setText("Inventario")
            self.lbl_sub.setText("Catálogo, Excel y rubros")
            self.btn_back.setText("← Panel admin")

    def _abrir_modulo(self, codigo):
        if codigo == "pdf":
            self._asegurar_catalogo()
            self.stack.setCurrentWidget(self.pagina_catalogo)
            self.lbl_titulo.setText("Catálogo")
            self.lbl_sub.setText("Productos, precios y stock")
            self.btn_back.setText("← Módulos")
            self._dialogo_catalogo_pdf()
            return
        if codigo == "catalogo":
            self._asegurar_catalogo()
            self.stack.setCurrentWidget(self.pagina_catalogo)
            self.lbl_titulo.setText("Catálogo")
            self.lbl_sub.setText("Productos, precios y stock")
        elif codigo == "excel":
            self._asegurar_catalogo()
            self.stack.setCurrentWidget(self._pagina_excel())
            self.lbl_titulo.setText("Excel y nube")
            self.lbl_sub.setText("Importar, exportar y mantenimiento")
        elif codigo == "deptos":
            self._mostrar_categorias()
            self.lbl_titulo.setText("Departamentos")
            self.lbl_sub.setText("Rubros del catálogo")
        elif codigo == "iva":
            self._mostrar_departamentos()
            self.lbl_titulo.setText("IVA por departamento")
            self.lbl_sub.setText("Impuesto de cada rubro")
        self.btn_back.setText("← Módulos")

    def _asegurar_catalogo(self):
        if self.catalogo:
            return
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        bar = QFrame()
        bar.setFixedHeight(58)
        bar.setStyleSheet("QFrame { background: #FFFFFF; border-bottom: 1px solid #E2E8F0; }")
        tl = QHBoxLayout(bar)
        tl.setContentsMargins(16, 0, 16, 0)
        for b in (self.btn_nuevo, self.btn_modif, self.btn_eliminar, self.btn_catalogo):
            tl.addWidget(b)
        tl.addStretch()
        v.addWidget(bar)
        self.catalogo = CatalogoProductos()
        self.catalogo.aplicar_permisos_perfil(self.user_role)
        self.catalogo._apply_catalogo_theme(forzar_claro=True)
        v.addWidget(self.catalogo, 1)
        self.pagina_catalogo = wrap
        self.stack.addWidget(wrap)

    def _pagina_excel(self):
        if getattr(self, "_excel_page", None):
            return self._excel_page
        self._asegurar_catalogo()
        from src.motor_descuentos.compartido import TarjetaModulo
        page = QWidget()
        page.setStyleSheet("background: #F1F5F9;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)
        hint = QLabel("Cada tarjeta abre su acción. El catálogo se actualiza al terminar.")
        hint.setStyleSheet("color: #475569; font-size: 13px; background: transparent; border: none;")
        lay.addWidget(hint)
        grid = QGridLayout()
        grid.setSpacing(18)
        acciones = (
            ("importar", "📥", "Importar Excel", "Cargar productos desde un archivo .xlsx", self.catalogo._importar),
            ("exportar", "📤", "Exportar Excel", "Descargar el catálogo actual a un archivo Excel.", self.catalogo._exportar),
            ("nube", "☁️", "Precarga nube", "Sumar productos precargados si el local está vacío.", self.catalogo._descargar_precarga),
            ("unificar", "🧹", "Unificar duplicados", "Junta códigos repetidos y suma el stock.", self.catalogo._unificar_duplicados),
        )
        self._excel_cards = []
        for i, (cod, ico, tit, sub, fn) in enumerate(acciones):
            card = TarjetaModulo(cod, ico, tit, sub)
            card.clicked.connect(fn)
            self._excel_cards.append(card)
            grid.addWidget(card, i // 2, i % 2)
        lay.addLayout(grid)
        lay.addStretch()
        self._excel_page = page
        self.stack.addWidget(page)
        self.aplicar_permisos_perfil(self.user_role)
        return page

    def _modificar_sel(self):
        self._asegurar_catalogo()
        self.catalogo._modificar_seleccionado()

    def sincronizacion_silenciosa(self):
        if not self.isVisible() or not self.catalogo:
            return
        if self.stack.currentWidget() is not self.pagina_catalogo:
            return
        if self.catalogo.motor_busqueda.isRunning():
            return
        if self.catalogo.filtros.txt_buscar.hasFocus():
            return
        bar = self.catalogo.tabla.verticalScrollBar()
        scroll_pos = bar.value() if bar else 0
        target_count = self.catalogo.tabla.loaded_count
        self.catalogo.cargar_datos()
        if target_count > 50:
            while (
                self.catalogo.tabla.loaded_count < target_count
                and self.catalogo.tabla.loaded_count < len(self.catalogo.all_rows)
            ):
                self.catalogo.tabla.cargar_siguiente_pagina()
        if bar:
            bar.setValue(scroll_pos)

    def _mostrar_departamentos(self, *args, **kwargs):
        self._asegurar_catalogo()
        if self.panel_deptos is None:
            self.panel_deptos = PanelDepartamentos()
            self.panel_deptos.volver.connect(self._on_back)
            self.panel_deptos.departamentos_cambiados.connect(self.catalogo._cargar_deptos)
            self.panel_deptos.departamentos_cambiados.connect(self.catalogo.cargar_datos)
            self.stack.addWidget(self.panel_deptos)
        self.stack.setCurrentWidget(self.panel_deptos)

    def _mostrar_categorias(self, *args, **kwargs):
        self._asegurar_catalogo()
        if self.panel_categorias is None:
            self.panel_categorias = PanelCategorias()
            self.panel_categorias.volver.connect(self._on_back)
            self.panel_categorias.categorias_cambiadas.connect(self.catalogo._cargar_deptos)
            self.panel_categorias.categorias_cambiadas.connect(self.catalogo.cargar_datos)
            self.stack.addWidget(self.panel_categorias)
        self.stack.setCurrentWidget(self.panel_categorias)

    def _volver_catalogo(self):
        self._on_back()

    def _png_vitrina_producto(self, producto):
        try:
            from src.carteleria.motor_carteleria.iconos_tv import png_vitrina_path
            return png_vitrina_path(producto) or ""
        except Exception:
            return ""

    def _dialogo_catalogo_pdf(self):
        self._asegurar_catalogo()
        ids_pre = set()
        tabla = getattr(self.catalogo, "tabla", None)
        if tabla:
            for i in range(tabla.rowCount()):
                item_id = tabla.item(i, 1)
                chk = tabla.item(i, 0)
                if not item_id:
                    continue
                pid = item_id.text()
                if chk and chk.checkState() == Qt.CheckState.Checked:
                    ids_pre.add(str(pid))
        from src.ui_global.inventario_ui.moleculas.dialogo_catalogo_clientes import abrir_catalogo_clientes
        abrir_catalogo_clientes(self, preseleccion_ids=ids_pre)

    def cargar_datos(self):
        if not self.catalogo:
            return
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
                self._asegurar_catalogo()
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

        if not self.catalogo:
            QMessageBox.information(self, "Aviso", "Entrá primero al catálogo.")
            return
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
