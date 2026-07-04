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

from src.jefe.reportes.admin_reportes.componentes.modern_card import ModernCard

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


class AIAssistantWidget(ModernCard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            #card {
                
                border: 2px solid #8B5CF6;
                border-radius: 20px;
            }
        """)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(25, 20, 25, 20)
        lay.setSpacing(10)
        
        # Header
        h_lay = QHBoxLayout()
        lbl_icon = QLabel("🤖")
        lbl_icon.setStyleSheet("font-size: 24px;")
        lbl_title = QLabel("Antigravity AI - Análisis Estratégico")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 900; ")
        
        self.lbl_status = QLabel("Pensando...")
        self.lbl_status.setStyleSheet("font-size: 12px;  font-style: italic;")
        self.lbl_status.hide()
        
        h_lay.addWidget(lbl_icon)
        h_lay.addWidget(lbl_title)
        h_lay.addStretch()
        h_lay.addWidget(self.lbl_status)
        lay.addLayout(h_lay)
        
        # Content
        self.lbl_content = QLabel("Recopilando datos para generar insights...")
        self.lbl_content.setWordWrap(True)
        self.lbl_content.setStyleSheet("font-size: 14px;  line-height: 1.5;")
        lay.addWidget(self.lbl_content)
        
        # Timer for animation
        from PyQt6.QtCore import QTimer
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate_typing)
        self.full_text = ""
        self.current_char = 0

    def update_insights(self, chart_data, pago_sum, donut_data):
        self.lbl_status.show()
        self.lbl_content.setText("")
        
        # Generar texto de insights
        total_ventas = sum([d.get('ventas', 0) for d in chart_data.values()])
        if total_ventas == 0:
            self.full_text = "No hay datos suficientes en este periodo para generar un análisis."
        else:
            # Insight 1: Mejor día
            mejor_dia = max(chart_data.items(), key=lambda x: x[1].get('ventas', 0))[0]
            val_mejor_dia = chart_data[mejor_dia].get('ventas', 0)
            
            # Insight 2: Depto estrella
            mejor_depto = "N/A"
            if donut_data:
                mejor_depto = max(donut_data.items(), key=lambda x: x[1])[0]
                
            # Insight 3: Forma de pago
            mejor_forma = "N/A"
            if pago_sum:
                mejor_forma = max(pago_sum.items(), key=lambda x: x[1])[0]
                
            self.full_text = f"""<ul>
                <li style='margin-bottom: 8px;'>📈 <b>Pico de Ventas:</b> El mejor desempeño fue el día <b>{mejor_dia}</b> con <b>${val_mejor_dia:,.2f}</b>. Asegúrate de replicar la estrategia de ese día.</li>
                <li style='margin-bottom: 8px;'>🏆 <b>Departamento Estrella:</b> <b>{mejor_depto}</b> está liderando en volumen. Considera ubicar promociones cruzadas cerca de esta sección.</li>
                <li style='margin-bottom: 8px;'>💳 <b>Preferencia de Pago:</b> La mayoría de tus clientes prefiere usar <b>{mejor_forma}</b>. Analiza si las comisiones de este método están optimizadas.</li>
            </ul>"""
            
        self.current_char = 0
        self.anim_timer.start(10) # 10ms por caracter HTML (approx)

    def _animate_typing(self):
        # We need to type HTML carefully, but for simplicity we just chunk it or show it directly if it's HTML.
        # To avoid breaking HTML tags during typing, we will just show it instantly after a small "thinking" delay.
        # Actually, let's just simulate 1 second of thinking, then show all.
        self.lbl_status.hide()
        self.lbl_content.setText(self.full_text)
        self.anim_timer.stop()

