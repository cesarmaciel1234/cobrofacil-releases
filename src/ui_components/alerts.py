from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class MensajeAtencion(QDialog):
    def __init__(self, mensaje="Ingresa Artículo Falta Precio", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(550, 250)
        self.mensaje = mensaje
        self.setup_ui()

    def setup_ui(self):
        # VOLVEMOS AL ESTILO INDUSTRIAL (Cian oscuro / Rojo)
        self.setStyleSheet("background-color: #008080; border: 4px solid #FFFFFF;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        header_lbl = QLabel("Mensaje de Atención")
        header_lbl.setAlignment(Qt.AlignCenter)
        header_lbl.setStyleSheet("color: #FF0000; font-size: 24px; font-weight: bold; border: none;")
        layout.addWidget(header_lbl)
        
        msg_lbl = QLabel(self.mensaje)
        msg_lbl.setWordWrap(True)
        msg_lbl.setAlignment(Qt.AlignCenter)
        msg_lbl.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold; border: none; padding: 20px;")
        layout.addWidget(msg_lbl)
        
        layout.addStretch()
        
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        btn_ok = QPushButton("ENT=Sí")
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #DDDDDD;
                color: #000000;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #555;
                padding: 5px 20px;
            }
        """)
        btn_ok.clicked.connect(self.accept)
        footer_layout.addWidget(btn_ok)
        
        btn_esc = QPushButton("✖ ESC=NO")
        btn_esc.setStyleSheet("""
            QPushButton {
                background-color: #DDDDDD;
                color: #000000;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #555;
                padding: 5px 15px;
            }
        """)
        btn_esc.clicked.connect(self.reject)
        footer_layout.addWidget(btn_esc)
        
        layout.addLayout(footer_layout)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.accept()
        super().keyPressEvent(event)
