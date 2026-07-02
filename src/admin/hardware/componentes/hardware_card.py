from src.utils.theme_manager import theme_manager
import os
import sys
import time
import webbrowser
import subprocess
import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QScrollArea, QGridLayout, 
                             QMessageBox, QComboBox, QPlainTextEdit, QGroupBox, QGraphicsDropShadowEffect)
from src.utils.qt_compat import invoke_method, pyqtSlot
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QIcon

try:
    from PyQt6.QtPrintSupport import QPrinterInfo, QPrinter
except ImportError:
    QPrinterInfo = None
    QPrinter = None

from src.config import config


class HardwareCard(QFrame):
    def __init__(self, title, description, icon, download_url=None, action_callback=None, btn_text="📥 DESCARGAR DRIVER", btn_color="#6366f1", hover_color="#4f46e5"):
        super().__init__()
        self.download_url = download_url
        self.setFixedSize(300, 190)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #f8fafc);
                border: 1px solid #e2e8f0;
                border-radius: 20px;
            }
            QFrame:hover {
                border: 2px solid #6366f1;
                
            }
        """)
        
        # Sombra de impacto suave
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15); shadow.setXOffset(0); shadow.setYOffset(4); shadow.setColor(QColor(0,0,0,30))
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self); layout.setContentsMargins(20,20,20,20); layout.setSpacing(8)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 32px; border: none; background: transparent;")
        layout.addWidget(lbl_icon)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-weight: 900; font-size: 15px;  border: none; background: transparent;")
        layout.addWidget(lbl_title)
        
        lbl_desc = QLabel(description)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(" font-size: 11px; border: none; background: transparent; line-height: 14px;")
        layout.addWidget(lbl_desc)
        
        layout.addStretch()
        
        if action_callback or download_url:
            btn = QPushButton(btn_text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {btn_color}; color: white; border: none; padding: 10px; 
                    border-radius: 12px; font-weight: 800; font-size: 10px;
                }}
                QPushButton:hover {{ background: {hover_color}; }}
            """)
            if action_callback:
                btn.clicked.connect(action_callback)
            else:
                btn.clicked.connect(lambda: webbrowser.open(self.download_url))
            layout.addWidget(btn)

