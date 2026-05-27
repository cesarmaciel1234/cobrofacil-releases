from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton, QGridLayout, QSizePolicy,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QMessageBox, QInputDialog, QCheckBox,
    QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QFont, QColor
import os, shutil, datetime
from src.config import config
try:
    from src.database import db_manager
except ImportError:
    from database import db_manager

class ConfigButton(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, icon_emoji, text, parent=None):
        super().__init__(parent)
        self.setFixedSize(110, 100)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Estilo tipo botón interactivo
        self.setStyleSheet("""
            ConfigButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 8px;
            }
            ConfigButton:hover {
                background-color: #EBF5FF;
                border: 1px solid #93C5FD;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 5)
        layout.setSpacing(5)
        
        # Icono (Emoji)
        self.lbl_icon = QLabel(icon_emoji)
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setStyleSheet("font-size: 32px; background: transparent; border: none;")
        layout.addWidget(self.lbl_icon)
        
        # Texto
        self.lbl_text = QLabel(text)
        self.lbl_text.setAlignment(Qt.AlignCenter)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setStyleSheet("font-size: 11px; font-weight: bold; color: #333333; background: transparent; border: none;")
        layout.addWidget(self.lbl_text)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

class DialogoCajeros(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("👥 Gestión de Personal - CajaFacil Pro")
        self.setFixedSize(700, 600)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        self.setup_ui()

    def setup_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(30, 30, 30, 30)
        main_lay.setSpacing(15)

        # --- HEADER ---
        header = QLabel("👥 Gestión de Cajeros y Administradores")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #1E3A8A; border:none;")
        main_lay.addWidget(header)
        
        lbl_info = QLabel("Administra los accesos y roles del personal de tu negocio.")
        lbl_info.setStyleSheet("color: #64748B; font-size: 13px; margin-bottom: 5px; border:none;")
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
                gridline-color: transparent; alternate-background-color: #F8FAFC;
                selection-background-color: #DBEAFE; selection-color: #1E40AF;
            }
            QHeaderView::section { 
                background-color: #F1F5F9; padding: 15px; border: none; 
                font-weight: 900; color: #475569; font-size: 11px; text-transform: uppercase;
            }
        """)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.itemClicked.connect(self._al_seleccionar)
        main_lay.addWidget(self.tabla)
        self.cargar_usuarios()

        # --- CARD DE EDICIÓN ---
        card = QFrame()
        card.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 15px;")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(20, 20, 20, 20)
        card_lay.setSpacing(15)

        lbl_card = QLabel("📝 CARGAR / EDITAR PERSONAL")
        lbl_card.setStyleSheet("font-weight: 900; color: #1E3A8A; font-size: 11px; border: none;")
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
        btn_del.setStyleSheet("background: #FEE2E2; color: #EF4444; border: 1px solid #FECACA; padding: 12px; border-radius: 10px; font-weight: bold;")
        btn_del.clicked.connect(self.eliminar_usuario)
        
        btn_save = QPushButton("💾 Guardar Usuario")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("background: #10B981; color: white; padding: 12px; border-radius: 10px; font-weight: bold; border: none;")
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
        self.setWindowTitle("Configurar Ticket")
        self.setFixedSize(400, 360)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Nombre del Negocio:"))
        self.txt_name = QLineEdit(config.get('business_name', ''))
        layout.addWidget(self.txt_name)
        
        layout.addWidget(QLabel("Dirección:"))
        self.txt_addr = QLineEdit(config.get('address', ''))
        layout.addWidget(self.txt_addr)
        
        layout.addWidget(QLabel("Teléfono:"))
        self.txt_phone = QLineEdit(config.get('phone', ''))
        layout.addWidget(self.txt_phone)

        layout.addWidget(QLabel("CUIT / RUT:"))
        self.txt_cuit = QLineEdit(config.get('business_cuit', ''))
        layout.addWidget(self.txt_cuit)
        
        layout.addWidget(QLabel("Mensaje al final del ticket:"))
        self.txt_msg = QLineEdit(config.get('footer_message', ''))
        layout.addWidget(self.txt_msg)
        
        btn = QPushButton("Guardar Configuración")
        btn.setStyleSheet("background-color: #3B82F6; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        btn.clicked.connect(self.guardar)
        layout.addStretch(); layout.addWidget(btn)

    def guardar(self):
        config.set('business_name', self.txt_name.text())
        config.set('address', self.txt_addr.text())
        config.set('phone', self.txt_phone.text())
        config.set('business_cuit', self.txt_cuit.text())
        config.set('footer_message', self.txt_msg.text())
        self.accept()

class DialogoLectorCodigos(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Probar Lector de Códigos de Barras")
        self.setFixedSize(500, 350)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("Configuración y Prueba del Lector")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)
        
        lbl_inst = QLabel("1. Haz clic en el cuadro de texto azul.\n2. Dispara el escáner sobre cualquier código de barras.")
        lbl_inst.setStyleSheet("font-size: 14px; color: #475569;")
        lbl_inst.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_inst)
        
        self.txt_scan = QLineEdit()
        self.txt_scan.setPlaceholderText("Escanea aquí...")
        self.txt_scan.setStyleSheet("background: #E0F2FE; border: 2px dashed #38BDF8; font-size: 30px; font-weight: bold; color: #0284C7; padding: 10px;")
        self.txt_scan.setAlignment(Qt.AlignCenter)
        self.txt_scan.returnPressed.connect(self.procesar_escaneo)
        layout.addWidget(self.txt_scan)
        
        self.lbl_resultado = QLabel("")
        self.lbl_resultado.setStyleSheet("font-size: 16px; font-weight: bold; color: #10B981;")
        self.lbl_resultado.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_resultado)
        
        layout.addStretch()
        btn = QPushButton("Terminar Prueba")
        btn.setStyleSheet("background-color: #64748B; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def procesar_escaneo(self):
        codigo = self.txt_scan.text().strip()
        if codigo:
            self.lbl_resultado.setText(f"✅ ¡Éxito! Código leído: {codigo}\nEl escáner está configurado correctamente (Envía ENTER).")
            self.txt_scan.setStyleSheet("background: #D1FAE5; border: 2px solid #10B981; font-size: 30px; font-weight: bold; color: #065F46; padding: 10px;")
            self.txt_scan.clear()

class ConfigCategory(QWidget):
    def __init__(self, title, items, callback=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Título de Categoría
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E293B; border-bottom: 1px solid #CBD5E1; padding-bottom: 5px;")
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
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        layout.addWidget(lbl_title)
        
        lbl_inst = QLabel("Selecciona en qué momentos debe abrirse el cajón de dinero:")
        lbl_inst.setStyleSheet("font-size: 13px; color: #475569; margin-bottom: 10px;")
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
        btn_test.setStyleSheet("background-color: #6366F1; color: white; padding: 12px; font-weight: bold; border-radius: 8px;")
        btn_test.clicked.connect(self.probar_cajon)
        
        btn_alarm = QPushButton("🚨 Probar Alarma SOS")
        btn_alarm.setStyleSheet("background-color: #EF4444; color: white; padding: 12px; font-weight: bold; border-radius: 8px;")
        btn_alarm.clicked.connect(self.probar_alarma)
        
        row_test.addWidget(btn_test)
        row_test.addWidget(btn_alarm)
        layout.addLayout(row_test)
        
        layout.addStretch()
        
        btn_save = QPushButton("Guardar Configuración")
        btn_save.setStyleSheet("background-color: #10B981; color: white; padding: 10px; font-weight: bold; border-radius: 8px;")
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
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 900; color: #1E3A8A;")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        lbl_inst = QLabel("Asigná una tiketera y cajón a cada operador.\nEl sistema usa automáticamente la del que desbloquó la terminal.")
        lbl_inst.setStyleSheet("font-size: 12px; color: #64748b;")
        lbl_inst.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_inst)

        layout.addSpacing(6)

        # CAJERO (principal)
        box1 = QFrame()
        box1.setStyleSheet("QFrame { background: #EFF6FF; border: 2px solid #1E3A8A; border-radius: 10px; } QLabel { border: none; background: transparent; }")
        b1 = QVBoxLayout(box1); b1.setContentsMargins(16, 12, 16, 12); b1.setSpacing(6)
        b1.addWidget(QLabel("🔵  [1]  CAJERO — Tiketera / Cajón:", styleSheet="font-size: 13px; font-weight: 900; color: #1E3A8A;"))
        
        row1 = QHBoxLayout()
        self.cmb_p1 = QComboBox()
        self.cmb_p1.setStyleSheet("padding: 7px; border: 1px solid #93C5FD; border-radius: 6px; font-size: 13px; background: white;")
        row1.addWidget(self.cmb_p1, 1)
        
        btn_test1 = QPushButton("📄 Test P1")
        btn_test1.setCursor(Qt.PointingHandCursor)
        btn_test1.setStyleSheet("background: #1E3A8A; color: white; border-radius: 6px; font-weight: bold; padding: 7px 15px;")
        btn_test1.clicked.connect(lambda: self.print_test_ticket_generic(self.cmb_p1.currentText()))
        row1.addWidget(btn_test1)
        
        b1.addLayout(row1)
        layout.addWidget(box1)

        # AUXILIAR (secundario)
        box2 = QFrame()
        box2.setStyleSheet("QFrame { background: #ECFDF5; border: 2px solid #059669; border-radius: 10px; } QLabel { border: none; background: transparent; }")
        b2 = QVBoxLayout(box2); b2.setContentsMargins(16, 12, 16, 12); b2.setSpacing(6)
        b2.addWidget(QLabel("🟢  [2]  AUXILIAR — Tiketera / Cajón:", styleSheet="font-size: 13px; font-weight: 900; color: #059669;"))
        
        row2 = QHBoxLayout()
        self.cmb_p2 = QComboBox()
        self.cmb_p2.setStyleSheet("padding: 7px; border: 1px solid #6EE7B7; border-radius: 6px; font-size: 13px; background: white;")
        row2.addWidget(self.cmb_p2, 1)
        
        btn_test2 = QPushButton("📄 Test P2")
        btn_test2.setCursor(Qt.PointingHandCursor)
        btn_test2.setStyleSheet("background: #059669; color: white; border-radius: 6px; font-weight: bold; padding: 7px 15px;")
        btn_test2.clicked.connect(lambda: self.print_test_ticket_generic(self.cmb_p2.currentText()))
        row2.addWidget(btn_test2)
        
        b2.addLayout(row2)
        layout.addWidget(box2)

        # PUERTO SERIAL (COM)
        box3 = QFrame()
        box3.setStyleSheet("QFrame { background: #F8FAFC; border: 2px solid #CBD5E1; border-radius: 10px; } QLabel { border: none; background: transparent; }")
        b3 = QVBoxLayout(box3); b3.setContentsMargins(16, 12, 16, 12); b3.setSpacing(6)
        
        b3_hdr = QHBoxLayout()
        b3_hdr.addWidget(QLabel("🔌  PUERTO SERIAL — Cajón / Sensor (COM):", styleSheet="font-size: 13px; font-weight: 900; color: #475569;"))
        btn_ref = QPushButton("🔄")
        btn_ref.setCursor(Qt.PointingHandCursor)
        btn_ref.setFixedSize(30, 30)
        btn_ref.setStyleSheet("background: #E2E8F0; border: 1px solid #CBD5E1; border-radius: 5px; font-size: 14px; font-weight: bold;")
        btn_ref.clicked.connect(self._load_printers_and_ports)
        b3_hdr.addStretch(); b3_hdr.addWidget(btn_ref)
        b3.addLayout(b3_hdr)
        
        self.cmb_serial_port = QComboBox()
        self.cmb_serial_port.setStyleSheet("padding: 7px; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 13px; background: white;")
        b3.addWidget(self.cmb_serial_port)
        layout.addWidget(box3)

        self._load_printers_and_ports()
        layout.addStretch()

        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("background: #F1F5F9; color: #475569; padding: 10px 22px; border-radius: 6px; font-weight: bold;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾  Guardar")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("background: #1E3A8A; color: white; padding: 10px 22px; border-radius: 6px; font-weight: bold;")
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
            self.cmb_serial_port.blockSignals(True)
            self.cmb_serial_port.clear()
            ports_list = ["Ninguno (USB Directo / OPOS)"] + [f"COM{i}" for i in range(1, 31)]
            try:
                import serial.tools.list_ports
                detected = [p.device for p in serial.tools.list_ports.comports()]
                for d in detected:
                    if d not in ports_list:
                        ports_list.insert(1, d)
            except Exception:
                pass
            self.cmb_serial_port.addItems(ports_list)
            
            saved_port = config.get("printer_name", "")
            if not saved_port:
                self.cmb_serial_port.setCurrentIndex(0)
            else:
                idx = self.cmb_serial_port.findText(saved_port)
                if idx != -1:
                    self.cmb_serial_port.setCurrentIndex(idx)
                else:
                    self.cmb_serial_port.addItem(saved_port)
                    self.cmb_serial_port.setCurrentText(saved_port)
            self.cmb_serial_port.blockSignals(False)
        except Exception: pass

    def _guardar(self):
        p1 = self.cmb_p1.currentText()
        p2 = self.cmb_p2.currentText()
        if p1 == "(Sin impresora)": p1 = ""
        if p2 == "(Sin impresora)": p2 = ""
        config.set("ticket_printer", p1)
        config.set("ticket_printer_2", p2)
        
        com_val = self.cmb_serial_port.currentText()
        if "Ninguno" in com_val:
            config.set("printer_name", "")
        else:
            config.set("printer_name", com_val)
            
        QMessageBox.information(self, "✅ Guardado con Éxito",
            f"Cajero 1 → {p1 or 'Sin impresora'}\nCajero 2 → {p2 or 'Sin impresora'}\nPuerto COM → {config.get('printer_name', 'Ninguno')}")
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
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 900; color: #1E3A8A;")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        lbl_inst = QLabel(
            "Configura el identificador numérico inmutable para esta PC en la red.\n"
            "Cada terminal debe tener un ID único (ej: 1, 2, 3...)."
        )
        lbl_inst.setStyleSheet("font-size: 12px; color: #64748b;")
        lbl_inst.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_inst)

        # Caja ID Input
        h_lay = QHBoxLayout()
        h_lay.addWidget(QLabel("ID de Caja Física:", styleSheet="font-weight: bold; font-size: 13px; color: #334155;"))
        
        self.txt_caja_id = QLineEdit()
        self.txt_caja_id.setText(str(config.get("caja_id", 1)))
        self.txt_caja_id.setStyleSheet("padding: 8px; border: 2px solid #CBD5E1; border-radius: 6px; font-weight: bold; font-size: 15px;")
        self.txt_caja_id.setAlignment(Qt.AlignCenter)
        h_lay.addWidget(self.txt_caja_id)
        layout.addLayout(h_lay)

        layout.addStretch()

        btn_save = QPushButton("💾 Guardar Identificador")
        btn_save.setStyleSheet("background-color: #1E3A8A; color: white; padding: 12px; font-weight: bold; border-radius: 6px;")
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
        lbl_tit.setStyleSheet("font-size: 18px; font-weight: 900; color: #EA580C;")
        lbl_tit.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_tit)

        lbl_inst = QLabel("Configurá desde qué montos acumulados en efectivo\nla terminal debe parpadear exigiendo un retiro de caja:")
        lbl_inst.setStyleSheet("font-size: 12px; color: #64748b;")
        lbl_inst.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_inst)

        # Amarillo (Nivel 1)
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("🟡 Alerta Amarilla ($):", styleSheet="font-weight: bold; color: #EAB308; font-size: 13px;"))
        self.txt_nar = QLineEdit()
        self.txt_nar.setText(str(int(float(config.get("limite_efectivo_naranja", 50000)))))
        self.txt_nar.setStyleSheet("padding: 6px; border: 1px solid #CBD5E1; border-radius: 5px; font-weight: bold; font-size: 14px;")
        self.txt_nar.setAlignment(Qt.AlignRight)
        h1.addWidget(self.txt_nar)
        lay.addLayout(h1)

        # Naranja (Nivel 2)
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("🟠 Alerta Naranja ($):", styleSheet="font-weight: bold; color: #EA580C; font-size: 13px;"))
        self.txt_roj = QLineEdit()
        self.txt_roj.setText(str(int(float(config.get("limite_efectivo_rojo", 70000)))))
        self.txt_roj.setStyleSheet("padding: 6px; border: 1px solid #CBD5E1; border-radius: 5px; font-weight: bold; font-size: 14px;")
        self.txt_roj.setAlignment(Qt.AlignRight)
        h2.addWidget(self.txt_roj)
        lay.addLayout(h2)

        lay.addStretch()

        btn_save = QPushButton("💾 Guardar Configuración")
        btn_save.setStyleSheet("background: #EA580C; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
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
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E3A8A; border:none;")
        main_lay.addWidget(header)
        
        lbl_desc = QLabel("Ajusta cómo el sistema lee tus etiquetas EAN-13.")
        lbl_desc.setStyleSheet("color: #64748B; font-size: 13px; margin-bottom: 5px; border:none;")
        main_lay.addWidget(lbl_desc)

        # --- CARD DE CONFIGURACIÓN ---
        card = QFrame()
        card.setStyleSheet("""
            QFrame { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; }
            QLabel { border: none; font-weight: bold; color: #475569; font-size: 11px; }
            QLineEdit, QComboBox { 
                background: white; border: 1px solid #CBD5E1; border-radius: 6px; 
                padding: 10px; font-weight: normal; color: #1E293B; font-size: 13px;
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
        sim_card.setStyleSheet("background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px;")
        sim_lay = QVBoxLayout(sim_card)
        sim_lay.setContentsMargins(15, 15, 15, 15)
        
        lbl_sim = QLabel("🧪 PROBADOR DE CÓDIGOS")
        lbl_sim.setStyleSheet("color: #1E40AF; font-weight: 900; border: none; font-size: 11px;")
        sim_lay.addWidget(lbl_sim)

        self.txt_test = QLineEdit()
        self.txt_test.setPlaceholderText("Pega un código EAN-13 aquí para probar...")
        self.txt_test.setStyleSheet("background: white; border: 1px solid #3B82F6; padding: 10px; font-family: 'Consolas';")
        self.txt_test.textChanged.connect(self.simular_prueba)
        sim_lay.addWidget(self.txt_test)

        self.lbl_res_test = QLabel("Resultado: —")
        self.lbl_res_test.setStyleSheet("color: #1E3A8A; font-weight: bold; border: none;")
        sim_lay.addWidget(self.lbl_res_test)
        main_lay.addWidget(sim_card)

        # --- AYUDA ---
        btn_help = QPushButton("❓ Ver Formatos Comunes (Systel, Kretz, etc.)")
        btn_help.setStyleSheet("color: #3B82F6; font-weight: bold; border: none; background: transparent; font-size: 11px;")
        btn_help.setCursor(Qt.PointingHandCursor)
        btn_help.clicked.connect(self._sugerir_formatos)
        main_lay.addWidget(btn_help)

        # --- BOTONES ---
        main_lay.addStretch()
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("padding: 12px; font-weight: bold; background: #F1F5F9; color: #475569; border-radius: 8px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 Guardar Configuración")
        btn_save.setStyleSheet("padding: 12px; font-weight: bold; background: #1E3A8A; color: white; border-radius: 8px;")
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
               "• <b>Systel/Kretz:</b> Inicio PLU: 3, Largo: 4 | Inicio Valor: 8, Largo: 5 | Divisor: 1000<br>"
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
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E3A8A; border:none;")
        main_lay.addWidget(header)
        
        lbl_desc = QLabel("Configura la integración con ARCA (ex-AFIP) o tu ticketera fiscal física.")
        lbl_desc.setStyleSheet("color: #64748B; font-size: 13px; margin-bottom: 5px; border:none;")
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
            QFrame { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; }
            QLabel { border: none; font-weight: bold; color: #334155; font-size: 11px; }
            QLineEdit, QComboBox { 
                background: white; border: 1px solid #CBD5E1; border-radius: 6px; 
                padding: 8px; font-weight: normal; color: #1E293B; font-size: 13px;
            }
        """)
        arca_lay = QVBoxLayout(box_arca)
        arca_lay.setSpacing(10)
        
        lbl_arca_title = QLabel("🌐 FACTURA ELECTRÓNICA ARCA (AFIP Web Services)")
        lbl_arca_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #1E3A8A; border-bottom: 1px solid #CBD5E1; padding-bottom: 5px;")
        arca_lay.addWidget(lbl_arca_title)

        # Checkbox Activar
        self.chk_arca_enabled = QCheckBox("Habilitar Facturación Electrónica (ARCA)")
        self.chk_arca_enabled.setChecked(config.get("factura_electronica_mode", False))
        self.chk_arca_enabled.setStyleSheet("font-weight: bold; font-size: 13px; color: #1E293B; border: none;")
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
                background-color: #E2E8F0; color: #334155; font-weight: bold; border-radius: 6px; padding: 6px 12px;
                border: 1px solid #CBD5E1;
            }
            QPushButton:hover { background-color: #CBD5E1; }
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
                background-color: #E2E8F0; color: #334155; font-weight: bold; border-radius: 6px; padding: 6px 12px;
                border: 1px solid #CBD5E1;
            }
            QPushButton:hover { background-color: #CBD5E1; }
        """)
        btn_browse_crt.clicked.connect(self.buscar_certificado)
        h_crt.addWidget(self.txt_crt, 1)
        h_crt.addWidget(btn_browse_crt)
        grid_arca.addLayout(h_crt, 3, 1)

        arca_lay.addLayout(grid_arca)

        # Checkbox Homologación
        self.chk_sandbox = QCheckBox("Modo Homologación / Sandbox (Pruebas AFIP)")
        self.chk_sandbox.setChecked(config.get("arca_sandbox_mode", False))
        self.chk_sandbox.setStyleSheet("font-size: 12px; color: #475569; border: none;")
        arca_lay.addWidget(self.chk_sandbox)

        scroll_lay.addWidget(box_arca)

        # ── SECCIÓN 2: IMPRESORA FISCAL HOLOGADA (Hasar/Epson) ──
        box_fiscal = QFrame()
        box_fiscal.setStyleSheet(box_arca.styleSheet())
        fiscal_lay = QVBoxLayout(box_fiscal)
        fiscal_lay.setSpacing(10)

        lbl_fiscal_title = QLabel("📟 IMPRESORA FISCAL FÍSICA (Hasar / Epson TM)")
        lbl_fiscal_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #EA580C; border-bottom: 1px solid #CBD5E1; padding-bottom: 5px;")
        fiscal_lay.addWidget(lbl_fiscal_title)

        # Checkbox Activar Fiscal
        self.chk_fiscal_enabled = QCheckBox("Habilitar Impresora Fiscal Homologada")
        self.chk_fiscal_enabled.setChecked(config.get("fiscal_printer_mode", False))
        self.chk_fiscal_enabled.setStyleSheet("font-weight: bold; font-size: 13px; color: #1E293B; border: none;")
        fiscal_lay.addWidget(self.chk_fiscal_enabled)
        
        lbl_info_excl = QLabel("⚠️ Si se activa, las ventas digitales irán al controlador fiscal físico,\ny las ventas en Efectivo continuarán imprimiendo de forma no-fiscal.")
        lbl_info_excl.setStyleSheet("color: #D97706; font-size: 10.5px; border: none; font-weight: normal;")
        lbl_info_excl.setWordWrap(True)
        fiscal_lay.addWidget(lbl_info_excl)

        scroll_lay.addWidget(box_fiscal)

        # ── SECCIÓN 3: RUTEO POR MÉTODO DE PAGO ──
        box_pago = QFrame()
        box_pago.setStyleSheet(box_arca.styleSheet())
        pago_lay = QVBoxLayout(box_pago)
        pago_lay.setSpacing(10)

        lbl_pago_title = QLabel("💳 RUTEO DE COMPROBANTES POR MÉTODO DE PAGO")
        lbl_pago_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #1E3A8A; border-bottom: 1px solid #CBD5E1; padding-bottom: 5px;")
        pago_lay.addWidget(lbl_pago_title)

        lbl_pago_desc = QLabel("Seleccione los métodos de pago que emitirán factura fiscal legal / ARCA:")
        lbl_pago_desc.setStyleSheet("color: #475569; font-size: 11px; font-weight: normal; border: none;")
        pago_lay.addWidget(lbl_pago_desc)

        h_checks = QHBoxLayout()
        h_checks.setSpacing(15)
        
        # Obtener métodos configurados
        metodos_activos = config.get("fiscal_payment_methods", ["Tarjeta", "Transferencia", "Mixto"])
        
        self.chk_met_efectivo = QCheckBox("Efectivo")
        self.chk_met_efectivo.setChecked("Efectivo" in metodos_activos)
        self.chk_met_efectivo.setStyleSheet("font-size: 12px; color: #1E293B; border: none;")
        
        self.chk_met_tarjeta = QCheckBox("Tarjeta")
        self.chk_met_tarjeta.setChecked("Tarjeta" in metodos_activos)
        self.chk_met_tarjeta.setStyleSheet("font-size: 12px; color: #1E293B; border: none;")
        
        self.chk_met_transf = QCheckBox("Transferencia")
        self.chk_met_transf.setChecked("Transferencia" in metodos_activos)
        self.chk_met_transf.setStyleSheet("font-size: 12px; color: #1E293B; border: none;")
        
        self.chk_met_mixto = QCheckBox("Mixto")
        self.chk_met_mixto.setChecked("Mixto" in metodos_activos)
        self.chk_met_mixto.setStyleSheet("font-size: 12px; color: #1E293B; border: none;")

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
        btn_cancel.setStyleSheet("padding: 12px; font-weight: bold; background: #F1F5F9; color: #475569; border-radius: 8px; border: none;")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 Guardar Cambios")
        btn_save.setStyleSheet("padding: 12px; font-weight: bold; background: #1E3A8A; color: white; border-radius: 8px; border: none;")
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
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E3A8A; border:none;")
        main_lay.addWidget(header)

        # Sección IVA General
        general_box = QFrame()
        general_box.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;")
        gen_lay = QHBoxLayout(general_box)
        gen_lay.setContentsMargins(15, 12, 15, 12)
        
        lbl_gen = QLabel("Tasa de IVA General por defecto (%):")
        lbl_gen.setStyleSheet("font-size: 13px; color: #334155; font-weight: bold; border:none;")
        
        self.txt_iva_gen = QLineEdit(str(config.get("tax_percentage", 21.0)))
        self.txt_iva_gen.setFixedWidth(80)
        self.txt_iva_gen.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 4px; padding: 6px; font-size: 13px;")
        
        gen_lay.addWidget(lbl_gen)
        gen_lay.addWidget(self.txt_iva_gen)
        gen_lay.addStretch()
        main_lay.addWidget(general_box)

        # Título Tabla
        lbl_tbl = QLabel("Tasas de IVA específicas por Departamento:")
        lbl_tbl.setStyleSheet("font-size: 13px; color: #475569; font-weight: bold; border:none;")
        main_lay.addWidget(lbl_tbl)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre Departamento", "Tasa IVA (%)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #F1F5F9; color: #475569; font-weight: bold; border: 1px solid #E2E8F0; padding: 5px; }")
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #E2E8F0; border-radius: 6px; }
            QTableWidget::item { padding: 8px; color: #1E293B; }
        """)
        main_lay.addWidget(self.table)

        self._cargar_departamentos()

        # Botones de Acción
        h_act = QHBoxLayout()
        btn_add = QPushButton("➕ Agregar Departamento")
        btn_add.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 8px 12px; border-radius: 6px; border: none;")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self._agregar_departamento)
        
        btn_del = QPushButton("🗑️ Eliminar Seleccionado")
        btn_del.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; padding: 8px 12px; border-radius: 6px; border: none;")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.clicked.connect(self._eliminar_departamento)

        h_act.addWidget(btn_add)
        h_act.addWidget(btn_del)
        h_act.addStretch()
        main_lay.addLayout(h_act)

        # Botones Inferiores (Guardar/Cancelar)
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("padding: 10px 18px; font-weight: bold; background: #F1F5F9; color: #475569; border-radius: 8px; border: none;")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 Guardar Todo")
        btn_save.setStyleSheet("padding: 10px 18px; font-weight: bold; background: #1E3A8A; color: white; border-radius: 8px; border: none;")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self._guardar)
        
        h_btns.addWidget(btn_cancel)
        h_btns.addStretch()
        h_btns.addWidget(btn_save)
        main_lay.addLayout(h_btns)

    def _cargar_departamentos(self):
        from src.database import db_manager
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
                from src.database import db_manager
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
            from src.database import db_manager
            
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
                    db_manager.execute_non_query(
                        "INSERT OR IGNORE INTO departamentos (nombre, iva) VALUES (?, ?)",
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
        header.setStyleSheet("background-color: #F8FAFC; border-bottom: 1px solid #E2E8F0;")
        header.setFixedHeight(70)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(30, 0, 30, 0)
        
        btn_volver = QPushButton("🔙 Volver")
        btn_volver.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6; color: white; font-weight: bold; font-size: 14px;
                border-radius: 6px; padding: 8px 20px;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        btn_volver.setCursor(QCursor(Qt.PointingHandCursor))
        btn_volver.clicked.connect(self.request_dashboard.emit)
        h_layout.addWidget(btn_volver)
        
        h_layout.addSpacing(20)
        
        lbl_title = QLabel("Configuración del Sistema")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0F172A;")
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
            ("🔑", "PIN Contraseña\nLocal"),
            ("🚀", "PunPro\nPresto"),
            ("🧾", "Facturación"),
            ("📝", "Modificar\nFolios"),
            ("💻", "Administrar\nCajas")
        ], callback=self.ejecutar_accion)
        content_layout.addWidget(cat_general)
        
        cat_pers = ConfigCategory("Personalización", [
            ("🖼️", "Logotipo del\nPrograma"),
            ("🎫", "Ticket"),
            ("💳", "Formas de\nPago"),
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
            ("📱", "Recargas\nElectrónicas"),
            ("💡", "Pago de\nServicios"),
            ("🚚", "Compras /\nProveedores"),
            ("☁️", "Nube\nPunPro"),
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
            dlg.exec_()
        elif opcion == "Cajeros":
            dlg = DialogoCajeros(self)
            dlg.exec_()
        elif opcion == "Administrar\nCajas":
            dlg = DialogoAdministrarCajas(self)
            dlg.exec_()
        elif opcion == "Ticket":
            dlg = DialogoTicket(self)
            dlg.exec_()
        elif opcion == "Logotipo del\nPrograma":
            val, ok = QInputDialog.getText(self, "Logotipo / Nombre", "Ingresa el nombre de tu negocio para la interfaz:", text=config.get('business_name', ''))
            if ok: config.set('business_name', val)
        elif opcion == "Lector de\nCódigos":
            dlg = DialogoLectorCodigos(self)
            dlg.exec_()
        elif opcion == "Dos Tiketeras\n2 Cajas":
            dlg = DialogoDosTiketeras(self)
            dlg.exec_()
        elif opcion == "Cajón de\nDinero":
            dlg = DialogoCajon(self)
            dlg.exec_()
        elif opcion == "Símbolo de\nMoneda":
            val, ok = QInputDialog.getText(self, "Símbolo de Moneda", "Ingresa el símbolo que se utilizará (Ej: $ o €):", text=config.get('currency_symbol', '$'))
            if ok: config.set('currency_symbol', val)
        elif opcion == "Báscula":
            dlg = DialogoBalanza(self)
            dlg.exec_()
        elif opcion == "Hardware\nIndustrial":
            self.request_screen.emit(13)
        elif opcion == "PIN Contraseña\nLocal":
            dlg = DialogoPINLocal(self)
            dlg.exec_()
        elif opcion == "Facturación":
            dlg = DialogoFacturacion(self)
            dlg.exec_()
        elif opcion == "Impuestos":
            dlg = DialogoImpuestos(self)
            dlg.exec_()
        elif opcion == "Respaldo":
            try:
                backup_dir = os.path.join(os.path.dirname(db_manager.db_path), "backups")
                os.makedirs(backup_dir, exist_ok=True)
                backup_file = os.path.join(backup_dir, f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
                shutil.copy2(db_manager.db_path, backup_file)
                QMessageBox.information(self, "Respaldo Exitoso", f"Se ha creado una copia de seguridad segura de tus datos en:\n{backup_file}")
            except Exception as e:
                QMessageBox.critical(self, "Error de Respaldo", f"Hubo un error al copiar la base de datos:\n{e}")
        elif opcion == "Actualizaciones":
            dlg = DialogoActualizaciones(self)
            dlg.exec_()
        else:
            QMessageBox.information(self, "Módulo en Desarrollo", f"La función '{opcion.replace(chr(10), ' ')}' estará disponible en la próxima actualización del sistema.")

class DialogoActualizaciones(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Actualizaciones Automáticas")
        self.setFixedSize(550, 220)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        lbl_title = QLabel("ACTUALIZACIONES AUTOMATICAS")
        lbl_title.setStyleSheet("color: #082c63; font-size: 13px; font-weight: bold;")
        layout.addWidget(lbl_title)
        
        # Fila de Auto-Check
        row1 = QHBoxLayout()
        self.chk_auto = QCheckBox("Checar si hay actualizaciones disponibles automáticamente al")
        self.chk_auto.setChecked(config.get('auto_update_check', True))
        
        self.cmb_when = QComboBox()
        self.cmb_when.addItems(["Salir del programa", "Iniciar el programa"])
        self.cmb_when.setCurrentText(config.get('auto_update_when', "Salir del programa"))
        
        lbl_icon = QLabel("🔄")
        lbl_icon.setStyleSheet("font-size: 20px; color: #3B82F6;")
        
        row1.addWidget(self.chk_auto)
        row1.addWidget(self.cmb_when)
        row1.addWidget(lbl_icon)
        row1.addStretch()
        layout.addLayout(row1)
        
        # Botón de Chequeo Manual
        self.btn_check = QPushButton("📦 Checar si hay una actualización disponible ...")
        self.btn_check.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC; 
                border: 1px solid #CBD5E1; 
                padding: 8px 15px; 
                border-radius: 4px;
                color: #333333;
            }
            QPushButton:hover { background-color: #F1F5F9; border-color: #94A3B8; }
        """)
        self.btn_check.clicked.connect(self.checar_actualizacion)
        layout.addWidget(self.btn_check, alignment=Qt.AlignLeft)
        
        # Mensaje de Información (Firewall)
        frame_info = QFrame()
        frame_info.setStyleSheet("background-color: #FEF9C3; border: 1px solid #FDE047; border-radius: 4px;")
        lay_info = QHBoxLayout(frame_info)
        lbl_info = QLabel("ℹ️ No olvides permitir que el programa tenga acceso a Internet permitiéndole el paso a través\nde Firewalls ya sea de Windows o de tu antivirus.")
        lbl_info.setStyleSheet("color: #854D0E; font-size: 11px; border: none;")
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
                QMessageBox.information(self, "Al día", f"CajaFacil Pro está actualizado.\nVersión: {res.version_local}")
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



class DialogoPINLocal(QDialog):
    """
    Diálogo para cambiar el PIN de acceso local utilizado por las terminales
    secundarias en el Modo Espectador LAN.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cambio de PIN de Seguridad Local")
        self.setFixedSize(450, 380)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("background-color: #FFFFFF; font-family: 'Segoe UI', Arial, sans-serif;")
        
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
        
        lbl_title = QLabel("🔑 PIN DE SEGURIDAD LOCAL")
        lbl_title.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 16px; letter-spacing: 0.5px; border: none; background: transparent;")
        header_layout.addWidget(lbl_title)
        
        lbl_subtitle = QLabel("Acceso para terminales secundarias en Modo Espectador LAN")
        lbl_subtitle.setStyleSheet("color: #E2E8F0; font-size: 11px; border: none; background: transparent;")
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
                background-color: #F8FAFC;
                border: 1.5px solid #E2E8F0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1E293B;
            }
            QLineEdit:focus {
                border: 1.5px solid #0D9488;
                background-color: #FFFFFF;
            }
        """
        
        self.txt_actual_pin = QLineEdit()
        self.txt_actual_pin.setEchoMode(QLineEdit.Password)
        self.txt_actual_pin.setPlaceholderText("Ingrese PIN actual")
        self.txt_actual_pin.setStyleSheet(input_style)
        
        self.txt_nuevo_pin = QLineEdit()
        self.txt_nuevo_pin.setEchoMode(QLineEdit.Password)
        self.txt_nuevo_pin.setPlaceholderText("Mínimo 4 caracteres/dígitos")
        self.txt_nuevo_pin.setStyleSheet(input_style)
        
        self.txt_confirmar_pin = QLineEdit()
        self.txt_confirmar_pin.setEchoMode(QLineEdit.Password)
        self.txt_confirmar_pin.setPlaceholderText("Repita el nuevo PIN")
        self.txt_confirmar_pin.setStyleSheet(input_style)
        
        lbl_act = QLabel("PIN Actual:")
        lbl_act.setStyleSheet("font-size: 12px; font-weight: bold; color: #475569; border: none; background: transparent;")
        
        lbl_nue = QLabel("Nuevo PIN:")
        lbl_nue.setStyleSheet("font-size: 12px; font-weight: bold; color: #475569; border: none; background: transparent;")
        
        lbl_conf = QLabel("Confirmar PIN:")
        lbl_conf.setStyleSheet("font-size: 12px; font-weight: bold; color: #475569; border: none; background: transparent;")
        
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
                background-color: #F1F5F9;
                color: #64748B;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                border: 1px solid #E2E8F0;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
                color: #334155;
            }
        """)
        btn_cancelar.clicked.connect(self.reject)
        
        btn_guardar = QPushButton("💾 Guardar PIN")
        btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #0D9488;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                border: None;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0F766E;
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
            QMessageBox.critical(self, "PIN Incorrecto", "El PIN actual ingresado no coincide con el guardado en el sistema.")
            return
            
        if len(nuevo) < 4:
            QMessageBox.warning(self, "PIN Muy Corto", "El nuevo PIN debe tener al menos 4 caracteres de longitud.")
            return
            
        if nuevo != confirmar:
            QMessageBox.critical(self, "PINs No Coinciden", "El nuevo PIN y su confirmación no coinciden.")
            return
            
        # Guardar el PIN como HASH en la configuración
        nuevo_hash = hashlib.sha256(nuevo.encode()).hexdigest()
        config.set("local_pin", nuevo_hash)
        QMessageBox.information(self, "PIN Actualizado", "El PIN de seguridad local se ha guardado exitosamente.")
        self.accept()
