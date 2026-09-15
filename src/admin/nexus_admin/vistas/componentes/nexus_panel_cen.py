from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QScrollArea, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
import random

class CyberNodeCard(QFrame):
    clicked = pyqtSignal(str)
    
    def __init__(self, origen, role, is_active=True):
        super().__init__()
        self.origen = origen
        self.role = role
        self.is_active = is_active
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(140, 80)
        
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(10, 10, 10, 10)
        self.lay.setSpacing(5)
        
        icon = "??" if "CAJA" in role else "??" if "CARTEL" in role else "??" if "ADMIN" in role else "??"
        
        self.lbl_title = QLabel(f"{icon} {role}")
        self.lbl_title.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_origen = QLabel(origen.split('|')[0] if '|' in origen else origen)
        self.lbl_origen.setFont(QFont("Consolas", 7))
        self.lbl_origen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_status = QLabel("? ONLINE")
        self.lbl_status.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lay.addWidget(self.lbl_title)
        self.lay.addWidget(self.lbl_origen)
        self.lay.addWidget(self.lbl_status)
        
        self.update_style()
        
    def update_style(self, selected=False):
        if not self.is_active:
            bg = "#1E1E1E"
            border = "#333333"
            color_title = "#666666"
            color_status = "#444444"
            status_txt = "? OFFLINE"
        elif selected:
            bg = "rgba(16, 185, 129, 0.1)"
            border = "#10B981"
            color_title = "#10B981"
            color_status = "#34D399"
            status_txt = "? SELECTED"
        else:
            bg = "rgba(59, 130, 246, 0.05)"
            border = "#3B82F6"
            color_title = "#60A5FA"
            color_status = "#3B82F6"
            status_txt = "? ONLINE"
            
        self.setStyleSheet(f"""
            CyberNodeCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            CyberNodeCard:hover {{
                background-color: rgba(59, 130, 246, 0.15);
                border: 1px solid #60A5FA;
            }}
        """)
        self.lbl_title.setStyleSheet(f"color: {color_title}; border: none; background: transparent;")
        self.lbl_origen.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
        self.lbl_status.setStyleSheet(f"color: {color_status}; border: none; background: transparent;")
        self.lbl_status.setText(status_txt)
        
    def set_active(self, active):
        self.is_active = active
        self.update_style()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.origen)

