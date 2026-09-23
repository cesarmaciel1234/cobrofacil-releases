import os

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QPushButton

from src.utils.paths import get_resource_path


class BotonChatbot(QPushButton):
    """Abre el asistente. El chat vive en componentes_barra_inferior/chatbot."""

    def __init__(self, parent=None):
        super().__init__("", parent)
        self.setObjectName("TerminalBtnChatbot")
        self.setFixedSize(65, 50)
        icon_path = get_resource_path(os.path.join("src", "assets", "chatbot.svg"))
        self.setIcon(QIcon(icon_path))
        self.setIconSize(QSize(22, 22))
        self.setToolTip("Asistente Virtual")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
