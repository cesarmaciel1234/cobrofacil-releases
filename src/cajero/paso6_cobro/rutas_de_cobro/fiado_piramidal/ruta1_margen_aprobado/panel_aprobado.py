# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal

class PanelMargenAprobado(QFrame):
    confirmado = pyqtSignal(int, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelVerde")
        self.setStyleSheet("""
            QFrame#PanelVerde {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10B981, stop:1 #047857);
                border-radius: 16px;
                border: 2px solid #064E3B;
            }
        """)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(15)

        self.icono = QLabel("\u2714") # Heavy check mark
        self.icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icono.setStyleSheet("color: #FFFFFF; font-size: 100px; font-weight: bold; margin-bottom: 10px;")
        lay.addWidget(self.icono)

        self.lbl_titulo = QLabel("APROBADO")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("color: #FFFFFF; font-size: 40px; font-weight: 900; letter-spacing: 4px;")
        lay.addWidget(self.lbl_titulo)

        self.lbl_nombre = QLabel("NOMBRE CLIENTE")
        self.lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_nombre.setStyleSheet("color: #D1FAE5; font-size: 24px; font-weight: 700;")
        lay.addWidget(self.lbl_nombre)

        lay.addStretch()

        self.btn_confirmar = QLabel("[ ENTER ] CONFIRMAR")
        self.btn_confirmar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_confirmar.setStyleSheet(
            "QLabel { color: #047857; background-color: #FFFFFF; font-size: 24px; font-weight: 900; "
            "border-radius: 12px; padding: 20px; text-transform: uppercase; letter-spacing: 2px; }"
        )
        lay.addWidget(self.btn_confirmar)
        
        lay.addSpacing(15)
        
        

    def poblar(self, datos):
        from PyQt6.QtCore import QTimer
        self._datos = datos
        nombre_raw = str(datos.get('nombre', '') or '').strip()
        nombre_amable = nombre_raw.title() if (nombre_raw.isupper() or nombre_raw.islower()) else nombre_raw
        if nombre_amable:
            self.lbl_nombre.setText(f"¡Hola, {nombre_amable}! 👋")
        else:
            self.lbl_nombre.setText("Cliente Aprobado")
        self._listo_para_enter = False
        # Evitar que el mismo Enter del buscador filtre y confirme en el mismo frame
        QTimer.singleShot(350, self._armar_enter)

    def _armar_enter(self):
        self._listo_para_enter = True

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if getattr(self, '_listo_para_enter', False):
                self.confirmado.emit(int(self._datos['id']), 0.0)
        else:
            event.ignore()
