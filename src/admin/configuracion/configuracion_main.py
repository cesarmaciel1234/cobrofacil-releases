"""Configuración del Sistema — hub por módulos (carga liviana)."""

from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QMessageBox, QInputDialog, QLineEdit,
    QStackedWidget, QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

from src.admin.configuracion.componentes.config_category import ConfigCategory
from src.motor_descuentos.compartido import TarjetaModulo


_CATEGORIAS = (
    ("general", "⚙️", "General", "Alertas, cajas, cajeros y facturación.", [
        ("🚨", "Alertas de\nEfectivo"),
        ("⚙️", "Opciones\nhabilitadas"),
        ("👥", "Cajeros"),
        ("🔑", "Base de datos\nPC Esclava"),
        ("🧾", "Facturación"),
        ("📝", "Modificar\nFolios"),
        ("💻", "Administrar\nCajas"),
    ]),
    ("pers", "🎨", "Personalización", "Ticket, impuestos, moneda y unidades.", [
        ("🖼️", "Logotipo del\nPrograma"),
        ("🎫", "Ticket"),
        ("💰", "Impuestos"),
        ("✂️", "Corte"),
        ("💲", "Símbolo de\nMoneda"),
        ("📊", "Unidades de\nMedida"),
    ]),
    ("disp", "🔌", "Dispositivos", "Tiketeras, lector, cajón, báscula y TPV.", [
        ("🖨️🖨️", "Dos Tiketeras\n2 Cajas"),
        ("🔫", "Lector de\nCódigos"),
        ("💵", "Cajón de\nDinero"),
        ("⚖️", "Báscula"),
        ("📠", "Terminal\nTPV"),
        ("🔌", "Hardware\nIndustrial"),
    ]),
    ("serv", "🌐", "Servicios", "Nube, correo y app del jefe.", [
        ("📱", "App\nCobro Fácil"),
        ("🌐", "Integraciones\nNube"),
        ("📧", "Notificaciones\npor Correo"),
    ]),
    ("mant", "🛠️", "Mantenimiento", "Respaldo, licencia y actualizaciones.", [
        ("🔄", "Respaldo"),
        ("🔑", "Licencia"),
        ("⚡", "Actualizaciones"),
    ]),
)


