import sys
import os

# Asegurar que la raíz del proyecto esté en el path para poder importar 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import logging
from src.utils.qt_compat import qt_exec

from PyQt6.QtWidgets import QApplication, QStackedWidget
from src.carteleria.dashboard.dashboard_main import CarteleriaDashboard

logger = logging.getLogger("PunPro")

class CarteleriaApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cartelería Autónoma - Apple Style Modular")
        self.setMinimumSize(1024, 768)
        self.setStyleSheet("QStackedWidget { background: #F8FAFC; border: none; }")

        self.dashboard = CarteleriaDashboard()
        self.addWidget(self.dashboard)

        # Variables para inicialización diferida (Lazy Loading)
        self.tv_main = None
        self.admin = None
        self.inv = None
        self.ofe = None
        self.red = None
        self.prov = None
        self.png_prod = None
        
        self.estilo_completo = ""  # Cacheamos el estilo para aplicarlo on-demand

        # Conectar Dashboard
        self.dashboard.request_launch_tv.connect(self.lanzar_tv)
        self.dashboard.request_admin_tv.connect(self.lanzar_admin)
        self.dashboard.request_inventario.connect(self.lanzar_inv)
        self.dashboard.request_ofertas.connect(self.lanzar_ofe)
        self.dashboard.request_red_lan.connect(self.lanzar_red)
        self.dashboard.request_proveedores.connect(self.lanzar_prov)
        self.dashboard.request_png_productos.connect(self.lanzar_png_productos)
        self.dashboard.request_exit.connect(self.close)
        self.dashboard.request_toggle_theme.connect(self.toggle_carteleria_theme)

        # Conectar Admin (Volver al dashboard) - Solo si existieran (se conectan en el lazy load)
        
        from PyQt6.QtGui import QShortcut, QKeySequence
        self.shortcut = QShortcut(QKeySequence("Esc"), self)
        self.shortcut.activated.connect(self.volver_dashboard)

    def lanzar_tv(self):
        logger.info("Lanzando TV...")
        from src.carteleria.lanzador_tv.lanzador_directo import get_lanzador_directo
        lanzador = get_lanzador_directo()
        if lanzador.lanzar():
            logger.info("TV lanzada en kiosk (F11 para salir).")
        else:
            logger.error("No se pudo lanzar la cartelería TV.")

    def volver_dashboard(self):
        try:
            from src.carteleria.lanzador_tv.lanzador_directo import get_lanzador_directo
            get_lanzador_directo().detener()
        except Exception:
            pass
        if self.tv_main:
            try:
                self.tv_main.detener_carteleria()
            except Exception:
                pass
        self.setCurrentWidget(self.dashboard)
        self.showMaximized()

    def lanzar_admin(self):
        if not self.admin:
            from src.carteleria.admin15_carteleria import CarteleriaConfigPanel
            self.admin = CarteleriaConfigPanel()
            self.addWidget(self.admin)
            self.admin.request_back.connect(self.volver_dashboard)
        self.setCurrentWidget(self.admin)
        self.showMaximized()

    def lanzar_inv(self):
        # Siempre recrear para evitar quedar con estado roto cacheado
        if self.inv:
            self.removeWidget(self.inv)
            self.inv.deleteLater()
            self.inv = None
            
        from src.ui_global.inventario_ui.vistas.inventario_main import Admin1Inventario
        self.inv = Admin1Inventario()
        self.addWidget(self.inv)
        self.inv.request_dashboard.connect(self.volver_dashboard)
        if self.estilo_completo: self.inv.setStyleSheet(self.estilo_completo)
        if hasattr(self.inv, "_apply_inventario_theme"): self.inv._apply_inventario_theme()
        
        # La carteleria no tiene login → current_user es None → rol seria "cajero"
        # Forzamos admin para que los botones de edicion funcionen
        if hasattr(self.inv, "aplicar_permisos_perfil"):
            self.inv.aplicar_permisos_perfil("admin")
        if hasattr(self.inv, "catalogo") and hasattr(self.inv.catalogo, "aplicar_permisos_perfil"):
            self.inv.catalogo.aplicar_permisos_perfil("admin")
            
        self.setCurrentWidget(self.inv)
        self.showMaximized()

    def lanzar_ofe(self):
        if not self.ofe:
            try:
                from src.motor_descuentos.vistas.ofertas_main import Admin2Ofertas
                self.ofe = Admin2Ofertas()
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    "Motor de Promociones",
                    f"No se pudo abrir el módulo:\n{e}",
                )
                return
            self.addWidget(self.ofe)
            self.ofe.request_dashboard.connect(self.volver_dashboard)
            if self.estilo_completo:
                self.ofe.setStyleSheet(self.estilo_completo)
        self.setCurrentWidget(self.ofe)
        self.showMaximized()

    def lanzar_red(self):
        if not self.red:
            from src.carteleria.red_lan.red_lan_main import Admin6RedLan
            self.red = Admin6RedLan()
            self.addWidget(self.red)
            self.red.request_dashboard.connect(self.volver_dashboard)
            if self.estilo_completo: self.red.setStyleSheet(self.estilo_completo)
        self.setCurrentWidget(self.red)
        self.showMaximized()

    def lanzar_png_productos(self):
        if self.png_prod:
            self.removeWidget(self.png_prod)
            self.png_prod.deleteLater()
            self.png_prod = None
        from src.carteleria.creador_png.panel_png_productos import PanelPngProductos
        self.png_prod = PanelPngProductos()
        self.addWidget(self.png_prod)
        self.png_prod.volver.connect(self.volver_dashboard)
        if self.estilo_completo:
            self.png_prod.setStyleSheet(self.estilo_completo)
        self.setCurrentWidget(self.png_prod)
        self.showMaximized()

    def lanzar_prov(self):
        if not self.prov:
            from src.ui_global.proveedor.vista_proveedor import VistaProveedor
            self.prov = VistaProveedor()
            self.addWidget(self.prov)
            # Para proveedor, no hay señal back al dashboard estándar, usan su propio btn cerrar
            if self.estilo_completo: self.prov.setStyleSheet(self.estilo_completo)
        
        self.setCurrentWidget(self.prov)
        if hasattr(self.prov, 'cargar_datos'):
            self.prov.cargar_datos()
        self.showMaximized()

    def toggle_carteleria_theme(self):
        from src.utils.theme_manager import theme_manager
        theme_manager.toggle_theme()
        self.apply_theme()

    def apply_theme(self):
        try:
            from src.config import config
            from src.utils.paths import get_resource_path
            from src.utils.theme_manager import theme_manager
            import os
            
            tema_actual = theme_manager.current_theme
            qss_filename = "estilo_dia.qss" if tema_actual == "light" else "estilo_noche.qss"
            qss_path = get_resource_path(os.path.join("src", "ui_components", qss_filename))
            
            if not os.path.exists(qss_path):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                qss_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "src", "ui_components", qss_filename)

            with open(qss_path, "r", encoding="utf-8") as f:
                estilo_tema = f.read()

            base_path = os.path.join(os.path.dirname(qss_path), "base.qss")
            estilo_base = ""
            if os.path.exists(base_path):
                with open(base_path, "r", encoding="utf-8") as f_base:
                    estilo_base = f_base.read()

            estilo_completo = estilo_base + "\n" + estilo_tema
            self.estilo_completo = estilo_completo
            
            self.dashboard.setStyleSheet(estilo_completo)
            # Admin config es UI clara propia: el QSS noche deja marcos oscuros superpuestos.
            if self.inv: self.inv.setStyleSheet(estilo_completo)
            if self.ofe: self.ofe.setStyleSheet(estilo_completo)
            if self.red: self.red.setStyleSheet(estilo_completo)
            if self.prov: self.prov.setStyleSheet(estilo_completo)
            if self.png_prod: self.png_prod.setStyleSheet(estilo_completo)
            
            # Notificar al inventario para que actualice sus colores internos
            if self.inv and hasattr(self.inv, "_apply_inventario_theme"):
                self.inv._apply_inventario_theme()
                
            # Notificar al dashboard principal
            if hasattr(self.dashboard, "apply_dashboard_theme"):
                self.dashboard.apply_dashboard_theme(theme_manager.is_dark())
                
        except Exception as e:
            print("Error aplicando tema global a los paneles de cartelería:", e)

