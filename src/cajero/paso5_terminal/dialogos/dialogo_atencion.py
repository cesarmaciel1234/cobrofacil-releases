from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

class DialogoAtencion(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(500, 300)
        self.setObjectName("TerminalDialogoAtencion")
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Mensaje de Atención")
        header.setObjectName("TerminalDialogoAtencionHeader")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Body
        body = QLabel("Cancelar\n¿Desea eliminar el artículo?")
        body.setObjectName("TerminalDialogoAtencionBody")
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(body)
        
        layout.addStretch()
        
        # Footer
        footer = QHBoxLayout()
        lbl_ent = QLabel("ENT-Continuar")
        lbl_ent.setObjectName("TerminalDialogoAtencionEnt")
        lbl_esc = QLabel("ESC-NO")
        lbl_esc.setObjectName("TerminalDialogoAtencionEsc")
        footer.addWidget(lbl_ent)
        footer.addStretch()
        footer.addWidget(lbl_esc)
        layout.addLayout(footer)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.accept()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