class Admin5Configuracion(QWidget):
    request_dashboard = pyqtSignal()
    request_screen = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._paginas = {}
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
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        self.stack.addWidget(self._armar_hub())

    def _barra(self, titulo, sub, on_back, texto_back="← Módulos"):
        header = QFrame()
        header.setFixedHeight(72)
        header.setStyleSheet("QFrame { background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0; }")
        h = QHBoxLayout(header)
        h.setContentsMargins(28, 0, 28, 0)
        btn = QPushButton(texto_back)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet(
            "QPushButton { background-color: #2563EB; color: #FFFFFF; font-weight: 700;"
            " font-size: 13px; border: none; border-radius: 8px; padding: 9px 18px; }"
            "QPushButton:hover { background-color: #1D4ED8; }"
        )
        btn.clicked.connect(on_back)
        h.addWidget(btn)
        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel(titulo)
        t.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A; background: transparent; border: none;")
        s = QLabel(sub)
        s.setStyleSheet("font-size: 12px; font-weight: 500; color: #64748B; background: transparent; border: none;")
        col.addWidget(t)
        col.addWidget(s)
        h.addSpacing(16)
        h.addLayout(col)
        h.addStretch()
        return header

    def _armar_hub(self):
        page = QWidget()
        page.setStyleSheet("background: #F8FAFC;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._barra(
            "Configuración del sistema",
            "Elegí un módulo. Los diálogos se abren al hacer clic.",
            self.request_dashboard.emit,
            "← Panel admin",
        ))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        wrap = QWidget()
        wrap.setStyleSheet("background: #F8FAFC;")
        grid = QGridLayout(wrap)
        grid.setContentsMargins(28, 28, 28, 28)
        grid.setSpacing(16)
        for i, (codigo, ico, titulo, sub, _items) in enumerate(_CATEGORIAS):
            card = TarjetaModulo(codigo, ico, titulo, sub)
            card.clicked.connect(lambda c=codigo: self._abrir(c))
            grid.addWidget(card, i // 3, i % 3)
        grid.setRowStretch(2, 1)
        scroll.setWidget(wrap)
        lay.addWidget(scroll, 1)
        return page

    def _ir_hub(self):
        self.stack.setCurrentIndex(0)

    def _abrir(self, codigo):
        if codigo not in self._paginas:
            self._paginas[codigo] = self._pagina_categoria(codigo)
            self.stack.addWidget(self._paginas[codigo])
        self.stack.setCurrentWidget(self._paginas[codigo])

    def _pagina_categoria(self, codigo):
        meta = next(c for c in _CATEGORIAS if c[0] == codigo)
        _cod, _ico, titulo, sub, items = meta
        page = QWidget()
        page.setStyleSheet("background: #F8FAFC;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._barra(titulo, sub, self._ir_hub))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner.setStyleSheet("background: #F8FAFC;")
        il = QVBoxLayout(inner)
        il.setContentsMargins(28, 22, 28, 32)
        il.addWidget(ConfigCategory(titulo, items, callback=self.ejecutar_accion))
        il.addStretch()
        scroll.setWidget(inner)
        lay.addWidget(scroll, 1)
        return page

    def _dialogo(self, modulo, clase):
        mod = __import__(modulo, fromlist=[clase])
        qt_exec(getattr(mod, clase)(self))

    def ejecutar_accion(self, opcion):
        mapa = {
            "Alertas de\nEfectivo": ("src.admin.configuracion.componentes.dialogo_alertas_efectivo", "DialogoAlertasEfectivo"),
            "Opciones\nhabilitadas": ("src.admin.configuracion.componentes.dialogo_opciones_habilitadas", "DialogoOpcionesHabilitadas"),
            "Cajeros": ("src.ui_global.perfil_empleados_ui.dialogo_perfiles", "DialogoPerfiles"),
            "Ticket": ("src.admin.configuracion.componentes.dialogo_ticket", "DialogoTicket"),
            "Logotipo del\nPrograma": ("src.admin.configuracion.componentes.dialogo_ticket", "DialogoTicket"),
            "Lector de\nCódigos": ("src.admin.configuracion.componentes.dialogo_lector_codigos", "DialogoLectorCodigos"),
            "Dos Tiketeras\n2 Cajas": ("src.admin.configuracion.componentes.dialogo_dos_tiketeras", "DialogoDosTiketeras"),
            "Cajón de\nDinero": ("src.admin.configuracion.componentes.dialogo_cajon", "DialogoCajon"),
            "Símbolo de\nMoneda": ("src.admin.configuracion.componentes.dialogo_simbolo_moneda", "DialogoSimboloMoneda"),
            "Unidades de\nMedida": ("src.admin.configuracion.componentes.dialogo_unidades_medida", "DialogoUnidadesMedida"),
            "Báscula": ("src.admin.configuracion.componentes.dialogo_balanza", "DialogoBalanza"),
            "Base de datos\nPC Esclava": ("src.admin.configuracion.componentes.dialogo_pin_local", "DialogoPINLocal"),
            "Facturación": ("src.admin.configuracion.componentes.dialogo_facturacion", "DialogoFacturacion"),
            "Impuestos": ("src.admin.configuracion.componentes.dialogo_impuestos", "DialogoImpuestos"),
            "Respaldo": ("src.admin.configuracion.componentes.dialogo_respaldo", "DialogoRespaldo"),
            "Terminal\nTPV": ("src.admin.configuracion.componentes.dialogo_terminal_tpv", "DialogoTerminalTPV"),
            "Actualizaciones": ("src.admin.configuracion.componentes.dialogo_actualizaciones", "DialogoActualizaciones"),
            "Integraciones\nNube": ("src.admin.configuracion.componentes.dialogo_integraciones_nube", "DialogoIntegracionesNube"),
            "Licencia": ("src.admin.configuracion.componentes.dialogo_licencia", "DialogoLicencia"),
            "Notificaciones\npor Correo": ("src.admin.configuracion.componentes.dialogo_notificaciones_correo", "DialogoNotificacionesCorreo"),
        }
        if opcion == "Hardware\nIndustrial":
            self.request_screen.emit(13)
            return
        if opcion == "Administrar\nCajas":
            pwd, ok = QInputDialog.getText(
                self,
                "Licencia Multi-Caja Requerida",
                "El modo de Red Multi-Caja es exclusivo para licencias PRO.\n"
                "Ingrese la clave de activación:",
                QLineEdit.EchoMode.Password,
            )
            if ok and pwd == "209470":
                self._dialogo(
                    "src.admin.configuracion.componentes.dialogo_administrar_cajas",
                    "DialogoAdministrarCajas",
                )
            elif ok:
                QMessageBox.warning(
                    self,
                    "Acceso Denegado",
                    "Clave incorrecta. Esta función será desbloqueada al adquirir "
                    "el módulo de Red en próximas actualizaciones.",
                )
            return
        if opcion == "App\nCobro Fácil":
            QMessageBox.information(
                self,
                "App Cobro Fácil",
                "Búscanos en las redes para tener tu App Móvil de Jefe, donde podrás "
                "ver cada billete que entra en la caja o sale; tenemos alarmas de "
                "apertura de caja sin permiso.",
            )
            return
        par = mapa.get(opcion)
        if par:
            self._dialogo(*par)
            return
        QMessageBox.information(self, "En desarrollo", f"La opción '{opcion}' está en desarrollo.")

    def _abrir_configuracion_carteleria(self):
        self._dialogo(
            "src.admin.configuracion.componentes.configuracion_pcmaestra",
            "DialogoConfiguracionCarteleria",
        )
