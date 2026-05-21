import os
import sys
import datetime
import random
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QScrollArea, QTabWidget, QApplication,
                             QProgressBar, QDialog, QTableWidgetItem, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QPoint, QEasingCurve
from PyQt5.QtGui import QFont, QColor

# Imports pesados
import matplotlib
try:
    matplotlib.use("Qt5Agg")
except: pass
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN ELITE LIGHT ---
AI_TIPS = [
    "\"No es cuánto dinero ganas, sino cuánto dinero conservas.\" — Robert Kiyosaki",
    "\"Si no encuentras una forma de ganar dinero mientras duermes, trabajarás hasta que mueras.\" — Warren Buffett",
    "\"Cuidar de los pequeños gastos; un pequeño agujero hunde un gran barco.\" — Benjamin Franklin",
    "\"Lo que no se mide, no se puede mejorar.\" — Peter Drucker",
    "\"La mejor inversión que puedes hacer es en ti mismo.\" — Warren Buffett",
    "\"Un presupuesto es decirle a tu dinero a dónde ir en lugar de preguntar a dónde fue.\" — Dave Ramsey"
]

def apply_shadow(widget, blur=20, x=0, y=4, alpha=30):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(x, y)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)

class ToastNotification(QFrame):
    def __init__(self, parent, message, icon="💡", duration=8000):
        super().__init__(parent)
        self.setFixedWidth(380)
        self.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-left: 5px solid #6366f1;
                border-radius: 12px;
            }
        """)
        apply_shadow(self, alpha=40)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 24px; border: none;")
        layout.addWidget(lbl_icon)
        
        v_layout = QVBoxLayout()
        lbl_title = QLabel("MENTORÍA FINANCIERA")
        lbl_title.setStyleSheet("color: #6366f1; font-size: 10px; font-weight: 900; letter-spacing: 1px;")
        v_layout.addWidget(lbl_title)
        
        lbl_msg = QLabel(message)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("color: #1e293b; font-size: 13px; font-weight: 500; font-style: italic;")
        v_layout.addWidget(lbl_msg)
        layout.addLayout(v_layout)
        
        # Position
        self.adjustSize()
        px = parent.width() - self.width() - 30
        py = parent.height() - self.height() - 30
        self.move(px, parent.height())
        self.show()
        
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(600)
        self.anim.setStartValue(QPoint(px, parent.height()))
        self.anim.setEndValue(QPoint(px, py))
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()
        
        QTimer.singleShot(duration, self.dismiss)

    def dismiss(self):
        if not self.parent(): return
        self.anim_out = QPropertyAnimation(self, b"pos")
        self.anim_out.setDuration(500)
        self.anim_out.setStartValue(self.pos())
        self.anim_out.setEndValue(QPoint(self.x(), self.parent().height() + 100))
        self.anim_out.finished.connect(self.deleteLater)
        self.anim_out.start()

class Admin9Contabilidad(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.is_loaded = False
        self.db = None
        self.erp_externo = None
        
        # MAGIC LIGHT THEME
        self.setStyleSheet("""
            QWidget { background-color: #f8fafc; font-family: 'Segoe UI', Inter; }
            QLabel { color: #1e293b; }
        """)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.loading_screen = QFrame()
        ll = QVBoxLayout(self.loading_screen)
        self.lbl_loading = QLabel("✨ Preparando Magia Financiera...")
        self.lbl_loading.setStyleSheet("color: #6366f1; font-size: 22px; font-weight: bold;")
        self.lbl_loading.setAlignment(Qt.AlignCenter)
        ll.addWidget(self.lbl_loading)
        self.main_layout.addWidget(self.loading_screen)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.is_loaded:
            self.is_loaded = True
            QTimer.singleShot(50, self.load_heavy_modules)

    def load_heavy_modules(self):
        try:
            ext_path = r"C:\Users\cesar\OneDrive\Desktop\proyecto enero\negocio contable"
            if os.path.exists(ext_path):
                if ext_path not in sys.path: sys.path.insert(0, ext_path)
                import importlib.util
                db_file = os.path.join(ext_path, "database.py")
                spec_db = importlib.util.spec_from_file_location("ext_db", db_file)
                ext_db = importlib.util.module_from_spec(spec_db)
                from src.utils.paths import get_base_path
                self.db = ext_db.Database(os.path.join(get_base_path(), "punpro.db"))
                
                main_file = os.path.join(ext_path, "main.py")
                spec_main = importlib.util.spec_from_file_location("contabilidad_externa", main_file)
                contabilidad_main = importlib.util.module_from_spec(spec_main)
                spec_main.loader.exec_module(contabilidad_main)
                self.erp_externo = contabilidad_main.ButcheryAccounting(role="admin", company="PunPro")
                
            self.build_final_ui()
            self.loading_screen.deleteLater()
            QTimer.singleShot(1500, self.show_random_tip)
        except Exception as e:
            self.lbl_loading.setText(f"❌ Error: {str(e)}")

    def build_final_ui(self):
        # HEADER LIGHT
        header = QFrame()
        header.setStyleSheet("background-color: white; border-bottom: 1px solid #e2e8f0;")
        header.setFixedHeight(75)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(25, 0, 25, 0)
        
        btn_back = QPushButton("🔙 VOLVER AL PANEL")
        btn_back.setStyleSheet("""
            QPushButton { background: #f1f5f9; color: #475569; font-weight: 800; border-radius: 12px; padding: 10px 20px; border: 1px solid #e2e8f0; }
            QPushButton:hover { background: #e2e8f0; color: #1e293b; }
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)
        hl.addWidget(btn_back)
        
        lbl_title = QLabel("📈 CENTRO FINANCIERO <span style='color: #6366f1;'>PREMIUM</span>")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: 900; color: #0f172a;")
        hl.addWidget(lbl_title)
        hl.addStretch()
        self.main_layout.addWidget(header)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: #f8fafc; }
            QTabBar::tab { background: #e2e8f0; color: #64748b; padding: 12px 25px; font-weight: bold; border-top-left-radius: 10px; border-top-right-radius: 10px; margin-right: 4px; }
            QTabBar::tab:selected { background: #6366f1; color: white; }
            QTabBar::tab:hover:!selected { background: #cbd5e1; }
        """)
        
        self.tab_resumen = QWidget()
        self.build_native_dashboard(self.tab_resumen)
        self.tabs.addTab(self.tab_resumen, "📊 Dashboard Magia")
        
        if self.erp_externo:
            # FORCE LIGHT STYLE TO EXTERNAL TABS
            light_style = """
                QWidget { background-color: #f8fafc; color: #1e293b; }
                QFrame#Card { background-color: white; border: 1px solid #e2e8f0; border-radius: 15px; }
                QTableWidget { background-color: white; border-radius: 10px; gridline-color: #f1f5f9; color: #1e293b; }
                QHeaderView::section { background-color: #f1f5f9; color: #6366f1; font-weight: bold; border: none; padding: 10px; }
                QLineEdit, QComboBox, QDateEdit { background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px; color: #1e293b; }
                QPushButton { background: #6366f1; color: white; border-radius: 8px; padding: 10px; font-weight: bold; }
                QPushButton:hover { background: #4f46e5; }
            """
            
            def add_tab(widget, name):
                if widget:
                    widget.setStyleSheet(light_style)
                    self.tabs.addTab(widget, name)

            add_tab(getattr(self.erp_externo, 'tab_central_payments', None), "⚡ Pagos")
            add_tab(getattr(self.erp_externo, 'tab_income', None), "💼 Tesorería")
            add_tab(getattr(self.erp_externo, 'tab_expenses', None), "📉 Gastos")
            add_tab(getattr(self.erp_externo, 'tab_loans', None), "🏦 Préstamos")
            add_tab(getattr(self.erp_externo, 'tab_checks', None), "💳 Cheques")
            add_tab(getattr(self.erp_externo, 'tab_proveedores', None), "🤝 Proveedores")
            add_tab(getattr(self.erp_externo, 'tab_history', None), "📚 Historial")
        
        self.main_layout.addWidget(self.tabs)
        self.update_dashboard()

    def build_native_dashboard(self, parent):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        container = QWidget()
        container.setStyleSheet("background: #f8fafc;")
        body = QVBoxLayout(container)
        body.setContentsMargins(30, 30, 30, 30)
        body.setSpacing(30)
        
        # --- COMMAND CENTER HEADER LIGHT ---
        header_frame = QFrame()
        header_frame.setFixedHeight(110)
        header_frame.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6); border-radius: 20px;")
        apply_shadow(header_frame)
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(35, 0, 35, 0)
        
        titles_v = QVBoxLayout()
        main_title = QLabel("CENTRO DE COMANDO FINANCIERO")
        main_title.setStyleSheet("font-size: 24px; font-weight: 900; color: white; letter-spacing: 1px;")
        sub_title = QLabel("ESTRATEGIA • CONTROL • MAGIA OPERATIVA")
        sub_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #e0e7ff; letter-spacing: 2px;")
        titles_v.addWidget(main_title); titles_v.addWidget(sub_title)
        h_layout.addLayout(titles_v)
        h_layout.addStretch()
        
        btn_magic = QPushButton("✨ GENERAR MAGIA")
        btn_magic.setStyleSheet("background: white; color: #6366f1; padding: 12px 25px; font-weight: 900; border-radius: 12px;")
        h_layout.addWidget(btn_magic)
        body.addWidget(header_frame)

        # --- KPI ROW LIGHT ---
        kpi_row = QHBoxLayout()
        self.card_dia = self.crear_kpi_card("📅 NETO HOY", "$0.00", "Flujo diario", "#0ea5e9")
        self.card_mes = self.crear_kpi_card("🗓️ NETO MES", "$0.00", "Rendimiento mensual", "#10b981")
        self.card_ano = self.crear_kpi_card("🏆 BALANCE ANUAL", "$0.00", "Acumulado 2026", "#8b5cf6")
        kpi_row.addWidget(self.card_dia); kpi_row.addWidget(self.card_mes); kpi_row.addWidget(self.card_ano)
        body.addLayout(kpi_row)

        # --- MIDDLE ROW ---
        mid_row = QHBoxLayout()
        self.alert_card = self.crear_card("⚠️ ALERTAS", "No hay deudas críticas hoy.", "#f59e0b")
        self.debt_card = self.crear_card_progress("🔥 CONSUMO", "Gastos vs Ingresos", "#f43f5e")
        self.goal_card = self.crear_card_progress("🎯 OBJETIVO", "Progreso de ventas", "#10b981")
        mid_row.addWidget(self.alert_card); mid_row.addWidget(self.debt_card); mid_row.addWidget(self.goal_card)
        body.addLayout(mid_row)

        # --- CHART LIGHT ---
        chart_frame = QFrame()
        chart_frame.setStyleSheet("background: white; border-radius: 20px; border: 1px solid #f1f5f9;")
        apply_shadow(chart_frame, blur=30, alpha=15)
        chart_l = QVBoxLayout(chart_frame)
        chart_l.setContentsMargins(20, 20, 20, 20)
        
        chart_title = QLabel("📊 TENDENCIA DE CRECIMIENTO")
        chart_title.setStyleSheet("color: #475569; font-weight: 800; font-size: 13px; margin-bottom: 15px;")
        chart_l.addWidget(chart_title)
        
        self.canvas = FigureCanvas(plt.figure(figsize=(9, 4)))
        self.canvas.figure.patch.set_facecolor('none')
        self.ax = self.canvas.figure.add_subplot(111)
        self.ax.set_facecolor('none')
        chart_l.addWidget(self.canvas)
        body.addWidget(chart_frame)
        
        scroll.setWidget(container)
        QVBoxLayout(parent).addWidget(scroll)

    def crear_kpi_card(self, tit, val, sub, col):
        f = QFrame(); f.setFixedHeight(140)
        f.setStyleSheet("background: white; border-radius: 20px; border: 1px solid #f1f5f9;")
        apply_shadow(f, alpha=20)
        l = QVBoxLayout(f); l.setContentsMargins(25, 20, 25, 20)
        t = QLabel(tit); t.setStyleSheet(f"color: {col}; font-weight: 900; font-size: 11px;")
        v = QLabel(val); v.setObjectName("val"); v.setStyleSheet("color: #0f172a; font-size: 32px; font-weight: 900;")
        s = QLabel(sub); s.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 500;")
        l.addWidget(t); l.addStretch(); l.addWidget(v); l.addWidget(s)
        return f

    def crear_card(self, tit, msg, col):
        f = QFrame(); f.setFixedHeight(120); f.setStyleSheet("background: white; border-radius: 15px; border: 1px solid #f1f5f9;")
        apply_shadow(f, alpha=15)
        l = QVBoxLayout(f)
        t = QLabel(tit); t.setStyleSheet(f"color: {col}; font-weight: 900; font-size: 10px;")
        self.alert_text = QLabel(msg); self.alert_text.setWordWrap(True); self.alert_text.setStyleSheet("color: #334155; font-size: 13px; font-weight: 500;")
        l.addWidget(t); l.addWidget(self.alert_text); l.addStretch()
        return f

    def crear_card_progress(self, tit, sub, col):
        f = QFrame(); f.setFixedHeight(120); f.setStyleSheet("background: white; border-radius: 15px; border: 1px solid #f1f5f9;")
        apply_shadow(f, alpha=15)
        l = QVBoxLayout(f)
        t = QLabel(tit); t.setStyleSheet(f"color: {col}; font-weight: 900; font-size: 10px;")
        s = QLabel(sub); s.setStyleSheet("color: #64748b; font-size: 11px;")
        p = QProgressBar(); p.setFixedHeight(10); p.setTextVisible(False)
        p.setStyleSheet(f"QProgressBar {{ background: #f1f5f9; border-radius: 5px; }} QProgressBar::chunk {{ background: {col}; border-radius: 5px; }}")
        if tit == "🎯 OBJETIVO": self.goal_bar = p; self.goal_lbl = s
        else: self.debt_bar = p; self.debt_lbl = s
        l.addWidget(t); l.addWidget(s); l.addWidget(p); l.addStretch()
        return f

    def update_dashboard(self):
        if not self.db: return
        try:
            today = datetime.date.today()
            stats = self.db.get_stats(today.month, today.year)
            pure = self.db.get_pure_accounting_stats(today)
            
            def set_val(card, val):
                card.findChild(QLabel, "val").setText(f"${val:,.2f}")
            
            set_val(self.card_dia, pure['day']['net'])
            set_val(self.card_mes, pure['month']['net'])
            set_val(self.card_ano, pure['year']['net'])
            
            # Alertas
            vencidos = sum(1 for k, v in stats.get("balances", {}).items() if v > 0)
            self.alert_text.setText(f"Tienes {vencidos} deudas activas" if vencidos else "✅ Salud financiera óptima.")
            
            # Barras
            inc = stats.get("total_income", 1)
            exp = stats.get("total_expenses", 0)
            ratio = min(int(exp / inc * 100), 100) if inc > 0 else 0
            self.debt_bar.setValue(ratio)
            self.debt_lbl.setText(f"Consumo: {ratio}%")
            
            meta = 1200000
            prog = min(int(inc / meta * 100), 100)
            self.goal_bar.setValue(prog)
            self.goal_lbl.setText(f"Progreso Meta: {prog}%")
            
            self.update_chart(today.year)
        except: pass

    def update_chart(self, year):
        try:
            inc, exp = self.db.get_trend_data(year)
            self.ax.clear()
            months = ["E", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
            for i in range(12):
                color = '#4f46e5' if inc[i] >= exp[i] else '#f43f5e'
                self.ax.bar(i, inc[i], color='#e2e8f0', width=0.5, alpha=0.5)
                self.ax.bar(i, inc[i]-exp[i], bottom=exp[i] if inc[i]>exp[i] else inc[i], width=0.5, color=color)
            
            self.ax.set_xticks(range(12)); self.ax.set_xticklabels(months, color='#64748b', fontsize=9, fontweight='bold')
            self.ax.tick_params(colors='#94a3b8', labelsize=8)
            for s in self.ax.spines.values(): s.set_visible(False)
            self.ax.yaxis.grid(True, linestyle='--', alpha=0.3, color='#e2e8f0')
            self.canvas.draw()
        except: pass

    def select_tab(self, index):
        """Navega a una pestaña específica del módulo. Llamado desde main_window con índice 900+."""
        if hasattr(self, 'tabs'):
            self.tabs.setCurrentIndex(index)
        else:
            # El módulo aún no cargó (lazy load), guardamos para aplicar al finalizar
            self._pending_tab = index

    def show_random_tip(self):
        tip = random.choice(AI_TIPS)
        ToastNotification(self, tip)
