# catalogo_productos.py - Coordinador de catalogo de productos.
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from src.services.inventario_service import InventarioService
from src.services.session_service import SessionService
from src.config import config

from src.ui_global.inventario_ui.moleculas.filtros_inventario import FiltrosInventario
from src.ui_global.inventario_ui.paneles.tabla_inventario import TablaInventario
from src.ui_global.inventario_ui.atomos.pie_inventario import PieInventario

class MotorBusquedaInventario(QThread):
    busqueda_terminada = pyqtSignal(list, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buscar = ""
        self.depto = None
        self._motor = None
        
    def setup(self, buscar, depto):
        self.buscar = buscar
        self.depto = depto
        
    def run(self):
        try:
            filas, _ = InventarioService.obtener_lista_de_productos(self.buscar, self.depto, limite=50000)
            sin_stock = sum(1 for r in filas if (r.get('stock') or 0.0) <= 0)
            self.busqueda_terminada.emit(filas, sin_stock)
        except Exception as e:
            import logging
            logging.getLogger("MotorBusquedaInventario").error(f"Error en busqueda: {e}")
            self.busqueda_terminada.emit([], 0)

class CatalogoProductos(QWidget):
    volver = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_rows = []
        self.user_role = SessionService.obtener_rol_usuario()
        
        self.motor_busqueda = MotorBusquedaInventario(self)
        self.motor_busqueda.busqueda_terminada.connect(self._on_busqueda_terminada)
        
        self._setup_ui()
        self._cargar_deptos()
        self.cargar_datos()
        self.aplicar_permisos_perfil()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        self.setObjectName("catalogoProductosMain")

        from src.shared.urgencia_stock_banner import UrgenciaStockBanner
        self._urgencia_banner = UrgenciaStockBanner(self)
        layout.addWidget(self._urgencia_banner)

        # 1. Barra de filtros
        self.filtros = FiltrosInventario(self)
        self.filtros.filtros_cambiados.connect(self.cargar_datos)
        self.filtros.urgencia_toggled.connect(self._toggle_venta_sin_stock)
        layout.addWidget(self.filtros)

        self._sync_urgencia_banner()

        # 2. Tabla de productos
        self.tabla = TablaInventario(self)
        self.tabla.producto_doble_clic.connect(self._modificar_por_id)
        self.tabla.seleccion_cambiada.connect(self._on_seleccion_cambiada)
        layout.addWidget(self.tabla)

        # 3. Pie informativo
        self.pie = PieInventario(self)
        layout.addWidget(self.pie)

    def aplicar_permisos_perfil(self, rol=None):
        """Bloquea o desbloquea funciones segun el rol del perfil del usuario."""
        from src.services.session_service import SessionService
        if rol is None:
            self.user_role = SessionService.obtener_rol_usuario()
        else:
            self.user_role = str(rol).lower()

        # Si es cajero, no puede alterar el inventario (es de solo lectura)
        es_lectura_solamente = (self.user_role == "cajero")
        
        # Deshabilitar edicion por doble click si es cajero
        if es_lectura_solamente:
            try:
                self.tabla.producto_doble_clic.disconnect(self._modificar_por_id)
            except:
                pass
        else:
            try:
                self.tabla.producto_doble_clic.disconnect(self._modificar_por_id)
            except:
                pass
            self.tabla.producto_doble_clic.connect(self._modificar_por_id)

        # La casilla de urgencia de stock tampoco la puede cambiar un cajero
        self.filtros.chk_urgencia.setEnabled(not es_lectura_solamente)

    def _apply_catalogo_theme(self):
        # Colores del tema activo
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
        self.filtros.aplicar_tema(bg, text, border)
        self.tabla.aplicar_tema(bg, text, border, hover, sel_bg, sel_text, header_bg, header_text)

    def _sync_urgencia_banner(self):
        activo = bool(self.filtros.chk_urgencia.isChecked())
        self._urgencia_banner.set_active(activo)
        self.filtros.chk_urgencia.setStyleSheet(
            "QCheckBox { font-weight: 800; color: #B91C1C; padding: 4px 8px; "
            "border: 2px solid #DC2626; border-radius: 6px; background: #FEE2E2; }"
            "QCheckBox::indicator { width: 18px; height: 18px; }"
            if activo
            else "QCheckBox { font-weight: 800; color: #B91C1C; padding: 4px 8px; "
            "border: 1px solid #FECACA; border-radius: 6px; background: #FFF7ED; }"
            "QCheckBox::indicator { width: 18px; height: 18px; }"
        )

    def _toggle_venta_sin_stock(self, checked: bool):
        if checked:
            r = QMessageBox.warning(
                self,
                "Modo urgencia — vender sin stock",
                "Estás activando una excepción a las reglas de inventario.\n\n"
                "• El cajero podrá vender productos sin existencia.\n"
                "• Habrá una alerta PARPADEANTE en inventario y en el terminal.\n\n"
                "Desactivalo cuando termine la urgencia.",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if r != QMessageBox.StandardButton.Ok:
                self.filtros.set_chk_urgencia_state(False)
                self._sync_urgencia_banner()
                return

        config.set("opt_stock_negativo", bool(checked))
        self._sync_urgencia_banner()

    def showEvent(self, event):
        super().showEvent(event)
        self.filtros.set_chk_urgencia_state(bool(config.get("opt_stock_negativo", False)))
        self._sync_urgencia_banner()
        self.aplicar_permisos_perfil()

    def _cargar_deptos(self):
        try:
            from src.motor_inventario.motor_departamentos import MotorDepartamentos
            deps = MotorDepartamentos().obtener_categorias()
            self.filtros.set_departamentos(deps)
        except Exception as e:
            import logging
            logging.getLogger("CatalogoProductos").error(f"Error al cargar departamentos: {e}")

    def cargar_datos(self):
        buscar = self.filtros.obtener_texto_buscar()
        depto = self.filtros.obtener_departamento_seleccionado()

        self.pie.lbl_total.setText("🔄 Buscando productos... Por favor espera.")
        self.pie.lbl_stock0.setText("")
        self.tabla.setRowCount(0)
        
        self.motor_busqueda.setup(buscar, depto)
        self.motor_busqueda.start()

    def _on_busqueda_terminada(self, filas, sin_stock):
        self.all_rows = filas
        self.tabla.set_datos(filas)
        self.pie.actualizar_totales(len(filas), sin_stock)

    def _on_seleccion_cambiada(self, cantidad):
        self.pie.actualizar_seleccion(cantidad)

    def _modificar_por_id(self, id_p):
        r = InventarioService.buscar_producto_por_id(id_p)
        if not r: 
            return
            
        def get_val(col, default=0.0):
            return r.get(col) if r.get(col) is not None else default

        datos = {
            'id': r.get('id'), 
            'codigo': r.get('codigo') or '', 
            'nombre': r.get('nombre') or '',
            'precio': get_val('precio', 0.0), 
            'precio_mayoreo': get_val('precio_mayoreo', 0.0),
            'cant_mayoreo': get_val('cant_mayoreo', 0.0),
            'cant_oferta': get_val('cant_oferta', 0.0), 
            'precio_oferta': get_val('precio_oferta', 0.0),
            'costo': get_val('costo', 0.0), 
            'stock': get_val('stock', 0.0),
            'stock_minimo': get_val('stock_minimo', 0.0), 
            'stock_maximo': get_val('stock_maximo', 0.0),
            'unidad': r.get('unidad') or 'UN', 
            'es_pesable': get_val('es_pesable', 0),
            'departamento': r.get('departamento') or '', 
            'categoria': r.get('categoria') or 'GENERAL'
        }
        
        from src.ui_global.inventario_ui.moleculas.dialogo_producto import DialogoProducto
        dlg = DialogoProducto(datos, self)
        if qt_exec(dlg):
            d = dlg.get_data()
            is_new = not bool(d.get('id'))
            ok, msg = InventarioService.guardar_producto(d, es_nuevo=is_new, producto_id=d.get('id'))
            if ok:
                self.cargar_datos()
                try:
                    from src.central_red_global.network_engine import get_network_engine
                    e = get_network_engine()
                    if e: 
                        e.broadcast_message("PRECIOS_ACTUALIZADOS", {})
                except: 
                    pass
            else:
                QMessageBox.warning(self, "Error", f"No se pudo guardar.\n\nDetalle técnico:\n{msg}")

    def _modificar_seleccionado(self):
        # Si el usuario es cajero, no permitir modificar
        if self.user_role == "cajero":
            QMessageBox.warning(self, "Acceso Denegado", "Tu perfil de cajero no tiene permiso para modificar productos.")
            return

        id_p = self.tabla.obtener_producto_id_seleccionado()
        if id_p:
            self._modificar_por_id(id_p)
        else:
            QMessageBox.information(self, "Selección", "Selecciona un producto primero.")

    def _exportar(self):
        from datetime import datetime
        nombre_def = f"productos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exportar productos", nombre_def,
            "Excel (*.xlsx);;Todos los archivos (*)")
        if not filepath: 
            return
        
        class WorkerExport(QThread):
            finished = pyqtSignal(bool, str)
            def __init__(self, path):
                super().__init__()
                self.path = path
            def run(self):
                ok, msg = InventarioService.exportar_a_excel(self.path)
                self.finished.emit(ok, msg)
                
        self._btn_sender = self.sender()
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
        if self.user_role == "cajero":
            QMessageBox.warning(self, "Acceso Denegado", "Tu perfil de cajero no tiene permiso para importar precargas.")
            return

        respuesta = QMessageBox.question(
            self, "Precarga desde la Nube",
            "¿Deseas descargar y sumar ~12,800 productos precargados desde la nube a tu base de datos?\n(Esto tomará un par de segundos)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes
        )
        if respuesta != QMessageBox.StandardButton.Yes: 
            return

        class WorkerPrecarga(QThread):
            finished = pyqtSignal(bool, str)
            def run(self):
                ok, msg = InventarioService.descargar_productos_nube()
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
                self.filtros.txt_buscar.clear()
                self.cargar_datos()

        self._worker_pre.finished.connect(on_fin_pre)
        self._worker_pre.start()

    def _unificar_duplicados(self):
        if self.user_role == "cajero":
            QMessageBox.warning(self, "Acceso Denegado", "Tu perfil de cajero no tiene permiso para modificar o unificar productos.")
            return

        respuesta = QMessageBox.question(
            self, "Unificar Duplicados",
            "¿Deseas buscar y unificar automáticamente todos los productos repetidos (con el mismo código)?\n\nEl sistema acumulará el stock en el producto principal y eliminará las copias vacías o basura.\nEste proceso no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if respuesta != QMessageBox.StandardButton.Yes: 
            return
        
        ok, msg = InventarioService.unificar_duplicados()
        QMessageBox.information(self, "Unificación Completada", msg)
        self.filtros.txt_buscar.clear()
        self.cargar_datos()

    def _importar(self):
        if self.user_role == "cajero":
            QMessageBox.warning(self, "Acceso Denegado", "Tu perfil de cajero no tiene permiso para importar planillas Excel.")
            return

        filepath, _ = QFileDialog.getOpenFileName(
            self, "Importar productos", "",
            "Excel (*.xlsx *.xls);;Todos los archivos (*)")
        if not filepath: 
            return

        class WorkerImport(QThread):
            finished = pyqtSignal(bool, str)
            def __init__(self, path):
                super().__init__()
                self.path = path
            def run(self):
                ok, msg = InventarioService.importar_desde_excel(self.path)
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
                self._cargar_deptos()
                self.cargar_datos()
        self._worker_imp.finished.connect(on_fin_imp)
        self._worker_imp.start()
