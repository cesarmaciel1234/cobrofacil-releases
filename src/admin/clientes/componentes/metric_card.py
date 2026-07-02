from src.utils.qt_compat import qt_exec
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLineEdit, QMessageBox, QDialog, 
                             QFormLayout, QDoubleSpinBox, QGraphicsDropShadowEffect, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor
from src.base_de_datos.database import DatabaseManager
from src.repositories.cliente_repository import ClienteRepository, FIADO_EXPRESS_LIMITE_DEFAULT


from src.admin.clientes.theme import _CLI

class MetricCard(QFrame):
    def __init__(self, titulo, icon, color="#3B82F6", parent=None):
        super().__init__(parent)
        self.setFixedHeight(108)
        self.setStyleSheet(
            f"background: {_CLI['card']}; border: 1px solid {_CLI['border']}; border-radius: 18px;"
        )
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(15, 23, 42, 18))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 10, 20, 10)
        lay.setSpacing(15)
        
        icon_frame = QFrame()
        icon_frame.setFixedSize(50, 50)
        icon_frame.setStyleSheet(f"background: {color}20; border-radius: 25px; border: none;")
        i_lay = QVBoxLayout(icon_frame)
        i_lay.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"font-size: 24px; color: {color}; background: transparent; border: none;")
        i_lay.addWidget(icon_lbl)
        lay.addWidget(icon_frame)
        
        v_lay = QVBoxLayout()
        v_lay.setSpacing(2)
        v_lay.setAlignment(Qt.AlignVCenter)
        self.lbl_tit = QLabel(titulo.upper())
        self.lbl_tit.setStyleSheet(
            f"color: {_CLI['text_soft']}; font-size: 11px; font-weight: 900; "
            "letter-spacing: 1px; border: none;"
        )
        v_lay.addWidget(self.lbl_tit)
        
        self.lbl_val = QLabel("0")
        self.lbl_val.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: 900; border: none;")
        v_lay.addWidget(self.lbl_val)
        lay.addLayout(v_lay)
        lay.addStretch()

    def set_valor(self, val, is_money=False):
        if is_money:
            self.lbl_val.setText(f"${val:,.2f}")
        else:
            self.lbl_val.setText(str(val))

