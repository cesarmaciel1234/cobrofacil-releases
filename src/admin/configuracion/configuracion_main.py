"""Configuración del Sistema — UI premium liviana (W10 bajo recurso)."""

from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QMessageBox, QInputDialog, QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

from src.admin.configuracion.componentes.dialogo_simbolo_moneda import DialogoSimboloMoneda
from src.admin.configuracion.componentes.dialogo_unidades_medida import DialogoUnidadesMedida
from src.admin.configuracion.componentes.dialogo_notificaciones_correo import DialogoNotificacionesCorreo
from src.admin.configuracion.componentes.dialogo_opciones_habilitadas import DialogoOpcionesHabilitadas
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
        self.setObjectName("AdminConfigPage")
        self.setStyleSheet("""
            QWidget#AdminConfigPage {
                background-color: #F8FAFC;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- HEADER ---
        header = QFrame()
        header.setObjectName("AdminConfigHeader")
        header.setFixedHeight(72)
        header.setStyleSheet("""
            QFrame#AdminConfigHeader {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E2E8F0;
            }
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(28, 0, 28, 0)
        h_layout.setSpacing(16)

        btn_volver = QPushButton("← Volver")
        btn_volver.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_volver.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 13px;
                border: none;
                border-radius: 8px;
                padding: 9px 18px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:pressed { background-color: #1E40AF; }
        """)
        btn_volver.clicked.connect(self.request_dashboard.emit)
        h_layout.addWidget(btn_volver)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_title = QLabel("Configuración del Sistema")
        lbl_title.setStyleSheet(
            "font-size: 20px; font-weight: 800; color: #0F172A; "
            "background: transparent; border: none;"
        )
        lbl_sub = QLabel("Ajustes del negocio, dispositivos y mantenimiento")
        lbl_sub.setStyleSheet(
            "font-size: 12px; font-weight: 500; color: #64748B; "
            "background: transparent; border: none;"
        )
        title_col.addWidget(lbl_title)
        title_col.addWidget(lbl_sub)
        h_layout.addLayout(title_col)
        h_layout.addStretch()
        main_layout.addWidget(header)

        # --- SCROLL ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: transparent; width: 10px; margin: 4px 2px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1; border-radius: 4px; min-height: 32px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(28, 22, 28, 32)
        content_layout.setSpacing(0)

        cat_general = ConfigCategory("General", [
            ("🚨", "Alertas de\nEfectivo"),
            ("⚙️", "Opciones\nhabilitadas"),
            ("👥", "Cajeros"),
            ("🔑", "Base de datos\nPC Esclava"),
            ("🧾", "Facturación"),
            ("📝", "Modificar\nFolios"),
            ("💻", "Administrar\nCajas"),
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_general)

        cat_pers = ConfigCategory("Personalización", [
            ("🖼️", "Logotipo del\nPrograma"),
            ("🎫", "Ticket"),
            ("💰", "Impuestos"),
            ("✂️", "Corte"),
            ("💲", "Símbolo de\nMoneda"),
            ("📊", "Unidades de\nMedida"),
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
            ("📧", "Notificaciones\npor Correo"),
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_serv)

        cat_mant = ConfigCategory("Mantenimiento", [
            ("🔄", "Respaldo"),
            ("🔑", "Licencia"),
            ("⚡", "Actualizaciones"),
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_mant)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def ejecutar_accion(self, opcion):
        if opcion == "Alertas de\nEfectivo":
            qt_exec(DialogoAlertasEfectivo(self))
        elif opcion == "Opciones\nhabilitadas":
            qt_exec(DialogoOpcionesHabilitadas(self))
        elif opcion == "Cajeros":
            qt_exec(DialogoPerfiles(self))
        elif opcion == "Administrar\nCajas":
            pwd, ok = QInputDialog.getText(
                self,
                "Licencia Multi-Caja Requerida",
                "El modo de Red Multi-Caja es exclusivo para licencias PRO.\n"
                "Ingrese la clave de activación:",
                QLineEdit.EchoMode.Password,
            )
            if ok and pwd == "209470":
                qt_exec(DialogoAdministrarCajas(self))
            elif ok:
                QMessageBox.warning(
                    self,
                    "Acceso Denegado",
                    "Clave incorrecta. Esta función será desbloqueada al adquirir "
                    "el módulo de Red en próximas actualizaciones.",
                )
        elif opcion in ("Ticket", "Logotipo del\nPrograma"):
            qt_exec(DialogoTicket(self))
        elif opcion == "Lector de\nCódigos":
            qt_exec(DialogoLectorCodigos(self))
        elif opcion == "Dos Tiketeras\n2 Cajas":
            qt_exec(DialogoDosTiketeras(self))
        elif opcion == "Cajón de\nDinero":
            qt_exec(DialogoCajon(self))
        elif opcion == "Símbolo de\nMoneda":
            qt_exec(DialogoSimboloMoneda(self))
        elif opcion == "Unidades de\nMedida":
            qt_exec(DialogoUnidadesMedida(self))
        elif opcion == "Báscula":
            qt_exec(DialogoBalanza(self))
        elif opcion == "Hardware\nIndustrial":
            self.request_screen.emit(13)
        elif opcion == "Base de datos\nPC Esclava":
            qt_exec(DialogoPINLocal(self))
        elif opcion == "Facturación":
            qt_exec(DialogoFacturacion(self))
        elif opcion == "Impuestos":
            qt_exec(DialogoImpuestos(self))
        elif opcion == "Respaldo":
            qt_exec(DialogoRespaldo(self))
        elif opcion == "Terminal\nTPV":
            qt_exec(DialogoTerminalTPV(self))
        elif opcion == "Actualizaciones":
            qt_exec(DialogoActualizaciones(self))
        elif opcion == "Integraciones\nNube":
            qt_exec(DialogoIntegracionesNube(self))
        elif opcion == "Licencia":
            qt_exec(DialogoLicencia(self))
        elif opcion == "Notificaciones\npor Correo":
            qt_exec(DialogoNotificacionesCorreo(self))
        elif opcion == "App\nCobro Fácil":
            QMessageBox.information(
                self,
                "App Cobro Fácil",
                "Búscanos en las redes para tener tu App Móvil de Jefe, donde podrás "
                "ver cada billete que entra en la caja o sale; tenemos alarmas de "
                "apertura de caja sin permiso.",
            )
        else:
            QMessageBox.information(
                self, "En desarrollo", f"La opción '{opcion}' está en desarrollo."
            )

    def _abrir_configuracion_carteleria(self):
        from src.admin.configuracion.componentes.configuracion_pcmaestra import (
            DialogoConfiguracionCarteleria,
        )
        qt_exec(DialogoConfiguracionCarteleria(self))
