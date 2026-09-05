from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from src.config import config

class PanelDatosNegocio(QWidget):
    """
    Componente Global para la edición de los Datos del Negocio (Nombre, Dirección, Teléfono, etc).
    Se utiliza tanto en el Administrador (Diseñador de Tickets) como en Cartelería.
    """
    datos_actualizados = pyqtSignal() # Emitido cuando el usuario guarda o cambia texto

    def __init__(self, parent=None, show_save_button=True):
        super().__init__(parent)
        self.show_save_button = show_save_button
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        self.setStyleSheet("background: #FFFFFF; border-radius: 6px; border: 1px solid #E2E8F0;")
        self.setGraphicsEffect(None)
        
        form_layout = QVBoxLayout(self)
        form_layout.setContentsMargins(25, 25, 25, 25)
        
        lbl_title = QLabel("📝 Datos del Negocio")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; border: none;")
        form_layout.addWidget(lbl_title)
        form_layout.addSpacing(10)
        
        self.txt_name = QLineEdit()
        self.txt_addr = QLineEdit()
        self.txt_phone = QLineEdit()
        self.txt_cuit = QLineEdit()
        self.txt_msg = QLineEdit()
        
        for txt, lbl in [
            (self.txt_name, "Nombre Comercial (Logotipo):"),
            (self.txt_addr, "Dirección Comercial:"),
            (self.txt_phone, "Teléfono / Contacto:"),
            (self.txt_cuit, "CUIT / RUT / NIT:"),
            (self.txt_msg, "Mensaje de Despedida:")
        ]:
            l = QLabel(lbl)
            l.setStyleSheet("font-size: 13px; font-weight: bold; border: none; color: #334155;")
            txt.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px; color: black; font-size: 13px; background: white;")
            txt.textChanged.connect(self._on_text_changed)
            form_layout.addWidget(l)
            form_layout.addWidget(txt)
            form_layout.addSpacing(5)
            
        form_layout.addStretch()
        
        if self.show_save_button:
            self.btn_save = QPushButton("💾 Guardar y Aplicar")
            self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.btn_save.setStyleSheet("background-color: #3B82F6; color: white; padding: 12px; font-weight: bold; border-radius: 6px; font-size: 14px; border: none;")
            self.btn_save.clicked.connect(self.guardar)
            form_layout.addWidget(self.btn_save)

    def _load_data(self):
        self.txt_name.setText(config.get('business_name', ''))
        self.txt_addr.setText(config.get('address', ''))
        self.txt_phone.setText(config.get('phone', ''))
        self.txt_cuit.setText(config.get('business_cuit', ''))
        self.txt_msg.setText(config.get('footer_message', ''))

    def _on_text_changed(self):
        self.datos_actualizados.emit()

    def guardar(self):
        config.set('business_name', self.txt_name.text().strip())
        config.set('address', self.txt_addr.text().strip())
        config.set('phone', self.txt_phone.text().strip())
        config.set('business_cuit', self.txt_cuit.text().strip())
        config.set('footer_message', self.txt_msg.text().strip())
        config.save()
        
        QMessageBox.information(self, "Guardado", "Datos del negocio actualizados correctamente.")

    def get_data(self):
        return {
            "business_name": self.txt_name.text().strip(),
            "address": self.txt_addr.text().strip(),
            "phone": self.txt_phone.text().strip(),
            "business_cuit": self.txt_cuit.text().strip(),
            "footer_message": self.txt_msg.text().strip()
        }
