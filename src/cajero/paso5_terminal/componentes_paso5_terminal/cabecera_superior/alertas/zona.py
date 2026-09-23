from PyQt6.QtWidgets import QFrame, QHBoxLayout


class ZonaAlertas(QFrame):
    """Hueco de las lámparas. No decide qué alerta va."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TerminalAlertasCabecera")
        self.alertas_layout = QHBoxLayout(self)
        self.alertas_layout.setContentsMargins(0, 0, 0, 0)
        self.alertas_layout.setSpacing(8)
        self.hide()
