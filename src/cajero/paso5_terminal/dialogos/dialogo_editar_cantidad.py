from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QDoubleSpinBox, QPushButton
from PyQt6.QtCore import Qt

class DialogoEditarCantidad(QDialog):
    def __init__(self, cant_actual, nombre, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(540, 340)
        self.setObjectName("TerminalDialogoEditarCantidad")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        box = QFrame()
        box.setObjectName("EditCantDialog")
        outer.addWidget(box)

        layout = QVBoxLayout(box)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        lbl_prod = QLabel(f"MODIFICAR: {nombre.upper()}")
        lbl_prod.setObjectName("EditCantProducto")
        layout.addWidget(lbl_prod)

        lbl_title = QLabel("CANTIDAD")
        lbl_title.setObjectName("EditCantTitle")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        self.spin = QDoubleSpinBox()
        self.spin.setRange(0.001, 9999.999)
        self.spin.setDecimals(3)
        self.spin.setValue(cant_actual)
        self.spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin.setFocus()
        self.spin.selectAll()
        self.spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        layout.addWidget(self.spin)

        btns = QHBoxLayout()
        btns.setSpacing(12)
        btn_ok = QPushButton("✅ CONFIRMAR (ENTER)")
        btn_ok.setObjectName("EditCantOk")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.clicked.connect(self.accept)

        btn_cancel = QPushButton("❌ CANCELAR (ESC)")
        btn_cancel.setObjectName("EditCantCancel")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)

        btns.addWidget(btn_ok, 1)
        btns.addWidget(btn_cancel, 1)
        layout.addLayout(btns)

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self.accept()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def get_value(self):
        return self.spin.value()