def lanzar_app(app=None):
    if app is None:
        app = QApplication(sys.argv)
        
    # LAN solo si no hay Servidor de Tienda (él ya tiene :8000 / UDP :37020)
    try:
        from src.utils.candados import is_store_server_running
        if not is_store_server_running():
            from src.central_red_global.lan_server import init_lan_server
            init_lan_server()
    except Exception:
        pass

    # Tras reinicio 888 (p. ej. paso a ESCLAVA), cerrar ventana previa si quedó colgada
    prev = getattr(app, "_carteleria_window", None)
    if prev is not None:
        try:
            prev.hide()
            prev.close()
        except Exception:
            pass
        app._carteleria_window = None
        
    window = CarteleriaApp()
    
    # Aplicar el tema global a los módulos administrativos, excluyendo el TV (CarteleriaTV)
    window.apply_theme()

    window.showMaximized()
    # Guardamos referencia para que no sea destruida por el recolector de basura
    app._carteleria_window = window 

    # Siempre poseer el event loop en este perfil (--role carteleria).
    # Antes: si _is_running quedaba True tras exit(888), se devolvía la ventana
    # sin qt_exec y main.py cerraba el proceso al instante.
    try:
        app._is_running = True
        return qt_exec(app)
    finally:
        app._is_running = False

if __name__ == "__main__":
    sys.exit(lanzar_app())


