from PyQt6.QtWidgets import QLabel, QSizePolicy


class EtiquetaVersion(QLabel):
    def __init__(self, version_sistema="COBRO FACIL", parent=None):
        super().__init__(f"🚀 {version_sistema}", parent)
        self.setObjectName("TerminalVersion")
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