class CyberMetric(QFrame):
    def __init__(self, title, icon):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background: rgba(15, 23, 42, 0.6); border: 1px solid #1E293B; border-radius: 8px;")
        lay = QVBoxLayout(self)
        
        lbl_t = QLabel(f"{icon} {title}")
        lbl_t.setStyleSheet("color: #64748B; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.val_label = QLabel("$ 0")
        self.val_label.setStyleSheet("color: #F8FAFC; font-size: 18px; font-weight: bold; border: none; background: transparent;")
        self.val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lay.addWidget(lbl_t)
        lay.addWidget(self.val_label)

class NexusPanelCen(QWidget):
    request_z_close = pyqtSignal(float)
    caja_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.active_boxes = {}
        self.node_widgets = {}
        self.selected_origen = "todas"
        
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0,0,0,0)
        self.lay.setSpacing(15)
        
        # TITLE
        self.lbl_title = QLabel("?? NEXUS GLOBAL DATABASE // LIVE TOPOLOGY")
        self.lbl_title.setStyleSheet("font-family: Consolas; font-size: 12px; font-weight: bold; color: #38BDF8;")
        self.lay.addWidget(self.lbl_title)
        
        # TOPOLOGY GRID
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#grid_container { background: transparent; }")
        
        self.grid_container = QWidget()
        self.grid_container.setObjectName("grid_container")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        self.scroll_area.setWidget(self.grid_container)
        self.lay.addWidget(self.scroll_area, 3)
        
        # BTN CLEAR SELECTION
        self.btn_todas = QPushButton("?? VER TODA LA RED")
        self.btn_todas.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_todas.setStyleSheet("background: #1E293B; color: #94A3B8; font-weight: bold; border: 1px solid #334155; padding: 8px; border-radius: 4px;")
        self.btn_todas.clicked.connect(lambda: self.select_node("todas"))
        self.lay.addWidget(self.btn_todas)
        
        # METRICS HUD
        self.metrics_container = QFrame()
        self.metrics_container.setStyleSheet("background: transparent; border: none;")
        m_lay = QHBoxLayout(self.metrics_container)
        m_lay.setContentsMargins(0,0,0,0)
        
        self.lbl_efectivo = CyberMetric("EFECTIVO CASH", "??")
        self.lbl_digital = CyberMetric("VENTAS DIGITALES", "??")
        self.lbl_fondo = CyberMetric("FONDO INICIAL", "??")
        
        m_lay.addWidget(self.lbl_efectivo)
        m_lay.addWidget(self.lbl_digital)
        m_lay.addWidget(self.lbl_fondo)
        
        self.lay.addWidget(self.metrics_container)
        
        # HIGHLIGHT ESPERADO
        self.f_esperado = QFrame()
        self.f_esperado.setStyleSheet("background: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; border-radius: 8px;")
        h_lay = QVBoxLayout(self.f_esperado)
        lbl_e = QLabel("TOTAL ESPERADO EN CAJAS")
        lbl_e.setStyleSheet("color: #34D399; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        lbl_e.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_live_esperado = QLabel("$ 0")
        self.lbl_live_esperado.setStyleSheet("color: #10B981; font-size: 26px; font-weight: bold; border: none; background: transparent;")
        self.lbl_live_esperado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_lay.addWidget(lbl_e)
        h_lay.addWidget(self.lbl_live_esperado)
        
        self.lay.addWidget(self.f_esperado)
        
        # ACTION BTN
        self.btn_cierre = QPushButton("F12 // EJECUTAR OVERRIDE (CIERRE Z)")
        self.btn_cierre.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cierre.setFixedHeight(45)
        self.btn_cierre.setStyleSheet('''
            QPushButton {
                background-color: #E11D48; color: white; font-weight: 900; font-size: 14px;
                letter-spacing: 2px; border: none; border-radius: 4px;
            }
            QPushButton:hover { background-color: #BE123C; }
        ''')
        self.btn_cierre.clicked.connect(lambda: self.request_z_close.emit(0.0))
        self.lay.addWidget(self.btn_cierre)
        
        self._tema_oscuro()

    def select_node(self, origen):
        self.selected_origen = origen
        for org, widget in self.node_widgets.items():
            widget.update_style(selected=(org == origen))
        self.caja_selected.emit(origen)

    def registrar_nodo_dinamico(self, origen):
        if origen not in self.node_widgets:
            role = "CAJA"
            if "|" in origen:
                parts = origen.split("|")
                if len(parts) > 1:
                    role = parts[1].upper()
            
            node = CyberNodeCard(origen, role)
            node.clicked.connect(self.select_node)
            self.node_widgets[origen] = node
            
            # Reposition all
            for i in reversed(range(self.grid_layout.count())): 
                self.grid_layout.itemAt(i).widget().setParent(None)
                
            row, col = 0, 0
            for w in self.node_widgets.values():
                self.grid_layout.addWidget(w, row, col)
                col += 1
                if col > 2:
                    col = 0
                    row += 1
                    
        self.node_widgets[origen].set_active(True)
        if self.selected_origen == origen:
            self.node_widgets[origen].update_style(selected=True)

    def mark_active(self, origen):
        if origen in self.node_widgets:
            self.node_widgets[origen].set_active(True)
            
    def mark_inactive(self, origen):
        if origen in self.node_widgets:
            self.node_widgets[origen].set_active(False)

    def update_theme(self, theme):
        if theme == "dark":
            self._tema_oscuro()
        else:
            self._tema_claro()

    def _tema_oscuro(self):
        self.btn_todas.setStyleSheet("background: #1E293B; color: #94A3B8; font-weight: bold; border: 1px solid #334155; padding: 8px; border-radius: 4px;")
        for w in self.node_widgets.values():
            w.update_style(selected=(w.origen == self.selected_origen))

    def _tema_claro(self):
        self.btn_todas.setStyleSheet("background: #E2E8F0; color: #475569; font-weight: bold; border: 1px solid #CBD5E1; padding: 8px; border-radius: 4px;")
        for w in self.node_widgets.values():
            w.update_style(selected=(w.origen == self.selected_origen))
