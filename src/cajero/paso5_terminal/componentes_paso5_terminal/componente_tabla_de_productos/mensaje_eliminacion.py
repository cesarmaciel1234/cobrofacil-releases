from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt

class MensajeEliminacion(QDialog):
    def __init__(self, nombre_articulo="", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 260)
        self.setObjectName("MensajeEliminacion")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("MensajeEliminacionCard")
        card.setStyleSheet("""
            QFrame#MensajeEliminacionCard {
                background: #FFFFFF;
                border: 3px solid #EF4444;
                border-radius: 18px;
            }
        """)
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(14)

        # Header
        header = QLabel("⚠️  Confirmar Eliminación")
        header.setObjectName("MensajeEliminacionHeader")
        header.setStyleSheet(
            "font-size: 20px; font-weight: 900; color: #EF4444; "
            "border: none; background: transparent; letter-spacing: 0.5px;"
        )
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Body
        body_text = "¿Desea eliminar el artículo del carrito?"
        if nombre_articulo:
            body_text = f"¿Desea eliminar '{nombre_articulo}' del carrito?"
            
        body = QLabel(body_text)
        body.setObjectName("MensajeEliminacionBody")
        body.setStyleSheet(
            "font-size: 15px; color: #475569; font-weight: 600; "
            "border: none; background: transparent;"
        )
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        layout.addWidget(body)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        btn_cancel = QPushButton("  ESC  Cancelar")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(
            "QPushButton { background: #64748B; color: white; font-weight: bold; "
            "font-size: 14px; padding: 12px 20px; border-radius: 10px; border: none; }"
            "QPushButton:hover { background: #475569; }"
        )
        btn_cancel.clicked.connect(self.reject)

        btn_delete = QPushButton("🗑  Eliminar")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setStyleSheet(
            "QPushButton { background: #EF4444; color: white; font-weight: bold; "
            "font-size: 14px; padding: 12px 20px; border-radius: 10px; border: none; }"
            "QPushButton:hover { background: #DC2626; }"
        )
        btn_delete.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel, 1)
        btn_row.addWidget(btn_delete, 1)
        layout.addLayout(btn_row)

        # Hacer que el botón eliminar tenga el foco por defecto
        btn_delete.setFocus()
        btn_delete.setDefault(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
