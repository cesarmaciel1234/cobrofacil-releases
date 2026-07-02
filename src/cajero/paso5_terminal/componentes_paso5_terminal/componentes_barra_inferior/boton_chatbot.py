import os
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from src.utils.paths import get_resource_path

class BotonChatbot(QPushButton):
    def __init__(self, parent=None):
        super().__init__("", parent)
        self.setFixedSize(50, 40)
        icon_path = get_resource_path(os.path.join("src", "assets", "chatbot.svg"))
        self.setIcon(QIcon(icon_path))
        self.setIconSize(QSize(22, 22))
        self.setToolTip("Asistente Virtual")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setObjectName("TerminalBtnChatbot")
