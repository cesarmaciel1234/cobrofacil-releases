from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, QTimer
from src.base_de_datos.database import db_manager
from src.config import config
from src.cajero.cajero_activo import CajeroActivo

class DialogoPIN(QDialog):
    """Diálogo súper simple de PIN de 4 a 6 dígitos."""
    def __init__(self, cajero_nombre, parent=None):
        super().__init__(parent)
        self.cajero_nombre = cajero_nombre
        self.ok = False
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(340, 280)
        self.setObjectName("TerminalDialogoPIN")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 25, 30, 25)
        lay.setSpacing(12)

        lbl = QLabel(f"👤  {self.cajero_nombre.upper()}")
        lbl.setObjectName("DialogoPINLbl1")
        lay.addWidget(lbl)

        lbl2 = QLabel("Ingresa el PIN:")
        lbl2.setObjectName("DialogoPINLbl2")
        lay.addWidget(lbl2)

        self.txt_pin = QLineEdit()
        self.txt_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pin.setMaxLength(6)
        self.txt_pin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_pin.setObjectName("DialogoPINTxt")
        self.txt_pin.returnPressed.connect(self._verificar)
        lay.addWidget(self.txt_pin)

        self.lbl_err = QLabel("")
        self.lbl_err.setObjectName("DialogoPINError")
        lay.addWidget(self.lbl_err)

        btn = QPushButton("✅  INGRESAR")
        btn.setObjectName("DialogoPINBtn")
        btn.clicked.connect(self._verificar)
        lay.addWidget(btn)

        QTimer.singleShot(100, self.txt_pin.setFocus)

    def _verificar(self):
        from src.utils.pin_auth import verify_pin
        entered_pin = self.txt_pin.text().strip()
        
        # Buscar el PIN en la base de datos para el usuario con este nombre
        res = db_manager.execute_query("SELECT pin FROM usuarios WHERE LOWER(username) = ?", (self.cajero_nombre.lower(),))
        pin_valido = None
        
        if res and res[0]['pin']:
            pin_valido = str(res[0]['pin'])
        else:
            # Fallback secundario: si no coincide el nombre configurado del cajero físico, usar el del usuario logueado en la sesión
            curr_usr = config.current_user if hasattr(config, 'current_user') else None
            if curr_usr:
                res_curr = db_manager.execute_query("SELECT pin FROM usuarios WHERE id = ?", (curr_usr.get("id"),))
                if res_curr and res_curr[0]['pin']:
                    pin_valido = str(res_curr[0]['pin'])

        if verify_pin(entered_pin, pin_valido or ""):
            self.ok = True
            self.accept()
        else:
            self.lbl_err.setText("❌ PIN incorrecto")
            self.txt_pin.clear()
            self.txt_pin.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            return  # No se puede saltar el PIN con ESC
        super().keyPressEvent(event)
