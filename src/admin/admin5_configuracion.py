from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt5.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton, QGridLayout, QSizePolicy,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QMessageBox, QInputDialog, QCheckBox,
    QFileDialog, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QCursor, QFont, QColor
import os, shutil, datetime, glob
from src.config import config
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

class DialogoSimboloMoneda(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Símbolo de Moneda")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel("💲 Símbolo de Moneda")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; ")
        lay.addWidget(lbl_title)
        
        lay.addWidget(QLabel("Selecciona o escribe el símbolo de moneda para el sistema:", styleSheet=" margin-bottom: 10px;"))
        
        self.cmb_moneda = QComboBox()
        self.cmb_moneda.setEditable(True)
        self.cmb_moneda.setStyleSheet("padding: 8px; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 14px;")
        self.cmb_moneda.addItems(["$", "€", "S/", "Q", "L", "Bs", "R$", "¥", "£"])
        
        curr = config.get("currency_symbol", "$")
        self.cmb_moneda.setCurrentText(curr)
        lay.addWidget(self.cmb_moneda)
        
        lay.addStretch()
        
        btn_save = QPushButton("💾 Guardar")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_save.clicked.connect(self.guardar)
        lay.addWidget(btn_save)
        
    def guardar(self):
        val = self.cmb_moneda.currentText().strip()
        if not val: val = "$"
        config.set('currency_symbol', val)
        QMessageBox.information(self, "Guardado", f"El símbolo de moneda ha sido actualizado a: {val}")
        self.accept()

