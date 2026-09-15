import os
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from src.admin.nexus_admin.vistas.componentes.panel_central.cyber_node_card import CyberNodeCard
from src.admin.nexus_admin.vistas.componentes.panel_central.cyber_metric import CyberMetric

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
        self.lbl_title = QLabel("📡 NEXUS GLOBAL DATABASE // LIVE TOPOLOGY")
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
        self.btn_todas = QPushButton("🌐 VER TODA LA RED")
        self.btn_todas.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_todas.setStyleSheet("background: #1E293B; color: #94A3B8; font-weight: bold; border: 1px solid #334155; padding: 8px; border-radius: 4px;")
        self.btn_todas.clicked.connect(lambda: self.select_node("todas"))
        self.lay.addWidget(self.btn_todas)
        
        # METRICS HUD
        self.metrics_container = QFrame()
        self.metrics_container.setStyleSheet("background: transparent; border: none;")
        m_lay = QHBoxLayout(self.metrics_container)
        m_lay.setContentsMargins(0,0,0,0)
        
        self.lbl_efectivo = CyberMetric("EFECTIVO CASH", "💵")
        self.lbl_digital = CyberMetric("VENTAS DIGITALES", "💳")
        self.lbl_fondo = CyberMetric("FONDO INICIAL", "💰")
        
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
                item = self.grid_layout.takeAt(i)
                
            row, col = 0, 0
            for w in self.node_widgets.values():
                self.grid_layout.addWidget(w, row, col)
                w.show()
                col += 1
                if col > 3:
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
