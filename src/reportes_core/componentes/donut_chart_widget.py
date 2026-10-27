from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager

import json
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QScrollArea, QGridLayout, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QLineEdit, QFileDialog, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint, QSize, QThread, QUrl
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QLinearGradient, QPolygon, QPainterPath
import datetime

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

def get_depto_icon(depto_name):
    if not depto_name:
        return "📦"
    name = depto_name.strip().upper()
    if "CARNE" in name or "VACUNO" in name or "RES" in name or "CERDO" in name or "VACUN" in name or "ASADO" in name or "TERNER" in name:
        return "🥩"
    if "AVE" in name or "POLLO" in name or "GRANJA" in name or "POLLER" in name:
        return "🍗"
    if "ACHURA" in name or "CHINCHU" in name or "MENUDE" in name or "RIÑON" in name or "MOLLEJ" in name or "INTESTI" in name:
        return "🍢"
    if "PREPARADO" in name or "ELABORADO" in name or "HAMBUR" in name or "MILANE" in name or "ROTIS" in name:
        return "🍳"
    if "EMBUTIDO" in name or "FIAMBRE" in name or "SALCHI" in name or "CHORI" in name or "JAMON" in name or "SALA" in name or "CHARCU" in name:
        return "🌭"
    if "ALMACEN" in name or "ALMACÉN" in name or "ABARRO" in name or "DESPEN" in name:
        return "🥫"
    if "BEBIDA" in name or "REFRES" in name or "GASEO" in name or "CERVE" in name or "VINO" in name or "TRAGO" in name:
        return "🥤"
    if "VERDU" in name or "FRUTA" in name or "VEGETA" in name or "HORTE" in name:
        return "🥦"
    if "PANAD" in name or "PAN" in name or "FACTU" in name or "FACTUR" in name or "BIZCO" in name:
        return "🍞"
    if "LACTEO" in name or "LÁCTEO" in name or "QUESO" in name or "LECHE" in name or "MANTE" in name or "YOGU" in name:
        return "🧀"
    if "LIMPIE" in name or "HIGIEN" in name or "JABON" in name or "DETER" in name or "PERFU" in name:
        return "🧼"
    if "CONGEL" in name or "HELA" in name:
        return "❄️"
    if "KIOS" in name or "GOLO" in name or "CARAME" in name or "CHOCO" in name:
        return "🍬"
    return "📦"


class DonutChartWidget(QWidget):
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#06B6D4", "#64748B"]
        self.setMinimumHeight(350)
        self.setAttribute(Qt.WA_Hover, True)
        self.hover_angle = -1
        self.setMouseTracking(True)

    def update_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QFont, QPen
        from PyQt6.QtCore import QRect, Qt
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        size = min(self.width(), self.height()) - 12
        if size < 80:
            size = 80

        rect = QRect(int((self.width() - size) / 2), int((self.height() - size) / 2), size, size)

        total = sum(self.data.values())
        if total <= 0:
            painter.setBrush(QColor("#EEF2F8"))
            painter.drawEllipse(rect); return

        start_angle = 90 * 16
        for i, (_cat, val) in enumerate(self.data.items()):
            if val <= 0: continue
            span_angle = int((val / total) * 360 * 16)
            color = QColor(self.colors[i % len(self.colors)])
            painter.setBrush(color)
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawPie(rect, start_angle, -span_angle)
            start_angle -= span_angle

        # Center hole
        inner_size = int(size * 0.60)
        inner_rect = QRect(int((self.width() - inner_size) / 2), int((self.height() - inner_size) / 2), inner_size, inner_size)
        painter.setBrush(QColor("#F1F5F9"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(inner_rect)

        painter.setPen(QColor("#1E293B"))

        # Format total to fit
        if total >= 1_000_000:
            t_str = f"${total/1_000_000:.1f}M"
        elif total >= 1_000:
            t_str = f"${total/1_000:.1f}K"
        else:
            t_str = f"${total:,.0f}"

        painter.setFont(QFont("Segoe UI", 13, QFont.Bold))
        painter.drawText(inner_rect, Qt.AlignCenter | Qt.TextDontClip, t_str)


