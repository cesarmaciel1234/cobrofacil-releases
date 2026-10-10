# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

class PanelClienteNuevo(QWidget):
    cliente_creado = pyqtSignal(dict) # Emits the dict of the new client

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(15)

        self.lbl_titulo = QLabel("NUEVO CLIENTE")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("color: #2563EB; font-size: 32px; font-weight: 900; letter-spacing: 2px;")
        lay.addWidget(self.lbl_titulo)
        
        self.lbl_sub = QLabel("Se crear\xe1 y asignar\xe1 un l\xedmite base de $50,000")
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sub.setStyleSheet("color: #64748B; font-size: 16px; font-weight: bold;")
        lay.addWidget(self.lbl_sub)
        
        self.txt_input = QLineEdit()
        self.txt_input.setPlaceholderText("Nombre del cliente...")
        self.txt_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_input.setStyleSheet("background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; padding: 10px; font-size: 24px; font-weight: bold; color: #0F172A;")
        lay.addWidget(self.txt_input)
        
        self.btn_crear = QPushButton("[ ENTER ] CREAR Y EVALUAR")
        self.btn_crear.setStyleSheet("background-color: #2563EB; color: white; font-size: 20px; font-weight: bold; padding: 15px; border-radius: 8px;")
        self.btn_crear.clicked.connect(self._procesar)
        lay.addWidget(self.btn_crear)
        
        lay.addStretch(1)

    def poblar_inicial(self, texto_buscado):
        self.txt_input.setText(texto_buscado)
        self.txt_input.setFocus()
        
    def _procesar(self):
        nombre = self.txt_input.text().strip()
        if not nombre:
            return
            
        from src.clientes_fiado.cerebro.cerebro import crear_cliente
        # Límite por defecto sugerido por el usuario: 50.000
        cliente_id, msg = crear_cliente(nombre, "", limite=50000.0)
        
        if cliente_id:
            # We return the dictionary pretending to be the search engine so route 1 or 2 handles it
            nuevo_datos = {
                'id': cliente_id,
                'nombre': nombre,
                'limite': 50000.0,
                'deuda': 0.0
            }
            self.cliente_creado.emit(nuevo_datos)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self._procesar()
        else:
            event.ignore()
