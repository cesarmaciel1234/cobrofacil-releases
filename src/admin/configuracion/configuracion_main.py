from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton, QGridLayout, QSizePolicy,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QMessageBox, QInputDialog, QCheckBox,
    QFileDialog, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QCursor, QFont, QColor
import os, shutil, datetime, glob
from src.config import config
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager


from src.admin.configuracion.componentes.dialogo_simbolo_moneda import DialogoSimboloMoneda
from src.admin.configuracion.componentes.dialogo_unidades_medida import DialogoUnidadesMedida
from src.admin.configuracion.componentes.dialogo_notificaciones_correo import DialogoNotificacionesCorreo
from src.admin.configuracion.componentes.dialogo_opciones_habilitadas import DialogoOpcionesHabilitadas
from src.admin.configuracion.componentes.config_button import ConfigButton
from src.ui_global.perfil_empleados_ui.dialogo_perfiles import DialogoPerfiles
from src.admin.configuracion.componentes.dialogo_ticket import DialogoTicket
from src.admin.configuracion.componentes.dialogo_lector_codigos import DialogoLectorCodigos
from src.admin.configuracion.componentes.config_category import ConfigCategory
from src.admin.configuracion.componentes.dialogo_cajon import DialogoCajon
from src.admin.configuracion.componentes.dialogo_dos_tiketeras import DialogoDosTiketeras
from src.admin.configuracion.componentes.dialogo_administrar_cajas import DialogoAdministrarCajas
from src.admin.configuracion.componentes.dialogo_alertas_efectivo import DialogoAlertasEfectivo
from src.admin.configuracion.componentes.dialogo_balanza import DialogoBalanza
from src.admin.configuracion.componentes.dialogo_facturacion import DialogoFacturacion
from src.admin.configuracion.componentes.dialogo_impuestos import DialogoImpuestos
from src.admin.configuracion.componentes.dialogo_licencia import DialogoLicencia
from src.admin.configuracion.componentes.dialogo_respaldo import DialogoRespaldo
from src.admin.configuracion.componentes.migration_worker import MigrationWorker
from src.admin.configuracion.componentes.dialogo_migracion_eleventa import DialogoMigracionEleventa
from src.admin.configuracion.componentes.dialogo_actualizaciones import DialogoActualizaciones
from src.admin.configuracion.componentes.dialogo_terminal_tpv import DialogoTerminalTPV
from src.admin.configuracion.componentes.dialogo_integraciones_nube import DialogoIntegracionesNube
from src.admin.configuracion.componentes.dialogo_pin_local import DialogoPINLocal

