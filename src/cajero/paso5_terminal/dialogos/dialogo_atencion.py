from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt

class DialogoAtencion(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 260)
        self.setObjectName("TerminalDialogoAtencion")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("DialogoAtencionCard")
        card.setStyleSheet("""
            QFrame#DialogoAtencionCard {
                background: #FFFFFF;
                border: 3px solid #1E3A8A;
                border-radius: 18px;
            }
        """)
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(14)

        # Header
        header = QLabel("⚠️  Confirmar Eliminación")
        header.setObjectName("TerminalDialogoAtencionHeader")
        header.setStyleSheet(
            "font-size: 20px; font-weight: 900; color: #1E3A8A; "
            "border: none; background: transparent; letter-spacing: 0.5px;"
        )
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Body
        body = QLabel("¿Desea eliminar el artículo del carrito?")
        body.setObjectName("TerminalDialogoAtencionBody")
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
            "QPushButton { background: #2563EB; color: white; font-weight: bold; "
            "font-size: 14px; padding: 12px 20px; border-radius: 10px; border: none; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_cancel.clicked.connect(self.reject)

        btn_delete = QPushButton("🗑  Eliminar")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setStyleSheet(
            "QPushButton { background: #DC2626; color: white; font-weight: bold; "
            "font-size: 14px; padding: 12px 20px; border-radius: 10px; border: none; }"
            "QPushButton:hover { background: #B91C1C; }"
        )
        btn_delete.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel, 1)
        btn_row.addWidget(btn_delete, 1)
        layout.addLayout(btn_row)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.accept()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
