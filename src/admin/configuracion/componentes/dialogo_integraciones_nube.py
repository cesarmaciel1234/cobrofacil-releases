from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton, QGridLayout, QSizePolicy,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QMessageBox, QInputDialog, QCheckBox,
    QFileDialog, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QCursor, QFont, QColor
import os, shutil, datetime, glob
from src.config import config
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager


class DialogoIntegracionesNube(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Integraciones Nube (API)")
        self.setFixedSize(500, 300)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        self._build()

    def _build(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(20, 20, 20, 20)
        main_lay.setSpacing(15)

        lbl_title = QLabel("🌐 Configuración de Servicios en la Nube")
        lbl_title.setStyleSheet(" font-size: 16px; font-weight: bold;")
        main_lay.addWidget(lbl_title)


        # SECCION: Telegram Bot
        box_tg = QFrame()
        box_tg.setStyleSheet(" border: 1px solid #CBD5E1; border-radius: 8px;")
        tg_lay = QVBoxLayout(box_tg)

        lbl_tg = QLabel("☁️ Notificaciones Z por Telegram")
        lbl_tg.setStyleSheet("font-weight: bold; font-size: 13px;  border: none;")
        tg_lay.addWidget(lbl_tg)

        self.txt_tg_token = QLineEdit(config.get("telegram_token", ""))
        self.txt_tg_token.setPlaceholderText("Token del Bot (ej: 123456:ABC-DEF...)")
        self.txt_tg_token.setEchoMode(QLineEdit.Password)
        self.txt_tg_token.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px;")
        tg_lay.addWidget(QLabel("Bot Token:"))
        tg_lay.addWidget(self.txt_tg_token)

        self.txt_tg_chat = QLineEdit(config.get("telegram_chat_id", ""))
        self.txt_tg_chat.setPlaceholderText("ID de Chat (ej: -100123456789)")
        self.txt_tg_chat.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px;")
        tg_lay.addWidget(QLabel("Chat ID:"))
        tg_lay.addWidget(self.txt_tg_chat)

        main_lay.addWidget(box_tg)

        main_lay.addStretch()

        # Botones Inferiores
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("padding: 8px 15px; border: none;  border-radius: 4px;")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 Guardar Credenciales")
        btn_save.setStyleSheet("padding: 8px 15px; font-weight: bold; background-color: #3B82F6; color: white;  border-radius: 4px; border: none;")
        btn_save.clicked.connect(self._guardar)

        h_btns.addWidget(btn_cancel)
        h_btns.addStretch()
        h_btns.addWidget(btn_save)

        main_lay.addLayout(h_btns)

    def _guardar(self):
        config.set("telegram_token", self.txt_tg_token.text().strip())
        config.set("telegram_chat_id", self.txt_tg_chat.text().strip())

        QMessageBox.information(self, "Guardado", "Credenciales de la nube guardadas correctamente en config.json.")
        self.accept()


