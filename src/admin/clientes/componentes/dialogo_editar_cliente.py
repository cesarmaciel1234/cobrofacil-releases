from src.utils.qt_compat import qt_exec
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLineEdit, QMessageBox, QDialog, 
                             QFormLayout, QDoubleSpinBox, QGraphicsDropShadowEffect, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor
from src.base_de_datos.database import DatabaseManager
from src.repositories.cliente_repository import ClienteRepository, FIADO_EXPRESS_LIMITE_DEFAULT


from src.admin.clientes.theme import _CLI

class DialogoEditarCliente(QDialog):
    """Editar nombre, teléfono, dirección y perfil del cliente."""

    def __init__(self, cliente_id: int, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.db = DatabaseManager()
        self.cliente = ClienteRepository.obtener_por_id(cliente_id) or {}
        self.setWindowTitle("Editar cliente")
        self.setFixedSize(420, 440)
        self.setStyleSheet(f"""
            QDialog {{ background: {_CLI['bg']}; }}
            QLabel {{ color: #334155; font-weight: 700; border: none; }}
            QLineEdit, QComboBox {{
                padding: 10px 12px; border: 1px solid {_CLI['border']};
                border-radius: 10px; background: white; font-size: 14px; color: {_CLI['text']};
            }}
            QLineEdit:focus, QComboBox:focus {{ border: 1px solid {_CLI['accent']}; }}
        """)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(14)

        tit = QLabel("✏️  EDITAR DATOS DEL CLIENTE")
        tit.setStyleSheet("font-size: 16px; font-weight: 900; color: #1E293B;")
        lay.addWidget(tit)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_nombre = QLineEdit(dict(self.cliente).get("nombre", ""))
        self.txt_nombre.setPlaceholderText("Nombre completo")

        dni_guardado = (dict(self.cliente).get("dni") or "").strip()
        self.txt_dni = QLineEdit(dni_guardado)
        self.txt_dni.setPlaceholderText("7+ dígitos")

        telefono = (dict(self.cliente).get("telefono") or "").strip()
        if telefono and telefono == dni_guardado:
            telefono = ""
        self.txt_telefono = QLineEdit(telefono)
        self.txt_telefono.setPlaceholderText("Teléfono / WhatsApp (opcional)")

        self.txt_direccion = QLineEdit(dict(self.cliente).get("direccion") or "")
        self.txt_direccion.setPlaceholderText("Calle, número, barrio…")

        self.cmb_perfil = QComboBox()
        self.cmb_perfil.addItem("⚡ Express (fiado mostrador)", "express")
        self.cmb_perfil.addItem("Regular (cuenta habitual)", "regular")
        tipo = (dict(self.cliente).get("tipo_cliente") or "regular").lower()
        self.cmb_perfil.setCurrentIndex(0 if tipo == "express" else 1)

        form.addRow("Nombre:", self.txt_nombre)
        form.addRow("DNI:", self.txt_dni)
        form.addRow("Teléfono:", self.txt_telefono)
        form.addRow("Dirección:", self.txt_direccion)
        form.addRow("Perfil:", self.cmb_perfil)
        lay.addLayout(form)
        lay.addStretch()

        foot = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet(
            "QPushButton { background: #E2E8F0; color: #475569; font-weight: 700; "
            "padding: 10px 20px; border-radius: 8px; border: none; }"
        )
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Guardar")
        btn_ok.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_ok.setStyleSheet(
            "QPushButton { background: #10B981; color: white; font-weight: 900; "
            "padding: 10px 24px; border-radius: 8px; border: none; }"
            "QPushButton:hover { background: #059669; }"
        )
        btn_ok.clicked.connect(self._guardar)
        foot.addWidget(btn_cancel)
        foot.addStretch()
        foot.addWidget(btn_ok)
        lay.addLayout(foot)

        self.txt_nombre.setFocus()
        self.txt_nombre.selectAll()

    def _guardar(self):
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Datos incompletos", "El nombre es obligatorio.")
            return

        dni_raw = self.txt_dni.text().strip()
        dni = ClienteRepository.normalizar_dni(dni_raw) if dni_raw else None
        if dni_raw and not dni:
            QMessageBox.warning(self, "DNI inválido", "El DNI debe tener al menos 7 dígitos.")
            return
        if dni:
            otro = ClienteRepository.buscar_por_dni(dni)
            if otro and int(dict(otro).get("id", 0)) != int(self.cliente_id):
                QMessageBox.warning(self, "DNI duplicado", f"El DNI {dni} ya pertenece a otro cliente.")
                return

        telefono = self.txt_telefono.text().strip()
        direccion = self.txt_direccion.text().strip()
        tipo = self.cmb_perfil.currentData() or "regular"
        ok = self.db.execute_non_query(
            "UPDATE clientes SET nombre = ?, dni = ?, telefono = ?, direccion = ?, tipo_cliente = ? WHERE id = ?",
            (nombre, dni, telefono or None, direccion or None, tipo, self.cliente_id),
        )
        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudieron guardar los cambios.")