class Admin5Configuracion(QWidget):
    request_dashboard = pyqtSignal()
    request_screen = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- HEADER ---
        header = QFrame()
        header.setStyleSheet(" border-bottom: 1px solid #E2E8F0;")
        header.setFixedHeight(70)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(30, 0, 30, 0)
        
        btn_volver = QPushButton("🔙 Volver")
        btn_volver.setStyleSheet("""
            QPushButton {
                 background-color: #3B82F6; color: white; font-weight: bold; font-size: 14px;
                border-radius: 6px; padding: 8px 20px;
            }
            QPushButton:hover {  }
        """)
        btn_volver.setCursor(QCursor(Qt.PointingHandCursor))
        btn_volver.clicked.connect(self.request_dashboard.emit)
        h_layout.addWidget(btn_volver)
        
        h_layout.addSpacing(20)
        
        lbl_title = QLabel("Configuración del Sistema")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; ")
        h_layout.addWidget(lbl_title)
        
        h_layout.addStretch()
        main_layout.addWidget(header)
        
        # --- SCROLL AREA ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 20, 40, 40)
        content_layout.setSpacing(10)
        
        # --- CATEGORÍAS ---
        cat_general = ConfigCategory("General", [
            ("🚨", "Alertas de\nEfectivo"),
            ("⚙️", "Opciones\nhabilitadas"),
            ("👥", "Cajeros"),
            ("🔑", "Base de datos\nPC Esclava"),
            ("🧾", "Facturación"),
            ("📝", "Modificar\nFolios"),
            ("💻", "Administrar\nCajas")
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_general)
        
        cat_pers = ConfigCategory("Personalización", [
            ("🖼️", "Logotipo del\nPrograma"),
            ("🎫", "Ticket"),
            ("💰", "Impuestos"),
            ("✂️", "Corte"),
            ("💲", "Símbolo de\nMoneda"),
            ("📊", "Unidades de\nMedida")
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_pers)
        
        cat_disp = ConfigCategory("Dispositivos", [
            ("🖨️🖨️", "Dos Tiketeras\n2 Cajas"),
            ("🔫", "Lector de\nCódigos"),
            ("💵", "Cajón de\nDinero"),
            ("⚖️", "Báscula"),
            ("📠", "Terminal\nTPV"),
            ("🔌", "Hardware\nIndustrial"),
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_disp)
        
        cat_serv = ConfigCategory("Servicios", [
            ("📱", "App\nCobro Fácil"),
            ("🌐", "Integraciones\nNube"),
            ("📧", "Notificaciones\npor Correo")
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_serv)
        
        cat_mant = ConfigCategory("Mantenimiento", [
            ("🔄", "Respaldo"),
            ("🔑", "Licencia"),
            ("⚡", "Actualizaciones")
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_mant)


        content_layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def ejecutar_accion(self, opcion):
        if opcion == "Alertas de\nEfectivo":
            dlg = DialogoAlertasEfectivo(self)
            qt_exec(dlg)
        elif opcion == "Opciones\nhabilitadas":
            dlg = DialogoOpcionesHabilitadas(self)
            qt_exec(dlg)
        elif opcion == "Cajeros":
            dlg = DialogoPerfiles(self)
            qt_exec(dlg)
        elif opcion == "Administrar\nCajas":
            # Bloqueo Premium de Red (Fase de Pruebas / Versión Paga)
            pwd, ok = QInputDialog.getText(self, "Licencia Multi-Caja Requerida", 
                                           "El modo de Red Multi-Caja es exclusivo para licencias PRO.\nIngrese la clave de activación:", 
                                           QLineEdit.Password)
            if ok and pwd == "209470":
                dlg = DialogoAdministrarCajas(self)
                qt_exec(dlg)
            elif ok:
                QMessageBox.warning(self, "Acceso Denegado", 
                                    "Clave incorrecta. Esta función será desbloqueada al adquirir el módulo de Red en próximas actualizaciones.")
        elif opcion == "Ticket":
            dlg = DialogoTicket(self)
            qt_exec(dlg)
        elif opcion == "Logotipo del\nPrograma":
            dlg = DialogoTicket(self)
            qt_exec(dlg)
        elif opcion == "Lector de\nCódigos":
            dlg = DialogoLectorCodigos(self)
            qt_exec(dlg)
        elif opcion == "Dos Tiketeras\n2 Cajas":
            dlg = DialogoDosTiketeras(self)
            qt_exec(dlg)
        elif opcion == "Cajón de\nDinero":
            dlg = DialogoCajon(self)
            qt_exec(dlg)
        elif opcion == "Símbolo de\nMoneda":
            dlg = DialogoSimboloMoneda(self)
            qt_exec(dlg)
        elif opcion == "Unidades de\nMedida":
            dlg = DialogoUnidadesMedida(self)
            qt_exec(dlg)
        elif opcion == "Báscula":
            dlg = DialogoBalanza(self)
            qt_exec(dlg)
        elif opcion == "Hardware\nIndustrial":
            self.request_screen.emit(13)
        elif opcion == "Base de datos\nPC Esclava":
            dlg = DialogoPINLocal(self)
            qt_exec(dlg)
        elif opcion == "Facturación":
            dlg = DialogoFacturacion(self)
            qt_exec(dlg)
        elif opcion == "Impuestos":
            dlg = DialogoImpuestos(self)
            qt_exec(dlg)
        elif opcion == "Respaldo":
            dlg = DialogoRespaldo(self)
            qt_exec(dlg)
        elif opcion == "Terminal\nTPV":
            dlg = DialogoTerminalTPV(self)
            qt_exec(dlg)
        elif opcion == "Actualizaciones":
            dlg = DialogoActualizaciones(self)
            qt_exec(dlg)
        elif opcion == "Integraciones\nNube":
            dlg = DialogoIntegracionesNube(self)
            qt_exec(dlg)

        elif opcion == "Licencia":
            dlg = DialogoLicencia(self)
            qt_exec(dlg)
        elif opcion == "Notificaciones\npor Correo":
            dlg = DialogoNotificacionesCorreo(self)
            qt_exec(dlg)
from src.admin.configuracion.componentes.dialogo_administrar_cajas import DialogoAdministrarCajas
from src.admin.configuracion.componentes.dialogo_alertas_efectivo import DialogoAlertasEfectivo
from src.admin.configuracion.componentes.dialogo_balanza import DialogoBalanza
from src.admin.configuracion.componentes.dialogo_facturacion import DialogoFacturacion
from src.admin.configuracion.componentes.dialogo_impuestos import DialogoImpuestos
from src.admin.configuracion.componentes.dialogo_licencia import DialogoLicencia
from src.admin.configuracion.componentes.dialogo_respaldo import DialogoRespaldo
from src.admin.configuracion.componentes.migration_worker import MigrationWorker
from src.admin.configuracion.componentes.dialogo_migracion_eleventa import DialogoMigracionEleventa
from src.admin.configuracion.componentes.dialogo_actualizaciones import DialogoActualizaciones
from src.admin.configuracion.componentes.dialogo_terminal_tpv import DialogoTerminalTPV
from src.admin.configuracion.componentes.dialogo_integraciones_nube import DialogoIntegracionesNube
from src.admin.configuracion.componentes.dialogo_pin_local import DialogoPINLocal

class Admin5Configuracion(QWidget):
    request_dashboard = pyqtSignal()
    request_screen = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- HEADER ---
        header = QFrame()
        header.setStyleSheet(" border-bottom: 1px solid #E2E8F0;")
        header.setFixedHeight(70)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(30, 0, 30, 0)
        
        btn_volver = QPushButton("🔙 Volver")
        btn_volver.setStyleSheet("""
            QPushButton {
                 background-color: #3B82F6; color: white; font-weight: bold; font-size: 14px;
                border-radius: 6px; padding: 8px 20px;
            }
            QPushButton:hover {  }
        """)
        btn_volver.setCursor(QCursor(Qt.PointingHandCursor))
        btn_volver.clicked.connect(self.request_dashboard.emit)
        h_layout.addWidget(btn_volver)
        
        h_layout.addSpacing(20)
        
        lbl_title = QLabel("Configuración del Sistema")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; ")
        h_layout.addWidget(lbl_title)
        
        h_layout.addStretch()
        main_layout.addWidget(header)
        
        # --- SCROLL AREA ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 20, 40, 40)
        content_layout.setSpacing(10)
        
        # --- CATEGORÍAS ---
        cat_general = ConfigCategory("General", [
            ("🚨", "Alertas de\nEfectivo"),
            ("⚙️", "Opciones\nhabilitadas"),
            ("👥", "Cajeros"),
            ("🔑", "Base de datos\nPC Esclava"),
            ("🧾", "Facturación"),
            ("📝", "Modificar\nFolios"),
            ("💻", "Administrar\nCajas")
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_general)
        
        cat_pers = ConfigCategory("Personalización", [
            ("🖼️", "Logotipo del\nPrograma"),
            ("🎫", "Ticket"),
            ("💰", "Impuestos"),
            ("✂️", "Corte"),
            ("💲", "Símbolo de\nMoneda"),
            ("📊", "Unidades de\nMedida")
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_pers)
        
        cat_disp = ConfigCategory("Dispositivos", [
            ("🖨️🖨️", "Dos Tiketeras\n2 Cajas"),
            ("🔫", "Lector de\nCódigos"),
            ("💵", "Cajón de\nDinero"),
            ("⚖️", "Báscula"),
            ("📠", "Terminal\nTPV"),
            ("🔌", "Hardware\nIndustrial"),
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_disp)
        
        cat_serv = ConfigCategory("Servicios", [
            ("📱", "App\nCobro Fácil"),
            ("🌐", "Integraciones\nNube"),
            ("📧", "Notificaciones\npor Correo")
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_serv)
        
        cat_mant = ConfigCategory("Mantenimiento", [
            ("🔄", "Respaldo"),
            ("🔑", "Licencia"),
            ("⚡", "Actualizaciones")
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_mant)


        content_layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def ejecutar_accion(self, opcion):
        if opcion == "Alertas de\nEfectivo":
            dlg = DialogoAlertasEfectivo(self)
            qt_exec(dlg)
        elif opcion == "Opciones\nhabilitadas":
            dlg = DialogoOpcionesHabilitadas(self)
            qt_exec(dlg)
        elif opcion == "Cajeros":
            dlg = DialogoPerfiles(self)
            qt_exec(dlg)
        elif opcion == "Administrar\nCajas":
            # Bloqueo Premium de Red (Fase de Pruebas / Versión Paga)
            pwd, ok = QInputDialog.getText(self, "Licencia Multi-Caja Requerida", 
                                           "El modo de Red Multi-Caja es exclusivo para licencias PRO.\nIngrese la clave de activación:", 
                                           QLineEdit.Password)
            if ok and pwd == "209470":
                dlg = DialogoAdministrarCajas(self)
                qt_exec(dlg)
            elif ok:
                QMessageBox.warning(self, "Acceso Denegado", 
                                    "Clave incorrecta. Esta función será desbloqueada al adquirir el módulo de Red en próximas actualizaciones.")
        elif opcion == "Ticket":
            dlg = DialogoTicket(self)
            qt_exec(dlg)
        elif opcion == "Logotipo del\nPrograma":
            dlg = DialogoTicket(self)
            qt_exec(dlg)
        elif opcion == "Lector de\nCódigos":
            dlg = DialogoLectorCodigos(self)
            qt_exec(dlg)
        elif opcion == "Dos Tiketeras\n2 Cajas":
            dlg = DialogoDosTiketeras(self)
            qt_exec(dlg)
        elif opcion == "Cajón de\nDinero":
            dlg = DialogoCajon(self)
            qt_exec(dlg)
        elif opcion == "Símbolo de\nMoneda":
            dlg = DialogoSimboloMoneda(self)
            qt_exec(dlg)
        elif opcion == "Unidades de\nMedida":
            dlg = DialogoUnidadesMedida(self)
            qt_exec(dlg)
        elif opcion == "Báscula":
            dlg = DialogoBalanza(self)
            qt_exec(dlg)
        elif opcion == "Hardware\nIndustrial":
            self.request_screen.emit(13)
        elif opcion == "Base de datos\nPC Esclava":
            dlg = DialogoPINLocal(self)
            qt_exec(dlg)
        elif opcion == "Facturación":
            dlg = DialogoFacturacion(self)
            qt_exec(dlg)
        elif opcion == "Impuestos":
            dlg = DialogoImpuestos(self)
            qt_exec(dlg)
        elif opcion == "Respaldo":
            dlg = DialogoRespaldo(self)
            qt_exec(dlg)
        elif opcion == "Terminal\nTPV":
            dlg = DialogoTerminalTPV(self)
            qt_exec(dlg)
        elif opcion == "Actualizaciones":
            dlg = DialogoActualizaciones(self)
            qt_exec(dlg)
        elif opcion == "Integraciones\nNube":
            dlg = DialogoIntegracionesNube(self)
            qt_exec(dlg)

        elif opcion == "Licencia":
            dlg = DialogoLicencia(self)
            qt_exec(dlg)
        elif opcion == "Notificaciones\npor Correo":
            dlg = DialogoNotificacionesCorreo(self)
            qt_exec(dlg)
        elif opcion == "App\nCobro Fácil":
            QMessageBox.information(self, "📱 App Cobro Fácil", "Búscanos en las redes para tener tu App Móvil de Jefe, donde podrás ver cada billete que entra en la caja o sale por que tenemos alarmas de apertura de caja sin permiso.")
        else:
            QMessageBox.information(self, "En desarrollo", f"La opción '{opcion}' está en desarrollo.")

    def _abrir_configuracion_carteleria(self):
        from src.admin.configuracion.componentes.configuracion_pcmaestra import DialogoConfiguracionCarteleria
        dlg = DialogoConfiguracionCarteleria(self)
        qt_exec(dlg)
