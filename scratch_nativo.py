from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt

class DialogoPagarCuentaNativo(QDialog):
    def __init__(self, cliente_nombre, deuda_anterior, total_venta, parent=None):
        super().__init__(parent)
        self.setWindowTitle('PAGAR CUENTA - Paso 6')
        self.setFixedSize(600, 400)
        self.setStyleSheet('''
            QDialog { background: #F8FAFC; border-radius: 16px; border: 2px solid #CBD5E1; }
            QLabel { font-family: 'Segoe UI', Arial; }
        ''')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        # ... logic
        