class DialogoUnidadesMedida(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Unidades de Medida")
        self.setFixedSize(450, 400)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel("📊 Unidades de Medida")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; ")
        lay.addWidget(lbl_title)
        
        lay.addWidget(QLabel("Configura las unidades para tus productos (Ej: Unidad, Kg, Litro):", styleSheet=" margin-bottom: 10px;"))
        
        self.txt_unidades = QTextEdit()
        self.txt_unidades.setStyleSheet("border: 1px solid #CBD5E1; border-radius: 6px; padding: 5px;")
        
        unidades = config.get("unidades_medida", "Unidad, Kg, Litro, Metro, Granel")
        self.txt_unidades.setText(unidades)
        lay.addWidget(self.txt_unidades)
        
        lbl_info = QLabel("⚠️ Escribe las unidades separadas por coma (,)")
        lbl_info.setStyleSheet(" font-size: 12px; font-weight: bold;")
        lay.addWidget(lbl_info)
        
        lay.addStretch()
        
        btn_save = QPushButton("💾 Guardar")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_save.clicked.connect(self.guardar)
        lay.addWidget(btn_save)
        
    def guardar(self):
        val = self.txt_unidades.toPlainText().strip()
        if not val:
            val = "Unidad, Kg, Granel"
        config.set('unidades_medida', val)
        QMessageBox.information(self, "Guardado", "Unidades de medida actualizadas correctamente.")
        self.accept()

class DialogoNotificacionesCorreo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notificaciones por Correo")
        self.setFixedSize(500, 480)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 20)
        lay.setSpacing(15)
        
        lbl_title = QLabel("📧 Reporte de Ventas por Correo")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; ")
        lay.addWidget(lbl_title)
        
        lbl_desc = QLabel("Recibe un correo todos los lunes con el resumen de la semana y el Top 7 de artículos más vendidos.")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(" font-size: 13px;")
        lay.addWidget(lbl_desc)
        
        # Checkbox activar
        self.chk_activo = QCheckBox("Activar Reporte Semanal Automático")
        self.chk_activo.setStyleSheet("font-size: 14px; font-weight: bold;  padding: 5px;")
        self.chk_activo.setChecked(config.get("email_report_active", False))
        lay.addWidget(self.chk_activo)
        
        form_frame = QFrame()
        form_frame.setStyleSheet("background: white; border: 1px solid #E2E8F0; border-radius: 12px;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        form_frame.setGraphicsEffect(shadow)
        
        f_lay = QVBoxLayout(form_frame)
        f_lay.setContentsMargins(20, 20, 20, 20)
        f_lay.setSpacing(10)
        
        lbl_info = QLabel("El sistema utilizará nuestro servidor seguro para enviarte tus reportes. Solo dinos a dónde quieres recibirlos.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet(" font-size: 13px; font-weight: bold; border: none;")
        f_lay.addWidget(lbl_info)
        
        f_lay.addSpacing(10)
        
        f_lay.addWidget(QLabel("Correo Destinatario (A dónde llegará el reporte):", styleSheet="border: none; font-weight: bold; font-size: 13px;"))
        self.txt_dest = QLineEdit(config.get("email_dest", ""))
        self.txt_dest.setStyleSheet("padding: 12px; border: 1px solid #CBD5E1; border-radius: 8px; font-size: 14px; background: #F8FAFC;")
        self.txt_dest.setPlaceholderText("ejemplo@gmail.com")
        f_lay.addWidget(self.txt_dest)
        
        lay.addWidget(form_frame)
        
        lay.addStretch()
        
        btn_test = QPushButton("📩 Guardar y Enviar Correo de Prueba")
        btn_test.setCursor(Qt.PointingHandCursor)
        btn_test.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_test.clicked.connect(self.probar)
        lay.addWidget(btn_test)
        
        btn_save = QPushButton("💾 Guardar Configuración")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_save.clicked.connect(self.guardar)
        lay.addWidget(btn_save)
        
    def guardar(self):
        config.set("email_report_active", self.chk_activo.isChecked())
        config.set("email_dest", self.txt_dest.text().strip())
        QMessageBox.information(self, "Guardado", "Configuración de correo guardada.")
        self.accept()
        
    def probar(self):
        self.guardar()
        from src.services.email_service import enviar_reporte_semanal_si_es_necesario
        try:
            exito = enviar_reporte_semanal_si_es_necesario(forzar_envio=True)
            if exito:
                QMessageBox.information(self, "Éxito", "El correo de prueba ha sido enviado. Revisa la bandeja de entrada del destino.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo enviar el correo. Revisa tus credenciales o conexión a internet.")
        except Exception as e:
            QMessageBox.critical(self, "Error Fatal", f"Fallo al enviar correo: {e}")

class DialogoOpcionesHabilitadas(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones Habilitadas / Permisos")
        self.setFixedSize(500, 500)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 20)
        lay.setSpacing(10)
        
        lbl_title = QLabel("⚙️ Opciones Habilitadas del Sistema")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; ")
        lay.addWidget(lbl_title)
        
        lbl_desc = QLabel("Activa o desactiva módulos y permisos globales del punto de venta. Los cambios se aplicarán al instante.")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(" font-size: 13px; margin-bottom: 10px;")
        lay.addWidget(lbl_desc)
        
        # Opciones
        self.opciones = [
            ("opt_stock_negativo", "Permitir vender sin stock (Stock Negativo)", False),
            ("opt_ventas_credito", "Habilitar Ventas a Crédito (Fiado)", True),
            ("opt_impresion_auto", "Imprimir ticket automáticamente al cobrar", True),
            ("opt_control_stock", "Descontar stock del inventario al vender", True),
            ("opt_solicitar_cajero", "Solicitar seleccionar cajero al abrir el sistema", False),
            ("opt_bot_asistente", "Activar Bot Asistente Animado (Burbuja IA)", True),
            ("opt_devoluciones", "Permitir realizar devoluciones de productos", True)
        ]
        
        self.checkboxes = {}
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        c_lay = QVBoxLayout(content)
        c_lay.setSpacing(15)
        
        for key, text, default in self.opciones:
            frame = QFrame()
            frame.setStyleSheet(" border: 1px solid #E2E8F0; border-radius: 6px;")
            f_lay = QHBoxLayout(frame)
            
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size: 13px; font-weight: bold;  border: none;")
            
            chk = QCheckBox()
            # Leer de config
            chk.setChecked(config.get(key, default))
            chk.setStyleSheet("""
                QCheckBox::indicator { width: 40px; height: 20px; }
                QCheckBox::indicator:unchecked { image: none;  border-radius: 10px; }
                QCheckBox::indicator:checked { image: none;  border-radius: 10px; }
            """)
            
            f_lay.addWidget(lbl)
            f_lay.addStretch()
            f_lay.addWidget(chk)
            
            self.checkboxes[key] = chk
            c_lay.addWidget(frame)
            
        c_lay.addStretch()
        scroll.setWidget(content)
        lay.addWidget(scroll)
        
        btn_save = QPushButton("💾 Guardar Permisos")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 12px; border-radius: 6px; font-weight: bold; font-size: 14px;")
        btn_save.clicked.connect(self.guardar)
        lay.addWidget(btn_save)
        
    def guardar(self):
        for key, _, _ in self.opciones:
            config.set(key, self.checkboxes[key].isChecked())
            
        QMessageBox.information(self, "Guardado", "Los permisos y opciones han sido actualizados exitosamente.")
        self.accept()

class ConfigButton(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, icon_emoji, text, parent=None):
        super().__init__(parent)
        self.setFixedSize(110, 100)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Estilo tipo botón interactivo
        self.setStyleSheet("""
            ConfigButton {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
            ConfigButton:hover {
                background-color: #F8FAFC;
                border: 1px solid #3B82F6;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 15, 5, 5)
        layout.setSpacing(8)
        
        # Icono (Emoji)
        self.lbl_icon = QLabel(icon_emoji)
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setStyleSheet("font-size: 32px; background: transparent; border: none;")
        layout.addWidget(self.lbl_icon)
        
        # Texto
        self.lbl_text = QLabel(text)
        self.lbl_text.setAlignment(Qt.AlignCenter)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setStyleSheet("font-size: 11px; font-weight: bold;  background: transparent; border: none;")
        layout.addWidget(self.lbl_text)
        
        # Botón Ayuda (Absoluto)
        self.btn_help = QPushButton("❓", self)
        self.btn_help.setFixedSize(22, 22)
        self.btn_help.move(85, 5)
        self.btn_help.setStyleSheet("border: none; font-size: 12px; background: transparent;")
        self.btn_help.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_help.clicked.connect(self._show_help)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def _show_help(self):
        from PyQt5.QtWidgets import QMessageBox
        explicaciones = {
            "Alertas de\nEfectivo": "Te avisa si hay mucho dinero en la caja para que lo guardes (evita robos).",
            "Opciones\nhabilitadas": "Activa o desactiva módulos clave como vender sin stock, fiar, imprimir solo, etc.",
            "Cajeros": "Crea usuarios y contraseñas para tus empleados.",
            "Base de datos\nPC Esclava": "Cambia la contraseña maestra usada para conectar computadoras secundarias por red.",
            "Administrar\nCajas": "Conecta varias computadoras para que cobren juntas en red.",
            "Logotipo del\nPrograma": "Cambia el nombre de tu negocio y el diseño del ticket.",
            "Ticket": "Diseña cómo sale el ticket impreso para el cliente.",
            "Impuestos": "Agrega el IVA u otros impuestos a tus ventas si lo necesitas.",
            "Símbolo de\nMoneda": "Elige si usas $ (Pesos/Dólares) o € (Euros).",
            "Unidades de\nMedida": "Para vender productos por Kilo, Litro, Unidad, Metro, etc.",
            "Dos Tiketeras\n2 Cajas": "Si tienes 2 empleados en la misma compu, cada uno usa su impresora.",
            "Lector de\nCódigos": "Una prueba para ver si tu escáner o pistola de códigos funciona bien.",
            "Cajón de\nDinero": "Hace que el cajón de billetes salte solo cuando terminas de cobrar.",
            "Báscula": "Conecta una balanza electrónica para que el peso pase solo a la pantalla.",
            "Terminal\nTPV": "Conecta MercadoPago Point o Clover para cobrar directo con tarjeta.",
            "Hardware\nIndustrial": "Opciones avanzadas para equipos grandes de supermercado.",
            "App\nCobro Fácil": "Búscanos en las redes para tener tu App Móvil de Jefe, donde podrás ver cada billete que entra o sale de la caja en tiempo real por nuestras alarmas de apertura de caja sin permiso.",
            "Integraciones\nNube": "Conecta otros servicios de internet.",
            "Notificaciones\npor Correo": "Te manda un email al celular cada vez que cierran la caja.",
            "Respaldo": "Guarda una copia de seguridad en un pendrive para no perder nada.",
            "Licencia": "Mira tu plan actual o compra la versión completa.",
            "Actualizaciones": "Descarga las últimas mejoras del programa gratis."
        }
        texto = explicaciones.get(self.lbl_text.text(), "Configura esta opción del sistema.")
        msg = f"ℹ️ {self.lbl_text.text().replace(chr(10), ' ')}\n\n{texto}"
        QMessageBox.information(self, "Ayuda Rápida", msg)

class DialogoCajeros(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("👥 Gestión de Personal - Cobro Fácil POS")
        self.setFixedSize(700, 600)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        self.setup_ui()

    def setup_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(30, 30, 30, 30)
        main_lay.setSpacing(15)

        # --- HEADER ---
        header = QLabel("👥 Gestión de Cajeros y Administradores")
        header.setStyleSheet("font-size: 22px; font-weight: bold;  border:none;")
        main_lay.addWidget(header)
        
        lbl_info = QLabel("Administra los accesos y roles del personal de tu negocio.")
        lbl_info.setStyleSheet(" font-size: 13px; margin-bottom: 5px; border:none;")
        main_lay.addWidget(lbl_info)

        # --- TABLA PREMIUM ---
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["ID", "USUARIO", "ROL / RANGO", "PIN"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setShowGrid(False)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet("""
            QTableWidget { 
                background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; 
                gridline-color: transparent; alternate-
                selection- selection-
            }
            QHeaderView::section { 
                 padding: 15px; border: none; 
                font-weight: 900;  font-size: 11px; text-transform: uppercase;
            }
        """)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.itemClicked.connect(self._al_seleccionar)
        main_lay.addWidget(self.tabla)
        self.cargar_usuarios()

        # --- CARD DE EDICIÓN ---
        card = QFrame()
        card.setStyleSheet("background: white; border: 1px solid #E2E8F0; border-radius: 16px;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 5)
        card.setGraphicsEffect(shadow)
        
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(25, 25, 25, 25)
        card_lay.setSpacing(15)

        lbl_card = QLabel("📝 CARGAR / EDITAR PERSONAL")
        lbl_card.setStyleSheet("font-weight: 900;  font-size: 11px; border: none;")
        card_lay.addWidget(lbl_card)

        # Formulario
        f_lay = QGridLayout()
        f_lay.setSpacing(12)

        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Nombre de Usuario...")
        self.txt_user.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px; font-weight: bold;")
        
        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Contraseña (vacío para no cambiar)")
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px;")
        
        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems(["cajero", "admin", "auxiliar"])
        self.cmb_rol.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px; font-weight: bold;")
        
        self.txt_pin = QLineEdit()
        self.txt_pin.setPlaceholderText("PIN (numérico, ej: 1234)...")
        self.txt_pin.setMaxLength(6)
        self.txt_pin.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px; font-weight: bold;")

        f_lay.addWidget(QLabel("Usuario:"), 0, 0)
        f_lay.addWidget(self.txt_user, 0, 1)
        f_lay.addWidget(QLabel("Contraseña:"), 1, 0)
        f_lay.addWidget(self.txt_pass, 1, 1)
        f_lay.addWidget(QLabel("Rol / Rango:"), 0, 2)
        f_lay.addWidget(self.cmb_rol, 0, 3)
        f_lay.addWidget(QLabel("PIN Operativo:"), 1, 2)
        f_lay.addWidget(self.txt_pin, 1, 3)

        card_lay.addLayout(f_lay)

        # Botones
        b_lay = QHBoxLayout()
        btn_del = QPushButton("🗑️ Eliminar")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet("  border: 1px solid #FECACA; padding: 12px; border-radius: 10px; font-weight: bold;")
        btn_del.clicked.connect(self.eliminar_usuario)
        
        btn_save = QPushButton("💾 Guardar Usuario")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 12px; border-radius: 10px; font-weight: bold; border: none;")
        btn_save.clicked.connect(self.guardar_usuario)
        
        b_lay.addWidget(btn_del, 1)
        b_lay.addStretch()
        b_lay.addWidget(btn_save, 2)
        card_lay.addLayout(b_lay)

        main_lay.addWidget(card)

    def cargar_usuarios(self):
        self.tabla.setRowCount(0)
        res = db_manager.execute_query("SELECT id, username, rol, pin FROM usuarios ORDER BY id")
        if res:
            for i, r in enumerate(res):
                self.tabla.insertRow(i)
                self.tabla.setRowHeight(i, 45)
                
                id_it = QTableWidgetItem(str(r['id']))
                id_it.setTextAlignment(Qt.AlignCenter)
                self.tabla.setItem(i, 0, id_it)
                
                usr_it = QTableWidgetItem(r['username'])
                usr_it.setFont(QFont("Segoe UI", 10, QFont.Bold))
                self.tabla.setItem(i, 1, usr_it)
                
                rol = r['rol'].upper()
                rol_it = QTableWidgetItem(rol)
                rol_it.setTextAlignment(Qt.AlignCenter)
                rol_it.setFont(QFont("Segoe UI", 9, QFont.Black))
                
                if rol == "ADMIN": rol_it.setForeground(QColor("#1E3A8A"))
                elif rol == "AUXILIAR": rol_it.setForeground(QColor("#059669"))
                else: rol_it.setForeground(QColor("#475569"))
                self.tabla.setItem(i, 2, rol_it)

                pin_val = str(r['pin'] or '1234')
                pin_it = QTableWidgetItem("••••" if len(pin_val) > 0 else "")
                pin_it.setTextAlignment(Qt.AlignCenter)
                pin_it.setData(Qt.UserRole, pin_val) # Guardar valor real
                self.tabla.setItem(i, 3, pin_it)

    def _al_seleccionar(self, item):
        row = self.tabla.currentRow()
        self.txt_user.setText(self.tabla.item(row, 1).text())
        rol = self.tabla.item(row, 2).text().lower()
        idx = self.cmb_rol.findText(rol)
        if idx >= 0: self.cmb_rol.setCurrentIndex(idx)
        self.txt_pass.clear()
        
        pin_item = self.tabla.item(row, 3)
        if pin_item:
            self.txt_pin.setText(pin_item.data(Qt.UserRole))
        else:
            self.txt_pin.clear()

    def guardar_usuario(self):
        usr = self.txt_user.text().strip()
        pwd = self.txt_pass.text().strip()
        rol = self.cmb_rol.currentText()
        pin = self.txt_pin.text().strip()
        if not usr: return
        if not pin: pin = "1234"
        
        import hashlib
        # Hash the PIN
        h_pin = hashlib.sha256(pin.encode()).hexdigest()
        
        exists = db_manager.execute_scalar("SELECT id FROM usuarios WHERE username = ?", (usr,))
        if exists:
            if pwd:
                h = hashlib.sha256(pwd.encode()).hexdigest()
                db_manager.execute_non_query("UPDATE usuarios SET password_hash = ?, rol = ?, pin = ? WHERE username = ?", (h, rol, h_pin, usr))
            else:
                db_manager.execute_non_query("UPDATE usuarios SET rol = ?, pin = ? WHERE username = ?", (rol, h_pin, usr))
        else:
            if not pwd: pwd = usr # Default password is the username
            h = hashlib.sha256(pwd.encode()).hexdigest()
            db_manager.execute_non_query("INSERT INTO usuarios (username, password_hash, rol, pin) VALUES (?, ?, ?, ?)", (usr, h, rol, h_pin))
        
        self.txt_user.clear(); self.txt_pass.clear(); self.txt_pin.clear(); self.cargar_usuarios()

    def eliminar_usuario(self):
        row = self.tabla.currentRow()
        if row < 0: return
        uid = self.tabla.item(row, 0).text()
        if uid == "1":
            QMessageBox.warning(self, "Protección", "El administrador raíz no puede ser eliminado.")
            return
        if QMessageBox.question(self, "Eliminar", f"¿Eliminar a {self.tabla.item(row, 1).text()}?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            db_manager.execute_non_query("DELETE FROM usuarios WHERE id = ?", (uid,))
            self.cargar_usuarios()

class DialogoTicket(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Diseñador de Ticket y Recibos")
        self.setFixedSize(750, 480)
        self.setStyleSheet(" font-family: 'Segoe UI';")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # LEFT: Form fields
        left_panel = QFrame()
        left_panel.setStyleSheet("background: white; border-radius: 16px; border: 1px solid #E2E8F0;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        left_panel.setGraphicsEffect(shadow)
        
        form_layout = QVBoxLayout(left_panel)
        form_layout.setContentsMargins(25, 25, 25, 25)
        
        lbl_title = QLabel("📝 Datos del Negocio")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold;  border: none;")
        form_layout.addWidget(lbl_title)
        form_layout.addSpacing(10)
        
        self.txt_name = QLineEdit(config.get('business_name', ''))
        self.txt_addr = QLineEdit(config.get('address', ''))
        self.txt_phone = QLineEdit(config.get('phone', ''))
        self.txt_cuit = QLineEdit(config.get('business_cuit', ''))
        self.txt_msg = QLineEdit(config.get('footer_message', ''))
        
        for txt, lbl in [
            (self.txt_name, "Nombre Comercial (Logotipo):"),
            (self.txt_addr, "Dirección Comercial:"),
            (self.txt_phone, "Teléfono / Contacto:"),
            (self.txt_cuit, "CUIT / RUT / NIT:"),
            (self.txt_msg, "Mensaje de Despedida:")
        ]:
            l = QLabel(lbl)
            l.setStyleSheet(" font-size: 13px; font-weight: bold; border: none;")
            txt.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px;  color: black; font-size: 13px;")
            txt.textChanged.connect(self._update_preview)
            form_layout.addWidget(l)
            form_layout.addWidget(txt)
            form_layout.addSpacing(5)
            
        form_layout.addStretch()
        
        btn_save = QPushButton("💾 Guardar y Aplicar")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 12px; font-weight: bold; border-radius: 6px; font-size: 14px;")
        btn_save.clicked.connect(self.guardar)
        form_layout.addWidget(btn_save)
        
        main_layout.addWidget(left_panel, 1)
        
        # RIGHT: Live Preview
        right_panel = QFrame()
        right_panel.setStyleSheet("background: transparent;")
        preview_layout = QVBoxLayout(right_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_prev_title = QLabel("👁️ Vista Previa del Ticket")
        lbl_prev_title.setStyleSheet("font-size: 14px; font-weight: bold; ")
        lbl_prev_title.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(lbl_prev_title)
        
        # Ticket Shape
        self.ticket_frame = QFrame()
        self.ticket_frame.setStyleSheet("""
            QFrame {
                background-color: #FEF9C3; /* Yellowish paper color */
                border: 1px solid #D1D5DB;
                border-radius: 0px;
                border-top: 2px dashed #9CA3AF;
                border-bottom: 2px dashed #9CA3AF;
            }
        """)
        
        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(15)
        shadow2.setColor(QColor(0, 0, 0, 30))
        shadow2.setOffset(0, 5)
        self.ticket_frame.setGraphicsEffect(shadow2)
        
        self.ticket_frame.setFixedWidth(280)
        
        t_lay = QVBoxLayout(self.ticket_frame)
        t_lay.setContentsMargins(15, 20, 15, 20)
        t_lay.setSpacing(5)
        
        self.lbl_t_name = QLabel()
        self.lbl_t_name.setAlignment(Qt.AlignCenter)
        self.lbl_t_name.setWordWrap(True)
        self.lbl_t_name.setStyleSheet("font-weight: 900; font-size: 16px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_name)
        
        self.lbl_t_cuit = QLabel()
        self.lbl_t_cuit.setAlignment(Qt.AlignCenter)
        self.lbl_t_cuit.setStyleSheet("font-size: 12px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_cuit)
        
        self.lbl_t_addr = QLabel()
        self.lbl_t_addr.setAlignment(Qt.AlignCenter)
        self.lbl_t_addr.setStyleSheet("font-size: 12px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_addr)
        
        self.lbl_t_phone = QLabel()
        self.lbl_t_phone.setAlignment(Qt.AlignCenter)
        self.lbl_t_phone.setStyleSheet("font-size: 12px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_phone)
        
        sep1 = QLabel("-" * 32)
        sep1.setAlignment(Qt.AlignCenter)
        sep1.setStyleSheet("color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(sep1)
        
        lbl_body = QLabel("Ticket Nro: 00000123\nFecha: 24/10/2026 15:30\n\n1 x Producto A      $150.00\n2 x Producto B      $500.00")
        lbl_body.setStyleSheet("font-family: 'Courier New', monospace; font-size: 12px; color: black; border: none;")
        t_lay.addWidget(lbl_body)
        
        sep2 = QLabel("-" * 32)
        sep2.setAlignment(Qt.AlignCenter)
        sep2.setStyleSheet("color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(sep2)
        
        lbl_total = QLabel("TOTAL: $650.00")
        lbl_total.setAlignment(Qt.AlignCenter)
        lbl_total.setStyleSheet("font-weight: bold; font-size: 14px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(lbl_total)
        
        self.lbl_t_msg = QLabel()
        self.lbl_t_msg.setAlignment(Qt.AlignCenter)
        self.lbl_t_msg.setWordWrap(True)
        self.lbl_t_msg.setStyleSheet("font-size: 12px; color: black; border: none; margin-top: 10px; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_msg)
        
        t_lay.addStretch()
        
        # Center the ticket
        t_container = QHBoxLayout()
        t_container.addStretch()
        t_container.addWidget(self.ticket_frame)
        t_container.addStretch()
        preview_layout.addLayout(t_container)
        
        main_layout.addWidget(right_panel, 1)
        
        self._update_preview()

    def _update_preview(self):
        self.lbl_t_name.setText(self.txt_name.text() or "MI EMPRESA")
        self.lbl_t_cuit.setText(self.txt_cuit.text() or "CUIT: 00-00000000-0")
        self.lbl_t_addr.setText(self.txt_addr.text() or "Dirección del Local")
        self.lbl_t_phone.setText(f"Tel: {self.txt_phone.text()}" if self.txt_phone.text() else "")
        self.lbl_t_msg.setText(self.txt_msg.text() or "Gracias por su compra!")

    def guardar(self):
        config.set('business_name', self.txt_name.text())
        config.set('address', self.txt_addr.text())
        config.set('phone', self.txt_phone.text())
        config.set('business_cuit', self.txt_cuit.text())
        config.set('footer_message', self.txt_msg.text())
        
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Guardado", "Diseño de ticket actualizado correctamente.")
        self.accept()

class DialogoLectorCodigos(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Probar Lector de Códigos de Barras")
        self.setFixedSize(500, 350)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("Configuración y Prueba del Lector")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; ")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)
        
        lbl_inst = QLabel("1. Haz clic en el cuadro de texto azul.\n2. Dispara el escáner sobre cualquier código de barras.")
        lbl_inst.setStyleSheet("font-size: 14px; ")
        lbl_inst.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_inst)
        
        self.txt_scan = QLineEdit()
        self.txt_scan.setPlaceholderText("Escanea aquí...")
        self.txt_scan.setStyleSheet(" border: 2px dashed #38BDF8; font-size: 30px; font-weight: bold;  padding: 10px;")
        self.txt_scan.setAlignment(Qt.AlignCenter)
        self.txt_scan.returnPressed.connect(self.procesar_escaneo)
        layout.addWidget(self.txt_scan)
        
        self.lbl_resultado = QLabel("")
        self.lbl_resultado.setStyleSheet("font-size: 16px; font-weight: bold; ")
        self.lbl_resultado.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_resultado)
        
        layout.addStretch()
        btn = QPushButton("Terminar Prueba")
        btn.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def procesar_escaneo(self):
        codigo = self.txt_scan.text().strip()
        if codigo:
            self.lbl_resultado.setText(f"✅ ¡Éxito! Código leído: {codigo}\nEl escáner está configurado correctamente (Envía ENTER).")
            self.txt_scan.setStyleSheet(" border: 2px solid #10B981; font-size: 30px; font-weight: bold;  padding: 10px;")
            self.txt_scan.clear()

class ConfigCategory(QWidget):
    def __init__(self, title, items, callback=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Título de Categoría
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold;  border-bottom: 1px solid #CBD5E1; padding-bottom: 5px;")
        layout.addWidget(lbl_title)
        
        # Grid para los botones
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setAlignment(Qt.AlignLeft)
        
        row, col = 0, 0
        max_cols = 7 # Máximo 7 botones por fila
        
        for icon, text in items:
            btn = ConfigButton(icon, text)
            if callback:
                btn.clicked.connect(lambda t=text: callback(t))
            grid.addWidget(btn, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
        layout.addLayout(grid)
        layout.addSpacing(20)



class DialogoCajon(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración del Cajón de Dinero")
        self.setFixedSize(450, 350)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("📦 Apertura Automática del Cajón")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; ")
        layout.addWidget(lbl_title)
        
        lbl_inst = QLabel("Selecciona en qué momentos debe abrirse el cajón de dinero:")
        lbl_inst.setStyleSheet("font-size: 13px;  margin-bottom: 10px;")
        layout.addWidget(lbl_inst)
        
        from PyQt5.QtWidgets import QCheckBox
        self.chk_efectivo = QCheckBox("Abrir en ventas con EFECTIVO")
        self.chk_tarjeta = QCheckBox("Abrir en ventas con TARJETA")
        self.chk_transf = QCheckBox("Abrir en ventas con TRANSFERENCIA")
        self.chk_mixto = QCheckBox("Abrir en ventas MIXTAS")
        
        # Cargar valores actuales
        self.chk_efectivo.setChecked(config.get("drawer_open_cash", True))
        self.chk_tarjeta.setChecked(config.get("drawer_open_card", False))
        self.chk_transf.setChecked(config.get("drawer_open_transfer", False))
        self.chk_mixto.setChecked(config.get("drawer_open_mixed", True))
        
        for chk in [self.chk_efectivo, self.chk_tarjeta, self.chk_transf, self.chk_mixto]:
            chk.setStyleSheet("font-size: 14px; padding: 5px;")
            layout.addWidget(chk)
            
        layout.addSpacing(20)
        
        row_test = QHBoxLayout()
        btn_test = QPushButton("⚡ Probar Apertura (Kick)")
        btn_test.setStyleSheet(" background-color: #3B82F6; color: white; padding: 12px; font-weight: bold; border-radius: 8px;")
        btn_test.clicked.connect(self.probar_cajon)
        
        btn_alarm = QPushButton("🚨 Probar Alarma SOS")
        btn_alarm.setStyleSheet(" background-color: #3B82F6; color: white; padding: 12px; font-weight: bold; border-radius: 8px;")
        btn_alarm.clicked.connect(self.probar_alarma)
        
        row_test.addWidget(btn_test)
        row_test.addWidget(btn_alarm)
        layout.addLayout(row_test)
        
        layout.addStretch()
        
        btn_save = QPushButton("Guardar Configuración")
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px; font-weight: bold; border-radius: 8px;")
        btn_save.clicked.connect(self.guardar)
        layout.addWidget(btn_save)

    def probar_cajon(self):
        try:
            from src.hardware.printer import printer_manager
            printer_manager.abrir_cajon()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def probar_alarma(self):
        parent = self.window()
        if hasattr(parent, 'mostrar_alerta_perimetral'):
            QMessageBox.information(self, "Alarma", "Iniciando simulacro de seguridad global (5 seg)...")
            parent.mostrar_alerta_perimetral(True)
            QTimer.singleShot(5000, lambda: parent.mostrar_alerta_perimetral(False))
        else:
            QMessageBox.warning(self, "Aviso", "Motor de alarma global no disponible.")

    def guardar(self):
        config.set("drawer_open_cash", self.chk_efectivo.isChecked())
        config.set("drawer_open_card", self.chk_tarjeta.isChecked())
        config.set("drawer_open_transfer", self.chk_transf.isChecked())
        config.set("drawer_open_mixed", self.chk_mixto.isChecked())
        self.accept()

class DialogoDosTiketeras(QDialog):
    """Asigna una tiketera a cada cajero. Al desbloquear, se usa la del cajero activo."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tiketeras por Cajero")
        self.setFixedSize(500, 520)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 22, 30, 22)
        layout.setSpacing(14)

        lbl_title = QLabel("🖨️  TIKETERA POR CAJERO")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 900; ")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        lbl_inst = QLabel("Asigná una tiketera y cajón a cada operador.\nEl sistema usa automáticamente la del que desbloquó la terminal.")
        lbl_inst.setStyleSheet("font-size: 12px; ")
        lbl_inst.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_inst)

        layout.addSpacing(6)

        # CAJERO (principal)
        box1 = QFrame()
        box1.setStyleSheet("QFrame {  border: 2px solid #1E3A8A; border-radius: 10px; } QLabel { border: none; background: transparent; }")
        b1 = QVBoxLayout(box1); b1.setContentsMargins(16, 12, 16, 12); b1.setSpacing(6)
        b1.addWidget(QLabel("🔵  [1]  CAJERO — Tiketera / Cajón:", styleSheet="font-size: 13px; font-weight: 900; "))
        
        row1 = QHBoxLayout()
        self.cmb_p1 = QComboBox()
        self.cmb_p1.setStyleSheet("padding: 7px; border: 1px solid #93C5FD; border-radius: 6px; font-size: 13px; background: white;")
        row1.addWidget(QLabel("🖨️ Impresora:"), 0)
        row1.addWidget(self.cmb_p1, 1)
        
        btn_test1 = QPushButton("📄 Test P1")
        btn_test1.setCursor(Qt.PointingHandCursor)
        btn_test1.setStyleSheet(" background-color: #3B82F6; color: white; border-radius: 6px; font-weight: bold; padding: 7px 15px;")
        btn_test1.clicked.connect(lambda: self.print_test_ticket_generic(self.cmb_p1.currentText()))
        row1.addWidget(btn_test1)
        b1.addLayout(row1)

        row1_com = QHBoxLayout()
        self.cmb_serial_port_1 = QComboBox()
        self.cmb_serial_port_1.setStyleSheet("padding: 7px; border: 1px solid #93C5FD; border-radius: 6px; font-size: 13px; background: white;")
        row1_com.addWidget(QLabel("🔌 Sensor COM (Cajón):"), 0)
        row1_com.addWidget(self.cmb_serial_port_1, 1)
        b1.addLayout(row1_com)
        
        layout.addWidget(box1)

        # AUXILIAR (secundario)
        box2 = QFrame()
        box2.setStyleSheet("QFrame {  border: 2px solid #059669; border-radius: 10px; } QLabel { border: none; background: transparent; }")
        b2 = QVBoxLayout(box2); b2.setContentsMargins(16, 12, 16, 12); b2.setSpacing(6)
        b2.addWidget(QLabel("🟢  [2]  AUXILIAR — Tiketera / Cajón:", styleSheet="font-size: 13px; font-weight: 900; "))
        
        row2 = QHBoxLayout()
        self.cmb_p2 = QComboBox()
        self.cmb_p2.setStyleSheet("padding: 7px; border: 1px solid #6EE7B7; border-radius: 6px; font-size: 13px; background: white;")
        row2.addWidget(QLabel("🖨️ Impresora:"), 0)
        row2.addWidget(self.cmb_p2, 1)
        
        btn_test2 = QPushButton("📄 Test P2")
        btn_test2.setCursor(Qt.PointingHandCursor)
        btn_test2.setStyleSheet(" background-color: #3B82F6; color: white; border-radius: 6px; font-weight: bold; padding: 7px 15px;")
        btn_test2.clicked.connect(lambda: self.print_test_ticket_generic(self.cmb_p2.currentText()))
        row2.addWidget(btn_test2)
        b2.addLayout(row2)

        row2_com = QHBoxLayout()
        self.cmb_serial_port_2 = QComboBox()
        self.cmb_serial_port_2.setStyleSheet("padding: 7px; border: 1px solid #6EE7B7; border-radius: 6px; font-size: 13px; background: white;")
        row2_com.addWidget(QLabel("🔌 Sensor COM (Cajón):"), 0)
        row2_com.addWidget(self.cmb_serial_port_2, 1)
        b2.addLayout(row2_com)
        
        layout.addWidget(box2)

        # Botón Recargar (Movido arriba o abajo, lo pondremos junto al stretch)
        btn_ref = QPushButton("🔄 Actualizar Puertos e Impresoras")
        btn_ref.setCursor(Qt.PointingHandCursor)
        btn_ref.setStyleSheet("  padding: 8px; border-radius: 6px; font-weight: bold;")
        btn_ref.clicked.connect(self._load_printers_and_ports)
        layout.addWidget(btn_ref)

        self._load_printers_and_ports()
        layout.addStretch()

        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("  padding: 10px 22px; border-radius: 6px; font-weight: bold;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾  Guardar")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px 22px; border-radius: 6px; font-weight: bold;")
        btn_save.clicked.connect(self._guardar)
        h_btns.addWidget(btn_cancel); h_btns.addStretch(); h_btns.addWidget(btn_save)
        layout.addLayout(h_btns)

    def print_test_ticket_generic(self, printer_name):
        if not printer_name or printer_name == "(Sin impresora)":
            QMessageBox.warning(self, "Error", "No hay impresora seleccionada para probar.")
            return
        
        try:
            import datetime
            from src.hardware.printer import PosPrinter
            test_printer = PosPrinter()
            test_printer.printer_name = printer_name
            
            # Formatear un ticket simple de prueba
            data = bytearray()
            data.extend(b"\x1B\x40") # Reset
            data.extend(b"\x1B\x61\x01") # Centro
            data.extend(f"CAJAFACIL PRO 2026\n".encode())
            data.extend(f"TEST IMPRESION OK\n".encode())
            data.extend(b"--------------------------------\n")
            data.extend(f"Impresora: {printer_name}\n".encode())
            data.extend(f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n".encode())
            data.extend(b"--------------------------------\n")
            data.extend(b"ESTADO: OPERATIVA / ACTIVA\n\n\n\n\n")
            data.extend(b"\x1D\x56\x41\x00") # Corte de papel
            
            test_printer._send_raw_data(bytes(data))
            QMessageBox.information(self, "Éxito", f"Prueba de impresión enviada a {printer_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo al imprimir: {e}")

    def _load_printers_and_ports(self):
        try:
            from PyQt5.QtPrintSupport import QPrinterInfo
            printers = list(QPrinterInfo.availablePrinterNames())
            for cmb in [self.cmb_p1, self.cmb_p2]:
                cmb.blockSignals(True)
                cmb.clear()
                cmb.addItem("(Sin impresora)")
                cmb.addItems(printers)
                cmb.blockSignals(False)

            p1 = config.get("ticket_printer", "")
            p2 = config.get("ticket_printer_2", "")
            if p1 in printers: self.cmb_p1.setCurrentText(p1)
            if p2 in printers: self.cmb_p2.setCurrentText(p2)
            
            # Cargar puertos COM dinámicamente
            for cmb_com in [self.cmb_serial_port_1, self.cmb_serial_port_2]:
                cmb_com.blockSignals(True)
                cmb_com.clear()
            
            ports_list = ["Ninguno (USB Directo / OPOS)"] + [f"COM{i}" for i in range(1, 31)]
            try:
                import serial.tools.list_ports
                detected = [p.device for p in serial.tools.list_ports.comports()]
                for d in detected:
                    if d not in ports_list:
                        ports_list.insert(1, d)
            except Exception:
                pass
                
            self.cmb_serial_port_1.addItems(ports_list)
            self.cmb_serial_port_2.addItems(ports_list)
            
            saved_port_1 = config.get("printer_name", "")
            saved_port_2 = config.get("drawer_com_port_2", "")
            
            if saved_port_1:
                idx1 = self.cmb_serial_port_1.findText(saved_port_1)
                if idx1 != -1: self.cmb_serial_port_1.setCurrentIndex(idx1)
                else:
                    self.cmb_serial_port_1.addItem(saved_port_1)
                    self.cmb_serial_port_1.setCurrentText(saved_port_1)

            if saved_port_2:
                idx2 = self.cmb_serial_port_2.findText(saved_port_2)
                if idx2 != -1: self.cmb_serial_port_2.setCurrentIndex(idx2)
                else:
                    self.cmb_serial_port_2.addItem(saved_port_2)
                    self.cmb_serial_port_2.setCurrentText(saved_port_2)
                    
            for cmb_com in [self.cmb_serial_port_1, self.cmb_serial_port_2]:
                cmb_com.blockSignals(False)
        except Exception: pass

    def _guardar(self):
        p1 = self.cmb_p1.currentText()
        p2 = self.cmb_p2.currentText()
        if p1 == "(Sin impresora)": p1 = ""
        if p2 == "(Sin impresora)": p2 = ""
        config.set("ticket_printer", p1)
        config.set("ticket_printer_2", p2)
        
        com_val_1 = self.cmb_serial_port_1.currentText()
        if "Ninguno" in com_val_1: config.set("printer_name", "")
        else: config.set("printer_name", com_val_1)
            
        com_val_2 = self.cmb_serial_port_2.currentText()
        if "Ninguno" in com_val_2: config.set("drawer_com_port_2", "")
        else: config.set("drawer_com_port_2", com_val_2)
            
        QMessageBox.information(self, "✅ Guardado con Éxito",
            f"Cajero 1 → Impresora: {p1 or 'Ninguna'} | COM: {config.get('printer_name', 'Ninguno')}\n"
            f"Cajero 2 → Impresora: {p2 or 'Ninguna'} | COM: {config.get('drawer_com_port_2', 'Ninguno')}")
        self.accept()


class DialogoAdministrarCajas(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📟 Administrar Cajas del Sistema")
        self.setFixedSize(400, 220)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        lbl_title = QLabel("📟  Identificación de Caja Local")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 900; ")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        lbl_inst = QLabel(
            "Configura el identificador numérico inmutable para esta PC en la red.\n"
            "Cada terminal debe tener un ID único (ej: 1, 2, 3...)."
        )
        lbl_inst.setStyleSheet("font-size: 12px; ")
        lbl_inst.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_inst)

        # Caja ID Input
        h_lay = QHBoxLayout()
        h_lay.addWidget(QLabel("ID de Caja Física:", styleSheet="font-weight: bold; font-size: 13px; "))
        
        self.txt_caja_id = QLineEdit()
        self.txt_caja_id.setText(str(config.get("caja_id", 1)))
        self.txt_caja_id.setStyleSheet("padding: 8px; border: 2px solid #CBD5E1; border-radius: 6px; font-weight: bold; font-size: 15px;")
        self.txt_caja_id.setAlignment(Qt.AlignCenter)
        h_lay.addWidget(self.txt_caja_id)
        layout.addLayout(h_lay)

        layout.addStretch()

        btn_save = QPushButton("💾 Guardar Identificador")
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 12px; font-weight: bold; border-radius: 6px;")
        btn_save.clicked.connect(self.guardar)
        layout.addWidget(btn_save)

    def guardar(self):
        try:
            val = int(self.txt_caja_id.text().strip())
            if val <= 0:
                raise ValueError()
            config.set("caja_id", val)
            QMessageBox.information(
                self, "ID de Caja Registrado", 
                f"Esta computadora ha sido guardada permanentemente como la CAJA {val:02d}.\n"
                "Los cierres y auditorías de esta terminal se filtrarán bajo esta firma."
            )
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Error de Validación", "El ID de caja debe ser un número entero mayor a cero.")


