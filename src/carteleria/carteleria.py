import sys
import os

# Asegurar que la raíz del proyecto esté en el path para poder importar 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.utils.qt_compat import qt_exec

from PyQt6.QtWidgets import QApplication
from src.carteleria.dashboard.dashboard_main import CarteleriaDashboard
from src.carteleria.motor_carteleria.main_board import CarteleriaMain
from src.carteleria.admin15_carteleria import CarteleriaConfigPanel
from src.carteleria.inventario_ui.inventario_main import Admin1Inventario
from src.carteleria.motor_descuentos_ui.ofertas_main import Admin2Ofertas
from src.carteleria.red_lan.red_lan_main import Admin6RedLan
from PyQt6.QtWidgets import QStackedWidget

class CarteleriaApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cartelería Autónoma - Apple Style Modular")
        self.setMinimumSize(1024, 768)

        self.dashboard = CarteleriaDashboard()
        self.tv_main = CarteleriaMain()
        self.admin = CarteleriaConfigPanel()
        
        # Nuevos módulos autónomos
        self.inv = Admin1Inventario()
        self.ofe = Admin2Ofertas()
        self.red = Admin6RedLan()

        self.addWidget(self.dashboard)
        self.addWidget(self.tv_main)
        self.addWidget(self.admin)
        self.addWidget(self.inv)
        self.addWidget(self.ofe)
        self.addWidget(self.red)

        # Conectar Dashboard
        self.dashboard.request_launch_tv.connect(self.lanzar_tv)
        self.dashboard.request_admin_tv.connect(self.lanzar_admin)
        self.dashboard.request_inventario.connect(self.lanzar_inv)
        self.dashboard.request_ofertas.connect(self.lanzar_ofe)
        self.dashboard.request_red_lan.connect(self.lanzar_red)
        self.dashboard.request_exit.connect(self.close)

        # Conectar Admin (Volver al dashboard)
        self.admin.request_back.connect(self.volver_dashboard)
        self.inv.request_dashboard.connect(self.volver_dashboard)
        self.ofe.request_dashboard.connect(self.volver_dashboard)
        self.red.request_dashboard.connect(self.volver_dashboard)
        
        # Conectar TV (Si tuviera un botón de salir, pero usualmente con Escape o doble clic. Implementaremos uno básico si lo solicita).
        # Por ahora, un atajo para salir de la TV:
        from PyQt6.QtGui import QShortcut, QKeySequence
        self.shortcut = QShortcut(QKeySequence("Esc"), self)
        self.shortcut.activated.connect(self.volver_dashboard)

    def volver_dashboard(self):
        self.setCurrentWidget(self.dashboard)
        self.showNormal()

    def lanzar_tv(self):
        self.setCurrentWidget(self.tv_main)
        self.showFullScreen()

    def lanzar_admin(self):
        self.setCurrentWidget(self.admin)
        self.showNormal()

    def lanzar_inv(self):
        self.setCurrentWidget(self.inv)
        self.showNormal()

    def lanzar_ofe(self):
        self.setCurrentWidget(self.ofe)
        self.showNormal()

    def lanzar_red(self):
        self.setCurrentWidget(self.red)
        self.showNormal()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Iniciar el motor de red centralizado para que este perfil pueda ser maestro/esclavo
    from src.central_red_global.lan_server import init_lan_server
    init_lan_server()
        
    window = CarteleriaApp()
    
    # Aplicar el tema global a los módulos administrativos, excluyendo el TV (CarteleriaTV)
    try:
        from src.config import config
        from src.utils.paths import get_resource_path
        import os
        
        tema_actual = config.get("theme", "light")
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
        
        window.dashboard.setStyleSheet(estilo_completo)
        window.admin.setStyleSheet(estilo_completo)
        window.inv.setStyleSheet(estilo_completo)
        window.ofe.setStyleSheet(estilo_completo)
        window.red.setStyleSheet(estilo_completo)
        
    except Exception as e:
        print("Error aplicando tema global a los paneles de cartelería:", e)

    window.show()
    sys.exit(qt_exec(app))

