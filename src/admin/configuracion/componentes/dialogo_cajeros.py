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
        self.txt_pin.setPlaceholderText("PIN (vacío = no cambiar)")
        self.txt_pin.setMaxLength(6)
        self.txt_pin.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px; font-weight: bold;")
        self.current_user_id = None

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

                pin_val = str(r['pin'] or '')
                pin_es_hash = len(pin_val) == 64  # SHA-256 = 64 hex chars
                
                if pin_es_hash:
                    # PIN hasheado: mostrar indicador seguro
                    pin_it = QTableWidgetItem("✓ Configurado")
                    pin_it.setForeground(QColor("#16A34A"))
                    pin_it.setFont(QFont("Segoe UI", 9, QFont.Bold))
                elif pin_val:
                    # PIN en texto plano (legado): mostrarlo para que el usuario lo actualice
                    pin_it = QTableWidgetItem(f"⚠ {pin_val}")
                    pin_it.setForeground(QColor("#D97706"))
                else:
                    pin_it = QTableWidgetItem("Sin PIN")
                    pin_it.setForeground(QColor("#94A3B8"))
                    
                pin_it.setTextAlignment(Qt.AlignCenter)
                self.tabla.setItem(i, 3, pin_it)

    def _al_seleccionar(self, item):
        row = self.tabla.currentRow()
        self.current_user_id = self.tabla.item(row, 0).text()
        self.txt_user.setText(self.tabla.item(row, 1).text())
        rol = self.tabla.item(row, 2).text().lower()
        idx = self.cmb_rol.findText(rol)
        if idx >= 0: self.cmb_rol.setCurrentIndex(idx)
        self.txt_pass.clear()
        self.txt_pin.clear()

    def guardar_usuario(self):
        usr = self.txt_user.text().strip()
        pwd = self.txt_pass.text().strip()
        rol = self.cmb_rol.currentText()
        pin = self.txt_pin.text().strip()
        if not usr: return
        
        import hashlib
        
        if getattr(self, 'current_user_id', None):
            # Update existing user
            uid = self.current_user_id
            
            query = "UPDATE usuarios SET username = ?, rol = ?"
            params = [usr, rol]
            
            if pwd:
                query += ", password_hash = ?"
                params.append(hashlib.sha256(pwd.encode()).hexdigest())
                
            if pin:
                query += ", pin = ?"
                params.append(hashlib.sha256(pin.encode()).hexdigest())
                
            query += " WHERE id = ?"
            params.append(uid)
            
            db_manager.execute_non_query(query, tuple(params))
        else:
            # Create new user
            if not pin: pin = "1234"
            if not pwd: pwd = usr # Default password is the username
            h = hashlib.sha256(pwd.encode()).hexdigest()
            h_pin = hashlib.sha256(pin.encode()).hexdigest()
            db_manager.execute_non_query("INSERT INTO usuarios (username, password_hash, rol, pin) VALUES (?, ?, ?, ?)", (usr, h, rol, h_pin))
        
        self.txt_user.clear(); self.txt_pass.clear(); self.txt_pin.clear(); self.current_user_id = None
        self.cargar_usuarios()

    def eliminar_usuario(self):
        row = self.tabla.currentRow()
        if row < 0: return
        uid = self.tabla.item(row, 0).text()
        if uid == "1":
            QMessageBox.warning(self, "Protección", "El administrador raíz no puede ser eliminado.")
            return
        if QMessageBox.question(self, "Eliminar", f"¿Eliminar a {self.tabla.item(row, 1).text()}?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            db_manager.execute_non_query("DELETE FROM usuarios WHERE id = ?", (uid,))
            self.cargar_usuarios()

