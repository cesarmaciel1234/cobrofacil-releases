"""Panel dedicado de red LAN / multicaja."""

from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QMessageBox, QApplication,
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QCursor

from src.config import config
from src.base_de_datos.database import db_manager
from src.navigation.screen_indices import Screen


class Admin6RedLan(QWidget):
    request_dashboard = pyqtSignal()
    request_screen    = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    # ──────────────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN
    # ──────────────────────────────────────────────────────────────────────────
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet("background: #F8FAFC; border-bottom: 1px solid #E2E8F0;")
        h = QHBoxLayout(header)
        h.setContentsMargins(24, 16, 24, 16)

        btn_back = QPushButton("← Dashboard")
        btn_back.setCursor(QCursor(Qt.PointingHandCursor))
        btn_back.setStyleSheet(
            "QPushButton { background: white; border: 1px solid #CBD5E1; "
            "border-radius: 8px; padding: 8px 16px; font-weight: 600; }"
            "QPushButton:hover { background: #F1F5F9; }"
        )
        btn_back.clicked.connect(self.request_dashboard.emit)
        h.addWidget(btn_back)

        title = QLabel("🌐 Servidor LAN / Multicaja")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0F172A; border: none;")
        h.addWidget(title)
        h.addStretch()
        root.addWidget(header)

        # ── Scroll Body ───────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F1F5F9; border: none; }")

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(32, 24, 32, 32)
        lay.setSpacing(20)

        # ── Tarjeta Estado actual ─────────────────────────────────────────────
        self._card_estado = self._build_card_estado()
        lay.addWidget(self._card_estado)

        # ── Tarjeta cambiar modo ──────────────────────────────────────────────
        lay.addWidget(self._build_card_cambiar_modo())

        # ── Botones de acciones secundarias ───────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_cajas = QPushButton("📟 Administrar cajas")
        btn_cajas.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cajas.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: bold; "
            "padding: 12px 20px; border-radius: 8px; border: none; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_cajas.clicked.connect(self._open_administrar_cajas)
        btn_row.addWidget(btn_cajas)

        btn_pin = QPushButton("🔑 Contraseña PC esclava")
        btn_pin.setCursor(QCursor(Qt.PointingHandCursor))
        btn_pin.setStyleSheet(
            "QPushButton { background: #0D9488; color: white; font-weight: bold; "
            "padding: 12px 20px; border-radius: 8px; border: none; }"
            "QPushButton:hover { background: #0F766E; }"
        )
        btn_pin.clicked.connect(self._open_pin_esclava)
        btn_row.addWidget(btn_pin)

        btn_cfg = QPushButton("⚙️ Configuración completa")
        btn_cfg.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cfg.setStyleSheet(
            "QPushButton { background: white; color: #334155; font-weight: 600; "
            "padding: 12px 20px; border-radius: 8px; border: 1px solid #CBD5E1; }"
            "QPushButton:hover { background: #F8FAFC; }"
        )
        btn_cfg.clicked.connect(lambda: self.request_screen.emit(Screen.CONFIGURACION))
        btn_row.addWidget(btn_cfg)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        lay.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)

    # ──────────────────────────────────────────────────────────────────────────
    # TARJETA ESTADO
    # ──────────────────────────────────────────────────────────────────────────
    def _build_card_estado(self) -> QFrame:
        is_master      = getattr(db_manager, "is_master", True)
        caja_id        = config.get("caja_id", 1)
        db_engine      = getattr(db_manager, "db_engine_type", "sqlite")
        db_host        = config.get("db_host", "") or "localhost"
        modo           = "PC MAESTRA (servidor)" if is_master else "PC ESCLAVA (terminal LAN)"
        color_modo     = "#065F46" if is_master else "#1E3A8A"
        bg_modo        = "#D1FAE5" if is_master else "#DBEAFE"

        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: white; border: 1px solid #E2E8F0; border-radius: 12px; }"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)

        # Título del modo
        row_modo = QHBoxLayout()
        lbl_modo_titulo = QLabel("Modo actual:")
        lbl_modo_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #374151; border: none;")

        self.lbl_modo_badge = QLabel(f"  {modo}  ")
        self.lbl_modo_badge.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {color_modo}; "
            f"background: {bg_modo}; border-radius: 8px; padding: 4px 12px; border: none;"
        )
        row_modo.addWidget(lbl_modo_titulo)
        row_modo.addWidget(self.lbl_modo_badge)
        row_modo.addStretch()
        lay.addLayout(row_modo)

        # Detalles técnicos
        for line in (
            f"Motor de datos: {db_engine.upper()}",
            f"Host de red: {db_host}",
            f"ID de caja local: {caja_id}",
            "Descubrimiento UDP: puerto 37020",
        ):
            lbl = QLabel(line)
            lbl.setStyleSheet("font-size: 13px; color: #6B7280; border: none;")
            lay.addWidget(lbl)

        return card

    # ──────────────────────────────────────────────────────────────────────────
    # TARJETA CAMBIAR MODO
    # ──────────────────────────────────────────────────────────────────────────
    def _build_card_cambiar_modo(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: white; border: 2px solid #E2E8F0; border-radius: 14px; }"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.setSpacing(16)

        titulo = QLabel("🔁  Cambiar modo de esta PC")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A; border: none;")
        lay.addWidget(titulo)

        # Fila de los dos modos
        modo_row = QHBoxLayout()
        modo_row.setSpacing(16)

        # ── Bloque MAESTRA ────────────────────────────────────────────────────
        bloque_m = QFrame()
        bloque_m.setStyleSheet(
            "QFrame { background: #F0FDF4; border: 2px solid #86EFAC; border-radius: 12px; }"
        )
        lay_m = QVBoxLayout(bloque_m)
        lay_m.setContentsMargins(18, 16, 18, 16)
        lay_m.setSpacing(8)

        QLabel_m = QLabel("🖥️  PC MAESTRA")
        QLabel_m.setStyleSheet("font-size: 15px; font-weight: bold; color: #166534; border: none;")
        lay_m.addWidget(QLabel_m)

        desc_m = QLabel(
            "Esta PC maneja su propia base de datos\n"
            "local (SQLite). Ideal cuando trabaja\n"
            "de forma autónoma o es el servidor."
        )
        desc_m.setStyleSheet("font-size: 12px; color: #374151; border: none;")
        desc_m.setWordWrap(True)
        lay_m.addWidget(desc_m)

        self.btn_hacer_maestra = QPushButton("✅ Convertir en MAESTRA")
        self.btn_hacer_maestra.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_hacer_maestra.setStyleSheet(
            "QPushButton { background: #16A34A; color: white; font-weight: bold; "
            "padding: 10px 16px; border-radius: 8px; border: none; font-size: 13px; }"
            "QPushButton:hover { background: #15803D; }"
            "QPushButton:disabled { background: #D1FAE5; color: #6EE7B7; }"
        )
        self.btn_hacer_maestra.clicked.connect(self._convertir_maestra)
        lay_m.addWidget(self.btn_hacer_maestra)

        # ── Bloque ESCLAVA ────────────────────────────────────────────────────
        bloque_e = QFrame()
        bloque_e.setStyleSheet(
            "QFrame { background: #EFF6FF; border: 2px solid #93C5FD; border-radius: 12px; }"
        )
        lay_e = QVBoxLayout(bloque_e)
        lay_e.setContentsMargins(18, 16, 18, 16)
        lay_e.setSpacing(8)

        QLabel_e = QLabel("📡  PC ESCLAVA  (terminal LAN)")
        QLabel_e.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E3A8A; border: none;")
        lay_e.addWidget(QLabel_e)

        desc_e = QLabel(
            "Esta PC se conecta a la base de datos\n"
            "de otra PC (la Maestra) por la red.\n"
            "Ingresá la IP de la Maestra:"
        )
        desc_e.setStyleSheet("font-size: 12px; color: #374151; border: none;")
        desc_e.setWordWrap(True)
        lay_e.addWidget(desc_e)

        self.txt_ip_maestra = QLineEdit()
        self.txt_ip_maestra.setPlaceholderText("IP de la Maestra  (ej: 192.168.0.100)")
        self.txt_ip_maestra.setStyleSheet(
            "border: 1.5px solid #93C5FD; border-radius: 8px; padding: 8px 12px; "
            "font-size: 13px; background: white;"
        )
        # Precargar la IP guardada si ya era esclava
        ip_guardada = config.get("db_host", "")
        if ip_guardada and ip_guardada not in ("localhost", "127.0.0.1", ""):
            self.txt_ip_maestra.setText(ip_guardada)
        self.txt_ip_maestra.returnPressed.connect(self._convertir_esclava)
        lay_e.addWidget(self.txt_ip_maestra)

        self.btn_hacer_esclava = QPushButton("🔗 Convertir en ESCLAVA")
        self.btn_hacer_esclava.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_hacer_esclava.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: bold; "
            "padding: 10px 16px; border-radius: 8px; border: none; font-size: 13px; }"
            "QPushButton:hover { background: #1D4ED8; }"
            "QPushButton:disabled { background: #DBEAFE; color: #93C5FD; }"
        )
        self.btn_hacer_esclava.clicked.connect(self._convertir_esclava)
        lay_e.addWidget(self.btn_hacer_esclava)

        modo_row.addWidget(bloque_m, 1)
        modo_row.addWidget(bloque_e, 1)
        lay.addLayout(modo_row)

        # Advertencia
        aviso = QLabel(
            "⚠️  Al cambiar de modo se recarga la conexión a la base de datos. "
            "Guardá cualquier operación pendiente antes de cambiar."
        )
        aviso.setWordWrap(True)
        aviso.setStyleSheet(
            "font-size: 12px; color: #92400E; background: #FFFBEB; "
            "border: 1px solid #FCD34D; border-radius: 8px; padding: 10px;"
        )
        lay.addWidget(aviso)

        # Actualizar estado inicial de botones
        self._actualizar_botones()
        return card

    # ──────────────────────────────────────────────────────────────────────────
    # ACCIONES
    # ──────────────────────────────────────────────────────────────────────────
    def _actualizar_botones(self):
        """Deshabilita el botón del modo ya activo."""
        is_master = getattr(db_manager, "is_master", True)
        self.btn_hacer_maestra.setEnabled(not is_master)
        self.btn_hacer_esclava.setEnabled(is_master)
        if not is_master:
            self.btn_hacer_maestra.setText("✅ MAESTRA  (activo)")
        else:
            self.btn_hacer_maestra.setText("✅ Convertir en MAESTRA")
        if is_master:
            self.btn_hacer_esclava.setText("🔗 ESCLAVA  (inactivo)")
        else:
            self.btn_hacer_esclava.setText("🔗 Convertir en ESCLAVA")

    def _convertir_maestra(self):
        """Pasa esta PC a modo MAESTRA (BD local SQLite)."""
        resp = QMessageBox.question(
            self, "Cambiar a MAESTRA",
            "¿Convertir esta PC en MAESTRA?\n\n"
            "Se usará la base de datos LOCAL (SQLite).\n"
            "Si había ventas sin sincronizar con la Maestra anterior, pueden perderse.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        try:
            # Borrar IP de esclava en config
            config.set("db_host", "")
            db_manager.reconectar_local()
            self._refrescar_estado()
            QMessageBox.information(
                self, "✅ Modo MAESTRA activado",
                "Esta PC ahora funciona como MAESTRA con su base de datos local.\n"
                "Reiniciá la aplicación si notas algún problema."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cambiar a MAESTRA:\n{e}")

    def _convertir_esclava(self):
        """Pasa esta PC a modo ESCLAVA conectándose a la IP indicada."""
        ip = self.txt_ip_maestra.text().strip()
        if not ip:
            QMessageBox.warning(self, "Falta la IP", "Ingresá la IP de la PC Maestra.")
            self.txt_ip_maestra.setFocus()
            return

        resp = QMessageBox.question(
            self, "Cambiar a ESCLAVA",
            f"¿Conectar esta PC como ESCLAVA a la Maestra en:\n\n"
            f"  🖥️  {ip}\n\n"
            "Esta PC usará la base de datos de esa máquina por la red.\n"
            "Asegurate de que la Maestra esté encendida y en la misma red.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        # Mostrar spinner visual
        self.btn_hacer_esclava.setEnabled(False)
        self.btn_hacer_esclava.setText("⏳ Conectando...")
        QApplication.processEvents()

        try:
            config.set("db_host", ip)
            db_manager.reconectar_mariadb(ip)
            self._refrescar_estado()
            QMessageBox.information(
                self, "✅ Modo ESCLAVA activado",
                f"Esta PC ahora funciona como ESCLAVA conectada a:\n  {ip}\n\n"
                "Si la conexión falla, verificá que la Maestra esté activa\n"
                "y que el firewall permita el puerto 3306."
            )
        except Exception as e:
            # Revertir si falla
            config.set("db_host", "")
            QMessageBox.critical(
                self, "Error de conexión",
                f"No se pudo conectar como ESCLAVA a {ip}:\n\n{e}\n\n"
                "Verificá que la IP sea correcta y la Maestra esté encendida."
            )
        finally:
            self._actualizar_botones()

    def _refrescar_estado(self):
        """Actualiza el badge de modo y los botones."""
        is_master  = getattr(db_manager, "is_master", True)
        modo       = "PC MAESTRA (servidor)" if is_master else "PC ESCLAVA (terminal LAN)"
        color_modo = "#065F46" if is_master else "#1E3A8A"
        bg_modo    = "#D1FAE5" if is_master else "#DBEAFE"
        self.lbl_modo_badge.setText(f"  {modo}  ")
        self.lbl_modo_badge.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {color_modo}; "
            f"background: {bg_modo}; border-radius: 8px; padding: 4px 12px; border: none;"
        )
        self._actualizar_botones()

    # ──────────────────────────────────────────────────────────────────────────
    # DIÁLOGOS SECUNDARIOS
    # ──────────────────────────────────────────────────────────────────────────
    def _open_administrar_cajas(self):
        from src.admin.admin5_configuracion import DialogoAdministrarCajas
        qt_exec(DialogoAdministrarCajas(self))

    def _open_pin_esclava(self):
        from src.admin.admin5_configuracion import DialogoPINLocal
        qt_exec(DialogoPINLocal(self))