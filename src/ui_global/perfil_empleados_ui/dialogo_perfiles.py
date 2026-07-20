import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QFrame, QGridLayout, 
    QLineEdit, QComboBox, QPushButton, QMessageBox, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from src.config import config
from src.cerebro_global.perfil_empleados_cerebro.gestor_perfiles import GestorPerfiles

class DialogoPerfiles(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("👥 Gestión de Personal - Cobro Fácil POS")
        self.setFixedSize(700, 600)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        
        # Determinar jerarquía del usuario logueado
        user_info = getattr(config, 'current_user', {})
        self.rol_actual = user_info.get('rol', 'cajero').lower()
        
        self.setup_ui()

    def setup_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(30, 30, 30, 30)
        main_lay.setSpacing(15)

        # --- HEADER ---
        header_text = "👥 Gestión de Perfiles"
        if self.rol_actual == 'admin':
            header_text = "👥 Gestión de Cajeros y Auxiliares"
            
        header = QLabel(header_text)
        header.setStyleSheet("font-size: 22px; font-weight: bold; border:none;")
        main_lay.addWidget(header)
        
        lbl_info = QLabel("Administra los accesos y roles del personal de tu negocio.")
        lbl_info.setStyleSheet("font-size: 13px; margin-bottom: 5px; border:none; color: gray;")
        main_lay.addWidget(lbl_info)

        # --- TABLA PREMIUM ---
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["ID", "USUARIO", "ROL / RANGO", "PIN"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setShowGrid(False)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet("""
            QTableWidget { 
                background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; 
                gridline-color: transparent;
            }
            QTableWidget::item:selected {
                background-color: #EFF6FF;
                color: black;
            }
            QHeaderView::section { 
                 padding: 15px; border: none; 
                font-weight: 900; font-size: 11px; text-transform: uppercase;
            }
        """)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
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
        lbl_card.setStyleSheet("font-weight: 900; font-size: 11px; border: none;")
        card_lay.addWidget(lbl_card)

        # Formulario
        f_lay = QGridLayout()
        f_lay.setSpacing(12)

        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Nombre de Usuario...")
        self.txt_user.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px; font-weight: bold;")
        
        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Contraseña (vacío para no cambiar)")
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px;")
        
        self.cmb_rol = QComboBox()
        # JERARQUÍA: Jefe puede crear jefes. Admin solo cajeros/auxiliares.
        roles_permitidos = ["cajero", "auxiliar"]
        if self.rol_actual == 'jefe':
            roles_permitidos.extend(["admin", "jefe"])
            
        self.cmb_rol.addItems(roles_permitidos)
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
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet("border: 1px solid #FECACA; padding: 12px; border-radius: 10px; font-weight: bold; color: #EF4444;")
        btn_del.clicked.connect(self.eliminar_usuario)
        
        btn_save = QPushButton("💾 Guardar Usuario")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet("background-color: #3B82F6; color: white; padding: 12px; border-radius: 10px; font-weight: bold; border: none;")
        btn_save.clicked.connect(self.guardar_usuario)
        
        b_lay.addWidget(btn_del, 1)
        b_lay.addStretch()
        b_lay.addWidget(btn_save, 2)
        card_lay.addLayout(b_lay)

        main_lay.addWidget(card)

    def cargar_usuarios(self):
        self.tabla.setRowCount(0)
        usuarios = GestorPerfiles.obtener_usuarios_permitidos(self.rol_actual)
        
        for i, u in enumerate(usuarios):
            self.tabla.insertRow(i)
            self.tabla.setRowHeight(i, 45)
            
            id_it = QTableWidgetItem(str(u['id']))
            id_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(i, 0, id_it)
            
            usr_it = QTableWidgetItem(u['username'])
            usr_it.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tabla.setItem(i, 1, usr_it)
            
            rol = u['rol'].upper()
            rol_it = QTableWidgetItem(rol)
            rol_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            rol_it.setFont(QFont("Segoe UI", 9, QFont.Weight.Black))
            
            if rol == "JEFE": rol_it.setForeground(QColor("#B45309")) # Naranja oscuro
            elif rol == "ADMIN": rol_it.setForeground(QColor("#1E3A8A"))
            elif rol == "AUXILIAR": rol_it.setForeground(QColor("#059669"))
            else: rol_it.setForeground(QColor("#475569"))
            self.tabla.setItem(i, 2, rol_it)

            pin_val = str(u['pin'] or '')
            pin_es_hash = len(pin_val) == 64
            
            if pin_es_hash:
                pin_it = QTableWidgetItem("🔒 Configurado")
                pin_it.setForeground(QColor("#16A34A"))
                pin_it.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            elif pin_val:
                pin_it = QTableWidgetItem(f"⚠️ {pin_val}")
                pin_it.setForeground(QColor("#D97706"))
            else:
                pin_it = QTableWidgetItem("Sin PIN")
                pin_it.setForeground(QColor("#94A3B8"))
                
            pin_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(i, 3, pin_it)

    def _al_seleccionar(self, item):
        row = self.tabla.currentRow()
        self.current_user_id = int(self.tabla.item(row, 0).text())
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
        if not usr: 
            return
            
        try:
            GestorPerfiles.crear_o_actualizar_usuario(self.current_user_id, usr, pwd, rol, pin)
            QMessageBox.information(self, "Éxito", "Usuario guardado correctamente.")
            self.txt_user.clear()
            self.txt_pass.clear()
            self.txt_pin.clear()
            self.current_user_id = None
            self.cargar_usuarios()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")

    def eliminar_usuario(self):
        if not self.current_user_id:
            QMessageBox.warning(self, "Aviso", "Selecciona un usuario de la lista.")
            return
            
        ans = QMessageBox.question(self, "Confirmar", "¿Eliminar este usuario?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ans == QMessageBox.StandardButton.Yes:
            try:
                GestorPerfiles.eliminar_usuario(self.current_user_id)
                self.current_user_id = None
                self.txt_user.clear()
                self.txt_pass.clear()
                self.txt_pin.clear()
                self.cargar_usuarios()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar: {e}")
