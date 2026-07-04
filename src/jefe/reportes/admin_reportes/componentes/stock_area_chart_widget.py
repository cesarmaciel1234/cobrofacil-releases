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


class StockAreaChartWidget(QWidget):
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.data_prev = None
        self.setMinimumHeight(380)
        self.setAttribute(Qt.WA_Hover, True)
        self.hover_index = -1
        self.setMouseTracking(True)
        
    def update_data(self, data, data_prev=None):
        self.data = data
        self.data_prev = data_prev
        self.update()
        
    def mouseMoveEvent(self, event):
        if not self.data: return
        w = self.width()
        padding_l, padding_r = 60, 20
        chart_w = w - padding_l - padding_r
        keys = list(self.data.keys())
        if not keys: return
        step = chart_w / max(1, len(keys) - 1)
        x_pos = event.pos().x() - padding_l
        idx = int(round(x_pos / step))
        if 0 <= idx < len(keys):
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
        from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPainterPath, QLinearGradient
        from PyQt6.QtCore import QPoint, QRect, Qt
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        padding_l, padding_r, padding_t, padding_b = 60, 30, 30, 40
        chart_w, chart_h = w - padding_l - padding_r, h - padding_t - padding_b
        
        # Background lines
        painter.setPen(QPen(QColor("#EEF2F8"), 1, Qt.DashLine))
        painter.setFont(QFont("Segoe UI", 8))
        
        if not self.data:
            painter.drawText(self.rect(), Qt.AlignCenter, "Sin datos")
            return
            
        max_val = max(max([d.get('ventas', 0) for d in self.data.values()]), 1)
        if self.data_prev:
            max_prev = max(max([d.get('ventas', 0) for d in self.data_prev.values()]), 1)
            max_val = max(max_val, max_prev)
            
        magnitude = 10**(len(str(int(max_val))) - 1) if max_val >= 10 else 1
        max_val = ((int(max_val) // magnitude) + 1) * magnitude
        
        for i in range(6):
            y = h - padding_b - (i * chart_h / 5)
            painter.drawLine(padding_l, int(y), w - padding_r, int(y))
            val_text = f"${(max_val * i / 5):,.0f}"
            painter.setPen(QColor("#94A3B8"))
            painter.drawText(QRect(0, int(y) - 10, padding_l - 10, 20), Qt.AlignRight | Qt.AlignVCenter, val_text)
            painter.setPen(QPen(QColor("#EEF2F8"), 1, Qt.DashLine))
            
        keys = list(self.data.keys())
        step = chart_w / max(1, len(keys) - 1)
        
        # X labels
        painter.setPen(QColor("#94A3B8"))
        for i, key in enumerate(keys):
            if len(keys) > 15 and i % 2 != 0: continue
            x = padding_l + i * step
            painter.drawText(QRect(int(x) - 30, h - padding_b + 10, 60, 20), Qt.AlignCenter, str(key)[:5])
            
        # Draw Previous Ventas Area
        if self.data_prev:
            pts_prev = []
            for i, key in enumerate(keys):
                x = padding_l + i * step
                v = self.data_prev.get(key, {}).get('ventas', 0)
                y = h - padding_b - (v / max_val) * chart_h
                pts_prev.append(QPoint(int(x), int(y)))
                
            path_prev = QPainterPath()
            path_prev.moveTo(pts_prev[0])
            for i in range(1, len(pts_prev)):
                # Bezier smoothing
                p1 = pts_prev[i-1]
                p2 = pts_prev[i]
                c1 = QPoint(int((p1.x() + p2.x()) / 2), p1.y())
                c2 = QPoint(int((p1.x() + p2.x()) / 2), p2.y())
                path_prev.cubicTo(c1, c2, p2)
                
            pen_prev = QPen(QColor("#94A3B8"), 3, Qt.DashLine)
            painter.setPen(pen_prev)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path_prev)

        # Draw Current Ventas Area
        pts_v = []
        for i, key in enumerate(keys):
            x = padding_l + i * step
            y = h - padding_b - (self.data[key].get('ventas', 0) / max_val) * chart_h
            pts_v.append(QPoint(int(x), int(y)))
            
        path_v = QPainterPath()
        path_v.moveTo(pts_v[0])
        for i in range(1, len(pts_v)):
            p1 = pts_v[i-1]
            p2 = pts_v[i]
            c1 = QPoint(int((p1.x() + p2.x()) / 2), p1.y())
            c2 = QPoint(int((p1.x() + p2.x()) / 2), p2.y())
            path_v.cubicTo(c1, c2, p2)
            
        fill_path = QPainterPath(path_v)
        fill_path.lineTo(padding_l + (len(keys)-1)*step, h - padding_b)
        fill_path.lineTo(padding_l, h - padding_b)
        fill_path.closeSubpath()
        
        grad_v = QLinearGradient(0, padding_t, 0, h - padding_b)
        grad_v.setColorAt(0, QColor(59, 130, 246, 100))
        grad_v.setColorAt(1, QColor(59, 130, 246, 0))
        painter.fillPath(fill_path, QBrush(grad_v))
        
        painter.setPen(QPen(QColor(59, 130, 246), 4))
        painter.drawPath(path_v)
        
        # Hover
        if self.hover_index != -1 and self.hover_index < len(keys):
            x = padding_l + self.hover_index * step
            painter.setPen(QPen(QColor("#CBD5E1"), 1, Qt.DashLine))
            painter.drawLine(int(x), padding_t, int(x), h - padding_b)
            
            v_val = self.data[keys[self.hover_index]].get('ventas', 0)
            y_v = h - padding_b - (v_val / max_val) * chart_h
            
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.setBrush(QColor(59, 130, 246))
            painter.drawEllipse(QPoint(int(x), int(y_v)), 6, 6)
            
            if self.data_prev:
                v_prev = self.data_prev.get(keys[self.hover_index], {}).get('ventas', 0)
                y_prev = h - padding_b - (v_prev / max_val) * chart_h
                painter.setBrush(QColor("#94A3B8"))
                painter.drawEllipse(QPoint(int(x), int(y_prev)), 5, 5)
                
            # Tooltip
            tt_w = 260
            tt_h = 100 if self.data_prev else 60
            tt_rect = QRect(int(x) - tt_w//2, padding_t - 20, tt_w, tt_h)
            if x + tt_w//2 > w: tt_rect.moveLeft(w - tt_w - 10)
            if x - tt_w//2 < padding_l: tt_rect.moveLeft(padding_l + 10)
            
            painter.setBrush(QColor(255, 255, 255, 250))
            painter.setPen(QPen(QColor("#E2E8F0"), 1))
            painter.drawRoundedRect(tt_rect, 8, 8)
            painter.setPen(QColor("#1E293B"))
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.drawText(QRect(tt_rect.x(), tt_rect.y()+5, tt_rect.width(), 20), Qt.AlignCenter, f"{keys[self.hover_index]}")
            
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor(59, 130, 246))
            painter.drawText(QRect(tt_rect.x()+10, tt_rect.y()+30, tt_rect.width()-20, 20), Qt.AlignLeft, "Actual:")
            painter.drawText(QRect(tt_rect.x()+10, tt_rect.y()+30, tt_rect.width()-20, 20), Qt.AlignRight, f"${v_val:,.0f}")
            
            if self.data_prev:
                painter.setPen(QColor("#94A3B8"))
                painter.drawText(QRect(tt_rect.x()+10, tt_rect.y()+50, tt_rect.width()-20, 20), Qt.AlignLeft, "Anterior:")
                painter.drawText(QRect(tt_rect.x()+10, tt_rect.y()+50, tt_rect.width()-20, 20), Qt.AlignRight, f"${v_prev:,.0f}")
                
                diff = v_val - v_prev
                if v_prev > 0:
                    pct = (diff / v_prev) * 100
                else:
                    pct = 100.0 if diff > 0 else 0.0
                
                rect_diff = QRect(tt_rect.x()+10, tt_rect.y()+72, tt_rect.width()-20, 20)
                painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                if diff > 0:
                    painter.setPen(QColor("#10B981"))
                    painter.drawText(rect_diff, Qt.AlignCenter, f"▲ +${diff:,.0f} (+{pct:.1f}%)")
                elif diff < 0:
                    painter.setPen(QColor("#EF4444"))
                    painter.drawText(rect_diff, Qt.AlignCenter, f"▼ -${abs(diff):,.0f} ({pct:.1f}%)")
                else:
                    painter.setPen(QColor("#94A3B8"))
                    painter.drawText(rect_diff, Qt.AlignCenter, "Sin cambios")


