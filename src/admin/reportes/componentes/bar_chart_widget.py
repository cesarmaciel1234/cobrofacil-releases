from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager

import json
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, 
    QScrollArea, QGridLayout, QGraphicsDropShadowEffect, QStackedWidget,
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


class BarChartWidget(QWidget):
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.colors = ["#475569", "#64748B", "#94A3B8", "#CBD5E1", "#E2E8F0", "#F1F5F9"]
        self.setMinimumHeight(350)
        self.setAttribute(Qt.WA_Hover, True)
        self.hover_index = -1
        self.setMouseTracking(True)
        
    def update_data(self, data):
        self.data = data
        self.update()

    def mouseMoveEvent(self, event):
        if not self.data: return
        w = self.width()
        padding_l, padding_r = 80, 40
        chart_w = w - padding_l - padding_r
        days = list(self.data.keys())
        if not days: return
        spacing = chart_w / len(days)
        x_pos = event.pos().x() - padding_l
        idx = int(x_pos / spacing)
        if 0 <= idx < len(days):
            if self.hover_index != idx:
                self.hover_index = idx
                self.update()
        else:
            if self.hover_index != -1:
                self.hover_index = -1
                self.update()

    def leaveEvent(self, event):
        self.hover_index = -1
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
        from PyQt6.QtCore import QPoint, QRect, Qt
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        padding_l, padding_r, padding_t, padding_b = 80, 40, 40, 60
        chart_w, chart_h = w - padding_l - padding_r, h - padding_t - padding_b
        
        max_total = 0
        for day, methods in self.data.items():
            max_total = max(max_total, sum(methods.values()))
        if max_total == 0: max_total = 1000
        magnitude = 10**(len(str(int(max_total))) - 1) if max_total >= 10 else 1
        max_total = ((int(max_total) // magnitude) + 1) * magnitude
        
        # Grid lines
        painter.setPen(QPen(QColor("#F1F5F9"), 1, Qt.DashLine))
        painter.setFont(QFont("Segoe UI", 9))
        for i in range(6):
            y = h - padding_b - (i * chart_h / 5)
            painter.drawLine(padding_l, int(y), w - padding_r, int(y))
            val = (max_total / 5) * i
            painter.setPen(QColor("#94A3B8"))
            painter.drawText(QRect(0, int(y - 10), padding_l - 10, 20), Qt.AlignRight | Qt.AlignVCenter, f"${val:,.0f}")
            painter.setPen(QPen(QColor("#F1F5F9"), 1, Qt.DashLine))

        days = list(self.data.keys())
        if not days: return
        bar_w = min(40, (chart_w / len(days)) * 0.6)
        spacing = chart_w / len(days)
        
        methods_list = ["Efectivo", "Tarjeta", "Transferencia", "Vales", "Crédito", "Cheque"]
        
        for i, day in enumerate(days):
            x = padding_l + (i * spacing) + (spacing - bar_w) / 2
            current_y = h - padding_b
            
            day_values = []
            for j, m in enumerate(methods_list):
                val = self.data[day].get(m, 0)
                if val > 0: day_values.append((j, m, val))
                
            for j, m, value in day_values:
                bar_h = (value / max_total) * chart_h
                
                rect_y = current_y - bar_h
                # Gap between segments
                if current_y < h - padding_b:
                    rect_y -= 2
                    
                color = self.colors[j % len(self.colors)]
                if self.hover_index != -1 and self.hover_index != i:
                    # dim non-hovered
                    color = "#E2E8F0"
                
                painter.setBrush(QColor(color))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(int(x), int(rect_y), int(bar_w), int(bar_h), 4, 4)
                
                current_y = rect_y
                
            # X Label
            painter.setPen(QColor("#64748B"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(QRect(int(x - 20), int(h - padding_b + 10), int(bar_w + 40), 30), Qt.AlignCenter, str(day)[:5])

        # Total floating label
        total_val = sum([sum(self.data[d].values()) for d in days])
        painter.setFont(QFont("Segoe UI", 16, QFont.Bold))
        painter.setPen(QColor("#64748B"))
        painter.drawText(QRect(w - 250, 10, 230, 30), Qt.AlignRight | Qt.AlignVCenter, f"${total_val:,.2f}")
        
        # Hover Tooltip
        if self.hover_index != -1 and self.hover_index < len(days):
            day = days[self.hover_index]
            tt_w, tt_h = 220, 30 + len(methods_list)*20
            x = padding_l + (self.hover_index * spacing) + spacing/2
            y = padding_t
            
            tt_rect = QRect(int(x) - tt_w//2, int(y), tt_w, tt_h)
            if tt_rect.right() > w: tt_rect.moveRight(w - 10)
            if tt_rect.left() < padding_l: tt_rect.moveLeft(padding_l + 10)
            
            painter.setBrush(QColor(255, 255, 255, 245))
            painter.setPen(QPen(QColor("#E2E8F0"), 1))
            painter.drawRoundedRect(tt_rect, 8, 8)
            
            painter.setPen(QColor("#1E293B"))
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.drawText(QRect(tt_rect.x(), tt_rect.y()+5, tt_rect.width(), 20), Qt.AlignCenter, str(day))
            
            painter.setFont(QFont("Segoe UI", 9))
            cy = tt_rect.y() + 30
            for j, m in enumerate(methods_list):
                val = self.data[day].get(m, 0)
                if val > 0:
                    painter.setBrush(QColor(self.colors[j % len(self.colors)]))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(tt_rect.x()+10, cy+6, 8, 8)
                    painter.setPen(QColor("#475569"))
                    painter.drawText(QRect(tt_rect.x()+25, cy, tt_w-35, 20), Qt.AlignLeft, m)
                    painter.drawText(QRect(tt_rect.x()+25, cy, tt_w-35, 20), Qt.AlignRight, f"${val:,.0f}")
                    cy += 20


