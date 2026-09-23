from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, QTimer
from src.base_de_datos.database import db_manager
from src.config import config

_ESTILO = """
QDialog#TerminalDialogoPIN {
    background: #FFFFFF;
    border: 2px solid #1E3A8A;
    border-radius: 16px;
}
QDialog#TerminalDialogoPIN QLabel {
    background: transparent;
    border: none;
    color: #1E3A8A;
}
QLabel#DialogoPINLbl1 {
    font-size: 20px;
    font-weight: 900;
    color: #1E3A8A;
}
QLabel#DialogoPINLbl2 {
    font-size: 13px;
    font-weight: 600;
    color: #64748B;
}
QLineEdit#DialogoPINTxt {
    font-size: 28px;
    font-weight: 900;
    letter-spacing: 10px;
    border: 2px solid #CBD5E1;
    border-radius: 10px;
    padding: 12px;
    min-height: 52px;
    background: #F8FAFC;
    color: #0F172A;
}
QLineEdit#DialogoPINTxt:focus {
    border: 2px solid #2563EB;
    background: #FFFFFF;
}
QLabel#DialogoPINError {
    font-size: 12px;
    font-weight: 700;
    color: #B91C1C;
    min-height: 18px;
}
QPushButton#DialogoPINBtn {
    background: #1E3A8A;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 900;
    border: none;
    border-radius: 10px;
    padding: 12px;
    min-height: 48px;
}
QPushButton#DialogoPINBtn:hover { background: #2563EB; }
QPushButton#DialogoPINCancel {
    background: transparent;
    color: #64748B;
    border: none;
    font-size: 13px;
    font-weight: 600;
    min-height: 32px;
}
"""


class DialogoPIN(QDialog):
    """PIN de 4 a 6 dígitos. Esc cancela (no saltea el candado del padre)."""

    def __init__(self, cajero_nombre, parent=None):
        super().__init__(parent)
        self.cajero_nombre = cajero_nombre
        self.ok = False
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(380, 340)
        self.setObjectName("TerminalDialogoPIN")
        self.setStyleSheet(_ESTILO)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(10)

        lbl = QLabel(str(self.cajero_nombre or "").upper())
        lbl.setObjectName("DialogoPINLbl1")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl)

        lbl2 = QLabel("Ingresá el PIN")
        lbl2.setObjectName("DialogoPINLbl2")
        lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl2)

        self.txt_pin = QLineEdit()
        self.txt_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pin.setMaxLength(6)
        self.txt_pin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_pin.setObjectName("DialogoPINTxt")
        self.txt_pin.setPlaceholderText("••••")
        self.txt_pin.returnPressed.connect(self._verificar)
        lay.addWidget(self.txt_pin)

        self.lbl_err = QLabel("")
        self.lbl_err.setObjectName("DialogoPINError")
        self.lbl_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.lbl_err)

        btn = QPushButton("INGRESAR")
        btn.setObjectName("DialogoPINBtn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._verificar)
        lay.addWidget(btn)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("DialogoPINCancel")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        lay.addWidget(btn_cancel)

        QTimer.singleShot(80, self.txt_pin.setFocus)

    def _verificar(self):
        from src.utils.pin_auth import verify_pin
        entered_pin = self.txt_pin.text().strip()
        if not entered_pin:
            self.lbl_err.setText("Ingresá el PIN")
            self.txt_pin.setFocus()
            return

        res = db_manager.execute_query(
            "SELECT pin FROM usuarios WHERE LOWER(username) = ?",
            (self.cajero_nombre.lower(),),
        )
        pin_valido = None
        if res and res[0]["pin"]:
            pin_valido = str(res[0]["pin"])
        else:
            curr_usr = config.current_user if hasattr(config, "current_user") else None
            if curr_usr:
                res_curr = db_manager.execute_query(
                    "SELECT pin FROM usuarios WHERE id = ?", (curr_usr.get("id"),)
                )
                if res_curr and res_curr[0]["pin"]:
                    pin_valido = str(res_curr[0]["pin"])

        if verify_pin(entered_pin, pin_valido or ""):
            self.ok = True
            self.accept()
            return
        self.lbl_err.setText("PIN incorrecto")
        self.txt_pin.clear()
        self.txt_pin.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)