class DialogoAlertasEfectivo(QDialog):
    """Permite configurar los topes de efectivo en caja para activar los parpadeos SOS en la terminal."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alertas SOS de Efectivo en Caja")
        self.setFixedSize(400, 260)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 20)
        lay.setSpacing(12)

        lbl_tit = QLabel("⚠️  Umbrales de Retiro SOS")
        lbl_tit.setStyleSheet("font-size: 18px; font-weight: 900; ")
        lbl_tit.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_tit)

        lbl_inst = QLabel("Configurá desde qué montos acumulados en efectivo\nla terminal debe parpadear exigiendo un retiro de caja:")
        lbl_inst.setStyleSheet("font-size: 12px; ")
        lbl_inst.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_inst)

        # Amarillo (Nivel 1)
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("🟡 Alerta Amarilla ($):", styleSheet="font-weight: bold;  font-size: 13px;"))
        self.txt_nar = QLineEdit()
        self.txt_nar.setText(str(int(float(config.get("limite_efectivo_naranja", 50000)))))
        self.txt_nar.setStyleSheet("padding: 6px; border: 1px solid #CBD5E1; border-radius: 5px; font-weight: bold; font-size: 14px;")
        self.txt_nar.setAlignment(Qt.AlignRight)
        h1.addWidget(self.txt_nar)
        lay.addLayout(h1)

        # Naranja (Nivel 2)
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("🟠 Alerta Naranja ($):", styleSheet="font-weight: bold;  font-size: 13px;"))
        self.txt_roj = QLineEdit()
        self.txt_roj.setText(str(int(float(config.get("limite_efectivo_rojo", 70000)))))
        self.txt_roj.setStyleSheet("padding: 6px; border: 1px solid #CBD5E1; border-radius: 5px; font-weight: bold; font-size: 14px;")
        self.txt_roj.setAlignment(Qt.AlignRight)
        h2.addWidget(self.txt_roj)
        lay.addLayout(h2)

        lay.addStretch()

        btn_save = QPushButton("💾 Guardar Configuración")
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_save.clicked.connect(self._guardar)
        lay.addWidget(btn_save)

    def _guardar(self):
        try:
            nar = float(self.txt_nar.text().strip())
            roj = float(self.txt_roj.text().strip())
            if nar >= roj:
                QMessageBox.warning(self, "Advertencia", "El límite rojo debe ser estrictamente mayor al límite naranja.")
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingresá valores numéricos válidos.")


class DialogoBalanza(QDialog):
    """Configuración avanzada de balanzas (Systel, Kretz, Moretti, etc.)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚖️ Configuración de Báscula / Balanza")
        self.setFixedSize(540, 750)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        self._build()

    def _build(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(30, 30, 30, 30)
        main_lay.setSpacing(15)

        # --- TÍTULO ---
        header = QLabel("⚖️ Configuración de Balanza")
        header.setStyleSheet("font-size: 20px; font-weight: bold;  border:none;")
        main_lay.addWidget(header)
        
        lbl_desc = QLabel("Ajusta cómo el sistema lee tus etiquetas EAN-13.")
        lbl_desc.setStyleSheet(" font-size: 13px; margin-bottom: 5px; border:none;")
        main_lay.addWidget(lbl_desc)

        # --- CARD DE CONFIGURACIÓN ---
        card = QFrame()
        card.setStyleSheet("""
            QFrame {  border: 1px solid #E2E8F0; border-radius: 12px; }
            QLabel { border: none; font-weight: bold;  font-size: 11px; }
            QLineEdit, QComboBox { 
                background: white; border: 1px solid #CBD5E1; border-radius: 6px; 
                padding: 10px; font-weight: normal;  font-size: 13px;
            }
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(20, 20, 20, 20)
        card_lay.setSpacing(12)

        # Estado
        card_lay.addWidget(QLabel("ESTADO DEL SISTEMA:"))
        self.chk_enabled = QComboBox()
        self.chk_enabled.addItems(["Desactivada", "Activada (Modo Inteligente)"])
        self.chk_enabled.setCurrentIndex(1 if config.get("balanza_habilitada", True) else 0)
        card_lay.addWidget(self.chk_enabled)

        # Modo de Interpretación
        card_lay.addWidget(QLabel("INTERPRETAR VALOR COMO:"))
        self.cmb_modo = QComboBox()
        self.cmb_modo.addItems(["Peso Neto (Kg)", "Importe Total ($)"])
        self.cmb_modo.setCurrentText(config.get("balanza_modo", "Peso Neto (Kg)"))
        card_lay.addWidget(self.cmb_modo)

        # Grid de Parámetros EAN-13
        grid = QGridLayout()
        grid.setSpacing(12)

        # Prefijo
        grid.addWidget(QLabel("PREFIJO BASE (20):"), 0, 0)
        self.txt_pref = QLineEdit(str(config.get("balanza_prefijo", "20")))
        grid.addWidget(self.txt_pref, 0, 1)

        # PLU (Donde empieza y cuántos dígitos)
        grid.addWidget(QLabel("PLU (Inicio / Largo):"), 1, 0)
        h_plu = QHBoxLayout()
        self.txt_plu_start = QLineEdit(str(config.get("balanza_plu_inicio", 3)))
        self.txt_plu_len = QLineEdit(str(config.get("balanza_plu_largo", 4)))
        h_plu.addWidget(self.txt_plu_start); h_plu.addWidget(self.txt_plu_len)
        grid.addLayout(h_plu, 1, 1)

        # Valor (Donde empieza y cuántos dígitos)
        grid.addWidget(QLabel("VALOR (Inicio / Largo):"), 2, 0)
        h_val = QHBoxLayout()
        self.txt_val_start = QLineEdit(str(config.get("balanza_val_inicio", 8)))
        self.txt_val_len = QLineEdit(str(config.get("balanza_val_largo", 5)))
        h_val.addWidget(self.txt_val_start); h_val.addWidget(self.txt_val_len)
        grid.addLayout(h_val, 2, 1)

        # Divisor
        grid.addWidget(QLabel("DIVISOR (Ej: 1000):"), 3, 0)
        self.txt_divisor = QLineEdit(str(config.get("balanza_divisor", 1000)))
        grid.addWidget(self.txt_divisor, 3, 1)

        card_lay.addLayout(grid)
        main_lay.addWidget(card)

        # --- SIMULADOR ---
        sim_card = QFrame()
        sim_card.setStyleSheet(" border: 1px solid #BFDBFE; border-radius: 12px;")
        sim_lay = QVBoxLayout(sim_card)
        sim_lay.setContentsMargins(15, 15, 15, 15)
        
        lbl_sim = QLabel("🧪 PROBADOR DE CÓDIGOS")
        lbl_sim.setStyleSheet(" font-weight: 900; border: none; font-size: 11px;")
        sim_lay.addWidget(lbl_sim)

        self.txt_test = QLineEdit()
        self.txt_test.setPlaceholderText("Pega un código EAN-13 aquí para probar...")
        self.txt_test.setStyleSheet("background: white; border: 1px solid #3B82F6; padding: 10px; font-family: 'Consolas';")
        self.txt_test.textChanged.connect(self.simular_prueba)
        sim_lay.addWidget(self.txt_test)

        self.lbl_res_test = QLabel("Resultado: —")
        self.lbl_res_test.setStyleSheet(" font-weight: bold; border: none;")
        sim_lay.addWidget(self.lbl_res_test)
        main_lay.addWidget(sim_card)

        # --- AYUDA ---
        btn_help = QPushButton("❓ Ver Formatos Comunes (Systel, Kretz, etc.)")
        btn_help.setStyleSheet(" font-weight: bold; border: none; background: transparent; font-size: 11px;")
        btn_help.setCursor(Qt.PointingHandCursor)
        btn_help.clicked.connect(self._sugerir_formatos)
        main_lay.addWidget(btn_help)

        # --- BOTONES ---
        main_lay.addStretch()
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("padding: 12px; font-weight: bold;   border-radius: 8px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 Guardar Configuración")
        btn_save.setStyleSheet("padding: 12px; font-weight: bold;  background-color: #3B82F6; color: white; border-radius: 8px;")
        btn_save.clicked.connect(self._guardar)
        
        h_btns.addWidget(btn_cancel)
        h_btns.addStretch()
        h_btns.addWidget(btn_save)
        main_lay.addLayout(h_btns)

    def simular_prueba(self):
        txt = self.txt_test.text().strip()
        if len(txt) != 13:
            self.lbl_res_test.setText("Esperando código de 13 dígitos...")
            return
        try:
            pref = self.txt_pref.text().strip()
            p_start = int(self.txt_plu_start.text()) - 1
            p_len = int(self.txt_plu_largo.text()) if hasattr(self, 'txt_plu_largo') else int(self.txt_plu_len.text())
            plu = txt[p_start : p_start + p_len]
            
            v_start = int(self.txt_val_start.text()) - 1
            v_len = int(self.txt_val_largo.text()) if hasattr(self, 'txt_val_largo') else int(self.txt_val_len.text())
            v_raw = txt[v_start : v_start + v_len]
            divisor = int(self.txt_divisor.text())
            
            valor = int(v_raw) / divisor
            modo = self.cmb_modo.currentText()
            simb = "$" if "Importe" in modo else "Kg"
            self.lbl_res_test.setText(f"✅ PLU: {plu} | {simb}: {valor:.3f}")
        except:
            self.lbl_res_test.setText("❌ Error en configuración.")

    def _sugerir_formatos(self):
        msg = ("<b>Formatos Comunes:</b><br><br>"
               "• <b>Estándar Eleventa / Systel (5-Dig):</b> Inicio PLU: 3, Largo: 5 | Inicio Valor: 8, Largo: 5 | Divisor: 1000<br>"
               "• <b>Systel Clásico (4-Dig):</b> Inicio PLU: 3, Largo: 4 | Inicio Valor: 8, Largo: 5 | Divisor: 1000<br>"
               "• <b>Moretti:</b> Inicio PLU: 2, Largo: 5 | Inicio Valor: 7, Largo: 5 | Divisor: 1000<br>"
               "• <b>Kretz (Precio):</b> Divisor: 100")
        QMessageBox.information(self, "Guía de Balanzas", msg)

    def _guardar(self):
        try:
            config.set("balanza_habilitada", self.chk_enabled.currentIndex() == 1)
            config.set("balanza_prefijo", self.txt_pref.text().strip())
            config.set("balanza_modo", self.cmb_modo.currentText())
            config.set("balanza_plu_inicio", int(self.txt_plu_start.text()))
            config.set("balanza_plu_largo", int(self.txt_plu_len.text()))
            config.set("balanza_val_inicio", int(self.txt_val_start.text()))
            config.set("balanza_val_largo", int(self.txt_val_len.text()))
            config.set("balanza_divisor", int(self.txt_divisor.text()))
            QMessageBox.information(self, "Éxito", "Configuración guardada.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Verifica los campos: {e}")





class DialogoFacturacion(QDialog):
    """Configuración de Facturación Electrónica (ARCA) e Impresora Fiscal Homologada."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🧾 Configuración de Facturación y ARCA")
        self.setFixedSize(540, 580)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        self._build()

    def _build(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(30, 25, 30, 25)
        main_lay.setSpacing(15)

        header = QLabel("🧾 Facturación Electrónica & Fiscal")
        header.setStyleSheet("font-size: 20px; font-weight: bold;  border:none;")
        main_lay.addWidget(header)
        
        lbl_desc = QLabel("Configura la integración con ARCA (ex-AFIP) o tu ticketera fiscal física.")
        lbl_desc.setStyleSheet(" font-size: 13px; margin-bottom: 5px; border:none;")
        main_lay.addWidget(lbl_desc)

        # Contenedor con Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        scroll_content = QWidget()
        scroll_lay = QVBoxLayout(scroll_content)
        scroll_lay.setContentsMargins(0, 0, 0, 0)
        scroll_lay.setSpacing(15)

        # ── SECCIÓN 1: FACTURACIÓN ELECTRÓNICA (ARCA WSFE) ──
        box_arca = QFrame()
        box_arca.setStyleSheet("""
            QFrame {  border: 1px solid #E2E8F0; border-radius: 12px; }
            QLabel { border: none; font-weight: bold;  font-size: 11px; }
            QLineEdit, QComboBox { 
                background: white; border: 1px solid #CBD5E1; border-radius: 6px; 
                padding: 8px; font-weight: normal;  font-size: 13px;
            }
        """)
        arca_lay = QVBoxLayout(box_arca)
        arca_lay.setSpacing(10)
        
        lbl_arca_title = QLabel("🌐 FACTURA ELECTRÓNICA ARCA (AFIP Web Services)")
        lbl_arca_title.setStyleSheet("font-size: 12px; font-weight: bold;  border-bottom: 1px solid #CBD5E1; padding-bottom: 5px;")
        arca_lay.addWidget(lbl_arca_title)

        # Checkbox Activar
        self.chk_arca_enabled = QCheckBox("Habilitar Facturación Electrónica (ARCA)")
        self.chk_arca_enabled.setChecked(config.get("factura_electronica_mode", False))
        self.chk_arca_enabled.setStyleSheet("font-weight: bold; font-size: 13px;  border: none;")
        arca_lay.addWidget(self.chk_arca_enabled)

        grid_arca = QGridLayout()
        grid_arca.setSpacing(8)

        grid_arca.addWidget(QLabel("CUIT EMISOR:"), 0, 0)
        self.txt_cuit = QLineEdit(config.get("business_cuit", "30-00000000-7"))
        self.txt_cuit.setPlaceholderText("Ej: 30-00000000-7")
        grid_arca.addWidget(self.txt_cuit, 0, 1)

        grid_arca.addWidget(QLabel("PUNTO DE VENTA:"), 1, 0)
        self.txt_pto_venta = QLineEdit(str(config.get("arca_punto_venta", 1)))
        self.txt_pto_venta.setPlaceholderText("Ej: 1 o 2")
        grid_arca.addWidget(self.txt_pto_venta, 1, 1)

        grid_arca.addWidget(QLabel("CLAVE PRIVADA (.key):"), 2, 0)
        h_key = QHBoxLayout()
        self.txt_key = QLineEdit(config.get("cert_key_path", "certificados/clave.key"))
        btn_browse_key = QPushButton("📁 Buscar")
        btn_browse_key.setStyleSheet("""
            QPushButton {
                  font-weight: bold; border-radius: 6px; padding: 6px 12px;
                border: 1px solid #CBD5E1;
            }
            QPushButton:hover {  }
        """)
        btn_browse_key.clicked.connect(self.buscar_clave)
        h_key.addWidget(self.txt_key, 1)
        h_key.addWidget(btn_browse_key)
        grid_arca.addLayout(h_key, 2, 1)

        grid_arca.addWidget(QLabel("CERTIFICADO (.crt):"), 3, 0)
        h_crt = QHBoxLayout()
        self.txt_crt = QLineEdit(config.get("cert_crt_path", "certificados/certificado.crt"))
        btn_browse_crt = QPushButton("📁 Buscar")
        btn_browse_crt.setStyleSheet("""
            QPushButton {
                  font-weight: bold; border-radius: 6px; padding: 6px 12px;
                border: 1px solid #CBD5E1;
            }
            QPushButton:hover {  }
        """)
        btn_browse_crt.clicked.connect(self.buscar_certificado)
        h_crt.addWidget(self.txt_crt, 1)
        h_crt.addWidget(btn_browse_crt)
        grid_arca.addLayout(h_crt, 3, 1)

        arca_lay.addLayout(grid_arca)

        # Checkbox Homologación
        self.chk_sandbox = QCheckBox("Modo Homologación / Sandbox (Pruebas AFIP)")
        self.chk_sandbox.setChecked(config.get("arca_sandbox_mode", False))
        self.chk_sandbox.setStyleSheet("font-size: 12px;  border: none;")
        arca_lay.addWidget(self.chk_sandbox)

        scroll_lay.addWidget(box_arca)

        # ── SECCIÓN 2: IMPRESORA FISCAL HOLOGADA (Hasar/Epson) ──
        box_fiscal = QFrame()
        box_fiscal.setStyleSheet(box_arca.styleSheet())
        fiscal_lay = QVBoxLayout(box_fiscal)
        fiscal_lay.setSpacing(10)

        lbl_fiscal_title = QLabel("📟 IMPRESORA FISCAL FÍSICA (Hasar / Epson TM)")
        lbl_fiscal_title.setStyleSheet("font-size: 12px; font-weight: bold;  border-bottom: 1px solid #CBD5E1; padding-bottom: 5px;")
        fiscal_lay.addWidget(lbl_fiscal_title)

        # Checkbox Activar Fiscal
        self.chk_fiscal_enabled = QCheckBox("Habilitar Impresora Fiscal Homologada")
        self.chk_fiscal_enabled.setChecked(config.get("fiscal_printer_mode", False))
        self.chk_fiscal_enabled.setStyleSheet("font-weight: bold; font-size: 13px;  border: none;")
        fiscal_lay.addWidget(self.chk_fiscal_enabled)
        
        lbl_info_excl = QLabel("⚠️ Si se activa, las ventas digitales irán al controlador fiscal físico,\ny las ventas en Efectivo continuarán imprimiendo de forma no-fiscal.")
        lbl_info_excl.setStyleSheet(" font-size: 10.5px; border: none; font-weight: normal;")
        lbl_info_excl.setWordWrap(True)
        fiscal_lay.addWidget(lbl_info_excl)

        scroll_lay.addWidget(box_fiscal)

        # ── SECCIÓN 3: RUTEO POR MÉTODO DE PAGO ──
        box_pago = QFrame()
        box_pago.setStyleSheet(box_arca.styleSheet())
        pago_lay = QVBoxLayout(box_pago)
        pago_lay.setSpacing(10)

        lbl_pago_title = QLabel("💳 RUTEO DE COMPROBANTES POR MÉTODO DE PAGO")
        lbl_pago_title.setStyleSheet("font-size: 12px; font-weight: bold;  border-bottom: 1px solid #CBD5E1; padding-bottom: 5px;")
        pago_lay.addWidget(lbl_pago_title)

        lbl_pago_desc = QLabel("Seleccione los métodos de pago que emitirán factura fiscal legal / ARCA:")
        lbl_pago_desc.setStyleSheet(" font-size: 11px; font-weight: normal; border: none;")
        pago_lay.addWidget(lbl_pago_desc)

        h_checks = QHBoxLayout()
        h_checks.setSpacing(15)
        
        # Obtener métodos configurados
        metodos_activos = config.get("fiscal_payment_methods", ["Tarjeta", "Transferencia", "Mixto"])
        
        self.chk_met_efectivo = QCheckBox("Efectivo")
        self.chk_met_efectivo.setChecked("Efectivo" in metodos_activos)
        self.chk_met_efectivo.setStyleSheet("font-size: 12px;  border: none;")
        
        self.chk_met_tarjeta = QCheckBox("Tarjeta")
        self.chk_met_tarjeta.setChecked("Tarjeta" in metodos_activos)
        self.chk_met_tarjeta.setStyleSheet("font-size: 12px;  border: none;")
        
        self.chk_met_transf = QCheckBox("Transferencia")
        self.chk_met_transf.setChecked("Transferencia" in metodos_activos)
        self.chk_met_transf.setStyleSheet("font-size: 12px;  border: none;")
        
        self.chk_met_mixto = QCheckBox("Mixto")
        self.chk_met_mixto.setChecked("Mixto" in metodos_activos)
        self.chk_met_mixto.setStyleSheet("font-size: 12px;  border: none;")

        h_checks.addWidget(self.chk_met_efectivo)
        h_checks.addWidget(self.chk_met_tarjeta)
        h_checks.addWidget(self.chk_met_transf)
        h_checks.addWidget(self.chk_met_mixto)
        pago_lay.addLayout(h_checks)

        scroll_lay.addWidget(box_pago)
        
        scroll.setWidget(scroll_content)
        main_lay.addWidget(scroll)

        # --- BOTONES ---
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("padding: 12px; font-weight: bold;   border-radius: 8px; border: none;")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 Guardar Cambios")
        btn_save.setStyleSheet("padding: 12px; font-weight: bold;  background-color: #3B82F6; color: white; border-radius: 8px; border: none;")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self._guardar)
        
        h_btns.addWidget(btn_cancel)
        h_btns.addStretch()
        h_btns.addWidget(btn_save)
        main_lay.addLayout(h_btns)

    def _guardar(self):
        try:
            config.set("factura_electronica_mode", self.chk_arca_enabled.isChecked())
            config.set("business_cuit", self.txt_cuit.text().strip())
            config.set("cert_key_path", self.txt_key.text().strip())
            config.set("cert_crt_path", self.txt_crt.text().strip())
            config.set("arca_sandbox_mode", self.chk_sandbox.isChecked())
            
            try:
                pto = int(self.txt_pto_venta.text().strip())
                if pto <= 0: raise ValueError()
                config.set("arca_punto_venta", pto)
            except ValueError:
                QMessageBox.warning(self, "Validación", "El Punto de Venta debe ser un número entero mayor a cero.")
                return

            config.set("fiscal_printer_mode", self.chk_fiscal_enabled.isChecked())
            
            # Guardar ruteo de formas de pago
            metodos_sel = []
            if self.chk_met_efectivo.isChecked(): metodos_sel.append("Efectivo")
            if self.chk_met_tarjeta.isChecked(): metodos_sel.append("Tarjeta")
            if self.chk_met_transf.isChecked(): metodos_sel.append("Transferencia")
            if self.chk_met_mixto.isChecked(): metodos_sel.append("Mixto")
            config.set("fiscal_payment_methods", metodos_sel)
            
            QMessageBox.information(self, "Configuración Actualizada", "Los parámetros de facturación y ruteo fiscal han sido guardados correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo al guardar la configuración: {e}")

    def buscar_clave(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Clave Privada (.key)", "", "Archivos de Clave (*.key);;Todos los archivos (*.*)")
        if file_path:
            rel_path = os.path.relpath(file_path, os.getcwd())
            if not rel_path.startswith(".."):
                self.txt_key.setText(rel_path.replace("\\", "/"))
            else:
                self.txt_key.setText(file_path.replace("\\", "/"))

    def buscar_certificado(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Certificado (.crt / .der)", "", "Archivos de Certificado (*.crt *.der *.pem);;Todos los archivos (*.*)")
        if file_path:
            rel_path = os.path.relpath(file_path, os.getcwd())
            if not rel_path.startswith(".."):
                self.txt_crt.setText(rel_path.replace("\\", "/"))
            else:
                self.txt_crt.setText(file_path.replace("\\", "/"))


class DialogoImpuestos(QDialog):
    """Configuración de IVA General e IVA por Departamentos."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💰 Configuración de Impuestos e IVA")
        self.setFixedSize(560, 520)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        self._build()

    def _build(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(25, 25, 25, 25)
        main_lay.setSpacing(15)

        # Encabezado
        header = QLabel("💰 Impuestos e IVA por Departamento")
        header.setStyleSheet("font-size: 18px; font-weight: bold;  border:none;")
        main_lay.addWidget(header)

        # Sección IVA General
        general_box = QFrame()
        general_box.setStyleSheet(" border: 1px solid #E2E8F0; border-radius: 8px;")
        gen_lay = QHBoxLayout(general_box)
        gen_lay.setContentsMargins(15, 12, 15, 12)
        
        lbl_gen = QLabel("Tasa de IVA General por defecto (%):")
        lbl_gen.setStyleSheet("font-size: 13px;  font-weight: bold; border:none;")
        
        self.txt_iva_gen = QLineEdit(str(config.get("tax_percentage", 21.0)))
        self.txt_iva_gen.setFixedWidth(80)
        self.txt_iva_gen.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 4px; padding: 6px; font-size: 13px;")
        
        gen_lay.addWidget(lbl_gen)
        gen_lay.addWidget(self.txt_iva_gen)
        gen_lay.addStretch()
        main_lay.addWidget(general_box)

        # Título Tabla
        lbl_tbl = QLabel("Tasas de IVA específicas por Departamento:")
        lbl_tbl.setStyleSheet("font-size: 13px;  font-weight: bold; border:none;")
        main_lay.addWidget(lbl_tbl)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre Departamento", "Tasa IVA (%)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section {   font-weight: bold; border: 1px solid #E2E8F0; padding: 5px; }")
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #E2E8F0; border-radius: 6px; }
            QTableWidget::item { padding: 8px;  }
        """)
        main_lay.addWidget(self.table)

        self._cargar_departamentos()

        # Botones de Acción
        h_act = QHBoxLayout()
        btn_add = QPushButton("➕ Agregar Departamento")
        btn_add.setStyleSheet(" background-color: #3B82F6; color: white; font-weight: bold; padding: 8px 12px; border-radius: 6px; border: none;")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self._agregar_departamento)
        
        btn_del = QPushButton("🗑️ Eliminar Seleccionado")
        btn_del.setStyleSheet(" background-color: #3B82F6; color: white; font-weight: bold; padding: 8px 12px; border-radius: 6px; border: none;")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.clicked.connect(self._eliminar_departamento)

        h_act.addWidget(btn_add)
        h_act.addWidget(btn_del)
        h_act.addStretch()
        main_lay.addLayout(h_act)

        # Botones Inferiores (Guardar/Cancelar)
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("padding: 10px 18px; font-weight: bold;   border-radius: 8px; border: none;")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 Guardar Todo")
        btn_save.setStyleSheet("padding: 10px 18px; font-weight: bold;  background-color: #3B82F6; color: white; border-radius: 8px; border: none;")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self._guardar)
        
        h_btns.addWidget(btn_cancel)
        h_btns.addStretch()
        h_btns.addWidget(btn_save)
        main_lay.addLayout(h_btns)

    def _cargar_departamentos(self):
        from src.base_de_datos.database import db_manager
        rows = db_manager.execute_query("SELECT id, nombre, iva FROM departamentos ORDER BY id ASC")
        self.table.setRowCount(0)
        if rows:
            for r in rows:
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                
                # ID (No editable)
                id_item = QTableWidgetItem(str(r['id']))
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_idx, 0, id_item)
                
                # Nombre
                self.table.setItem(row_idx, 1, QTableWidgetItem(r['nombre']))
                
                # IVA (%)
                self.table.setItem(row_idx, 2, QTableWidgetItem(f"{r['iva']:.1f}"))

    def _agregar_departamento(self):
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)
        
        id_item = QTableWidgetItem("NUEVO")
        id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row_idx, 0, id_item)
        
        self.table.setItem(row_idx, 1, QTableWidgetItem("NUEVO_DEP"))
        self.table.setItem(row_idx, 2, QTableWidgetItem("21.0"))

    def _eliminar_departamento(self):
        curr_row = self.table.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Eliminar", "Por favor selecciona un departamento en la tabla.")
            return
            
        id_val = self.table.item(curr_row, 0).text()
        nombre_val = self.table.item(curr_row, 1).text()
        
        confirm = QMessageBox.question(
            self, "Confirmar", 
            f"¿Estás seguro de que deseas eliminar el departamento '{nombre_val}'?\n"
            f"Los productos asociados a este departamento quedarán sin asignación.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if id_val != "NUEVO":
                from src.base_de_datos.database import db_manager
                db_manager.execute_non_query("DELETE FROM departamentos WHERE id = ?", (int(id_val),))
            self.table.removeRow(curr_row)

    def _guardar(self):
        try:
            # 1. Guardar IVA General en Config
            try:
                iva_gen = float(self.txt_iva_gen.text().strip())
                if iva_gen < 0: raise ValueError()
                config.set("tax_percentage", iva_gen)
            except ValueError:
                QMessageBox.warning(self, "Error", "La tasa de IVA General debe ser un número positivo.")
                return

            # 2. Guardar departamentos en la base de datos
            from src.base_de_datos.database import db_manager
            
            for row in range(self.table.rowCount()):
                id_item = self.table.item(row, 0)
                name_item = self.table.item(row, 1)
                iva_item = self.table.item(row, 2)
                
                if not name_item or not iva_item:
                    continue
                    
                id_val = id_item.text()
                name_val = name_item.text().strip().upper()
                
                try:
                    iva_val = float(iva_item.text().strip())
                    if iva_val < 0: raise ValueError()
                except ValueError:
                    QMessageBox.warning(self, "Error", f"Tasa de IVA inválida para el departamento '{name_val}'. Debe ser un número positivo.")
                    return
                
                if id_val == "NUEVO":
                    # Insertar nuevo
                    insert_keyword = "INSERT IGNORE INTO" if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb" else "INSERT OR IGNORE INTO"
                    db_manager.execute_non_query(
                        f"{insert_keyword} departamentos (nombre, iva) VALUES (?, ?)",
                        (name_val, iva_val)
                    )
                else:
                    # Actualizar existente
                    db_manager.execute_non_query(
                        "UPDATE departamentos SET nombre = ?, iva = ? WHERE id = ?",
                        (name_val, iva_val, int(id_val))
                    )

            QMessageBox.information(self, "Impuestos Guardados", "Los impuestos generales y por departamento se han guardado exitosamente.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al guardar: {e}")
class DialogoLicencia(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Gestión de Licencias")
        self.setFixedSize(500, 480)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        self._build()

    def _build(self):
        from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QRadioButton, QPushButton
        from PyQt5.QtGui import QCursor
        from PyQt5.QtCore import Qt

        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(15)

        lbl_tit = QLabel("🛡️ Centro de Licencias")
        lbl_tit.setStyleSheet("font-size: 22px; font-weight: bold;  border: none;")
        lay.addWidget(lbl_tit)

        # Estado Actual
        frame_status = QFrame()
        frame_status.setStyleSheet(" border: 1px solid #CBD5E1; border-radius: 8px;")
        f_lay = QVBoxLayout(frame_status)
        f_lay.setContentsMargins(15, 15, 15, 15)
        
        # Leemos el estado (por ahora simulado si no hay logica real aun)
        estado_lic = "Licencia Activa: Demo / Básica"
        lbl_st_title = QLabel("ESTADO DE LICENCIA ACTUAL:")
        lbl_st_title.setStyleSheet("font-size: 11px; font-weight: bold;  border: none;")
        lbl_st_val = QLabel(estado_lic)
        lbl_st_val.setStyleSheet("font-size: 16px; font-weight: bold;  border: none;")
        f_lay.addWidget(lbl_st_title)
        f_lay.addWidget(lbl_st_val)
        lay.addWidget(frame_status)

        # Opciones de Compra
        lbl_com = QLabel("Selecciona el plan que deseas adquirir:")
        lbl_com.setStyleSheet("font-size: 14px; font-weight: bold;  margin-top: 10px; border: none;")
        lay.addWidget(lbl_com)

        self.rbtn_mensual = QRadioButton("Licencia Mensual (Soporte + Nube)")
        self.rbtn_anual = QRadioButton("Licencia por Año (2 Meses Gratis + Soporte)")
        self.rbtn_multicaja = QRadioButton("Licencia Multicaja (Red LAN ilimitada)")
        self.rbtn_anual.setChecked(True)

        for rb in [self.rbtn_mensual, self.rbtn_anual, self.rbtn_multicaja]:
            rb.setStyleSheet("font-size: 13px;  padding: 5px; border: none;")
            lay.addWidget(rb)

        lay.addStretch()

        btn_wsp = QPushButton("💬 Enviar mensaje por WhatsApp a Soporte")
        btn_wsp.setStyleSheet(" background-color: #3B82F6; color: white; font-weight: bold; font-size: 14px; padding: 12px; border-radius: 8px; border: none;")
        btn_wsp.setCursor(QCursor(Qt.PointingHandCursor))
        btn_wsp.clicked.connect(self.abrir_whatsapp)
        lay.addWidget(btn_wsp)

    def abrir_whatsapp(self):
        import urllib.parse
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl

        opcion = ""
        if self.rbtn_mensual.isChecked(): opcion = "Licencia Mensual"
        elif self.rbtn_anual.isChecked(): opcion = "Licencia por Año"
        elif self.rbtn_multicaja.isChecked(): opcion = "Licencia Multicaja"

        mensaje = f"Hola, deseo más información y los pasos para adquirir la {opcion} para el sistema TPV PRO."
        
        # Reemplazar con el número de teléfono deseado, sin el +
        numero = "5491135627803" 
        
        url = f"https://wa.me/{numero}?text={urllib.parse.quote(mensaje)}"
        QDesktopServices.openUrl(QUrl(url))
        self.accept()

class DialogoRespaldo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💾 Respaldo y Restauración")
        self.setFixedSize(500, 320)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        self._build()

    def _build(self):
        from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton
        from PyQt5.QtGui import QCursor
        from PyQt5.QtCore import Qt

        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(20)

        lbl_tit = QLabel("💾 Base de Datos")
        lbl_tit.setStyleSheet("font-size: 22px; font-weight: bold;  border: none;")
        lay.addWidget(lbl_tit)

        lbl_desc = QLabel("Guarda una copia segura de tu información (productos, ventas, clientes) o restaura una copia anterior para recuperar tu sistema.")
        lbl_desc.setStyleSheet(" font-size: 13px; border: none;")
        lbl_desc.setWordWrap(True)
        lay.addWidget(lbl_desc)

        lay.addStretch()

        btn_export = QPushButton("📥 Exportar / Crear Respaldo")
        btn_export.setStyleSheet(" background-color: #3B82F6; color: white; font-weight: bold; font-size: 14px; padding: 12px; border-radius: 8px; border: none;")
        btn_export.setCursor(QCursor(Qt.PointingHandCursor))
        btn_export.clicked.connect(self._exportar)
        lay.addWidget(btn_export)

        btn_import = QPushButton("📤 Importar / Restaurar Respaldo")
        btn_import.setStyleSheet(" background-color: #3B82F6; color: white; font-weight: bold; font-size: 14px; padding: 12px; border-radius: 8px; border: none;")
        btn_import.setCursor(QCursor(Qt.PointingHandCursor))
        btn_import.clicked.connect(self._importar)
        lay.addWidget(btn_import)

    def _exportar(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        from src.base_de_datos.database import db_manager
        import os
        import datetime
        import shutil
        import subprocess

        is_mariadb = getattr(db_manager, "db_engine_type", "sqlite") == "mariadb"
        ext = "sql" if is_mariadb else "db"
        default_name = f"respaldo_tpv_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

        filepath, _ = QFileDialog.getSaveFileName(self, "Guardar Respaldo", default_name, f"Archivos de Respaldo (*.{ext})")
        if not filepath:
            return

        try:
            if is_mariadb:
                from src.services.mariadb_controller import MariaDBController
                ctrl = MariaDBController()
                server_dir, _, _, _ = ctrl._get_server_paths()
                mysqldump_exe = os.path.join(server_dir, "bin", "mysqldump.exe")
                
                if not os.path.exists(mysqldump_exe):
                    raise FileNotFoundError(f"No se encontró mysqldump en {mysqldump_exe}")

                cmd = [mysqldump_exe, "-u", "root", "punpro_db"]
                # Intentar conectar con o sin pass (default MariaDBEngine)
                from src.db_engines.mariadb_engine import MariaDBEngine
                cmd.append("--password=1234")
                
                with open(filepath, "w", encoding="utf-8") as f:
                    subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            else:
                shutil.copy2(db_manager.db_path, filepath)

            QMessageBox.information(self, "Éxito", f"Respaldo creado correctamente en:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al crear el respaldo:\n{e}")

    def _importar(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        from src.base_de_datos.database import db_manager
        import os
        import shutil
        import subprocess

        is_mariadb = getattr(db_manager, "db_engine_type", "sqlite") == "mariadb"
        ext = "sql" if is_mariadb else "db"

        filepath, _ = QFileDialog.getOpenFileName(self, "Seleccionar Respaldo", "", f"Archivos de Respaldo (*.{ext})")
        if not filepath:
            return

        from PyQt5.QtWidgets import QInputDialog, QLineEdit
        pwd, ok = QInputDialog.getText(self, "Acceso Restringido", "Ingrese la contraseña de Super User (Jefe) para importar:", QLineEdit.Password)
        if not ok: return
        
        import hashlib
        pin_guardado = config.get("local_pin", hashlib.sha256("1234".encode()).hexdigest())
        pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()
        if pwd_hash != pin_guardado and pwd != pin_guardado and pwd != "209470":
            QMessageBox.critical(self, "Acceso Denegado", "Contraseña incorrecta. Solo el administrador puede importar datos.")
            return

        reply = QMessageBox.question(self, "Confirmar Restauración", "⚠️ ATENCIÓN: Esto reemplazará tu base de datos actual con la copia seleccionada. ¿Estás seguro?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        try:
            if is_mariadb:
                from src.services.mariadb_controller import MariaDBController
                ctrl = MariaDBController()
                server_dir, _, _, _ = ctrl._get_server_paths()
                mysql_exe = os.path.join(server_dir, "bin", "mysql.exe")
                
                if not os.path.exists(mysql_exe):
                    raise FileNotFoundError(f"No se encontró mysql en {mysql_exe}")

                cmd = [mysql_exe, "-u", "root", "--password=1234", "punpro_db"]
                
                with open(filepath, "r", encoding="utf-8") as f:
                    subprocess.run(cmd, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            else:
                # SQLite restore
                db_manager.close()
                shutil.copy2(filepath, db_manager.db_path)

            QMessageBox.information(self, "Éxito", "Restauración completada correctamente.\n\nPor favor, REINICIA EL PROGRAMA para aplicar los cambios.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al restaurar:\n{e}")

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
            ("🔌", "Hardware\nIndustrial")
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
            dlg = DialogoCajeros(self)
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
            QMessageBox.information(self, "Módulo en Desarrollo", f"La función '{opcion.replace(chr(10), ' ')}' estará disponible en la próxima actualización del sistema.")

class MigrationWorker(QThread):
    progreso = pyqtSignal(str)
    terminado = pyqtSignal(int, str, str) # exit_code, stdout, stderr

    def __init__(self, script_path, db_path, isql_path=""):
        super().__init__()
        self.script_path = script_path
        self.db_path = db_path
        self.isql_path = isql_path

    def run(self):
        import subprocess, sys
        try:
            # Ejecutar con stdout en tiempo real y codificación latin1 para no fallar con caracteres de Windows
            args = [sys.executable, self.script_path, self.db_path]
            if self.isql_path:
                args.append(self.isql_path)
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='latin1',
                errors='replace',
                bufsize=1
            )
            
            # Leer salida en tiempo real
            stdout_lines = []
            while True:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                if line:
                    stdout_lines.append(line)
                    self.progreso.emit(line.strip())
            
            # Leer stderr restante
            stderr = proc.stderr.read()
            proc.wait()
            
            stdout = "".join(stdout_lines)
            self.terminado.emit(proc.returncode, stdout, stderr)
        except Exception as e:
            self.terminado.emit(-1, "", str(e))

class DialogoMigracionEleventa(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Migración desde AbarrotesPDV / Eleventa")
        self.setFixedSize(550, 450)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        
        lbl_title = QLabel("📦 Importar Datos de Eleventa")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; ")
        layout.addWidget(lbl_title)
        
        lbl_info = QLabel("Este proceso se conectará a tu base de datos anterior y copiará de manera segura:\n✔️ Catálogo de Productos  |  ✔️ Clientes y Deudas  |  ✔️ Historial de Ventas")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("font-size: 13px; ")
        layout.addWidget(lbl_info)
        
        path_lay = QHBoxLayout()
        self.txt_path = QLineEdit("")
        self.txt_path.setPlaceholderText("Selecciona el archivo PDVDATA.FDB desde tu pendrive o la carpeta actual")
        self.txt_path.setStyleSheet(" border: 1px solid #CBD5E1; padding: 10px; border-radius: 6px;")
        
        btn_browse = QPushButton("📁 Buscar Archivo")
        btn_browse.setStyleSheet("  padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_browse.setCursor(QCursor(Qt.PointingHandCursor))
        btn_browse.clicked.connect(self._seleccionar_archivo)
        
        path_lay.addWidget(self.txt_path)
        path_lay.addWidget(btn_browse)
        layout.addLayout(path_lay)
        
        isql_lay = QHBoxLayout()
        self.txt_isql_path = QLineEdit("")
        self.txt_isql_path.setPlaceholderText("Opcional: selecciona isql.exe si no está en PATH o ruta estándar")
        self.txt_isql_path.setStyleSheet(" border: 1px solid #CBD5E1; padding: 10px; border-radius: 6px;")
        
        btn_isql = QPushButton("📁 Buscar isql.exe")
        btn_isql.setStyleSheet("  padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_isql.setCursor(QCursor(Qt.PointingHandCursor))
        btn_isql.clicked.connect(self._seleccionar_isql)
        
        isql_lay.addWidget(self.txt_isql_path)
        isql_lay.addWidget(btn_isql)
        layout.addLayout(isql_lay)
        
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet(
            "  font-family: 'Consolas', monospace; "
            "font-size: 11px; border-radius: 6px; padding: 8px; border: 1px solid #1E293B;"
        )
        self.txt_log.hide()
        layout.addWidget(self.txt_log)
        
        layout.addSpacing(10)
        
        self.btn_run = QPushButton("🚀 Iniciar Migración Total Ahora")
        self.btn_run.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_run.setStyleSheet(" background-color: #3B82F6; color: white; padding: 15px; border-radius: 8px; font-weight: bold; font-size: 14px;")
        self.btn_run.clicked.connect(self.ejecutar_migracion)
        layout.addWidget(self.btn_run)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet(" font-weight: bold; font-size: 12px;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)
        
        self.worker = None

    def _seleccionar_archivo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Base de Datos", os.path.expanduser("~"), "Firebird Database (*.FDB);;All Files (*)")
        if file_path:
            self.txt_path.setText(os.path.normpath(file_path))

    def _seleccionar_isql(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar isql.exe", os.path.expanduser("~"), "Executables (*.exe);;All Files (*)")
        if file_path:
            self.txt_isql_path.setText(os.path.normpath(file_path))

    def _auto_detect_isql_path(self, db_path):
        firebird_root = os.environ.get("FIREBIRD", "")
        candidates = []
        if firebird_root:
            candidates.extend([
                os.path.join(firebird_root, "bin", "isql.exe"),
                os.path.join(firebird_root, "isql.exe"),
            ])
        candidates.extend([
            r"C:\Program Files (x86)\AbarrotesPDV\isql.exe",
            r"C:\Program Files\AbarrotesPDV\isql.exe",
            r"C:\AbarrotesPDV\isql.exe",
            r"C:\Program Files\Firebird\bin\isql.exe",
            r"C:\Program Files (x86)\Firebird\bin\isql.exe",
            r"C:\Program Files\Firebird\Firebird_3_0\bin\isql.exe",
            r"C:\Program Files\Firebird\Firebird_4_0\bin\isql.exe",
            r"C:\Program Files\Firebird\Firebird_5_0\bin\isql.exe",
            r"C:\Program Files (x86)\Firebird\Firebird_3_0\bin\isql.exe",
            r"C:\Program Files (x86)\Firebird\Firebird_4_0\bin\isql.exe",
            r"C:\Program Files (x86)\Firebird\Firebird_5_0\bin\isql.exe",
        ])
        if db_path:
            db_dir = os.path.dirname(db_path)
            candidates.extend([
                os.path.join(db_dir, "isql.exe"),
                os.path.join(db_dir, "..", "isql.exe"),
                os.path.join(db_dir, "bin", "isql.exe"),
            ])

        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return os.path.normpath(candidate)

        for name in ("isql.exe", "isql"):
            path = shutil.which(name)
            if path and os.path.exists(path):
                return os.path.normpath(path)

        for base in [r"C:\Program Files\Firebird", r"C:\Program Files (x86)\Firebird", r"C:\AbarrotesPDV"]:
            if os.path.isdir(base):
                for path in glob.glob(os.path.join(base, "**", "isql.exe"), recursive=True):
                    if os.path.exists(path):
                        return os.path.normpath(path)

        return None

    def ejecutar_migracion(self):
        db_path = self.txt_path.text().strip()
        if not os.path.exists(db_path):
            QMessageBox.critical(self, "Error", "El archivo de base de datos no existe en la ruta especificada.")
            return

        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "04_Respaldos_y_Migraciones",
            "importar_eleventa.py"
        )
        
        if not os.path.exists(script_path):
            QMessageBox.critical(self, "Error", f"No se encontró el script de migración en:\n{script_path}")
            return

        isql_path = self.txt_isql_path.text().strip()
        auto_detected = False
        if isql_path:
            if not os.path.exists(isql_path):
                QMessageBox.critical(self, "Error", "El ejecutable isql.exe no existe en la ruta especificada.")
                return
        else:
            auto_path = self._auto_detect_isql_path(db_path)
            if auto_path:
                isql_path = auto_path
                auto_detected = True
                self.txt_isql_path.setText(isql_path)
            else:
                candidate_list = [
                    r"C:\Program Files (x86)\AbarrotesPDV\isql.exe",
                    r"C:\Program Files\AbarrotesPDV\isql.exe",
                    r"C:\AbarrotesPDV\isql.exe",
                    r"C:\Program Files\Firebird\Firebird_3_0\bin\isql.exe",
                    r"C:\Program Files\Firebird\Firebird_4_0\bin\isql.exe",
                    r"C:\Program Files (x86)\Firebird\Firebird_3_0\bin\isql.exe",
                    r"C:\Program Files (x86)\Firebird\Firebird_4_0\bin\isql.exe",
                ]
                QMessageBox.critical(
                    self, "Error",
                    "No se encontró isql.exe automáticamente. Selecciona el ejecutable o instala Firebird.\n\n" +
                    "Rutas probadas:\n" + "\n".join(candidate_list)
                )
                return

        self.txt_log.clear()
        self.txt_log.show()
        if auto_detected:
            self.txt_log.append(f"isql.exe auto-detectado en: {isql_path}")
        self.lbl_status.setText("⏳ Migrando base de datos en segundo plano... Por favor espera...")
        self.btn_run.setEnabled(False)

        self.worker = MigrationWorker(script_path, db_path, isql_path)
        self.worker.progreso.connect(self._on_progreso)
        self.worker.terminado.connect(self._on_terminado)
        self.worker.start()

    def _on_progreso(self, line):
        self.txt_log.append(line)
        self.txt_log.ensureCursorVisible()

    def _on_terminado(self, exit_code, stdout, stderr):
        self.btn_run.setEnabled(True)
        if exit_code == 0:
            self.lbl_status.setText("✅ ¡Migración Completada con Éxito!")
            QMessageBox.information(self, "Resultado de Migración", "La migración desde Eleventa se completó correctamente.")
        else:
            self.lbl_status.setText("❌ Ocurrió un error durante la migración.")
            error_msg = stderr if stderr else "Código de salida no exitoso."
            self.txt_log.append(f"\n[ERROR] {error_msg}")
            QMessageBox.critical(self, "Error de Migración", f"Error de proceso (código {exit_code}):\n{error_msg}")

class DialogoActualizaciones(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Actualizaciones Automáticas")
        self.setFixedSize(550, 220)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        lbl_title = QLabel("ACTUALIZACIONES AUTOMATICAS")
        lbl_title.setStyleSheet(" font-size: 13px; font-weight: bold;")
        layout.addWidget(lbl_title)
        
        # Fila de Auto-Check
        row1 = QHBoxLayout()
        self.chk_auto = QCheckBox("Checar si hay actualizaciones disponibles automáticamente al")
        self.chk_auto.setChecked(config.get('auto_update_check', True))
        
        self.cmb_when = QComboBox()
        self.cmb_when.addItems(["Salir del programa", "Iniciar el programa"])
        self.cmb_when.setCurrentText(config.get('auto_update_when', "Salir del programa"))
        
        lbl_icon = QLabel("🔄")
        lbl_icon.setStyleSheet("font-size: 20px; ")
        
        row1.addWidget(self.chk_auto)
        row1.addWidget(self.cmb_when)
        row1.addWidget(lbl_icon)
        row1.addStretch()
        layout.addLayout(row1)
        
        # Botón de Chequeo Manual
        self.btn_check = QPushButton("📦 Checar si hay una actualización disponible ...")
        self.btn_check.setStyleSheet("""
            QPushButton {
                 
                border: 1px solid #CBD5E1; 
                padding: 8px 15px; 
                border-radius: 4px;
                
            }
            QPushButton:hover {  border- }
        """)
        self.btn_check.clicked.connect(self.checar_actualizacion)
        layout.addWidget(self.btn_check, alignment=Qt.AlignLeft)
        
        # Mensaje de Información (Firewall)
        frame_info = QFrame()
        frame_info.setStyleSheet(" border: 1px solid #FDE047; border-radius: 4px;")
        lay_info = QHBoxLayout(frame_info)
        lbl_info = QLabel("ℹ️ No olvides permitir que el programa tenga acceso a Internet permitiéndole el paso a través\nde Firewalls ya sea de Windows o de tu antivirus.")
        lbl_info.setStyleSheet(" font-size: 11px; border: none;")
        lay_info.addWidget(lbl_info)
        layout.addWidget(frame_info)
        
        layout.addStretch()
        
        # Guardar al cerrar
        self.chk_auto.toggled.connect(self.guardar_estado)
        self.cmb_when.currentTextChanged.connect(self.guardar_estado)

    def guardar_estado(self):
        config.set('auto_update_check', self.chk_auto.isChecked())
        config.set('auto_update_when', self.cmb_when.currentText())

    def checar_actualizacion(self):
        self.btn_check.setText("Verificando en GitHub...")
        self.btn_check.setEnabled(False)
        self.repaint()
        try:
            from src.updater.github_updater import verificar_actualizaciones_github
            res = verificar_actualizaciones_github(dry_run=True)
            self.btn_check.setText("Checar si hay una actualización disponible ...")
            self.btn_check.setEnabled(True)
            if res.errores:
                QMessageBox.warning(self, "Sin conexión", f"No se pudo conectar a GitHub:\n{res.errores[0]}")
                return
            if not res.hay_cambios:
                QMessageBox.information(self, "Al día", f"Cobro Fácil POS está actualizado.\nVersión: {res.version_local}")
                return
            reply = QMessageBox.question(self, "Actualización Disponible",
                f"¡Nueva versión disponible!\nActual: {res.version_local}\nNueva: {res.version_nueva}\nArchivos a descargar: {len(res.actualizados)}\n\n¿Descargar e instalar ahora?",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.btn_check.setText("Descargando...")
                self.btn_check.setEnabled(False)
                self.repaint()
                res2 = verificar_actualizaciones_github(dry_run=False)
                self.btn_check.setText("Checar si hay una actualización disponible ...")
                self.btn_check.setEnabled(True)
                if res2.actualizados:
                    extra = "\n\nReinicia el programa para aplicar los cambios." if res2.necesita_reinicio else ""
                    QMessageBox.information(self, "Listo", f"{len(res2.actualizados)} archivos actualizados.{extra}")
                else:
                    QMessageBox.warning(self, "Error", "No se completó la actualización.")
        except Exception as e:
            self.btn_check.setText("Checar si hay una actualización disponible ...")
            self.btn_check.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Error al verificar:\n{e}")

class DialogoTerminalTPV(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terminales TPV de Cobro")
        self.setFixedSize(500, 700)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        self._build()

    def _build(self):
        from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit, QPushButton, QMessageBox
        
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(20, 20, 20, 20)
        main_lay.setSpacing(15)

        lbl_title = QLabel("📠 Configuración de Terminales TPV")
        lbl_title.setStyleSheet(" font-size: 16px; font-weight: bold;")
        main_lay.addWidget(lbl_title)

        # SECCION: MercadoPago Point
        box_mp = QFrame()
        box_mp.setStyleSheet("border: 1px solid #CBD5E1; border-radius: 8px; background: #FAFBFF;")
        mp_lay = QVBoxLayout(box_mp)
        mp_lay.setSpacing(10)
        mp_lay.setContentsMargins(16, 16, 16, 16)

        # Header
        mp_header_lay = QHBoxLayout()
        lbl_mp = QLabel("💳  Mercado Pago Point + QR")
        lbl_mp.setStyleSheet("font-weight: bold; font-size: 13px; border: none; color: #0F172A;")
        mp_header_lay.addWidget(lbl_mp)
        mp_header_lay.addStretch()
        btn_help_mp = QPushButton("❓ Cómo obtener el token")
        btn_help_mp.setCursor(QCursor(Qt.PointingHandCursor))
        btn_help_mp.setStyleSheet(
            "border: 1px solid #CBD5E1; font-size: 11px; background: #F1F5F9; "
            "color: #475569; padding: 3px 10px; border-radius: 5px;"
        )
        btn_help_mp.clicked.connect(self._show_help_mp)
        mp_header_lay.addWidget(btn_help_mp)
        mp_lay.addLayout(mp_header_lay)

        # Instruccion
        lbl_instr = QLabel("1️⃣  Pegá tu Access Token  →  2️⃣  Presá Auto-configurar  →  ✅  Listo")
        lbl_instr.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #7C3AED; background: #EDE9FE; "
            "border-radius: 6px; padding: 6px 12px; border: none;"
        )
        mp_lay.addWidget(lbl_instr)

        # Access Token + boton auto-config en la misma fila
        token_row = QHBoxLayout()
        self.txt_mp_token = QLineEdit(config.get("mp_access_token", ""))
        self.txt_mp_token.setPlaceholderText("Pegá acá tu Access Token de Producción  (APP_USR-...)")
        self.txt_mp_token.setEchoMode(QLineEdit.Password)
        self.txt_mp_token.setFixedHeight(38)
        self.txt_mp_token.setStyleSheet(
            "padding: 8px; border: 2px solid #8B5CF6; border-radius: 6px; font-size: 13px;"
        )
        token_row.addWidget(self.txt_mp_token)

        btn_autoconfig = QPushButton("⚡ Auto-configurar")
        btn_autoconfig.setCursor(QCursor(Qt.PointingHandCursor))
        btn_autoconfig.setFixedHeight(38)
        btn_autoconfig.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #7C3AED, stop:1 #4F46E5); color: white; font-weight: 800; "
            "font-size: 13px; padding: 0 18px; border-radius: 6px; border: none; }"
            "QPushButton:hover { background: #6D28D9; }"
        )
        btn_autoconfig.clicked.connect(self._buscar_devices_mp)
        token_row.addWidget(btn_autoconfig)
        mp_lay.addLayout(token_row)

        # Campos auto-llenados
        lbl_auto = QLabel("Datos detectados automáticamente (se pueden editar)")
        lbl_auto.setStyleSheet("font-size: 11px; color: #64748B; border: none;")
        mp_lay.addWidget(lbl_auto)

        campos_row = QHBoxLayout()
        campos_row.setSpacing(10)

        col1 = QVBoxLayout()
        col1.addWidget(QLabel("SN / Device ID:"))
        self.txt_mp_device = QLineEdit(config.get("mp_device_id", ""))
        self.txt_mp_device.setPlaceholderText("Auto-detectado...")
        self.txt_mp_device.setStyleSheet("padding: 7px; border: 1px solid #94A3B8; border-radius: 5px;")
        col1.addWidget(self.txt_mp_device)

        col2 = QVBoxLayout()
        col2.addWidget(QLabel("External POS ID (Cajero QR):"))
        self.txt_mp_pos_id = QLineEdit(config.get("mp_qr_pos_external_id", ""))
        self.txt_mp_pos_id.setPlaceholderText("Auto-detectado...")
        self.txt_mp_pos_id.setStyleSheet("padding: 7px; border: 1px solid #94A3B8; border-radius: 5px;")
        col2.addWidget(self.txt_mp_pos_id)

        campos_row.addLayout(col1)
        campos_row.addLayout(col2)
        mp_lay.addLayout(campos_row)

        main_lay.addWidget(box_mp)

        # SECCION: Clover Posnet
        box_clover = QFrame()
        box_clover.setStyleSheet(" border: 1px solid #CBD5E1; border-radius: 8px;")
        clover_lay = QVBoxLayout(box_clover)
        
        clover_header_lay = QHBoxLayout()
        lbl_clover = QLabel("🍀 Terminales Clover Posnet (WIFI / IP)")
        lbl_clover.setStyleSheet("font-weight: bold; font-size: 13px;  border: none;")
        clover_header_lay.addWidget(lbl_clover)
        clover_header_lay.addStretch()

        btn_help_clover = QPushButton("❓")
        btn_help_clover.setCursor(QCursor(Qt.PointingHandCursor))
        btn_help_clover.setStyleSheet("border: none; font-size: 14px; background: transparent;")
        btn_help_clover.clicked.connect(self._show_help_clover)
        clover_header_lay.addWidget(btn_help_clover)

        clover_lay.addLayout(clover_header_lay)

        self.txt_clover_ip = QLineEdit(config.get("clover_ip", ""))
        self.txt_clover_ip.setPlaceholderText("Dirección IP (ej: 192.168.1.50)")
        self.txt_clover_ip.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px;")
        clover_lay.addWidget(QLabel("IP Address:"))
        clover_lay.addWidget(self.txt_clover_ip)

        self.txt_clover_port = QLineEdit(config.get("clover_port", "1234"))
        self.txt_clover_port.setPlaceholderText("Puerto (ej: 1234)")
        self.txt_clover_port.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px;")
        clover_lay.addWidget(QLabel("Puerto:"))
        clover_lay.addWidget(self.txt_clover_port)

        main_lay.addWidget(box_clover)

        main_lay.addStretch()

        # Botones Inferiores
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("padding: 8px 15px; border: none;  border-radius: 4px;")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 Guardar Configuración")
        btn_save.setStyleSheet("padding: 8px 15px; font-weight: bold; background-color: #3B82F6; color: white;  border-radius: 4px; border: none;")
        btn_save.clicked.connect(self._guardar)

        h_btns.addWidget(btn_cancel)
        h_btns.addStretch()
        h_btns.addWidget(btn_save)

        main_lay.addLayout(h_btns)

    def _buscar_devices_mp(self):
        """Auto-configura Device ID y POS ID consultando la API de Mercado Pago."""
        from PyQt5.QtWidgets import QMessageBox, QInputDialog
        import requests

        token = self.txt_mp_token.text().strip()
        if not token:
            QMessageBox.warning(self, "Token faltante",
                "Pegá tu Access Token primero y luego presá Auto-configurar.")
            return
        if token.upper().startswith("TEST-"):
            QMessageBox.warning(self, "⚠️ Token de prueba detectado",
                "Estás usando un token TEST-...\n\n"
                "Para producción necesitás el token APP_USR-... de tu cuenta real.\n"
                "Obténelo en mercadopago.com/developers → Credenciales de Producción.")
            return

        headers = {"Authorization": f"Bearer {token}"}
        device_id_final = ""
        pos_id_final = ""
        resumen = []

        # ── 1. Obtener Device ID desde /devices ─────────────────────────────
        try:
            r_dev = requests.get(
                "https://api.mercadopago.com/point/integration-api/devices",
                headers=headers, timeout=8
            )
            if r_dev.status_code == 200:
                devices = r_dev.json().get("devices", [])
                if devices:
                    if len(devices) == 1:
                        device_id_final = devices[0].get("id", "")
                        resumen.append(f"✅  Device ID: {device_id_final}")
                    else:
                        opciones = [
                            f"{d.get('id','?')}  |  {d.get('device_model','')}  |  SN: {d.get('serial_number','')}"
                            for d in devices
                        ]
                        elegido, ok = QInputDialog.getItem(
                            self, "Seleccioná el terminal",
                            "Hay varios dispositivos vinculados.\nElegí el de esta caja:",
                            opciones, 0, False
                        )
                        if ok:
                            device_id_final = elegido.split("|")[0].strip()
                            resumen.append(f"✅  Device ID: {device_id_final}")
                else:
                    resumen.append("⚠️  Sin terminales Point vinculadas (no importa si usás solo QR)")
            elif r_dev.status_code == 401:
                QMessageBox.critical(self, "Token inválido",
                    "El token no es válido o expiró.\nVerificá en mercadopago.com/developers.")
                return
            else:
                resumen.append(f"⚠️  No se obtuvieron devices (HTTP {r_dev.status_code})")
        except Exception as e:
            resumen.append(f"⚠️  Error conectando a MP: {e}")

        # ── 2. Obtener External POS ID desde /pos (o crear si no hay) ───────
        try:
            from src.services.mercadopago_instore import obtener_user_id, asegurar_pos_qr
            uid = obtener_user_id(token)
            if uid:
                config.set("mp_user_id", uid)
            r_pos = requests.get(
                "https://api.mercadopago.com/pos",
                headers=headers, timeout=8
            )
            if r_pos.status_code == 200:
                pos_list = r_pos.json().get("results", [])
                if pos_list:
                    if len(pos_list) == 1:
                        pos_id_final = pos_list[0].get("external_id", "") or pos_list[0].get("name", "")
                        resumen.append(f"✅  POS ID (QR): {pos_id_final}")
                    else:
                        opciones_pos = [
                            f"{p.get('external_id','?')}  |  {p.get('name','')}"
                            for p in pos_list
                        ]
                        elegido_pos, ok2 = QInputDialog.getItem(
                            self, "Seleccioná el cajero QR",
                            "Hay varios puntos de venta.\nElegí el de esta caja:",
                            opciones_pos, 0, False
                        )
                        if ok2:
                            pos_id_final = elegido_pos.split("|")[0].strip()
                            resumen.append(f"✅  POS ID (QR): {pos_id_final}")
                else:
                    try:
                        _, pos_auto = asegurar_pos_qr(token)
                        pos_id_final = pos_auto
                        resumen.append(f"✅  POS QR creado/detectado: {pos_auto}")
                    except ValueError as e:
                        resumen.append(f"⚠️  {e}")
            else:
                resumen.append(f"⚠️  No se obtuvieron POS (HTTP {r_pos.status_code})")
        except Exception as e:
            resumen.append(f"⚠️  Error obteniendo POS: {e}")

        # ── 3. Llenar campos y mostrar resumen ───────────────────────────────
        if device_id_final:
            self.txt_mp_device.setText(device_id_final)
        if pos_id_final:
            self.txt_mp_pos_id.setText(pos_id_final)

        resultado = "\n".join(resumen)
        if device_id_final or pos_id_final:
            QMessageBox.information(self, "⚡ Auto-configuración completada",
                f"Se detectaron los siguientes datos:\n\n{resultado}\n\n"
                "Presá \"Guardar Configuración\" para aplicar.")
        else:
            QMessageBox.warning(self, "Sin datos automáticos",
                f"{resultado}\n\n"
                "Completá los campos manualmente.")

    def _show_help_mp(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Cómo obtener el Access Token",
            "💳  OBTENER EL ACCESS TOKEN DE MP\n\n"
            "1. Ingresá a: mercadopago.com/developers\n"
            "2. Presá \"Tus Integraciones\" → seleccioná tu app\n"
            "   (o creá una nueva con permisos QR + Point)\n"
            "3. En 'Credenciales de Producción' copiá el\n"
            "   Access Token  (empieza con APP_USR-...)\n\n"
            "⚠️  NUNCA uses el token TEST-... en producción.\n\n"
            "Después de pegar el token presá\n"
            "\"⚡ Auto-configurar\" y el sistema detecta\n"
            "el resto automáticamente."
        )

    def _show_help_clover(self):
        from PyQt5.QtWidgets import QMessageBox
        msg = ("ℹ️ CÓMO VINCULAR CLOVER POSNET\n\n"
               "1. Enciende tu terminal Clover y conéctala a la misma red WiFi que esta computadora.\n"
               "2. En la terminal Clover, abre la aplicación 'Network Pay' o revisa la configuración de red para ver su 'Dirección IP' (ej: 192.168.1.50).\n"
               "3. El puerto por defecto suele ser 1234 o 8080.\n\n"
               "Copia esa IP y Puerto aquí para que el sistema envíe los cobros automáticamente.")
        QMessageBox.information(self, "Ayuda - Clover", msg)

    def _guardar(self):
        from PyQt5.QtWidgets import QMessageBox
        import requests

        token = self.txt_mp_token.text().strip()
        config.set("mp_access_token", token)

        dev_id = self.txt_mp_device.text().strip()
        if dev_id.startswith("N950") and "NEWLAND_N950__" not in dev_id:
            dev_id = f"NEWLAND_N950__{dev_id}"

        config.set("mp_device_id", dev_id)
        config.set("mp_qr_pos_external_id", self.txt_mp_pos_id.text().strip())
        config.set("clover_ip", self.txt_clover_ip.text().strip())
        config.set("clover_port", self.txt_clover_port.text().strip())

        # Obtener y persistir el user_id de la cuenta automáticamente
        if token:
            try:
                me_resp = requests.get(
                    "https://api.mercadopago.com/users/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=6,
                    verify=False,
                )
                if me_resp.status_code == 200:
                    mp_user_id = me_resp.json().get("id")
                    if mp_user_id:
                        config.set("mp_user_id", str(mp_user_id))
            except Exception:
                # Sin conexión — no bloqueamos el guardado
                pass

        QMessageBox.information(self, "Guardado", "Configuración de terminales guardada correctamente.")
        self.accept()

class DialogoIntegracionesNube(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Integraciones Nube (API)")
        self.setFixedSize(500, 300)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        self._build()

    def _build(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(20, 20, 20, 20)
        main_lay.setSpacing(15)

        lbl_title = QLabel("🌐 Configuración de Servicios en la Nube")
        lbl_title.setStyleSheet(" font-size: 16px; font-weight: bold;")
        main_lay.addWidget(lbl_title)


        # SECCION: Telegram Bot
        box_tg = QFrame()
        box_tg.setStyleSheet(" border: 1px solid #CBD5E1; border-radius: 8px;")
        tg_lay = QVBoxLayout(box_tg)

        lbl_tg = QLabel("☁️ Notificaciones Z por Telegram")
        lbl_tg.setStyleSheet("font-weight: bold; font-size: 13px;  border: none;")
        tg_lay.addWidget(lbl_tg)

        self.txt_tg_token = QLineEdit(config.get("telegram_token", ""))
        self.txt_tg_token.setPlaceholderText("Token del Bot (ej: 123456:ABC-DEF...)")
        self.txt_tg_token.setEchoMode(QLineEdit.Password)
        self.txt_tg_token.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px;")
        tg_lay.addWidget(QLabel("Bot Token:"))
        tg_lay.addWidget(self.txt_tg_token)

        self.txt_tg_chat = QLineEdit(config.get("telegram_chat_id", ""))
        self.txt_tg_chat.setPlaceholderText("ID de Chat (ej: -100123456789)")
        self.txt_tg_chat.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px;")
        tg_lay.addWidget(QLabel("Chat ID:"))
        tg_lay.addWidget(self.txt_tg_chat)

        main_lay.addWidget(box_tg)

        main_lay.addStretch()

        # Botones Inferiores
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("padding: 8px 15px; border: none;  border-radius: 4px;")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 Guardar Credenciales")
        btn_save.setStyleSheet("padding: 8px 15px; font-weight: bold; background-color: #3B82F6; color: white;  border-radius: 4px; border: none;")
        btn_save.clicked.connect(self._guardar)

        h_btns.addWidget(btn_cancel)
        h_btns.addStretch()
        h_btns.addWidget(btn_save)

        main_lay.addLayout(h_btns)

    def _guardar(self):
        config.set("telegram_token", self.txt_tg_token.text().strip())
        config.set("telegram_chat_id", self.txt_tg_chat.text().strip())

        QMessageBox.information(self, "Guardado", "Credenciales de la nube guardadas correctamente en config.json.")
        self.accept()


class DialogoPINLocal(QDialog):
    """
    Diálogo para cambiar el PIN de acceso local utilizado por las terminales
    secundarias en el Modo Espectador LAN.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Base de Datos - Acceso PC Esclava")
        self.setFixedSize(450, 380)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet(" font-family: 'Segoe UI', Arial, sans-serif;")
        
        # Layout principal vertical sin márgenes para la cabecera
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Cabecera Premium Oscura con Degradado Teal
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E3A8A, stop:1 #0D9488);
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(25, 20, 25, 20)
        header_layout.setSpacing(4)
        
        lbl_title = QLabel("🔑 CONTRASEÑA DE RED (PC ESCLAVA)")
        lbl_title.setStyleSheet(" font-weight: bold; font-size: 16px; letter-spacing: 0.5px; border: none; background: transparent;")
        header_layout.addWidget(lbl_title)
        
        lbl_subtitle = QLabel("Contraseña requerida para conectar las computadoras secundarias por LAN")
        lbl_subtitle.setStyleSheet(" font-size: 11px; border: none; background: transparent;")
        header_layout.addWidget(lbl_subtitle)
        
        main_layout.addWidget(header)
        
        # Cuerpo con formulario
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(25, 20, 25, 20)
        body_layout.setSpacing(15)
        
        from PyQt5.QtWidgets import QFormLayout
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Inputs con diseño Premium
        input_style = """
            QLineEdit {
                
                border: 1.5px solid #E2E8F0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                
            }
            QLineEdit:focus {
                border: 1.5px solid #0D9488;
                
            }
        """
        
        self.txt_actual_pin = QLineEdit()
        self.txt_actual_pin.setEchoMode(QLineEdit.Password)
        self.txt_actual_pin.setPlaceholderText("Ingrese contraseña actual (Por defecto: 1234)")
        self.txt_actual_pin.setText("1234")
        self.txt_actual_pin.selectAll() # Remarcado por defecto para facilitar borrado
        self.txt_actual_pin.setStyleSheet(input_style)
        
        self.txt_nuevo_pin = QLineEdit()
        self.txt_nuevo_pin.setEchoMode(QLineEdit.Password)
        self.txt_nuevo_pin.setPlaceholderText("Mínimo 4 caracteres/dígitos")
        self.txt_nuevo_pin.setStyleSheet(input_style)
        
        self.txt_confirmar_pin = QLineEdit()
        self.txt_confirmar_pin.setEchoMode(QLineEdit.Password)
        self.txt_confirmar_pin.setPlaceholderText("Repita la nueva contraseña")
        self.txt_confirmar_pin.setStyleSheet(input_style)
        
        lbl_act = QLabel("Contraseña Actual:")
        lbl_act.setStyleSheet("font-size: 12px; font-weight: bold;  border: none; background: transparent;")
        
        lbl_nue = QLabel("Nueva Contraseña:")
        lbl_nue.setStyleSheet("font-size: 12px; font-weight: bold;  border: none; background: transparent;")
        
        lbl_conf = QLabel("Confirmar Contraseña:")
        lbl_conf.setStyleSheet("font-size: 12px; font-weight: bold;  border: none; background: transparent;")
        
        form_layout.addRow(lbl_act, self.txt_actual_pin)
        form_layout.addRow(lbl_nue, self.txt_nuevo_pin)
        form_layout.addRow(lbl_conf, self.txt_confirmar_pin)
        
        body_layout.addLayout(form_layout)
        body_layout.addSpacing(5)
        
        # Botones de Acción
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("""
            QPushButton {
                
                
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                border: 1px solid #E2E8F0;
                font-size: 13px;
            }
            QPushButton:hover {
                
                
            }
        """)
        btn_cancelar.clicked.connect(self.reject)
        
        btn_guardar = QPushButton("💾 Guardar Contraseña")
        btn_guardar.setStyleSheet("""
            QPushButton {
                
                background-color: #3B82F6; color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                border: None;
                font-size: 13px;
            }
            QPushButton:hover {
                
            }
        """)
        btn_guardar.clicked.connect(self.guardar_pin)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        
        body_layout.addLayout(btn_layout)
        main_layout.addWidget(body)
        
    def guardar_pin(self):
        actual = self.txt_actual_pin.text().strip()
        nuevo = self.txt_nuevo_pin.text().strip()
        confirmar = self.txt_confirmar_pin.text().strip()
        
        import hashlib
        
        # El PIN guardado ahora es un hash, pero por compatibilidad hacia atrás
        # si es '1234' (texto plano por defecto de versiones viejas) o su hash
        pin_guardado = config.get("local_pin", hashlib.sha256("1234".encode()).hexdigest())
        actual_hash = hashlib.sha256(actual.encode()).hexdigest()
        
        if actual_hash != pin_guardado and actual != pin_guardado:
            QMessageBox.critical(self, "Contraseña Incorrecta", "La contraseña actual ingresada no coincide con la guardada en el sistema.")
            return
            
        if len(nuevo) < 4:
            QMessageBox.warning(self, "Contraseña Muy Corta", "La nueva contraseña debe tener al menos 4 caracteres de longitud.")
            return
            
        if nuevo != confirmar:
            QMessageBox.critical(self, "No Coinciden", "La nueva contraseña y su confirmación no coinciden.")
            return
            
        # Guardar el PIN como HASH en la configuración
        nuevo_hash = hashlib.sha256(nuevo.encode()).hexdigest()
        config.set("local_pin", nuevo_hash)
        QMessageBox.information(self, "Contraseña Actualizada", "La llave de red se ha guardado exitosamente.")
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.txt_actual_pin.setFocus()
        self.txt_actual_pin.selectAll()