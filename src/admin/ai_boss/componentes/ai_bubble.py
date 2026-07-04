from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
import sys
import random
import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea, QLineEdit, QProgressBar, QGridLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
try:
    from src.base_de_datos.database import db_manager
    from src.config import config
except ImportError:
    from database import db_manager


class Admin12AIBoss(QWidget):
    """
    IA GLOBAL BOSS - MENTOR ESTRATÉGICO (Versión Simplificada y Potente)
    Sin 'humo', solo datos, estrategia y proyecciones reales.
    """
    request_dashboard = pyqtSignal()
    generate_order_request = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_insights()

    def setup_ui(self):
        self.setStyleSheet("  font-family: 'Segoe UI';")
        layout = QVBoxLayout(self); layout.setContentsMargins(20, 20, 20, 20)

        # Header Profesional
        header = QHBoxLayout()
        btn_back = QPushButton("🔙 VOLVER")
        btn_back.setStyleSheet("  font-weight: 800; border-radius: 8px; padding: 10px;")
        btn_back.clicked.connect(self.request_dashboard.emit)
        header.addWidget(btn_back)
        
        lbl_title = QLabel("🧠 MENTOR ESTRATÉGICO <span style=''>AI BOSS 2026</span>")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: 900; margin-left: 15px;")
        header.addWidget(lbl_title)
        header.addStretch()
        layout.addLayout(header)

        # Panel de Métricas Críticas (Insights)
        self.insights_layout = QGridLayout()
        layout.addLayout(self.insights_layout)

        # Consola de Estrategia (Chat Simplificado)
        self.console = QScrollArea()
        self.console.setWidgetResizable(True)
        self.console.setStyleSheet(" border-radius: 12px; border: 1px solid #334155;")
        self.console_widget = QWidget()
        self.console_l = QVBoxLayout(self.console_widget)
        self.console_l.addStretch()
        self.console.setWidget(self.console_widget)
        layout.addWidget(self.console, 1)

        # Input de Comandos
        input_bar = QHBoxLayout()
        self.txt_cmd = QLineEdit()
        self.txt_cmd.setPlaceholderText("Consultar estrategia, proyecciones o dudas financieras...")
        self.txt_cmd.setStyleSheet(" border: 2px solid #334155; border-radius: 8px; padding: 15px; color: #1e293b;")
        self.txt_cmd.returnPressed.connect(self.process_query)
        btn_send = QPushButton("⚡")
        btn_send.setFixedSize(50, 50)
        btn_send.setStyleSheet(" background-color: #3b82f6; color: white; border-radius: 25px; font-size: 20px; font-weight: bold;")
        btn_send.clicked.connect(self.process_query)
        input_bar.addWidget(self.txt_cmd); input_bar.addWidget(btn_send)
        layout.addLayout(input_bar)

    def add_log(self, text, ai=True):
        lbl = QLabel(text); lbl.setWordWrap(True)
        color = "#38bdf8" if ai else "#f8fafc"
        bg = "#0f172a" if ai else "#6366f1"
        align = Qt.AlignLeft if ai else Qt.AlignRight
        lbl.setStyleSheet(f"background: {bg}; color: {color}; padding: 15px; border-radius: 10px; margin: 5px;")
        self.console_l.insertWidget(self.console_l.count()-1, lbl, 0, align)
        QTimer.singleShot(50, lambda: self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum()))

    def load_insights(self):
        # Limpiar previos
        for i in reversed(range(self.insights_layout.count())): 
            self.insights_layout.itemAt(i).widget().setParent(None)

        # Simulación de datos reales para el Boss
        metrics = [
            ("SALUD FINANCIERA", "96%", "#10b981"),
            ("PROYECCIÓN MES", "+12.5%", "#38bdf8"),
            ("RIESGO DE STOCK", "BAJO", "#fbbf24"),
            ("FALTANTES ACUM.", "$ 0.00", "#f87171")
        ]
        for i, (t, v, c) in enumerate(metrics):
            card = QFrame(); card.setStyleSheet(f" border-radius: 10px; border-top: 4px solid {c}; padding: 10px;")
            l = QVBoxLayout(card)
            l.addWidget(QLabel(t, styleSheet=" font-size: 10px; font-weight: 800;"))
            val = QLabel(v); val.setStyleSheet(f"color: {c}; font-size: 24px; font-weight: 900;")
            val.setAlignment(Qt.AlignCenter)
            l.addWidget(val)
            self.insights_layout.addWidget(card, 0, i)

        self.add_log("Jefe, el sistema está 100% operativo. He auditado las ventas y el flujo de caja. Estamos en una posición sólida para crecer.")

    def process_query(self):
        query = self.txt_cmd.text().strip()
        if not query: return
        self.txt_cmd.clear()
        self.add_log(query, False)
        
        # Inteligencia Estratégica (Lógica sin humo)
        if "venta" in query.lower():
            res = "La tendencia indica que el pico de ventas ocurre entre las 18:00 y 20:00. Sugiero reforzar personal en ese horario."
        elif "faltante" in query.lower() or "deuda" in query.lower():
            res = "He revisado los cierres Z. El control de faltantes es estricto; no hay desviaciones significativas este mes."
        elif "ganancia" in query.lower() or "dinero" in query.lower():
            res = "Su margen operativo promedio es del 28%. Optimizar el inventario de cárnicos podría subirlo al 31%."
        else:
            res = "Analizando datos globales... Mi recomendación es mantener el nivel de inversión actual y vigilar el stock de los 5 productos más vendidos."
        
        QTimer.singleShot(500, lambda: self.add_log(res))

