"""Pantalla Admin → Cartelería → Configuración. No espera MariaDB."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QFrame, QScrollArea, QComboBox,
    QListWidget, QListWidgetItem,
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QCursor

from src.ui_components.panel_negocio import PanelDatosNegocio
from src.utils.letra import QSS_TITULO, QSS_ROTULO, fuente_nombre
from src.carteleria.configuracion.temas import TEMAS_TV, TEMA_DEFECTO, clave_tema
from src.carteleria.configuracion import estilo
from src.carteleria.configuracion.motor.cargar import leer_local
from src.carteleria.configuracion.motor.guardar import (
    persistir_memoria,
    persistir_local,
    revertir_memoria,
)
from src.carteleria.configuracion.motor.hilo import HiloCargar, HiloGuardar


class CarteleriaConfigPanel(QWidget):
    request_back = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hilo_cargar = None
        self._hilo_guardar = None
        self._listo = False
        self._sucio = False
        self._build()
        self._pintar(leer_local())
        self._escuchar_edicion()
        self._listo = True
        self._pedir_db()

    def _build(self):
        self.setObjectName("CarteleriaConfigPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(estilo.QSS_PANEL)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setStyleSheet(estilo.QSS_HEADER)
        h = QHBoxLayout(header)
        h.setContentsMargins(24, 20, 24, 20)

        btn_back = QPushButton("Volver")
        btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_back.clicked.connect(self.request_back.emit)
        btn_back.setStyleSheet(estilo.QSS_BTN_VOLVER)
        btn_back.setFont(fuente_nombre(11))
        h.addWidget(btn_back)

        title = QLabel("Configuración de Cartelería")
        title.setStyleSheet(QSS_TITULO + estilo.QSS_TITULO_PANTALLA)
        h.addWidget(title)
        h.addStretch()
        root.addWidget(header)

        wrapper = QWidget()
        wrapper.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        wrapper.setStyleSheet(estilo.QSS_FONDO)
        main_layout = QVBoxLayout(wrapper)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        negocio_frame = QFrame()
        negocio_frame.setStyleSheet(estilo.QSS_TARJETA)
        negocio_layout = QVBoxLayout(negocio_frame)
        negocio_layout.setContentsMargins(20, 20, 20, 20)
        lbl_negocio = QLabel("Datos del Negocio")
        lbl_negocio.setStyleSheet(QSS_TITULO + estilo.QSS_SECCION)
        negocio_layout.addWidget(lbl_negocio)
        self.panel_negocio = PanelDatosNegocio(self, show_save_button=False)
        self.panel_negocio.setGraphicsEffect(None)
        self.panel_negocio.setStyleSheet("background: transparent; border: none;")
        negocio_layout.addWidget(self.panel_negocio)
        main_layout.addWidget(negocio_frame)

        carteleria_frame = QFrame()
        carteleria_frame.setStyleSheet(estilo.QSS_TARJETA)
        c_layout = QVBoxLayout(carteleria_frame)
        c_layout.setContentsMargins(20, 20, 20, 20)
        c_layout.setSpacing(16)

        lbl_c_title = QLabel("Mensajes y Estilo")
        lbl_c_title.setStyleSheet(QSS_TITULO + estilo.QSS_SECCION)
        c_layout.addWidget(lbl_c_title)

        lbl_theme = QLabel("Estilo visual de la cartelería (5 temas)")
        lbl_theme.setStyleSheet(QSS_ROTULO + estilo.QSS_ROTULO_CAMPO)
        c_layout.addWidget(lbl_theme)

        self.lst_theme = QListWidget()
        self.lst_theme.setObjectName("ListaTemasTv")
        self.lst_theme.setUniformItemSizes(True)
        fuente = fuente_nombre(11)
        for key, label in TEMAS_TV:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setFont(fuente)
            self.lst_theme.addItem(item)
        self.lst_theme.setMinimumHeight(220)
        self.lst_theme.setStyleSheet(estilo.QSS_LISTA_TEMAS)
        c_layout.addWidget(self.lst_theme)

        lbl_perf = QLabel("Potencia de la PC de la TV")
        lbl_perf.setStyleSheet(QSS_ROTULO + estilo.QSS_ROTULO_CAMPO)
        c_layout.addWidget(lbl_perf)

        self.cmb_perf = QComboBox()
        self.cmb_perf.addItem("Chromium: look premium (PC baja o alta gama)", "auto")
        self.cmb_perf.addItem("Chromium: look premium", "eco")
        self.cmb_perf.addItem("Chromium: look premium", "max")
        self.cmb_perf.setStyleSheet(estilo.QSS_COMBO)
        c_layout.addWidget(self.cmb_perf)

        lbl_mensaje = QLabel("Mensaje principal (zócalo / banner)")
        lbl_mensaje.setStyleSheet(QSS_ROTULO + estilo.QSS_ROTULO_CAMPO)
        c_layout.addWidget(lbl_mensaje)

        self.txt_mensaje = QTextEdit()
        self.txt_mensaje.setMinimumHeight(100)
        self.txt_mensaje.setStyleSheet(estilo.QSS_TEXTO)
        c_layout.addWidget(self.txt_mensaje)
        main_layout.addWidget(carteleria_frame)

        btn_container = QFrame()
        btn_container.setStyleSheet("background: transparent; border: none;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addStretch()
        self.btn_save = QPushButton("Guardar cambios")
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.setFont(fuente_nombre(11))
        self.btn_save.setStyleSheet(estilo.QSS_GUARDAR)
        self.btn_save.clicked.connect(self._save_all)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addStretch()
        main_layout.addWidget(btn_container)
        main_layout.addStretch()

        scroll_local = QScrollArea()
        scroll_local.setStyleSheet(estilo.QSS_SCROLL)
        scroll_local.setWidgetResizable(True)
        scroll_local.setWidget(wrapper)
        root.addWidget(scroll_local)

    def _marcar_sucio(self, *_args):
        if self._listo:
            self._sucio = True

    def _escuchar_edicion(self):
        self.lst_theme.currentRowChanged.connect(self._marcar_sucio)
        self.cmb_perf.currentIndexChanged.connect(self._marcar_sucio)
        self.txt_mensaje.textChanged.connect(self._marcar_sucio)
        for campo in (
            self.panel_negocio.txt_name,
            self.panel_negocio.txt_addr,
            self.panel_negocio.txt_phone,
            self.panel_negocio.txt_cuit,
            self.panel_negocio.txt_msg,
        ):
            campo.textChanged.connect(self._marcar_sucio)

    def _tema_elegido(self):
        item = self.lst_theme.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole) or TEMA_DEFECTO
        return TEMA_DEFECTO

    def _seleccionar_tema(self, th):
        clave = clave_tema(th)
        for i in range(self.lst_theme.count()):
            if self.lst_theme.item(i).data(Qt.ItemDataRole.UserRole) == clave:
                self.lst_theme.setCurrentRow(i)
                return
        self.lst_theme.setCurrentRow(2)

    def _datos_formulario(self) -> dict:
        return {
            "business_name": self.panel_negocio.txt_name.text().strip(),
            "address": self.panel_negocio.txt_addr.text().strip(),
            "phone": self.panel_negocio.txt_phone.text().strip(),
            "cuit": self.panel_negocio.txt_cuit.text().strip(),
            "mensaje_despedida": self.panel_negocio.txt_msg.text().strip(),
            "mensaje_zocalo": self.txt_mensaje.toPlainText().strip(),
            "carteleria_theme": self._tema_elegido(),
            "carteleria_perf": self.cmb_perf.currentData(),
        }

    def _pintar(self, datos: dict | None):
        if not datos:
            return
        self.txt_mensaje.setPlainText(datos.get("mensaje_zocalo") or "")
        self._seleccionar_tema(datos.get("carteleria_theme", TEMA_DEFECTO))
        ip = self.cmb_perf.findData(datos.get("carteleria_perf", "auto"))
        if ip >= 0:
            self.cmb_perf.setCurrentIndex(ip)
        self.panel_negocio.txt_name.setText(datos.get("business_name") or "")
        self.panel_negocio.txt_addr.setText(datos.get("address") or "")
        self.panel_negocio.txt_phone.setText(datos.get("phone") or "")
        self.panel_negocio.txt_cuit.setText(datos.get("cuit") or "")
        self.panel_negocio.txt_msg.setText(datos.get("mensaje_despedida") or "")
        master_ip = str(datos.get("carteleria_master_ip") or "")
        if master_ip and master_ip not in ("127.0.0.1", "localhost", "0.0.0.0"):
            self.btn_save.setText("Guardar cambios globales (red)")

    def _pedir_db(self):
        self._hilo_cargar = HiloCargar(self)
        self._hilo_cargar.listo.connect(self._llego_db)
        self._hilo_cargar.start()

    def _llego_db(self, datos):
        if self._sucio:
            return
        self._listo = False
        self._pintar(datos)
        self._listo = True

    def _save_all(self):
        if self._hilo_guardar and self._hilo_guardar.isRunning():
            return
        datos = self._datos_formulario()
        try:
            persistir_memoria(datos)
            persistir_local(datos)
        except Exception as exc:
            QMessageBox.critical(self, "Error local", str(exc))
            return
        self.btn_save.setEnabled(False)
        self.btn_save.setText("Guardando en red…")
        self._hilo_guardar = HiloGuardar(datos, self)
        self._hilo_guardar.listo.connect(self._despues_guardar)
        self._hilo_guardar.start()

    def _despues_guardar(self, ok: bool, error: str):
        self.btn_save.setEnabled(True)
        if not ok:
            try:
                revertir_memoria()
            except Exception:
                pass
            self.btn_save.setText("Guardar cambios")
            QMessageBox.critical(
                self,
                "Error de red DB",
                f"No se pudo guardar la configuración global.\nDetalle: {error}",
            )
            return
        self.btn_save.setText("Guardado")
        QTimer.singleShot(1800, lambda: self.btn_save.setText("Guardar cambios"))
