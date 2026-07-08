from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QFormLayout, QSpinBox)
from PyQt6.QtCore import Qt
from src.config import config

class DialogoConfiguracionCarteleria(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Cartelería (PC Maestra)")
        self.setFixedSize(450, 350)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f4f8;
            }
            QLabel {
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit, QSpinBox {
                font-size: 14px;
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                color: white;
                background-color: #2980b9;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)

        layout = QVBoxLayout(self)
        
        titulo = QLabel("Ajustes Globales de Cartelería")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        form = QFormLayout()
        
        # Nombre del Negocio
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setText(config.get("business_name", "Carnicería"))
        form.addRow("Nombre del Negocio:", self.txt_nombre)
        
        # Teléfono
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setText(config.get("phone", "No disponible"))
        form.addRow("Teléfono de Contacto:", self.txt_telefono)
        
        # IP Maestra
        self.txt_ip = QLineEdit()
        self.txt_ip.setText(config.get("carteleria_master_ip", ""))
        self.txt_ip.setPlaceholderText("Ej: 192.168.0.53 (Dejar vacío si es esta misma PC)")
        form.addRow("IP Caja Maestra:", self.txt_ip)

        # Rotacion
        self.spin_rotacion = QSpinBox()
        self.spin_rotacion.setRange(5, 120)
        self.spin_rotacion.setSuffix(" seg")
        self.spin_rotacion.setValue(config.get("carteleria_rotacion", 15))
        form.addRow("Tiempo Rotación Banderín:", self.spin_rotacion)

        # SOS Tiempo
        self.spin_sos_tiempo = QSpinBox()
        self.spin_sos_tiempo.setRange(5, 60)
        self.spin_sos_tiempo.setSuffix(" seg")
        self.spin_sos_tiempo.setValue(config.get("carteleria_tiempo_sos", 10))
        form.addRow("Duración Oferta SOS:", self.spin_sos_tiempo)

        # SOS Frec
        self.spin_sos_frec = QSpinBox()
        self.spin_sos_frec.setRange(1, 10)
        self.spin_sos_frec.setSuffix(" ciclos")
        self.spin_sos_frec.setValue(config.get("carteleria_frec_sos", 2))
        form.addRow("Frecuencia SOS:", self.spin_sos_frec)

        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_guardar = QPushButton("Guardar Cambios")
        btn_guardar.clicked.connect(self._guardar)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background-color: #95a5a6;")
        btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        
        layout.addLayout(btn_layout)

    def _guardar(self):
        config.set("business_name", self.txt_nombre.text().strip())
        config.set("phone", self.txt_telefono.text().strip())
        config.set("carteleria_master_ip", self.txt_ip.text().strip())
        config.set("carteleria_rotacion", self.spin_rotacion.value())
        config.set("carteleria_tiempo_sos", self.spin_sos_tiempo.value())
        config.set("carteleria_frec_sos", self.spin_sos_frec.value())
        config.save()
        
        QMessageBox.information(self, "Guardado", "La configuración de la cartelería se ha guardado correctamente.\n(Los cambios se reflejarán instantáneamente en la pantalla).")
        self.accept()
