import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QDateEdit, QFrame, QHeaderView, QMessageBox, QTabWidget,
    QProgressBar, QScrollArea, QDialog, QFormLayout, QStatusBar, QFileDialog, QInputDialog,
    QGridLayout, QStackedWidget, QListWidget, QListWidgetItem, QSpinBox, QTextEdit
)
from PyQt5.QtCore import Qt, QDate, QTimer, QPropertyAnimation, QPoint, QEasingCurve
from PyQt5.QtGui import QFont, QIcon
import random
from database import Database
from styles import STYLE_SHEET
import datetime
import csv
import glob
import os
import logging
import calendar
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None
import threading
import subprocess
import re

# Configuración de logging profesional
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PunProERP")

# --- CONFIGURACIÓN UNIVERSAL ---
class Config:
    EXPENSE_CATEGORIES = ["Mercadería / Stock", "Servicios", "Sueldos", "Mantenimiento", "Alquiler", "Limpieza", "Otros"]
    INCOME_SOURCES = ["Ventas Directas", "Ventas Online", "Servicios Especiales", "Otros"]
    FIXED_COST_CATEGORIES = ["Alquiler", "Servicios", "Sueldos", "Impuestos", "Seguros", "Otros"]
    LOAN_CATEGORIES = ["Bancario", "Personal", "Inversión", "Otros"]
    ADMIN_PASSWORD = "2094"
    BACKUP_DIR = "backups"

AI_TIPS = [
    "\"No es cuánto dinero ganas, sino cuánto dinero conservas.\" — Robert Kiyosaki",
    "\"Si no encuentras una forma de ganar dinero mientras duermes, trabajarás hasta que mueras.\" — Warren Buffett",
    "\"Cuidar de los pequeños gastos; un pequeño agujero hunde un gran barco.\" — Benjamin Franklin",
    "\"Lo que no se mide, no se puede mejorar.\" — Peter Drucker",
    "\"La educación formal te dará una vida; la autoeducación te dará una fortuna.\" — Jim Rohn",
    "\"El riesgo viene de no saber lo que estás haciendo.\" — Warren Buffett",
    "\"El dinero es un esclavo terrible pero un excelente maestro.\" — P.T. Barnum",
    "\"Donde va el foco, fluye la energía y los resultados.\" — Tony Robbins",
    "\"No ahorres lo que queda después de gastar, gasta lo que queda después de ahorrar.\" — Warren Buffett",
    "\"La mejor inversión que puedes hacer es en ti mismo.\" — Warren Buffett",
    "\"Tu nivel de éxito rara vez superará tu nivel de desarrollo personal.\" — Jim Rohn",
    "\"La disciplina es el puente entre las metas y los logros.\" — Jim Rohn",
    "\"Un presupuesto es decirle a tu dinero a dónde ir en lugar de preguntar a dónde fue.\" — Dave Ramsey"
]

class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super(MatplotlibCanvas, self).__init__(fig)
        self.setParent(parent)

class ToastNotification(QFrame):
    def __init__(self, parent, message, icon="💬", duration=8000, click_callback=None):
        super().__init__(parent)
        self.click_callback = click_callback
        self.setFixedWidth(400) # Más grande
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e293b, stop:1 #0f172a);
                border: 2px solid #6366f1;
                border-radius: 16px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 28px; border: none; background: transparent;")
        lbl_icon.setFixedWidth(35)
        layout.addWidget(lbl_icon)
        
        v_layout = QVBoxLayout()
        v_layout.setSpacing(2)
        
        lbl_title = QLabel("MENTORÍA DE ÉXITO")
        lbl_title.setStyleSheet("color: #10b981; font-size: 10px; font-weight: 900; letter-spacing: 1px; background: transparent;")
        v_layout.addWidget(lbl_title)
        
        lbl_msg = QLabel(message)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: 600; font-style: italic; border: none; background: transparent;")
        v_layout.addWidget(lbl_msg)
        
        lbl_hint = QLabel("Click para que tu Mentor lo analice ➔")
        lbl_hint.setStyleSheet("color: #94a3b8; font-size: 9px; font-style: italic; background: transparent;")
        v_layout.addWidget(lbl_hint)
        
        layout.addLayout(v_layout)
        
        self.adjustSize()
        self.setFixedHeight(max(self.sizeHint().height(), 80))
        
        # Position: bottom-right
        px = parent.width() - self.width() - 30
        py = parent.height() - self.height() - 50
        self.move(px, parent.height())
        self.show()
        
        # Slide in
        self.anim_in = QPropertyAnimation(self, b"pos")
        self.anim_in.setDuration(500)
        self.anim_in.setStartValue(QPoint(px, parent.height()))
        self.anim_in.setEndValue(QPoint(px, py))
        self.anim_in.setEasingCurve(QEasingCurve.OutBack)
        self.anim_in.start()
        
        # Auto-dismiss
        QTimer.singleShot(duration, self.dismiss)
    
    def mousePressEvent(self, event):
        if self.click_callback:
            self.click_callback()
            self.dismiss()

    def dismiss(self):
        if not self.parent(): return
        px = self.x()
        self.anim_out = QPropertyAnimation(self, b"pos")
        self.anim_out.setDuration(400)
        self.anim_out.setStartValue(self.pos())
        self.anim_out.setEndValue(QPoint(px, self.parent().height() + 100))
        self.anim_out.setEasingCurve(QEasingCurve.InBack)
        self.anim_out.finished.connect(self.deleteLater)
        self.anim_out.start()

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PUNPRO - Quién está usando el sistema?")
        self.setFixedSize(900, 600)
        self.setStyleSheet(STYLE_SHEET)
        self.user_role = None
        self.company_name = None
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(30)
        
        title = QLabel("¿Quién está usando el sistema?")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: white; margin-bottom: 40px;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Profile Container (Grid)
        self.grid_widget = QWidget()
        self.profile_grid = QGridLayout(self.grid_widget)
        self.profile_grid.setSpacing(40)
        self.profile_grid.setContentsMargins(20, 20, 20, 20)
        
        self.load_all_profiles()
        
        main_layout.addWidget(self.grid_widget, 0, Qt.AlignCenter)
        main_layout.addStretch()
        
        # Style
        self.setStyleSheet(STYLE_SHEET + " QDialog { background-color: #0b0f19; }")

    def load_all_profiles(self):
        # Clear
        while self.profile_grid.count():
            item = self.profile_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        # 1. Admin Profile (Always at 0,0)
        self.add_profile_card("Administrador", "👑", "admin", 0, 0)
        
        # 2. Company Profiles
        db_files = [f for f in glob.glob("*.db") if not f.startswith("backup_") and f != "database.db"]
        col = 1
        row = 0
        for db in db_files:
            name = db.replace(".db", "").upper()
            self.add_profile_card(name, "🏢", "user", row, col, db.replace(".db", ""))
            col += 1
            if col > 3:
                col = 0
                row += 1
                
        # 3. New Company Option REMOVED from here (Boss only creates from inside)

    def add_profile_card(self, name, icon, role, row, col, company=None):
        card = QFrame()
        card.setFixedSize(170, 230)
        card.setCursor(Qt.PointingHandCursor)
        card.setObjectName("ProfileCard")
        card.setStyleSheet("""
            QFrame#ProfileCard {
                background-color: #1e293b;
                border-radius: 12px;
                border: 2px solid transparent;
            }
            QFrame:hover {
                border: 2px solid #6366f1;
                background-color: #334155;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 60px; margin-bottom: 10px;")
        lbl_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_icon)
        
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        lbl_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_name)
        
        # Make clickable
        card.mousePressEvent = lambda e: self.select_profile(role, company)
        self.profile_grid.addWidget(card, row, col)

    def select_profile(self, role, company):
        if role == "admin":
            password, ok = QInputDialog.getText(self, "Acceso Restringido", f"Ingrese la clave de Administrador:", QLineEdit.Password)
            if not ok: return
            if password != Config.ADMIN_PASSWORD: # Usar la clave de configuración
                QMessageBox.warning(self, "Acceso Denegado", "La clave ingresada es incorrecta.")
                return
                
        if role == "new":
            name, ok = QInputDialog.getText(self, "Nueva Empresa", "Nombre de la empresa:")
            if ok and name:
                self.user_role = "user"
                self.company_name = name.lower().replace(" ", "_")
                self.accept()
        else:
            self.user_role = role
            self.company_name = company
            self.accept()

class ClickableCard(QFrame):
    def __init__(self, card_type, callback):
        super().__init__()
        self.card_type = card_type
        self.callback = callback
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("StatCard")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.callback(self.card_type)

class ButcheryAccounting(QMainWindow):
    def __init__(self, role="admin", company=None):
        super().__init__()
        self.role = role
        self.company_name = company
        self.switch_requested = False
        
        # Determine database
        db_file = "database.db"
        if self.role == "user" and company:
            db_file = f"{company}.db"
        
        self.db = Database(db_file)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"PUNPRO ERP - {self.company_name.upper() if self.company_name else 'ADMIN'}")
        self.setMinimumSize(1280, 800)
        self.setStyleSheet(STYLE_SHEET)
        
        self.stat_labels = {}
        self.stat_trends = {}
        
        # Main Layout (Horizontal: Sidebar + Content)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. Main Content Area (Stack needs to be ready for Sidebar)
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Stacked Widget for pages
        self.stack = QStackedWidget()
        self.content_layout.addWidget(self.stack)
        
        self.init_header() # Crea la barra superior con el saludo y selector de fecha
        
        # 2. Sidebar (Connects to stack)
        self.init_sidebar() # Crea el menú lateral
        
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_container)
        
        # Initialize all pages (Order matters for stack index!)
        self.init_dashboard_tab()     # Índice 0: Pantalla principal
        self.init_central_payments_tab() # Índice 1: Pago rápido de deudas
        self.init_income_tab()        # 1
        self.init_expenses_tab()      # 3
        self.init_proveedores_tab()   # 3
        self.init_loans_tab()         # 5
        self.init_checks_tab()        # 5
        self.init_debts_tab()         # 7
        self.init_investments_tab()   # 8
        self.init_fixed_costs_tab()   # 7
        self.init_history_tab()       # 10
        self.init_ai_tab()            # 11
        self.init_reports_tab()       # 12
        # self.init_stock_tab()         # Eliminado por solicitud de enfoque contable/financiero
        
        if self.role == "admin":
            self.init_admin_tab()           # Índice 14
            self.init_admin_payments_tab()  # Índice 15
            self.init_audit_pro_tab()       # Índice 16 (Nivel 4)
            self.stack.setCurrentIndex(13)

        # Barra de estado inferior
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Sistema PunPro ERP Iniciado", 5000)

        self.load_all_data() # Carga inicial de números desde la DB
        QTimer.singleShot(1200, self.auto_check_fixed_costs)  # Diferido: espera que UI esté visible
        
        # Notificaciones y Tips
        QTimer.singleShot(1500, self.show_welcome_toast)
        self.tip_timer = QTimer(self)
        self.tip_timer.timeout.connect(self.show_random_tip)
        self.tip_timer.start(300000)
            
    def init_global_dashboard_tab(self):
        """Crea la pestaña donde el Admin ve el resumen de todas las sucursales."""
        self.tab_global_dashboard = QWidget()
        layout = QVBoxLayout(self.tab_global_dashboard)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title = QLabel("Panel Global de Empresas (Resumen de Red)")
        title.setStyleSheet("font-size: 28px; font-weight: 900; color: #38bdf8;")
        layout.addWidget(title)

        self.global_table = QTableWidget()
        self.global_table.setColumnCount(5)
        self.global_table.setHorizontalHeaderLabels(["Empresa", "Ingresos", "Egresos", "Deudas", "Saldo Neto"])
        self.global_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.global_table)
        self.stack.addWidget(self.tab_global_dashboard)

    def update_global_dashboard(self):
        """Escanea todos los archivos .db y suma los totales de cada empresa para el jefe."""
        db_files = [f for f in glob.glob("*.db") if not f.startswith("backup_") and f != "database.db"]
        self.global_table.setRowCount(0)
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        for db_file in db_files:
            try:
                temp_db = Database(db_file)
                stats = temp_db.get_stats(m, y)
                row = self.global_table.rowCount()
                self.global_table.insertRow(row)
                self.global_table.setItem(row, 0, QTableWidgetItem(db_file.replace(".db", "").upper()))
                self.global_table.setItem(row, 1, QTableWidgetItem(f"$ {stats['total_income']:,.2f}"))
                self.global_table.setItem(row, 2, QTableWidgetItem(f"$ {stats['total_expenses']:,.2f}"))
                self.global_table.setItem(row, 3, QTableWidgetItem(f"$ {sum(stats['balances'].values()):,.2f}"))
                self.global_table.setItem(row, 4, QTableWidgetItem(f"$ {stats['balance']:,.2f}"))
            except Exception as e:
                logger.error(f"Error cargando base de datos {db_file}: {e}")

    def update_prov_calc(self):
        kilos_text = self.prov_kilos.text().replace(',', '.')
        precio_text = self.prov_precio_kg.text().replace(',', '.')
        if not kilos_text or not precio_text: return
        import re
        if not re.match(r'^[\d\.\+\s]+$', kilos_text): return # Solo permite suma, no eval()
        try:
            # Reemplazo de eval() por cálculo seguro
            total_kilos = sum(float(x) for x in kilos_text.split('+') if x.strip())
            precio = float(precio_text)
            total = total_kilos * precio
            self.prov_amount.setText(f"{total:.2f}")
        except Exception as e:
            logger.error(f"Error en cálculo aritmético: {e}")

    def update_dashboard_chart(self):
        year = int(self.year_sel.currentText())
        inc_data, exp_data = self.db.get_trend_data(year)
        self.canvas.ax.clear()
        
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        x = list(range(12))
        
        # --- ESTILO VELAS JAPONESAS (TRADING) ---
        for i in range(12):
            inc = inc_data[i]
            exp = exp_data[i]
            
            # Dibujar "Mecha" (volumen total del mes)
            max_val = max(inc, exp)
            self.canvas.ax.plot([i, i], [0, max_val], color='#475569', linewidth=2, zorder=1)
            
            # Dibujar "Cuerpo de la Vela" (Ganancia o Pérdida)
            if inc >= exp:
                # Bullish (Ganancia)
                color = '#10b981' # Verde
                bottom = exp
                height = inc - exp
            else:
                # Bearish (Pérdida)
                color = '#f43f5e' # Rojo
                bottom = inc
                height = exp - inc
                
            # Si el cuerpo es 0 pero hay mecha, darle un mínimo para que se vea la raya
            if height == 0 and max_val > 0:
                height = max_val * 0.01
                
            # Renderizar la vela
            self.canvas.ax.bar(i, height, bottom=bottom, width=0.4, color=color, edgecolor='black', linewidth=1, zorder=2)
        
        # Forzar los límites para que ENE a DIC estén siempre visibles
        self.canvas.ax.set_xlim(-0.8, 11.8)
        
        # Ajuste de Y para no colapsar la grilla
        global_max = max(max(inc_data), max(exp_data))
        if global_max == 0:
            self.canvas.ax.set_ylim(0, 100) # Grid fantasma si no hay data
        else:
            self.canvas.ax.set_ylim(0, global_max * 1.1)
            
        # Etiquetas y Estilos estilo Binance Premium
        self.canvas.figure.patch.set_facecolor('#ffffff')  # Fondo claro
        self.canvas.ax.set_facecolor("#f8fafc")            # Fondo claro del área del gráfico
        
        self.canvas.ax.set_xticks(x)
        self.canvas.ax.set_xticklabels(months, color='#475569', fontsize=10, fontweight='bold')
        
        self.canvas.ax.grid(axis='y', color='#e2e8f0', linestyle='--', alpha=0.8, zorder=0)
        self.canvas.ax.tick_params(axis='both', colors='#64748b', labelsize=9)
        self.canvas.ax.spines['bottom'].set_color('#e2e8f0')
        self.canvas.ax.spines['left'].set_color('#e2e8f0')
        self.canvas.ax.spines['top'].set_visible(False)
        self.canvas.ax.spines['right'].set_visible(False)
        
        # Format Y axis as currency
        self.canvas.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
        
        # Forzar los márgenes reales (reemplaza tight_layout) para que no se corten las letras abajo
        self.canvas.figure.subplots_adjust(left=0.15, right=0.98, top=0.9, bottom=0.15)
        self.canvas.draw()

    def on_chart_click(self, event):
        if event.inaxes == self.canvas.ax and event.xdata is not None:
            month_idx = int(round(event.xdata))
            if 0 <= month_idx < 12:
                # Al cambiar el índice, salta el evento currentIndexChanged que llama a load_all_data()
                if self.month_sel.currentIndex() != month_idx:
                    self.month_sel.setCurrentIndex(month_idx)

    def init_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setStyleSheet("QFrame#Sidebar { background: #0a0f1e; border-right: 1px solid #1a1f35; }")
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(0)
        
        # Logo
        logo = QLabel("PUNPRO")
        logo.setStyleSheet("font-size: 22px; font-weight: 900; color: #fff; letter-spacing: 3px;")
        layout.addWidget(logo)
        
        tagline = QLabel("Financial Suite")
        tagline.setStyleSheet("font-size: 9px; color: #64748b; margin-bottom: 20px;")
        layout.addWidget(tagline)
        
        # Search
        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText("Buscar...")
        self.global_search.setStyleSheet("""
            QLineEdit {
                background: #111827; border: 1px solid #1f2937; border-radius: 8px;
                padding: 8px 12px; color: #e2e8f0; font-size: 11px;
            }
            QLineEdit:focus { border-color: #6366f1; }
        """)
        self.global_search.textChanged.connect(self.on_global_search)
        layout.addWidget(self.global_search)
        layout.addSpacing(16)
        
        # Navigation
        self.nav_list = QListWidget()
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.nav_list.setStyleSheet("""
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item {
                padding: 10px 14px; color: #94a3b8; font-size: 12px;
                font-weight: 600; border-radius: 8px; margin: 1px 0;
            }
            QListWidget::item:selected {
                background: #6366f1; color: #fff;
            }
            QListWidget::item:hover:!selected {
                background: #111827; color: #e2e8f0;
            }
            QScrollBar:vertical { width: 4px; background: transparent; }
            QScrollBar::handle:vertical { background: #1e293b; border-radius: 2px; }
        """)
        layout.addWidget(self.nav_list)
        self.init_sidebar_items()
        self.nav_list.itemClicked.connect(self.on_nav_change)
        
        layout.addStretch()

        # Footer: Backup + Logout
        footer = QHBoxLayout()
        footer.setSpacing(8)

        btn_backup = QPushButton("Backup")
        btn_backup.setStyleSheet("""
            QPushButton {
                background: #111827; color: #10b981; border: 1px solid #1f2937;
                border-radius: 6px; padding: 7px; font-size: 10px; font-weight: 700;
            }
            QPushButton:hover { background: #10b981; color: #fff; border-color: #10b981; }
        """)
        btn_backup.clicked.connect(self.create_instant_backup)

        btn_logout = QPushButton("Salir")
        btn_logout.setStyleSheet("""
            QPushButton {
                background: #111827; color: #ef4444; border: 1px solid #1f2937;
                border-radius: 6px; padding: 7px; font-size: 10px; font-weight: 700;
            }
            QPushButton:hover { background: #ef4444; color: #fff; border-color: #ef4444; }
        """)
        btn_logout.clicked.connect(self.switch_profile_ui)

        footer.addWidget(btn_backup)
        footer.addWidget(btn_logout)
        layout.addLayout(footer)

    def add_section_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #475569; font-size: 9px; font-weight: 900; letter-spacing: 1px; padding: 12px 0 4px 6px;")
        self.nav_list.addItem(QListWidgetItem())
        self.nav_list.setItemWidget(self.nav_list.item(self.nav_list.count()-1), lbl)

    def init_sidebar_items(self):
        # Aquí decidimos qué opciones de menú mostrar en el panel izquierdo
        if self.role == "admin":
            # El administrador tiene un menú simplificado con acceso al panel global (índice 13)
            self.add_nav_item("Panel Global", 13)
            self.add_nav_item("Ejecutar Pagos", 14)
            # Control Stock eliminado
            self.add_nav_item("Auditoría Pro", 15)
            self.add_nav_item("Inteligencia IA", 11)
            self.add_section_label("EXPORTACIÓN")
            self.add_nav_item("Reportes PDF", 12)
        else:
            self.add_nav_item("Resumen", 0)
            self.add_section_label("OPERACIONES")
            self.add_nav_item("Pagos Centralizados", 1)
            self.add_nav_item("Ingresos", 2)
            self.add_nav_item("Gastos Diarios", 3)
            self.add_nav_item("Proveedores", 4)
            self.add_nav_item("Préstamos", 5)
            self.add_nav_item("Cheques", 6)
            self.add_nav_item("Tarjetas", 7)
            self.add_nav_item("Inversiones", 8)
            self.add_nav_item("Costos Fijos", 9)
            self.add_section_label("ANÁLISIS")
            self.add_nav_item("Historial", 10)

            self.add_nav_item("Asistente IA", 11)
            # Control Stock eliminado
            self.add_section_label("EXPORTACIÓN")
            self.add_nav_item("Reportes PDF", 12)

    def add_nav_item(self, text, index):
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, index)
        self.nav_list.addItem(item)

    def on_nav_change(self, item):
        index = item.data(Qt.UserRole)
        if index is not None:
            self.stack.setCurrentIndex(index)

    def init_header(self):
        self.header = QFrame()
        self.header.setFixedHeight(60)
        self.header.setObjectName("Header")
        self.header.setStyleSheet("QFrame#Header { background: #0a0f1e; border-bottom: 1px solid #1a1f35; }")
        
        layout = QHBoxLayout(self.header)
        layout.setContentsMargins(24, 0, 24, 0)
        
        # Greeting
        hour = datetime.datetime.now().hour
        greeting = "Buenos días" if 5 <= hour < 12 else "Buenas tardes" if 12 <= hour < 20 else "Buenas noches"
        name = self.company_name.upper() if self.company_name else "Admin"
        
        lbl = QLabel(f"{greeting}, {name}")
        lbl.setStyleSheet("color: #e2e8f0; font-size: 15px; font-weight: 700;")
        layout.addWidget(lbl)
        
        layout.addStretch()
        
        # Period
        self.month_sel = QComboBox()
        self.month_sel.addItems(["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"])
        self.month_sel.setCurrentIndex(datetime.date.today().month - 1)
        self.month_sel.setFixedWidth(70)
        
        self.year_sel = QComboBox()
        self.year_sel.addItems([str(y) for y in range(2024, 2031)])
        self.year_sel.setCurrentText(str(datetime.date.today().year))
        self.year_sel.setFixedWidth(80)
        
        self.month_sel.currentIndexChanged.connect(self.load_all_data)
        self.year_sel.currentIndexChanged.connect(self.load_all_data)
        
        layout.addWidget(self.month_sel)
        layout.addWidget(self.year_sel)
        
        # Lock
        self.lock_label = QLabel("🔓")
        self.lock_label.setStyleSheet("font-size: 16px; margin-left: 12px;")
        layout.addWidget(self.lock_label)
        
        self.btn_unlock = QPushButton("Desbloquear")
        self.btn_unlock.setVisible(False)
        self.btn_unlock.setStyleSheet("background: #f59e0b; color: #fff; padding: 4px 12px; font-weight: 700; border-radius: 6px; font-size: 10px;")
        self.btn_unlock.clicked.connect(self.manual_unlock)
        layout.addWidget(self.btn_unlock)

    def manual_unlock(self):
        """Permite editar registros en periodos cerrados (Solo Admin o con permiso)."""
        self.lock_label.setText("🔓")
        self.btn_unlock.setVisible(False)
        self.status_bar.showMessage("Periodo desbloqueado para edición manual.", 5000)

    def show_welcome_toast(self):
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            msg = "¡Buen día! ¿Qué vamos a registrar hoy?"
        elif 12 <= hour < 20:
            msg = "¡Buenas tardes! Revisá cómo van los números del mes."
        else:
            msg = "Trabajando de noche... ¡No olvides hacer un backup!"
        ToastNotification(self, msg, "👋", 7000, click_callback=lambda: self.stack.setCurrentIndex(11))

    def show_random_tip(self):
        tip = random.choice(AI_TIPS)
        icons = ["💡", "📊", "🎯", "🧠", "✨"]
        ToastNotification(self, tip, random.choice(icons), 9000, 
                          click_callback=lambda: self.open_ai_teaching(tip))

    def create_instant_backup(self):
        try:
            import shutil
            source = self.db.db_name
            company = source.replace('.db', '')
            default_name = f"backup_{company}_{datetime.date.today().strftime('%Y-%m-%d')}.db"
            
            dest, _ = QFileDialog.getSaveFileName(
                self, "Guardar Backup", default_name, "SQLite DB (*.db)"
            )
            if not dest:
                return
            
            shutil.copy2(source, dest)
            self.status_bar.showMessage(f"✅ Backup guardado: {dest}", 5000)
            QMessageBox.information(self, "Backup Exitoso", f"Copia de seguridad guardada en:\n\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el backup:\n{str(e)}")

    def switch_profile_ui(self):
        """Embebido en TPV: no cerrar la app, sólo ignorar la acción.
        En modo standalone original cierr el QMainWindow."""
        # Si el widget tiene padre (está embebido en el TPV), no hacer nada
        if self.parent() is not None:
            return
        # Modo standalone: comportamiento original
        self.switch_requested = True
        self.close()

    def init_dashboard_tab(self):
        self.tab_dashboard = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(35)

        # --- FINANCIAL COMMAND CENTER HEADER ---
        header_frame = QFrame()
        header_frame.setFixedHeight(100)
        header_frame.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e1b4b, stop:1 #312e81); border-radius: 20px; border: 1px solid #4338ca;")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(30, 0, 30, 0)
        
        titles_v = QVBoxLayout()
        titles_v.setAlignment(Qt.AlignCenter)
        main_title = QLabel("TORRE DE CONTROL FINANCIERO")
        main_title.setStyleSheet("font-size: 24px; font-weight: 900; color: #ffffff; letter-spacing: 2px;")
        sub_title = QLabel("AUDITORÍA EN TIEMPO REAL • NIVEL DE INTELIGENCIA 4")
        sub_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #a5b4fc; letter-spacing: 1px;")
        titles_v.addWidget(main_title)
        titles_v.addWidget(sub_title)
        h_layout.addLayout(titles_v)
        h_layout.addStretch()
        
        btn_audit = QPushButton("🔍 AUDITORÍA IA")
        btn_audit.setFixedWidth(180)
        btn_audit.setStyleSheet("background: #10b981; color: white; padding: 12px; font-weight: 900; border-radius: 12px;")
        btn_audit.clicked.connect(self.run_proactive_audit)
        h_layout.addWidget(btn_audit)
        
        layout.addWidget(header_frame)

        # --- NUEVO PANEL DE ALERTAS Y METAS (NIVEL 4 EMPRESA) ---
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        
        # 1. Centro de Alertas de Vencimiento
        self.alert_card = QFrame()
        self.alert_card.setFixedHeight(120)
        self.alert_card.setStyleSheet("background: #0f172a; border-radius: 12px; border: 1px solid #1e293b;")
        alert_layout = QVBoxLayout(self.alert_card)
        alert_title = QLabel("⏰ ALERTAS Y VENCIMIENTOS")
        alert_title.setStyleSheet("color: #f59e0b; font-weight: 900; font-size: 11px;")
        self.alert_text = QLabel("Calculando vencimientos...")
        self.alert_text.setWordWrap(True)
        self.alert_text.setStyleSheet("color: #e2e8f0; font-size: 13px;")
        alert_layout.addWidget(alert_title)
        alert_layout.addWidget(self.alert_text)
        alert_layout.addStretch()
        top_row.addWidget(self.alert_card, 1)
        
        # 2. Termómetro de Endeudamiento Mensual
        self.debt_card = QFrame()
        self.debt_card.setFixedHeight(120)
        self.debt_card.setStyleSheet("background: #0f172a; border-radius: 12px; border: 1px solid #1e293b;")
        debt_layout = QVBoxLayout(self.debt_card)
        debt_title = QLabel("🌡️ COMPROMISO DE INGRESOS")
        debt_title.setStyleSheet("color: #ef4444; font-weight: 900; font-size: 11px;")
        self.debt_text = QLabel("De cada $100 que ingresaron este mes...")
        self.debt_text.setWordWrap(True)
        self.debt_text.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.debt_progress = QProgressBar()
        self.debt_progress.setFixedHeight(10)
        self.debt_progress.setTextVisible(False)
        debt_layout.addWidget(debt_title)
        debt_layout.addWidget(self.debt_text)
        debt_layout.addWidget(self.debt_progress)
        top_row.addWidget(self.debt_card, 1)
        
        # 3. Meta de Ventas Mensual
        self.goal_card = QFrame()
        self.goal_card.setFixedHeight(120)
        self.goal_card.setStyleSheet("background: #0f172a; border-radius: 12px; border: 1px solid #1e293b;")
        goal_layout = QVBoxLayout(self.goal_card)
        goal_title = QLabel("🎯 META DE RECAUDACIÓN")
        goal_title.setStyleSheet("color: #10b981; font-weight: 900; font-size: 11px;")
        self.goal_text = QLabel("Progreso de ventas del mes")
        self.goal_text.setStyleSheet("color: #e2e8f0; font-size: 13px; font-weight: bold;")
        self.goal_progress = QProgressBar()
        self.goal_progress.setFixedHeight(15)
        self.goal_progress.setStyleSheet("""
            QProgressBar { background: #1e293b; border-radius: 7px; border: none; text-align: center; color: white; font-weight: bold; }
            QProgressBar::chunk { background-color: #10b981; border-radius: 7px; }
        """)
        goal_layout.addWidget(goal_title)
        goal_layout.addWidget(self.goal_text)
        goal_layout.addWidget(self.goal_progress)
        top_row.addWidget(self.goal_card, 1)
        
        layout.addLayout(top_row)
        # --------------------------------------------

        # --- SECCIÓN DE CONTABILIDAD PURA (PRO) ---
        layout.addWidget(QLabel("CONTABILIDAD PURA (DIA / MES / AÑO)"))
        pure_row = QHBoxLayout()
        pure_row.setSpacing(20)
        
        self.card_pure_day = self.create_stat_card("📅 TOTAL DEL DÍA", "$0.00", "#38bdf8", "pure_day")
        self.card_pure_month = self.create_stat_card("🗓️ TOTAL DEL MES", "$0.00", "#10b981", "pure_month")
        self.card_pure_year = self.create_stat_card("🏆 ACUMULADO ANUAL", "$0.00", "#8b5cf6", "pure_year")
        
        pure_row.addWidget(self.card_pure_day)
        pure_row.addWidget(self.card_pure_month)
        pure_row.addWidget(self.card_pure_year)
        layout.addLayout(pure_row)

        # Row 1: Main Stats
        layout.addWidget(QLabel("RESUMEN FINANCIERO (Clic para más detalles)"))
        stats_row = QHBoxLayout()
        self.card_income = self.create_stat_card("💵 INGRESOS TOTALES", "$0.00", "#10b981", "income")
        self.card_total = self.create_stat_card("📉 EGRESOS TOTALES", "$0.00", "#f43f5e", "expenses")
        self.card_balance = self.create_stat_card("⚖️ BALANCE NETO", "$0.00", "#6366f1", "balance")
        stats_row.addWidget(self.card_income)
        stats_row.addWidget(self.card_total)
        stats_row.addWidget(self.card_balance)
        layout.addLayout(stats_row)

        # Row 1.5: Detailed Expenses
        layout.addWidget(QLabel("ESTRUCTURA DE COSTOS"))
        exp_row = QHBoxLayout()
        self.card_fixed = self.create_stat_card("📌 COSTOS FIJOS", "$0.00", "#818cf8", "fixed")
        self.card_variable = self.create_stat_card("⚡ COSTOS VARIABLES", "$0.00", "#fbbf24", "variable")
        exp_row.addWidget(self.card_fixed)
        exp_row.addWidget(self.card_variable)
        layout.addLayout(exp_row)

        # Row 2: Balances por Departamento
        layout.addWidget(QLabel("DEUDAS Y SALDOS PENDIENTES (Haz clic para ver cuotas/vencimientos)"))
        balances_row = QHBoxLayout()
        self.card_bal_loans = self.create_stat_card("PRÉSTAMOS", "$0.00", "#ef4444", "loans")
        self.card_bal_checks = self.create_stat_card("CHEQUES", "$0.00", "#ef4444", "checks")
        self.card_bal_cards = self.create_stat_card("TARJETAS", "$0.00", "#ef4444", "cards")
        self.card_bal_prov = self.create_stat_card("PROVEEDORES", "$0.00", "#ef4444", "prov")
        balances_row.addWidget(self.card_bal_loans)
        balances_row.addWidget(self.card_bal_checks)
        balances_row.addWidget(self.card_bal_cards)
        balances_row.addWidget(self.card_bal_prov)
        layout.addLayout(balances_row)

        # --- Visual Analytics Row ---
        chart_container = QFrame()
        chart_container.setObjectName("Card")
        chart_container.setFixedHeight(300)
        chart_layout = QVBoxLayout(chart_container)
        chart_title = QLabel("📊 VELAS FINANCIERAS TRADING (Haz clic en una vela para analizar el mes)")
        chart_title.setStyleSheet("font-weight: bold; color: #e2e8f0; font-size: 14px;")
        chart_layout.addWidget(chart_title)
        self.canvas = MatplotlibCanvas(self)
        self.canvas.mpl_connect('button_press_event', self.on_chart_click)
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_container)

        # Middle Row: Analysis & Categories
        middle_row = QHBoxLayout()
        middle_row.setSpacing(20)

        # Left: Analysis
        analysis_card = QFrame()
        analysis_card.setObjectName("Card")
        analysis_layout = QVBoxLayout(analysis_card)
        analysis_layout.addWidget(QLabel("DISTRIBUCIÓN DE GASTOS"))
        
        self.fixed_percent_lbl = QLabel("Fijos: 0%")
        self.fixed_progress = QProgressBar()
        analysis_layout.addWidget(self.fixed_percent_lbl)
        analysis_layout.addWidget(self.fixed_progress)
        
        self.var_percent_lbl = QLabel("Variables: 0%")
        self.var_progress = QProgressBar()
        analysis_layout.addWidget(self.var_percent_lbl)
        analysis_layout.addWidget(self.var_progress)
        analysis_layout.addStretch()
        middle_row.addWidget(analysis_card, 1)
        
        # Projections and Health
        health_container = QFrame()
        health_container.setObjectName("Card")
        health_layout = QVBoxLayout(health_container)
        health_layout.addWidget(QLabel("📊 PROYECCIÓN MENSUAL DE PAGOS"))
        
        self.progress_label = QLabel("Pendiente de pago: $0.00")
        self.progress_label.setStyleSheet("font-weight: bold; color: #94a3b8;")
        health_layout.addWidget(self.progress_label)
        
        self.liability_progress = QProgressBar()
        self.liability_progress.setValue(0)
        health_layout.addWidget(self.liability_progress)
        
        health_layout.addWidget(QLabel("Este gráfico muestra cuánto de tus deudas mensuales (Cuotas + Fijos + Cheques) ya has cubierto."))
        health_layout.addStretch()
        middle_row.addWidget(health_container, 1)
        
        # Categories Table
        cat_container = QFrame()
        cat_container.setObjectName("Card")
        cat_layout = QVBoxLayout(cat_container)
        cat_layout.addWidget(QLabel("📂 EGRESOS POR CATEGORÍA (Top 5)"))
        
        self.cat_list_layout = QVBoxLayout()
        cat_layout.addLayout(self.cat_list_layout)
        cat_layout.addStretch()
        
        middle_row.addWidget(cat_container, 1)
        
        layout.addLayout(middle_row)
        
        scroll.setWidget(container)
        
        dash_layout = QVBoxLayout(self.tab_dashboard)
        dash_layout.addWidget(scroll)
        self.stack.addWidget(self.tab_dashboard)

    def init_income_tab(self):
        self.tab_income = QWidget()
        main_layout = QVBoxLayout(self.tab_income)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 📊 DASHBOARD INGRESOS
        header = QFrame(); header.setObjectName("Card"); header.setFixedHeight(110)
        h_layout = QHBoxLayout(header)
        s1 = QVBoxLayout(); self.inc_stat_total = QLabel("$0.00"); self.inc_stat_total.setStyleSheet("font-size: 22px; font-weight: 800; color: #10b981;")
        s1.addWidget(QLabel("TOTAL INGRESOS")); s1.addWidget(self.inc_stat_total)
        s2 = QVBoxLayout(); self.inc_stat_avg = QLabel("$0.00"); self.inc_stat_avg.setStyleSheet("font-size: 22px; font-weight: 800; color: #6366f1;")
        s2.addWidget(QLabel("PROMEDIO DIARIO")); s2.addWidget(self.inc_stat_avg)
        s3 = QVBoxLayout(); self.inc_stat_count = QLabel("0"); self.inc_stat_count.setStyleSheet("font-size: 22px; font-weight: 800; color: #f59e0b;")
        s3.addWidget(QLabel("VENTAS REGISTRADAS")); s3.addWidget(self.inc_stat_count)
        h_layout.addLayout(s1); h_layout.addLayout(s2); h_layout.addLayout(s3)
        main_layout.addWidget(header)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left: Form
        form_container = QFrame()
        form_container.setObjectName("Card")
        form_container.setFixedWidth(320)
        form_layout = QVBoxLayout(form_container)
        form_layout.addWidget(QLabel("REGISTRAR INGRESO (VENTAS)"))
        
        self.inc_date = QDateEdit()
        self.inc_date.setCalendarPopup(True)
        self.inc_date.setDate(QDate.currentDate())
        form_layout.addWidget(QLabel("Fecha:"))
        form_layout.addWidget(self.inc_date)
        
        self.inc_source = QComboBox()
        self.inc_source.addItems(Config.INCOME_SOURCES)
        form_layout.addWidget(QLabel("Origen:"))
        form_layout.addWidget(self.inc_source)
        
        self.inc_amount = QLineEdit()
        self.inc_amount.setPlaceholderText("0.00")
        form_layout.addWidget(QLabel("Monto ($):"))
        form_layout.addWidget(self.inc_amount)
        
        self.inc_desc = QLineEdit()
        self.inc_desc.setPlaceholderText("Comentario...")
        form_layout.addWidget(QLabel("Descripción:"))
        form_layout.addWidget(self.inc_desc)
        
        btn_save = QPushButton("Guardar Ingreso")
        btn_save.clicked.connect(self.save_income)
        form_layout.addWidget(btn_save)
        form_layout.addStretch()
        content_layout.addWidget(form_container)

        # Right: Table
        table_container = QFrame()
        table_container.setObjectName("Card")
        table_layout = QVBoxLayout(table_container)
        self.inc_table = QTableWidget()
        self.inc_table.setColumnCount(5)
        self.inc_table.setHorizontalHeaderLabels(["Fecha", "Origen", "Descripción", "Monto", "Acción"])
        self.inc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.inc_table)
        content_layout.addWidget(table_container)
        main_layout.addLayout(content_layout)
        self.stack.addWidget(self.tab_income)

    def init_expenses_tab(self):
        self.tab_expenses = QWidget()
        main_layout = QVBoxLayout(self.tab_expenses)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 📊 DASHBOARD GASTOS
        header = QFrame(); header.setObjectName("Card"); header.setFixedHeight(110)
        h_layout = QHBoxLayout(header)
        s1 = QVBoxLayout(); self.exp_stat_total = QLabel("$0.00"); self.exp_stat_total.setStyleSheet("font-size: 22px; font-weight: 800; color: #ef4444;")
        s1.addWidget(QLabel("TOTAL EGRESOS")); s1.addWidget(self.exp_stat_total)
        s2 = QVBoxLayout(); self.exp_stat_max = QLabel("$0.00"); self.exp_stat_max.setStyleSheet("font-size: 22px; font-weight: 800; color: #f59e0b;")
        s2.addWidget(QLabel("EGRESO MÁXIMO")); s2.addWidget(self.exp_stat_max)
        s3 = QVBoxLayout(); self.exp_stat_count = QLabel("0"); self.exp_stat_count.setStyleSheet("font-size: 22px; font-weight: 800; color: #6366f1;")
        s3.addWidget(QLabel("OPERACIONES")); s3.addWidget(self.exp_stat_count)
        h_layout.addLayout(s1); h_layout.addLayout(s2); h_layout.addLayout(s3)
        main_layout.addWidget(header)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left: Form
        form_container = QFrame()
        form_container.setObjectName("Card")
        form_container.setFixedWidth(320)
        form_layout = QVBoxLayout(form_container)
        form_layout.addWidget(QLabel("REGISTRAR GASTO VARIABLE"))
        self.exp_date = QDateEdit()
        self.exp_date.setCalendarPopup(True)
        self.exp_date.setDate(QDate.currentDate())
        form_layout.addWidget(QLabel("Fecha:"))
        form_layout.addWidget(self.exp_date)
        self.exp_cat = QComboBox()
        self.exp_cat.addItems(Config.EXPENSE_CATEGORIES)
        form_layout.addWidget(QLabel("Categoría:"))
        form_layout.addWidget(self.exp_cat)
        self.exp_amount = QLineEdit()
        self.exp_amount.setPlaceholderText("0.00")
        form_layout.addWidget(QLabel("Monto ($):"))
        form_layout.addWidget(self.exp_amount)
        self.exp_desc = QLineEdit()
        self.exp_desc.setPlaceholderText("Descripción...")
        form_layout.addWidget(QLabel("Descripción:"))
        form_layout.addWidget(self.exp_desc)
        btn_save = QPushButton("Guardar Gasto")
        btn_save.clicked.connect(self.save_variable_expense)
        form_layout.addWidget(btn_save)
        form_layout.addStretch()
        content_layout.addWidget(form_container)

        # Right: Table
        table_container = QFrame()
        table_container.setObjectName("Card")
        table_layout = QVBoxLayout(table_container)
        
        # Search Bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por categoría o descripción...")
        self.search_input.textChanged.connect(self.update_expenses_table)
        search_layout.addWidget(QLabel("🔍"))
        search_layout.addWidget(self.search_input)
        table_layout.addLayout(search_layout)

        self.exp_table = QTableWidget()
        self.exp_table.setColumnCount(6)
        self.exp_table.setHorizontalHeaderLabels(["Fecha", "Tipo", "Categoría", "Descripción", "Monto", "Acción"])
        self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.exp_table.setColumnWidth(5, 100)
        table_layout.addWidget(self.exp_table)
        content_layout.addWidget(table_container)
        main_layout.addLayout(content_layout)
        self.stack.addWidget(self.tab_expenses)

    def init_proveedores_tab(self):
        self.tab_proveedores = QWidget()
        layout = QHBoxLayout(self.tab_proveedores)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Left: Form
        form_container = QFrame()
        form_container.setObjectName("Card")
        form_container.setFixedWidth(320)
        form_layout = QVBoxLayout(form_container)
        form_layout.addWidget(QLabel("NUEVA COMPRA A PROVEEDOR"))
        
        self.prov_date = QDateEdit()
        self.prov_date.setCalendarPopup(True)
        self.prov_date.setDate(QDate.currentDate())
        form_layout.addWidget(QLabel("Fecha:"))
        form_layout.addWidget(self.prov_date)

        self.prov_name = QLineEdit()
        self.prov_name.setPlaceholderText("Nombre Proveedor (Opcional)")
        form_layout.addWidget(QLabel("Proveedor:"))
        form_layout.addWidget(self.prov_name)

        self.prov_type = QComboBox()
        self.prov_type.addItems(["Carne (Media Res)", "Cerdo", "Pollo", "Achuras", "Otro"])
        self.prov_type.currentTextChanged.connect(self.on_prov_type_change)
        form_layout.addWidget(QLabel("Tipo de Mercadería:"))
        form_layout.addWidget(self.prov_type)

        self.prov_calc_label = QLabel("Calculadora (Pesos x Precio):")
        form_layout.addWidget(self.prov_calc_label)
        self.prov_kilos = QLineEdit()
        self.prov_kilos.setPlaceholderText("Kilos (ej: 78+80.5+75)")
        self.prov_kilos.textChanged.connect(self.update_prov_calc)
        self.prov_precio_kg = QLineEdit()
        self.prov_precio_kg.setPlaceholderText("Precio x Kg")
        self.prov_precio_kg.textChanged.connect(self.update_prov_calc)
        
        calc_layout = QHBoxLayout()
        calc_layout.addWidget(self.prov_kilos)
        calc_layout.addWidget(self.prov_precio_kg)
        form_layout.addLayout(calc_layout)

        self.prov_amount = QLineEdit()
        self.prov_amount.setPlaceholderText("0.00")
        form_layout.addWidget(QLabel("Monto Total ($):"))
        form_layout.addWidget(self.prov_amount)

        self.prov_payment = QComboBox()
        self.prov_payment.addItems(["Contado (Pago Inmediato)", "A Pagar (Deuda)"])
        form_layout.addWidget(QLabel("Forma de Pago:"))
        form_layout.addWidget(self.prov_payment)

        btn_save = QPushButton("Guardar Compra")
        btn_save.clicked.connect(self.save_proveedor)
        form_layout.addWidget(btn_save)
        form_layout.addStretch()
        layout.addWidget(form_container)

        table_container = QFrame()
        table_container.setObjectName("Card")
        table_layout = QVBoxLayout(table_container)
        table_layout.addWidget(QLabel("ÚLTIMAS COMPRAS REGISTRADAS (MES ACTUAL)"))
        self.prov_table = QTableWidget()
        self.prov_table.setColumnCount(10)
        self.prov_table.setHorizontalHeaderLabels(["Fecha", "Proveedor", "Mercadería", "Cant.", "Pesos/Detalle", "Total Kg/Und", "Precio Unit.", "Monto", "Estado", "Acciones"])
        self.prov_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.prov_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.prov_table.verticalHeader().setVisible(False)
        self.prov_table.setWordWrap(True)
        table_layout.addWidget(self.prov_table)
        
        layout.addWidget(table_container)
        self.stack.addWidget(self.tab_proveedores)

    def on_prov_type_change(self, text):
        if text in ["Pollo", "Achuras", "Otro"]:
            self.prov_calc_label.setText("Calculadora (Cantidad x Precio):")
            self.prov_kilos.setPlaceholderText("Cant. (ej: 5)")
            self.prov_precio_kg.setPlaceholderText("Precio x Caja/Unid.")
        else:
            self.prov_calc_label.setText("Calculadora (Pesos x Precio):")
            self.prov_kilos.setPlaceholderText("Kilos (ej: 78+80.5+75)")
            self.prov_precio_kg.setPlaceholderText("Precio x Kg")
        self.update_prov_calc()


    def init_fixed_costs_tab(self):
        self.tab_fixed = QWidget()
        layout = QHBoxLayout(self.tab_fixed)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        config_container = QFrame()
        config_container.setObjectName("Card")
        config_container.setFixedWidth(320)
        config_layout = QVBoxLayout(config_container)
        config_layout.addWidget(QLabel("CONFIGURAR COSTO FIJO"))
        self.fix_name = QLineEdit()
        self.fix_name.setPlaceholderText("Ej: Alquiler Local")
        config_layout.addWidget(QLabel("Nombre:"))
        config_layout.addWidget(self.fix_name)
        self.fix_cat = QComboBox()
        self.fix_cat.addItems(Config.FIXED_COST_CATEGORIES)
        config_layout.addWidget(QLabel("Categoría:"))
        config_layout.addWidget(self.fix_cat)
        self.fix_amount = QLineEdit()
        self.fix_amount.setPlaceholderText("0.00")
        config_layout.addWidget(QLabel("Monto Mensual ($):"))
        config_layout.addWidget(self.fix_amount)
        btn_add_fix = QPushButton("Agregar a la Lista")
        btn_add_fix.clicked.connect(self.add_fixed_cost_config)
        config_layout.addWidget(btn_add_fix)
        config_layout.addSpacing(30)
        apply_btn = QPushButton("PRECARGAR DEL MES ANTERIOR")
        apply_btn.setStyleSheet("background-color: #10b981; height: 50px; font-weight: bold;")
        apply_btn.clicked.connect(self.apply_monthly_fixed_costs)
        config_layout.addWidget(apply_btn)
        config_layout.addStretch()
        layout.addWidget(config_container)

        list_container = QFrame()
        list_container.setObjectName("Card")
        list_layout = QVBoxLayout(list_container)
        list_layout.addWidget(QLabel("COSTOS FIJOS CONFIGURADOS"))
        self.fix_table = QTableWidget()
        self.fix_table.setColumnCount(6)
        self.fix_table.setHorizontalHeaderLabels(["Vencimiento", "Descripción", "Monto Total", "Monto Restante", "Estado", "Acción"])
        self.fix_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        list_layout.addWidget(self.fix_table)
        layout.addWidget(list_container)
        self.stack.addWidget(self.tab_fixed)

    def init_loans_tab(self):
        self.tab_loans = QWidget()
        main_layout = QVBoxLayout(self.tab_loans)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 🏦 BANK DASHBOARD HEADER
        header_stats = QFrame()
        header_stats.setObjectName("Card")
        header_stats.setFixedHeight(120)
        stats_layout = QHBoxLayout(header_stats)
        
        # Stat 1: Total Debt
        s1 = QVBoxLayout(); self.loan_stat_total = QLabel("$0.00"); self.loan_stat_total.setStyleSheet("font-size: 24px; font-weight: 800; color: #ef4444;")
        s1.addWidget(QLabel("DEUDA TOTAL ACTIVA")); s1.addWidget(self.loan_stat_total)
        
        # Stat 2: Next Expiration
        s2 = QVBoxLayout(); self.loan_stat_next = QLabel("Sin Pendientes"); self.loan_stat_next.setStyleSheet("font-size: 24px; font-weight: 800; color: #f59e0b;")
        s2.addWidget(QLabel("PRÓXIMO VENCIMIENTO")); s2.addWidget(self.loan_stat_next)
        
        # Stat 3: Progress
        s3 = QVBoxLayout(); self.loan_stat_progress = QLabel("0%"); self.loan_stat_progress.setStyleSheet("font-size: 24px; font-weight: 800; color: #10b981;")
        s3.addWidget(QLabel("PROGRESO DE PAGO")); s3.addWidget(self.loan_stat_progress)
        
        stats_layout.addLayout(s1); stats_layout.addLayout(s2); stats_layout.addLayout(s3)
        main_layout.addWidget(header_stats)

        # Bottom content (Form + Tables)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left: New Loan Form
        form_container = QFrame()
        form_container.setObjectName("Card")
        form_container.setFixedWidth(320)
        form_layout = QVBoxLayout(form_container)
        form_layout.addWidget(QLabel("NUEVO PRÉSTAMO / CRÉDITO"))
        
        self.loan_name = QLineEdit()
        self.loan_name.setPlaceholderText("Nombre del Banco/Entidad")
        form_layout.addWidget(QLabel("Entidad:"))
        form_layout.addWidget(self.loan_name)
        
        # --- SECCIÓN: Capital, Interés y Cuotas (Calculadora Inteligente) ---
        
        # 1. Capital Solicitado
        self.loan_capital = QLineEdit()
        self.loan_capital.setPlaceholderText("Ej: 100000")
        form_layout.addWidget(QLabel("Capital Solicitado ($):"))
        form_layout.addWidget(self.loan_capital)
        
        # 2. Cuotas y Valor Exacto
        cuotas_layout = QHBoxLayout()
        self.loan_inst = QLineEdit()
        self.loan_inst.setPlaceholderText("Cant. (ej: 12)")
        self.loan_inst_amount = QLineEdit()
        self.loan_inst_amount.setPlaceholderText("Valor exacto cuota ($)")
        cuotas_layout.addWidget(self.loan_inst)
        cuotas_layout.addWidget(self.loan_inst_amount)
        form_layout.addWidget(QLabel("Cant. Cuotas / Valor de la Cuota:"))
        form_layout.addLayout(cuotas_layout)
        
        # 3. Interés y Monto Total
        tot_layout = QHBoxLayout()
        self.loan_interest = QLineEdit()
        self.loan_interest.setPlaceholderText("Interés Total ($)")
        self.loan_amount = QLineEdit()
        self.loan_amount.setPlaceholderText("Deuda Total ($)")
        tot_layout.addWidget(self.loan_interest)
        tot_layout.addWidget(self.loan_amount)
        form_layout.addWidget(QLabel("Interés Total / Monto Total a Pagar:"))
        form_layout.addLayout(tot_layout)
        
        # --- CONEXIONES MULTIDIRECCIONALES ---
        # No importa qué casilla llene el usuario, el sistema deduce el resto.
        self.loan_capital.textChanged.connect(lambda: self.on_loan_calc_change('capital'))
        self.loan_inst.textChanged.connect(lambda: self.on_loan_calc_change('cuotas'))
        self.loan_inst_amount.textChanged.connect(lambda: self.on_loan_calc_change('valor_cuota'))
        self.loan_interest.textChanged.connect(lambda: self.on_loan_calc_change('interes'))
        self.loan_amount.textChanged.connect(lambda: self.on_loan_calc_change('total'))
        
        
        # First Due Date
        self.loan_first_date = QDateEdit()
        self.loan_first_date.setCalendarPopup(True)
        self.loan_first_date.setDate(QDate.currentDate().addMonths(1))
        form_layout.addWidget(QLabel("Fecha primer vencimiento:"))
        form_layout.addWidget(self.loan_first_date)

        self.loan_cat = QComboBox()
        self.loan_cat.addItems(Config.LOAN_CATEGORIES)
        form_layout.addWidget(QLabel("Categoría:"))
        form_layout.addWidget(self.loan_cat)
        
        self.btn_loan = QPushButton("Crear Préstamo")
        self.btn_loan.clicked.connect(self.save_loan)
        form_layout.addWidget(self.btn_loan)
        form_layout.addStretch()
        content_layout.addWidget(form_container)

        # Right: Tables
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Loan Summary Table (with interest %)
        summary_container = QFrame()
        summary_container.setObjectName("Card")
        summary_layout = QVBoxLayout(summary_container)
        summary_layout.addWidget(QLabel("RESUMEN DE CRÉDITOS Y LÍNEAS ACTIVAS"))
        self.loan_summary_table = QTableWidget()
        self.loan_summary_table.setColumnCount(6)
        self.loan_summary_table.setHorizontalHeaderLabels(["Banco/Entidad", "Capital", "Interés", "Costo Fin.", "Saldo Pendiente", "Acción"])
        self.loan_summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        summary_layout.addWidget(self.loan_summary_table)
        right_layout.addWidget(summary_container, 1)

        # Installments Table
        inst_container = QFrame()
        inst_container.setObjectName("Card")
        inst_layout = QVBoxLayout(inst_container)
        inst_layout.addWidget(QLabel("CRONOGRAMA DE PAGOS (PRÓXIMAS CUOTAS)"))
        self.inst_table = QTableWidget()
        self.inst_table.setColumnCount(10)
        self.inst_table.setHorizontalHeaderLabels([
            "Préstamo", "Progreso", "Cap. Cuota", "Int. Cuota", "% Int.", "Monto Cuota", "Saldo Total", "Vencimiento", "Estado", "Acción"
        ])
        self.inst_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        inst_layout.addWidget(self.inst_table)
        right_layout.addWidget(inst_container, 2)
        
        content_layout.addWidget(right_container)
        main_layout.addLayout(content_layout)
        self.stack.addWidget(self.tab_loans)

    def init_checks_tab(self):
        self.tab_checks = QWidget()
        layout = QHBoxLayout(self.tab_checks)
        layout.setContentsMargins(20, 20, 20, 20)

        form_container = QFrame()
        form_container.setObjectName("Card")
        form_container.setFixedWidth(320)
        form_layout = QVBoxLayout(form_container)
        form_layout.addWidget(QLabel("CARGAR NUEVO CHEQUE"))
        self.check_bank = QLineEdit()
        form_layout.addWidget(QLabel("Banco:"))
        form_layout.addWidget(self.check_bank)
        self.check_num = QLineEdit()
        form_layout.addWidget(QLabel("Nro Cheque:"))
        form_layout.addWidget(self.check_num)
        self.check_amt = QLineEdit()
        form_layout.addWidget(QLabel("Monto ($):"))
        form_layout.addWidget(self.check_amt)
        self.check_date = QDateEdit()
        self.check_date.setCalendarPopup(True)
        self.check_date.setDate(QDate.currentDate())
        form_layout.addWidget(QLabel("Fecha de Pago:"))
        form_layout.addWidget(self.check_date)
        self.check_recp = QLineEdit()
        form_layout.addWidget(QLabel("Beneficiario:"))
        form_layout.addWidget(self.check_recp)
        btn_check = QPushButton("Guardar Cheque")
        btn_check.clicked.connect(self.save_check)
        form_layout.addWidget(btn_check)
        form_layout.addStretch()
        layout.addWidget(form_container)

        table_container = QFrame()
        table_container.setObjectName("Card")
        table_layout = QVBoxLayout(table_container)
        self.check_table = QTableWidget()
        self.check_table.setColumnCount(6)
        self.check_table.setHorizontalHeaderLabels(["Banco", "Nro", "Beneficiario", "Monto", "Vencimiento", "Acción"])
        self.check_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.check_table)
        layout.addWidget(table_container)
        self.stack.addWidget(self.tab_checks)

    def init_debts_tab(self):
        self.tab_debts = QWidget()
        layout = QHBoxLayout(self.tab_debts)
        layout.setContentsMargins(20, 20, 20, 20)

        form_container = QFrame()
        form_container.setObjectName("Card")
        form_container.setFixedWidth(320)
        form_layout = QVBoxLayout(form_container)
        form_layout.addWidget(QLabel("NUEVA DEUDA (TARJETA/PROV)"))
        self.debt_name = QLineEdit()
        form_layout.addWidget(QLabel("Nombre:"))
        form_layout.addWidget(self.debt_name)
        self.debt_cat = QComboBox()
        self.debt_cat.addItems(["Tarjeta", "Proveedor"])
        form_layout.addWidget(QLabel("Tipo:"))
        form_layout.addWidget(self.debt_cat)
        self.debt_amt = QLineEdit()
        form_layout.addWidget(QLabel("Monto ($):"))
        form_layout.addWidget(self.debt_amt)
        self.debt_date = QDateEdit()
        self.debt_date.setCalendarPopup(True)
        self.debt_date.setDate(QDate.currentDate())
        form_layout.addWidget(QLabel("Vencimiento:"))
        form_layout.addWidget(self.debt_date)
        btn_debt = QPushButton("Guardar Deuda")
        btn_debt.clicked.connect(self.save_general_debt)
        form_layout.addWidget(btn_debt)
        form_layout.addStretch()
        layout.addWidget(form_container)

        table_container = QFrame()
        table_container.setObjectName("Card")
        table_layout = QVBoxLayout(table_container)
        self.debt_table = QTableWidget()
        self.debt_table.setColumnCount(5)
        self.debt_table.setHorizontalHeaderLabels(["Nombre", "Tipo", "Monto", "Vencimiento", "Acción"])
        self.debt_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.debt_table)
        layout.addWidget(table_container)
        self.stack.addWidget(self.tab_debts)

    def init_investments_tab(self):
        self.tab_investments = QWidget()
        layout = QHBoxLayout(self.tab_investments)
        layout.setContentsMargins(20, 20, 20, 20)

        form_container = QFrame()
        form_container.setObjectName("Card")
        form_container.setFixedWidth(320)
        form_layout = QVBoxLayout(form_container)
        form_layout.addWidget(QLabel("REGISTRAR INVERSIÓN"))
        self.inv_name = QLineEdit()
        self.inv_name.setPlaceholderText("Ej: Plazo Fijo, Terreno, Bono")
        form_layout.addWidget(QLabel("Nombre de Inversión:"))
        form_layout.addWidget(self.inv_name)
        
        self.inv_type = QComboBox()
        self.inv_type.addItems(["Pago Único", "Plan de Pago (Cuotas)"])
        self.inv_type.currentTextChanged.connect(self.on_inv_type_changed)
        form_layout.addWidget(QLabel("Tipo:"))
        form_layout.addWidget(self.inv_type)
        
        self.inv_cuotas_lbl = QLabel("Cantidad de Cuotas:")
        self.inv_cuotas_lbl.hide()
        form_layout.addWidget(self.inv_cuotas_lbl)
        self.inv_cuotas = QSpinBox()
        self.inv_cuotas.setRange(2, 120)
        self.inv_cuotas.hide()
        form_layout.addWidget(self.inv_cuotas)
        
        self.inv_amt_lbl = QLabel("Monto a Invertir ($):")
        form_layout.addWidget(self.inv_amt_lbl)
        self.inv_amt = QLineEdit()
        self.inv_amt.setPlaceholderText("0.00")
        form_layout.addWidget(self.inv_amt)
        
        self.inv_date_lbl = QLabel("Fecha de Pago:")
        form_layout.addWidget(self.inv_date_lbl)
        self.inv_date = QDateEdit()
        self.inv_date.setCalendarPopup(True)
        self.inv_date.setDate(QDate.currentDate())
        form_layout.addWidget(self.inv_date)
        
        btn_inv = QPushButton("Enviar a Tesorería")
        btn_inv.setStyleSheet("background-color: #3b82f6; font-weight: bold;")
        btn_inv.clicked.connect(self.save_investment)
        form_layout.addWidget(btn_inv)
        form_layout.addStretch()
        layout.addWidget(form_container)

        table_container = QFrame()
        table_container.setObjectName("Card")
        table_layout = QVBoxLayout(table_container)
        table_layout.addWidget(QLabel("INVERSIONES PENDIENTES / EN CURSO"))
        self.inv_table = QTableWidget()
        self.inv_table.setColumnCount(5)
        self.inv_table.setHorizontalHeaderLabels(["Fecha Pago", "Inversión", "Total", "Restante", "Estado"])
        self.inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.inv_table)
        layout.addWidget(table_container)
        self.stack.addWidget(self.tab_investments)

    def on_inv_type_changed(self, text):
        if text == "Pago Único":
            self.inv_cuotas_lbl.hide()
            self.inv_cuotas.hide()
            self.inv_amt_lbl.setText("Monto a Invertir ($):")
            self.inv_date_lbl.setText("Fecha de Pago:")
        else:
            self.inv_cuotas_lbl.show()
            self.inv_cuotas.show()
            self.inv_amt_lbl.setText("Monto Total a Financiar ($):")
            self.inv_date_lbl.setText("Fecha del 1° Pago:")

    def save_investment(self):
        name = self.inv_name.text().strip()
        itype = self.inv_type.currentText()
        amt = self.inv_amt.text().replace(',', '.')
        
        if not name or not amt:
            QMessageBox.warning(self, "Error", "Complete los campos")
            return
            
        try:
            val = float(amt)
            if val <= 0: raise ValueError
            
            if itype == "Pago Único":
                date = self.inv_date.date().toString("yyyy-MM-dd")
                full_name = f"{name} (Único)"
                self.db.add_general_debt(full_name, "Inversión", val, date)
            else:
                cuotas = self.inv_cuotas.value()
                val_por_cuota = val / cuotas
                start_date = self.inv_date.date()
                
                for i in range(1, cuotas + 1):
                    full_name = f"{name} (Cuota {i}/{cuotas})"
                    payment_date = start_date.addMonths(i - 1).toString("yyyy-MM-dd")
                    self.db.add_general_debt(full_name, "Inversión", val_por_cuota, payment_date)
                    
            self.inv_name.clear(); self.inv_amt.clear()
            self.load_all_data()
            QMessageBox.information(self, "Éxito", "La inversión fue enviada a la Tesorería para su pago.")
        except:
            QMessageBox.warning(self, "Error", "Monto inválido")

    def update_investments_table(self):
        invs = [d for d in self.db.get_general_debts() if d[2] == 'Inversión']
        self.inv_table.setRowCount(0)
        for i in invs:
            row = self.inv_table.rowCount()
            self.inv_table.insertRow(row)
            self.inv_table.setItem(row, 0, QTableWidgetItem(i[4])) # Vencimiento
            self.inv_table.setItem(row, 1, QTableWidgetItem(i[1])) # Nombre + Tipo
            self.inv_table.setItem(row, 2, QTableWidgetItem(f"${i[3]:,.2f}"))
            
            rest = i[3] - (i[6] if i[6] else 0.0)
            self.inv_table.setItem(row, 3, QTableWidgetItem(f"${rest:,.2f}"))
            
            estado = "Parcial" if i[5] == 'partial' else "Pendiente"
            self.inv_table.setItem(row, 4, QTableWidgetItem(estado))


    def update_prov_calc(self):
        kilos_text = self.prov_kilos.text().replace(',', '.')
        precio_text = self.prov_precio_kg.text().replace(',', '.')
        if not kilos_text or not precio_text: return
        if not re.match(r'^[\d\.\+\s]+$', kilos_text): return 
        try:
            total_kilos = sum(float(x) for x in kilos_text.split('+') if x.strip())
            precio = float(precio_text)
            total = total_kilos * precio
            self.prov_amount.setText(f"{total:.2f}")
        except Exception as e:
            logger.error(f"Error en cálculo aritmético: {e}")

    def on_prov_type_change(self, text):
        is_meat = text in ["Carne (Media Res)", "Cerdo"]
        self.prov_kilos.setPlaceholderText("Kilos (ej: 78+80.5+75)" if is_meat else "Cantidad / Unidades")
        self.prov_calc_label.setText("Cálculo Automático (Kilos x Precio):" if is_meat else "Cálculo (Unidades x Precio):")

    def on_loan_calc_change(self, source):
        try:
            cap = float(self.loan_capital.text()) if self.loan_capital.text() else 0
            inst = int(self.loan_inst.text()) if self.loan_inst.text() else 0
            v_cuota = float(self.loan_inst_amount.text()) if self.loan_inst_amount.text() else 0
            inte = float(self.loan_interest.text()) if self.loan_interest.text() else 0
            tot = float(self.loan_amount.text()) if self.loan_amount.text() else 0
            
            self.loan_capital.blockSignals(True); self.loan_inst.blockSignals(True)
            self.loan_inst_amount.blockSignals(True); self.loan_interest.blockSignals(True); self.loan_amount.blockSignals(True)
            
            if source == 'capital' or source == 'cuotas' or source == 'valor_cuota':
                if cap > 0 and inst > 0 and v_cuota > 0:
                    tot = inst * v_cuota
                    inte = tot - cap
                elif cap > 0 and inst > 0 and inte > 0:
                    tot = cap + inte
                    v_cuota = tot / inst
            elif source == 'interes':
                if cap > 0: tot = cap + inte
                if inst > 0 and tot > 0: v_cuota = tot / inst
            elif source == 'total':
                if cap > 0: inte = tot - cap
                if inst > 0 and tot > 0: v_cuota = tot / inst
                
            if source != 'total': self.loan_amount.setText(f"{tot:.2f}")
            if source != 'interes': self.loan_interest.setText(f"{inte:.2f}")
            if source != 'valor_cuota': self.loan_inst_amount.setText(f"{v_cuota:.2f}")
            
            self.loan_capital.blockSignals(False); self.loan_inst.blockSignals(False)
            self.loan_inst_amount.blockSignals(False); self.loan_interest.blockSignals(False); self.loan_amount.blockSignals(False)
        except: pass

    def init_history_tab(self):
        self.tab_history = QWidget()
        layout = QVBoxLayout(self.tab_history)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header with Search
        header = QFrame()
        header.setObjectName("Card")
        header_layout = QHBoxLayout(header)
        header_layout.addWidget(QLabel("🔍 BUSCAR MOVIMIENTO:"))
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("Escribe para filtrar por descripción, categoría...")
        self.history_search.textChanged.connect(self.update_history_table)
        header_layout.addWidget(self.history_search)
        layout.addWidget(header)

        # Table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels(["Fecha", "Tipo", "Categoría", "Descripción", "Monto", "Estado", "Acción"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.history_table)
        self.stack.addWidget(self.tab_history)

    def init_admin_tab(self):
        self.tab_admin = QWidget()
        outer_layout = QVBoxLayout(self.tab_admin)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Unified Infinite Scroll Area ---
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QFrame.NoFrame)
        main_scroll.setStyleSheet("""
            QScrollArea { background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: #050a18;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #1e293b;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #38bdf8;
            }
        """)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)
        
        # Header with Motivation
        header_container = QFrame()
        header_container.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed); border-radius: 20px; padding: 10px;")
        header_layout = QVBoxLayout(header_container)
        
        title = QLabel("👑 PANEL DE CONTROL GLOBAL")
        title.setStyleSheet("font-size: 24px; font-weight: 900; color: white; background: transparent;")
        
        header_layout.addWidget(title)
        
        # --- Top Section: Radar, Fuga & Estrella (Fused into Header) ---
        radar_ranking_layout = QHBoxLayout()
        radar_ranking_layout.setSpacing(15)
        radar_ranking_layout.setContentsMargins(0, 5, 0, 0)
        
        card_style = "background: rgba(15, 23, 42, 0.5); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1);"
        title_style = "color: white; font-weight: bold; background: transparent; font-size: 13px;"
        
        # Radar
        radar_container = QVBoxLayout()
        r_title = QLabel("🚨 RADAR DE PELIGRO CRÍTICO")
        r_title.setStyleSheet(title_style)
        radar_container.addWidget(r_title)
        self.radar_frame = QFrame()
        self.radar_frame.setMinimumHeight(115)
        self.radar_frame.setStyleSheet(card_style)
        self.radar_layout = QVBoxLayout(self.radar_frame)
        self.radar_layout.setContentsMargins(15, 10, 15, 10)
        radar_container.addWidget(self.radar_frame)
        radar_ranking_layout.addLayout(radar_container, 1)
        
        # Ranking
        ranking_container = QVBoxLayout()
        rk_title = QLabel("🏆 RANKING FUGA DE CAPITALES")
        rk_title.setStyleSheet(title_style)
        ranking_container.addWidget(rk_title)
        self.ranking_frame = QFrame()
        self.ranking_frame.setMinimumHeight(115)
        self.ranking_frame.setStyleSheet(card_style)
        self.ranking_layout = QVBoxLayout(self.ranking_frame)
        self.ranking_layout.setContentsMargins(15, 10, 15, 10)
        ranking_container.addWidget(self.ranking_frame)
        radar_ranking_layout.addLayout(ranking_container, 1)
        
        # Empresa Estrella (Top Rendimiento)
        top_container = QVBoxLayout()
        t_title = QLabel("🌟 EMPRESA ESTRELLA")
        t_title.setStyleSheet(title_style)
        top_container.addWidget(t_title)
        self.top_frame = QFrame()
        self.top_frame.setMinimumHeight(115)
        self.top_frame.setStyleSheet(card_style)
        self.top_layout = QVBoxLayout(self.top_frame)
        self.top_layout.setContentsMargins(15, 10, 15, 10)
        top_container.addWidget(self.top_frame)
        radar_ranking_layout.addLayout(top_container, 1)
        
        header_layout.addLayout(radar_ranking_layout)
        layout.addWidget(header_container)
        
        # --- Consolidated Group Metrics ---
        self.group_stats_container = QWidget()
        group_stats_layout = QHBoxLayout(self.group_stats_container)
        group_stats_layout.setContentsMargins(0, 0, 0, 0)
        group_stats_layout.setSpacing(20)
        
        self.card_group_income = self.create_stat_card("💰 INGRESO GRUPO", "$0.00", "#10b981", "group")
        self.card_group_expense = self.create_stat_card("📉 GASTO GRUPO", "$0.00", "#f43f5e", "group")
        self.card_group_net = self.create_stat_card("🏆 RESULTADO NETO", "$0.00", "#6366f1", "group")
        
        group_stats_layout.addWidget(self.card_group_income)
        group_stats_layout.addWidget(self.card_group_expense)
        group_stats_layout.addWidget(self.card_group_net)
        layout.addWidget(self.group_stats_container)
        
        # --- Chart Section: Comparative Battle ---
        self.admin_chart_figure, self.admin_chart_ax = plt.subplots(figsize=(6, 2.5))
        self.admin_chart_figure.patch.set_facecolor('#0f172a')
        self.admin_chart_canvas = FigureCanvas(self.admin_chart_figure)
        self.admin_chart_canvas.setMinimumHeight(220)
        self.admin_chart_canvas.setStyleSheet("border-radius: 12px; border: 1px solid #1e293b;")
        layout.addWidget(self.admin_chart_canvas)
        
        # --- Mid Section: Matrix ---
        matrix_container = QVBoxLayout()
        matrix_container.addWidget(QLabel("MATRIZ DE RENDIMIENTO CORPORATIVO"))
        self.performance_table = QTableWidget()
        self.performance_table.setColumnCount(4)
        self.performance_table.setHorizontalHeaderLabels(["EMPRESA", "INGRESOS", "UTILIDAD", "STATUS"])
        self.performance_table.setMinimumHeight(240)
        self.performance_table.setStyleSheet("""
            QTableWidget { background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; color: #f8fafc; }
            QHeaderView::section { background: #1e293b; color: #38bdf8; font-weight: bold; border: none; }
        """)
        self.performance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        matrix_container.addWidget(self.performance_table)
        
        # Action Buttons
        admin_actions_layout = QHBoxLayout()
        admin_actions_layout.setSpacing(10)
        
        btn_transfer = QPushButton("💸 Transferir Fondos")
        btn_transfer.setStyleSheet("background-color: #6366f1; padding: 10px; border-radius: 8px; font-weight: bold; color: white;")
        btn_transfer.clicked.connect(self.show_transfer_dialog)
        
        btn_export = QPushButton("📊 Exportar Matriz (CSV)")
        btn_export.setStyleSheet("background-color: #10b981; padding: 10px; border-radius: 8px; font-weight: bold; color: white;")
        btn_export.clicked.connect(self.export_matrix_csv)
        
        btn_cierre = QPushButton("📅 Cierre Histórico de Mes")
        btn_cierre.setStyleSheet("background-color: #f59e0b; padding: 10px; border-radius: 8px; font-weight: bold; color: white;")
        btn_cierre.clicked.connect(self.close_month_global)
        
        admin_actions_layout.addWidget(btn_transfer)
        admin_actions_layout.addWidget(btn_export)
        admin_actions_layout.addWidget(btn_cierre)
        admin_actions_layout.addStretch()
        
        matrix_container.addLayout(admin_actions_layout)
        
        layout.addLayout(matrix_container)
        
        # --- Individual Companies Grid ---
        layout.addWidget(QLabel("UNIDADES DE NEGOCIO INDIVIDUALES"))
        self.admin_grid_widget = QWidget()
        self.admin_grid = QGridLayout(self.admin_grid_widget)
        self.admin_grid.setSpacing(20)
        self.admin_grid.setAlignment(Qt.AlignTop)
        layout.addWidget(self.admin_grid_widget)
        
        main_scroll.setWidget(scroll_content)
        outer_layout.addWidget(main_scroll)
        
        # Bottom Actions
        actions = QHBoxLayout()
        
        btn_new_company = QPushButton("➕ CREAR NUEVA EMPRESA")
        btn_new_company.setStyleSheet("background-color: #10b981; color: white; padding: 12px; font-weight: bold;")
        btn_new_company.clicked.connect(self.create_new_company_admin)
        
        btn_refresh = QPushButton("🔄 ACTUALIZAR RENDIMIENTOS")
        btn_refresh.setFixedWidth(250)
        btn_refresh.clicked.connect(self.update_admin_panel)
        
        actions.addWidget(btn_new_company)
        actions.addStretch()
        actions.addWidget(btn_refresh)
        layout.addLayout(actions)
        
        self.stack.addWidget(self.tab_admin)

    def init_admin_payments_tab(self):
        self.tab_admin_payments = QWidget()
        layout = QVBoxLayout(self.tab_admin_payments)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        title = QLabel("🏢 TESORERÍA CENTRAL - EJECUCIÓN DE PAGOS")
        title.setStyleSheet("font-size: 28px; font-weight: 900; color: #10b981;")
        layout.addWidget(title)
        
        desc = QLabel("Aquí puedes consultar las obligaciones (Préstamos, Cheques, Proveedores) de cualquier empresa de la red por ID para liquidarlas.")
        desc.setStyleSheet("color: #94a3b8; font-size: 14px; margin-bottom: 20px;")
        layout.addWidget(desc)
        
        # Controls
        controls = QHBoxLayout()
        self.admin_pay_company = QComboBox()
        db_files = [f for f in glob.glob("*.db") if not f.startswith("backup_") and f != "database.db"]
        self.admin_pay_company.addItems([f.replace(".db", "").upper() for f in db_files])
        self.admin_pay_company.currentTextChanged.connect(self.update_admin_payments_table)
        
        controls.addWidget(QLabel("Seleccionar Empresa:"))
        controls.addWidget(self.admin_pay_company)
        btn_refresh_pay = QPushButton("🔄 Actualizar Lista")
        btn_refresh_pay.clicked.connect(self.update_admin_payments_table)
        controls.addWidget(btn_refresh_pay)
        controls.addStretch()
        layout.addLayout(controls)
        
        # Filtro de búsqueda
        self.admin_pay_search = QLineEdit()
        self.admin_pay_search.setPlaceholderText("🔍 Filtrar por ID, concepto, tarjeta, proveedor, tipo o monto...")
        self.admin_pay_search.setStyleSheet("padding: 8px; font-size: 14px; border-radius: 5px;")
        self.admin_pay_search.textChanged.connect(self.filter_admin_payments_table)
        layout.addWidget(self.admin_pay_search)
        
        # Table of pending payments
        self.admin_pay_table = QTableWidget()
        self.admin_pay_table.setColumnCount(7)
        self.admin_pay_table.setHorizontalHeaderLabels(["ID", "Tipo", "Concepto", "Total", "Restante", "Vencimiento", "Estado"])
        self.admin_pay_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.admin_pay_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.admin_pay_table.itemClicked.connect(self.on_admin_pay_row_clicked)
        layout.addWidget(self.admin_pay_table)
        
        # Form for manual payment by ID
        form = QHBoxLayout()
        form.setSpacing(15)
        self.admin_pay_id = QLineEdit()
        self.admin_pay_id.setPlaceholderText("Ej: 5")
        self.admin_pay_id.setFixedWidth(100)
        self.admin_pay_type = QComboBox()
        self.admin_pay_type.addItems(["Cuota Préstamo", "Cheque", "Deuda (Tarjeta/Proveedor)"])
        self.admin_pay_amount = QLineEdit()
        self.admin_pay_amount.setPlaceholderText("Total o Parcial ($)")
        btn_pay = QPushButton("💳 EJECUTAR PAGO")
        btn_pay.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 12px; font-size: 14px; border-radius: 8px;")
        btn_pay.clicked.connect(self.execute_admin_payment)
        
        form.addStretch()
        form.addWidget(QLabel("ID:"))
        form.addWidget(self.admin_pay_id)
        form.addWidget(QLabel("Tipo:"))
        form.addWidget(self.admin_pay_type)
        form.addWidget(QLabel("Monto a Pagar:"))
        form.addWidget(self.admin_pay_amount)
        form.addWidget(btn_pay)
        layout.addLayout(form)
        
        self.admin_pay_id.textChanged.connect(self.on_admin_pay_id_changed)
        
        self.stack.addWidget(self.tab_admin_payments)

    def on_admin_pay_row_clicked(self, item):
        row = item.row()
        pid = self.admin_pay_table.item(row, 0).text()
        ptype = self.admin_pay_table.item(row, 1).text()
        prestante = self.admin_pay_table.item(row, 4).text().replace('$', '').replace(',', '')
        
        self.admin_pay_id.setText(pid)
        self.admin_pay_amount.setText(prestante)
        
        # Map internal type to combo box
        if ptype == "Cuota Préstamo": self.admin_pay_type.setCurrentText("Cuota Préstamo")
        elif ptype == "Cheque": self.admin_pay_type.setCurrentText("Cheque")
        else: self.admin_pay_type.setCurrentText("Deuda (Tarjeta/Proveedor)")

    def on_admin_pay_id_changed(self, text):
        if not text: return
        # Search for this ID in the table to guess the type
        for row in range(self.admin_pay_table.rowCount()):
            if self.admin_pay_table.item(row, 0).text() == text:
                ptype = self.admin_pay_table.item(row, 1).text()
                prestante = self.admin_pay_table.item(row, 4).text().replace('$', '').replace(',', '')
                self.admin_pay_amount.setText(prestante)
                if ptype == "Cuota Préstamo": self.admin_pay_type.setCurrentText("Cuota Préstamo")
                elif ptype == "Cheque": self.admin_pay_type.setCurrentText("Cheque")
                else: self.admin_pay_type.setCurrentText("Deuda (Tarjeta/Proveedor)")
                break

    def update_admin_payments_table(self):
        self.admin_pay_table.setRowCount(0)
        company = self.admin_pay_company.currentText()
        if not company: return
        db_path = f"{company.lower().replace(' ', '_')}.db"
        if not os.path.exists(db_path): return
        
        temp_db = Database(db_path)
        
        # Préstamos (Cuotas)
        for i in temp_db.get_installments():
            r = self.admin_pay_table.rowCount(); self.admin_pay_table.insertRow(r)
            paid = i['paid_amount'] if 'paid_amount' in i.keys() else 0.0
            rest = i['amount'] - paid
            estado = "Parcial" if i['status'] == 'partial' else "Pendiente"
            self.admin_pay_table.setItem(r, 0, QTableWidgetItem(str(i['id'])))
            self.admin_pay_table.setItem(r, 1, QTableWidgetItem("Cuota Préstamo"))
            self.admin_pay_table.setItem(r, 2, QTableWidgetItem(f"Cuota {i['number']} - {i['name']}"))
            self.admin_pay_table.setItem(r, 3, QTableWidgetItem(f"${i['amount']:,.2f}"))
            self.admin_pay_table.setItem(r, 4, QTableWidgetItem(f"${rest:,.2f}"))
            self.admin_pay_table.setItem(r, 5, QTableWidgetItem(i['due_date']))
            self.admin_pay_table.setItem(r, 6, QTableWidgetItem(estado))
            
        # Cheques
        for c in temp_db.get_checks():
            if c[6] == 'paid': continue
            r = self.admin_pay_table.rowCount(); self.admin_pay_table.insertRow(r)
            paid = c['paid_amount'] if 'paid_amount' in c.keys() else 0.0
            rest = c['amount'] - paid
            estado = "Parcial" if c['status'] == 'partial' else "Pendiente"
            self.admin_pay_table.setItem(r, 0, QTableWidgetItem(str(c[0])))
            self.admin_pay_table.setItem(r, 1, QTableWidgetItem("Cheque"))
            self.admin_pay_table.setItem(r, 2, QTableWidgetItem(f"N° {c[2]} - {c[5]}"))
            self.admin_pay_table.setItem(r, 3, QTableWidgetItem(f"${c[3]:,.2f}"))
            self.admin_pay_table.setItem(r, 4, QTableWidgetItem(f"${rest:,.2f}"))
            self.admin_pay_table.setItem(r, 5, QTableWidgetItem(c[4]))
            self.admin_pay_table.setItem(r, 6, QTableWidgetItem(estado))
            
        # Deudas / Costos Fijos / Inversiones
        for d in temp_db.get_general_debts():
            r = self.admin_pay_table.rowCount(); self.admin_pay_table.insertRow(r)
            paid = d['paid_amount'] if 'paid_amount' in d.keys() else 0.0
            rest = d['amount'] - paid
            estado = "Parcial" if d['status'] == 'partial' else "Pendiente"
            self.admin_pay_table.setItem(r, 0, QTableWidgetItem(str(d[0])))
            self.admin_pay_table.setItem(r, 1, QTableWidgetItem(d[2])) # Categoría dinámica (Tarjeta, Costo Fijo, Inversión, etc)
            self.admin_pay_table.setItem(r, 2, QTableWidgetItem(d[1])) # Nombre
            self.admin_pay_table.setItem(r, 3, QTableWidgetItem(f"${d[3]:,.2f}"))
            self.admin_pay_table.setItem(r, 4, QTableWidgetItem(f"${rest:,.2f}"))
            self.admin_pay_table.setItem(r, 5, QTableWidgetItem(d[4]))
            self.admin_pay_table.setItem(r, 6, QTableWidgetItem(estado))
            
        # Aplicar colores de vencimiento (Columna de Fecha es índice 5 ahora)
        for row in range(self.admin_pay_table.rowCount()):
            date_item = self.admin_pay_table.item(row, 5)
            if date_item:
                bg, fg = self.get_date_color_styles(date_item.text())
                for col in range(7):
                    item = self.admin_pay_table.item(row, col)
                    if item:
                        if bg == "#ef4444": item.setForeground(Qt.red)
                        elif bg == "#f59e0b": item.setForeground(Qt.darkYellow)
                        else: item.setForeground(Qt.darkGreen)

    def filter_admin_payments_table(self, text):
        text = text.lower()
        for row in range(self.admin_pay_table.rowCount()):
            match = False
            for col in range(self.admin_pay_table.columnCount()):
                item = self.admin_pay_table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.admin_pay_table.setRowHidden(row, not match)

    def execute_admin_payment(self):
        pid = self.admin_pay_id.text().strip()
        ptype = self.admin_pay_type.currentText()
        pamount = self.admin_pay_amount.text().strip()
        if not pid: return
        
        amt_val = None
        try:
            if pamount: amt_val = float(pamount.replace(',', '.'))
        except:
            QMessageBox.warning(self, "Error", "Monto parcial inválido. Ingrese un número o déjelo vacío para pagar el total.")
            return
            
        company = self.admin_pay_company.currentText()
        db_path = f"{company.lower().replace(' ', '_')}.db"
        temp_db = Database(db_path)
        
        msg = f"¿Ejecutar pago del ID {pid} ({ptype}) para la empresa {company}?"
        if amt_val: msg += f"\n\nPago Parcial por: ${amt_val:,.2f}"
        
        reply = QMessageBox.question(self, "Confirmar Pago", msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if ptype == "Cuota Préstamo": temp_db.pay_installment(pid, amt_val)
                elif ptype == "Cheque": temp_db.pay_check(pid, amt_val)
                else: temp_db.pay_general_debt(pid, amt_val)
                QMessageBox.information(self, "Éxito", "Pago registrado y debitado correctamente en la sucursal.")
                self.update_admin_payments_table()
                if self.role == "admin": self.update_admin_panel()
                self.admin_pay_id.clear()
                self.admin_pay_amount.clear()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo realizar el pago. Verifique el ID.\nDetalles: {e}")

    def create_admin_company_card(self, name, stats, row, col):
        status_color = "#10b981" if stats['balance'] >= 0 else "#ef4444"
        status_text = "✨ EXCELENTE" if stats['balance'] > 50000 else "📈 SALUDABLE" if stats['balance'] >= 0 else "⚠️ REVISAR"
        
        card = QFrame()
        card.setMinimumHeight(160)
        card.setObjectName("AdminCompanyCard")
        card.setStyleSheet(f"""
            QFrame#AdminCompanyCard {{
                background-color: #1e293b;
                border-radius: 12px;
                border: 1px solid {status_color}44;
            }}
            QFrame#AdminCompanyCard:hover {{
                border: 1px solid {status_color};
                background-color: #0f172a;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        top_row = QHBoxLayout()
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("font-size: 15px; font-weight: 900; color: #f8fafc;")
        
        lbl_status = QLabel(status_text)
        lbl_status.setStyleSheet(f"color: {status_color}; font-weight: 900; font-size: 9px;")
        
        top_row.addWidget(lbl_name)
        top_row.addStretch()
        top_row.addWidget(lbl_status)
        layout.addLayout(top_row)
        
        # Performance Balance
        balance = stats['balance']
        lbl_balance = QLabel(f"${balance:,.0f}")
        lbl_balance.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {status_color};")
        lbl_balance.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_balance)
        
        # Details Compact
        det_layout = QHBoxLayout()
        inc_lbl = QLabel(f"▲ ${stats['total_income']:,.0f}")
        inc_lbl.setStyleSheet("color: #10b981; font-size: 10px; font-weight: bold;")
        exp_lbl = QLabel(f"▼ ${stats['total_expenses']:,.0f}")
        exp_lbl.setStyleSheet("color: #ef4444; font-size: 10px; font-weight: bold;")
        det_layout.addWidget(inc_lbl); det_layout.addStretch(); det_layout.addWidget(exp_lbl)
        layout.addLayout(det_layout)
        
        self.admin_grid.addWidget(card, row, col)

    def create_stat_card(self, label, value, color, card_type=None):
        card = ClickableCard(card_type, self.show_card_details)
        card.setMinimumHeight(140)
        card.setObjectName("StatCard")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(5)
        
        lbl_title = QLabel(label)
        lbl_title.setObjectName("StatLabel")
        lbl_title.setStyleSheet(f"color: {color}; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px;")
        
        lbl_val = QLabel(value)
        lbl_val.setObjectName("StatValue")
        lbl_val.setStyleSheet("font-size: 32px; font-weight: 900; color: #ffffff;")
        
        trend_lbl = QLabel("")
        trend_lbl.setObjectName("TrendLabel")
        trend_lbl.setStyleSheet("font-size: 12px; font-weight: bold; padding: 4px 10px; border-radius: 8px;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        layout.addWidget(trend_lbl, 0, Qt.AlignLeft)
        
        if card_type:
            self.stat_labels[card_type] = lbl_val
            self.stat_trends[card_type] = trend_lbl
        
        return card

    def show_card_details(self, card_type):
        if not card_type: return
        
        self.current_dialog = QDialog(self)
        self.current_dialog.setWindowTitle(f"Detalles - {card_type.capitalize()}")
        # Add Maximize and Minimize buttons
        self.current_dialog.setWindowFlags(self.current_dialog.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.current_dialog.resize(950, 650)
        self.current_dialog.setStyleSheet(STYLE_SHEET + " QTableWidget { font-size: 14px; }")
        
        layout = QVBoxLayout(self.current_dialog)
        
        # Header de Resumen Pro para el Boss
        self.dialog_total_lbl = QLabel("Total: $0.00")
        self.dialog_total_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #6366f1; margin: 10px 0;")
        layout.addWidget(self.dialog_total_lbl)
        
        # DASHBOARD CORPORATIVO PRO (Para todos los módulos)
        self.dialog_total_lbl.setVisible(False) 
        header_stats = QFrame()
        header_stats.setObjectName("Card")
        header_stats.setFixedHeight(110)
        stats_layout = QHBoxLayout(header_stats)
        
        # Métrica 1
        s1 = QVBoxLayout(); self.d_stat1_val = QLabel("-"); self.d_stat1_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #6366f1;")
        self.d_stat1_lbl = QLabel("INDICADOR 1")
        s1.addWidget(self.d_stat1_lbl); s1.addWidget(self.d_stat1_val)
        
        # Métrica 2
        s2 = QVBoxLayout(); self.d_stat2_val = QLabel("-"); self.d_stat2_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #f59e0b;")
        self.d_stat2_lbl = QLabel("INDICADOR 2")
        s2.addWidget(self.d_stat2_lbl); s2.addWidget(self.d_stat2_val)
        
        # Métrica 3
        s3 = QVBoxLayout(); self.d_stat3_val = QLabel("-"); self.d_stat3_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #10b981;")
        self.d_stat3_lbl = QLabel("INDICADOR 3")
        s3.addWidget(self.d_stat3_lbl); s3.addWidget(self.d_stat3_val)
        
        stats_layout.addLayout(s1); stats_layout.addLayout(s2); stats_layout.addLayout(s3)
        layout.addWidget(header_stats)
        
        table = QTableWidget()
        layout.addWidget(table)
        
        self.refresh_dialog_table(card_type, table)
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setDefaultSectionSize(45) # Filas más altas para mejor lectura
        self.current_dialog.exec_()

    def refresh_dialog_table(self, card_type, table):
        table.setRowCount(0)
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        running_total = 0.0
        
        if card_type == "income":
            data = self.db.get_income(m, y)
            running_total = sum(d[2] for d in data)
            
            # Métricas Ingresos
            self.d_stat1_lbl.setText("TOTAL DEL MES")
            self.d_stat1_val.setText(f"${running_total:,.2f}")
            self.d_stat2_lbl.setText("PROMEDIO DIARIO")
            avg = running_total / 30
            self.d_stat2_val.setText(f"${avg:,.2f}")
            self.d_stat3_lbl.setText("RÉCORD DEL MES")
            max_val = max([d[2] for d in data]) if data else 0
            self.d_stat3_val.setText(f"${max_val:,.2f}")

            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Fecha", "Origen", "Descripción", "Monto"])
            for d in data:
                r = table.rowCount(); table.insertRow(r)
                table.setItem(r, 0, QTableWidgetItem(d[1]))
                table.setItem(r, 1, QTableWidgetItem(d[4]))
                table.setItem(r, 2, QTableWidgetItem(d[3]))
                
                amt_item = QTableWidgetItem(f"${d[2]:,.2f}")
                amt_item.setForeground(Qt.darkGreen)
                amt_item.setFont(QFont("Inter", 12, QFont.Bold))
                table.setItem(r, 3, amt_item)
        
        elif card_type in ["expenses", "fixed", "variable"]:
            exp_type = 'fijo' if card_type == 'fixed' else ('variable' if card_type == 'variable' else None)
            all_data = self.db.get_expenses(exp_type)
            period = f"{y}-{m:02d}"
            data = [d for d in all_data if d[1].startswith(period)]
            running_total = sum(d[3] for d in data)
            
            # Métricas Gastos
            self.d_stat1_lbl.setText(f"TOTAL {card_type.upper()}")
            self.d_stat1_val.setText(f"${running_total:,.2f}")
            self.d_stat1_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #ef4444;")
            
            self.d_stat2_lbl.setText("GATO MÁS ALTO")
            max_val = max([d[3] for d in data]) if data else 0
            self.d_stat2_val.setText(f"${max_val:,.2f}")
            
            self.d_stat3_lbl.setText("OPERACIONES")
            self.d_stat3_val.setText(str(len(data)))

            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Fecha", "Categoría", "Descripción", "Monto"])
            for d in data:
                r = table.rowCount(); table.insertRow(r)
                table.setItem(r, 0, QTableWidgetItem(d[1]))
                table.setItem(r, 1, QTableWidgetItem(d[2]))
                table.setItem(r, 2, QTableWidgetItem(d[4]))
                
                amt_item = QTableWidgetItem(f"${d[3]:,.2f}")
                amt_item.setForeground(Qt.red)
                amt_item.setFont(QFont("Inter", 12, QFont.Bold))
                table.setItem(r, 3, amt_item)

        elif card_type == "balance":
            income = self.db.get_income(m, y)
            expenses = self.db.get_expenses()
            period = f"{y}-{m:02d}"
            
            tot_inc = sum(d[2] for d in income)
            tot_exp = sum(d[3] for d in expenses if d[1].startswith(period))
            net = tot_inc - tot_exp
            
            # Métricas Balance
            self.d_stat1_lbl.setText("INGRESOS BRUTOS")
            self.d_stat1_val.setText(f"${tot_inc:,.2f}")
            self.d_stat2_lbl.setText("EGRESOS TOTALES")
            self.d_stat2_val.setText(f"${tot_exp:,.2f}")
            self.d_stat2_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #ef4444;")
            self.d_stat3_lbl.setText("GANANCIA NETA")
            self.d_stat3_val.setText(f"${net:,.2f}")
            self.d_stat3_val.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {'#10b981' if net >= 0 else '#ef4444'};")

            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Fecha", "Tipo", "Descripción", "Monto"])
            
            # Combine and sort by date
            combined = []
            for i in income: combined.append(('income', i))
            for e in expenses: 
                if e[1].startswith(period): combined.append(('expense', e))
            
            combined.sort(key=lambda x: x[1][1], reverse=True)
            
            for item_type, d in combined:
                amt = d[2] if item_type == 'income' else d[3]
                r = table.rowCount(); table.insertRow(r)
                table.setItem(r, 0, QTableWidgetItem(d[1]))
                
                type_item = QTableWidgetItem("INGRESO" if item_type == 'income' else "EGRESO")
                table.setItem(r, 1, type_item)
                
                desc = d[3] if item_type == 'income' else d[4]
                table.setItem(r, 2, QTableWidgetItem(desc))
                
                amt_item = QTableWidgetItem(f"${amt:,.2f}")
                amt_item.setFont(QFont("Inter", 12, QFont.Bold))
                if item_type == 'income':
                    amt_item.setForeground(Qt.darkGreen)
                    type_item.setForeground(Qt.darkGreen)
                else:
                    amt_item.setForeground(Qt.red)
                    type_item.setForeground(Qt.red)
                table.setItem(r, 3, amt_item)
                
        elif card_type == "loans":
            data = self.db.get_installments()
            is_admin = (self.role == "admin")
            cols = 6 if is_admin else 5
            table.setColumnCount(cols)
            labels = ["Entidad", "Cuota", "Vencimiento", "Cuota ($)", "Deuda Total", "Acción"]
            table.setHorizontalHeaderLabels(labels[:cols])
            
            # Métricas Préstamos (Dashboard Bancario)
            self.d_stat1_lbl.setText("DEUDA TOTAL ACTIVA")
            self.d_stat1_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #ef4444;")
            self.d_stat2_lbl.setText("PRÓXIMO VENCIMIENTO")
            self.d_stat3_lbl.setText("PROGRESO DE PAGO")

            loans = self.db.get_loans()
            global_debt = 0
            global_paid = 0
            for l in loans:
                if l[6] == 'active':
                    total_orig = l[2] or 0
                    pending = sum(x['amount'] - (x['paid_amount'] if 'paid_amount' in x.keys() else 0.0) for x in data if x['loan_id'] == l[0])
                    global_debt += pending
                    global_paid += (total_orig - pending)
            
            self.d_stat1_val.setText(f"${global_debt:,.2f}")
            if data: self.d_stat2_val.setText(data[0]['due_date'])
            tot_sum = global_debt + global_paid
            prog = (global_paid / tot_sum * 100) if tot_sum > 0 else 0
            self.d_stat3_val.setText(f"{prog:.1f}%")
            
            loans_processed = set()
            for d in data:
                loan_id = d['loan_id']
                if loan_id in loans_processed: continue
                loans_processed.add(loan_id)
                
                # Deuda total del préstamo para el resumen
                loan_total_pending = sum(x['amount'] - (x['paid_amount'] if 'paid_amount' in x.keys() else 0.0) for x in data if x['loan_id'] == loan_id)
                running_total += (d['amount'] - (d['paid_amount'] if 'paid_amount' in d.keys() else 0.0))
                
                r = table.rowCount(); table.insertRow(r)
                bg, fg = self.get_date_color_styles(d['due_date'])
                
                table.setItem(r, 0, QTableWidgetItem(str(d['name'])))
                table.setItem(r, 1, QTableWidgetItem(f"Cuota {d['number']}/{d['total_inst']}"))
                
                date_item = QTableWidgetItem(d['due_date'])
                table.setItem(r, 2, date_item)
                
                amt_paid_val = d['paid_amount'] if 'paid_amount' in d.keys() else 0.0
                table.setItem(r, 3, QTableWidgetItem(f"${(d['amount'] - amt_paid_val):,.2f}"))
                
                # Nueva Columna Directa: Deuda Total
                total_item = QTableWidgetItem(f"${loan_total_pending:,.2f}")
                total_item.setForeground(Qt.red)
                table.setItem(r, 4, total_item)
                
                if is_admin:
                    btn_pay = QPushButton("✅")
                    btn_pay.setStyleSheet(f"background-color: {bg}; color: {fg}; font-weight: bold;")
                    btn_pay.clicked.connect(lambda ch, id=d['id'], tbl=table: self.pay_installment_dialog(id, tbl))
                    table.setCellWidget(r, 5, btn_pay)

                for col in range(4):
                    item = table.item(r, col)
                    if item:
                        if bg == "#ef4444": item.setForeground(Qt.red)
                        elif bg == "#f59e0b": item.setForeground(Qt.darkYellow)
                        else: item.setForeground(Qt.darkGreen)
                
        elif card_type == "checks":
            data = self.db.get_checks()
            is_admin = (self.role == "admin")
            cols = 5 if is_admin else 4
            table.setColumnCount(cols)
            labels = ["Banco", "Beneficiario", "Vencimiento", "Monto", "Acción"]
            table.setHorizontalHeaderLabels(labels[:cols])
            
            # Métricas Cheques
            running_total = sum(d[3] for d in data if d[6] != 'paid')
            self.d_stat1_lbl.setText("TOTAL PENDIENTE")
            self.d_stat1_val.setText(f"${running_total:,.2f}")
            self.d_stat1_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #f59e0b;")
            self.d_stat2_lbl.setText("PRÓXIMO COBRO")
            self.d_stat2_val.setText(data[0][4] if data else "-")
            self.d_stat3_lbl.setText("CHEQUES ACTIVOS")
            self.d_stat3_val.setText(str(len([d for d in data if d[6] != 'paid'])))

            for d in data:
                if d[6] == 'paid': continue
                running_total += d[3]
                r = table.rowCount(); table.insertRow(r)
                bg, fg = self.get_date_color_styles(d[4])
                
                table.setItem(r, 0, QTableWidgetItem(d[1]))
                table.setItem(r, 1, QTableWidgetItem(d[5]))
                
                date_item = QTableWidgetItem(d[4])
                table.setItem(r, 2, date_item)
                
                table.setItem(r, 3, QTableWidgetItem(f"${d[3]:,.2f}"))
                
                if is_admin:
                    btn_pay = QPushButton("✅")
                    btn_pay.setStyleSheet(f"background-color: {bg}; color: {fg}; font-weight: bold;")
                    btn_pay.clicked.connect(lambda ch, id=d[0], tbl=table: self.pay_check_dialog(id, tbl))
                    table.setCellWidget(r, 4, btn_pay)

                for col in range(4):
                    item = table.item(r, col)
                    if item:
                        if bg == "#ef4444": item.setForeground(Qt.red)
                        elif bg == "#f59e0b": item.setForeground(Qt.darkYellow)
                        else: item.setForeground(Qt.darkGreen)
                
        elif card_type in ["cards", "prov"]:
            target_cat = "Tarjeta" if card_type == "cards" else "Proveedor"
            data = self.db.get_general_debts()
            is_admin = (self.role == "admin")
            cols = 4 if is_admin else 3
            table.setColumnCount(cols)
            labels = ["Nombre", "Vencimiento", "Monto", "Acción"]
            table.setHorizontalHeaderLabels(labels[:cols])
            
            # Métricas Pasivos
            debt_items = [d for d in data if d[2] == target_cat]
            running_total = sum(d[3] for d in debt_items)
            self.d_stat1_lbl.setText(f"TOTAL DEUDA {target_cat.upper()}")
            self.d_stat1_val.setText(f"${running_total:,.2f}")
            self.d_stat1_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #ef4444;")
            self.d_stat2_lbl.setText("VENCIMIENTO MÁS CERCANO")
            self.d_stat2_val.setText(debt_items[0][4] if debt_items else "-")
            self.d_stat3_lbl.setText("ENTIDADES")
            self.d_stat3_val.setText(str(len(debt_items)))

            for d in data:
                if d[2] != target_cat: continue
                running_total += d[3]
                r = table.rowCount(); table.insertRow(r)
                bg, fg = self.get_date_color_styles(d[4])
                
                table.setItem(r, 0, QTableWidgetItem(d[1]))
                
                date_item = QTableWidgetItem(d[4])
                table.setItem(r, 1, date_item)
                
                table.setItem(r, 2, QTableWidgetItem(f"${d[3]:,.2f}"))
                
                btn_pay = QPushButton("💰")
                btn_pay.setStyleSheet(f"background-color: {bg}; color: {fg}; font-weight: bold;")
                btn_pay.clicked.connect(lambda ch, id=d[0], tbl=table: self.pay_debt_dialog(id, tbl))
                table.setCellWidget(r, 3, btn_pay)

                for col in range(3):
                    item = table.item(r, col)
                    if item:
                        if bg == "#ef4444": item.setForeground(Qt.red)
                        elif bg == "#f59e0b": item.setForeground(Qt.darkYellow)
                        else: item.setForeground(Qt.darkGreen)
                
        elif card_type == "group":
            # Resumen consolidado de todas las sucursales para el Admin
            self.d_stat1_lbl.setText("TOTAL INGRESOS RED")
            self.d_stat2_lbl.setText("TOTAL EGRESOS RED")
            self.d_stat3_lbl.setText("RESULTADO CONSOLIDADO")
            
            db_files = [f for f in glob.glob("*.db") if not f.startswith("backup_") and f != "database.db"]
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Empresa", "Ingresos", "Egresos", "Saldo Neto"])
            
            total_inc, total_exp = 0, 0
            for db_f in db_files:
                try:
                    tdb = Database(db_f)
                    stats = tdb.get_stats(m, y)
                    r = table.rowCount(); table.insertRow(r)
                    name = db_f.replace(".db", "").upper()
                    table.setItem(r, 0, QTableWidgetItem(name))
                    table.setItem(r, 1, QTableWidgetItem(f"${stats['total_income']:,.2f}"))
                    table.setItem(r, 2, QTableWidgetItem(f"${stats['total_expenses']:,.2f}"))
                    
                    net = stats['total_income'] - stats['total_expenses']
                    net_item = QTableWidgetItem(f"${net:,.2f}")
                    net_item.setForeground(Qt.darkGreen if net >= 0 else Qt.red)
                    net_item.setFont(QFont("Inter", 12, QFont.Bold))
                    table.setItem(r, 3, net_item)
                    
                    total_inc += stats['total_income']
                    total_exp += stats['total_expenses']
                except: continue
            
            self.d_stat1_val.setText(f"${total_inc:,.2f}")
            self.d_stat2_val.setText(f"${total_exp:,.2f}")
            self.d_stat2_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #ef4444;")
            net_total = total_inc - total_exp
            self.d_stat3_val.setText(f"${net_total:,.2f}")
            self.d_stat3_val.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {'#10b981' if net_total >= 0 else '#ef4444'};")
            running_total = net_total

        elif card_type in ["pure_day", "pure_month", "pure_year"]:
            # Filtro por día, mes o año
            today = datetime.date.today()
            if card_type == "pure_day":
                period = today.strftime("%Y-%m-%d")
                self.d_stat1_lbl.setText("TOTAL DEL DÍA")
            elif card_type == "pure_month":
                period = today.strftime("%Y-%m")
                self.d_stat1_lbl.setText("TOTAL DEL MES")
            else:
                period = today.strftime("%Y-")
                self.d_stat1_lbl.setText("ACUMULADO ANUAL")
            
            income = self.db.get_income() # Get all and filter
            expenses = self.db.get_expenses()
            
            # Filter
            data_inc = [i for i in income if i[1].startswith(period)]
            data_exp = [e for e in expenses if e[1].startswith(period)]
            
            tot_inc = sum(d[2] for d in data_inc)
            tot_exp = sum(d[3] for d in data_exp)
            running_total = tot_inc - tot_exp
            
            self.d_stat1_val.setText(f"${running_total:,.2f}")
            self.d_stat2_lbl.setText("INGRESOS TOTALES")
            self.d_stat2_val.setText(f"${tot_inc:,.2f}")
            self.d_stat3_lbl.setText("EGRESOS TOTALES")
            self.d_stat3_val.setText(f"${tot_exp:,.2f}")
            self.d_stat3_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #ef4444;")

            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Fecha", "Tipo", "Descripción", "Monto"])
            
            combined = []
            for i in data_inc: combined.append(('income', i))
            for e in data_exp: combined.append(('expense', e))
            combined.sort(key=lambda x: x[1][1], reverse=True)
            
            for item_type, d in combined:
                amt = d[2] if item_type == 'income' else d[3]
                r = table.rowCount(); table.insertRow(r)
                table.setItem(r, 0, QTableWidgetItem(d[1]))
                type_item = QTableWidgetItem("INGRESO" if item_type == 'income' else "EGRESO")
                table.setItem(r, 1, type_item)
                desc = d[3] if item_type == 'income' else d[4]
                table.setItem(r, 2, QTableWidgetItem(desc))
                amt_item = QTableWidgetItem(f"${amt:,.2f}")
                amt_item.setFont(QFont("Inter", 12, QFont.Bold))
                if item_type == 'income':
                    amt_item.setForeground(Qt.darkGreen)
                    type_item.setForeground(Qt.darkGreen)
                else:
                    amt_item.setForeground(Qt.red)
                    type_item.setForeground(Qt.red)
                table.setItem(r, 3, amt_item)

        # Actualizar el Label de Total en el diálogo
        self.dialog_total_lbl.setText(f"Resumen de {card_type.capitalize()}: ${running_total:,.2f}")




    # --- LOGIC ---
    def save_variable_expense(self):
        try:
            date = self.exp_date.date().toString("yyyy-MM-dd")
            category = self.exp_cat.currentText()
            amount = float(self.exp_amount.text().replace(',', '.'))
            desc = self.exp_desc.text()
            if amount <= 0: raise ValueError
            self.db.add_expense(date, category, amount, desc, 'variable')
            self.exp_amount.clear()
            self.exp_desc.clear()
            self.load_all_data()
        except: QMessageBox.warning(self, "Error", "Monto inválido")

    def save_proveedor(self):
        amount_text = self.prov_amount.text()
        if not amount_text:
            QMessageBox.warning(self, "Error", "Debe calcular o ingresar un monto.")
            return
        try:
            amount = float(amount_text)
            date = self.prov_date.date().toString("yyyy-MM-dd")
            prov_name = self.prov_name.text() or "Proveedor General"
            prov_type = self.prov_type.currentText()
            
            kilos_text = self.prov_kilos.text().replace(',', '.')
            precio_text = self.prov_precio_kg.text().replace(',', '.')
            
            desc = f"Proveedor: {prov_name}\nMercadería: {prov_type}"
            if kilos_text and precio_text:
                import re
                if re.match(r'^[\d\.\+\s]+$', kilos_text):
                    parts = [p.strip() for p in kilos_text.split('+') if p.strip()]
                    cantidad = len(parts)
                    total_val = sum(float(p) for p in parts)
                    precio = float(precio_text)
                    
                    if prov_type in ["Pollo", "Achuras", "Otro"]:
                        pesos_str = " + ".join(parts)
                        desc = f"Proveedor: {prov_name}\n" \
                               f"Mercadería: {prov_type}\n" \
                               f"Cantidad: {cantidad} caja(s)\n" \
                               f"Detalle: {pesos_str}\n" \
                               f"TotalU: {total_val:g} unid\n" \
                               f"Precio: ${precio:,.0f}"
                    else:
                        pesos_str = ", ".join(parts)
                        desc = f"Proveedor: {prov_name}\n" \
                               f"Mercadería: {prov_type}\n" \
                               f"Cantidad: {cantidad} media(s)\n" \
                               f"Detalle: {pesos_str}\n" \
                               f"TotalU: {total_val:g} kg\n" \
                               f"Precio: ${precio:,.0f} x Kg"

            payment = self.prov_payment.currentText()
            if payment == "Contado (Pago Inmediato)":
                self.db.add_expense(date, "Carne / Proveedores", amount, desc, 'variable')
                ToastNotification(self, "Compra registrada como Gasto Pagado", "✅")
            else:
                self.db.add_general_debt(desc, "Proveedor", amount, date)
                ToastNotification(self, "Compra registrada como Deuda a Pagar", "✅")
                
            self.prov_kilos.clear()
            self.prov_precio_kg.clear()
            self.prov_amount.clear()
            self.prov_name.clear()
            self.load_all_data()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Verifique los datos: {e}")

    def on_loan_calc_change(self, source):
        # Calculadora Inteligente Multidireccional
        # Esto permite que si el banco le dice: "Son 12 cuotas exactas de $15,340",
        # el usuario escriba la cuota y el sistema calcule todo lo demás.
        try:
            cap = float(self.loan_capital.text().replace(',', '.') or 0)
            
            # Intentar obtener las cuotas (puede estar vacío)
            cuotas_text = self.loan_inst.text()
            cuotas = int(cuotas_text) if cuotas_text.isdigit() else 0
            
            # Helper: Escribe en la casilla sin detonar un evento recursivo infinito
            def update_field(field, value):
                field.blockSignals(True)
                field.setText(f"{value:.2f}")
                field.blockSignals(False)

            if source in ['capital', 'interes']:
                # Si cambian el capital o el interés: Actualiza Monto Total y Cuota
                inte = float(self.loan_interest.text().replace(',', '.') or 0)
                tot = cap + inte
                update_field(self.loan_amount, tot)
                if cuotas > 0:
                    update_field(self.loan_inst_amount, tot / cuotas)

            elif source == 'total':
                # Si el usuario modifica el "Deuda Total" directamente: Actualiza Interés y Cuota
                tot = float(self.loan_amount.text().replace(',', '.') or 0)
                inte = tot - cap
                update_field(self.loan_interest, inte)
                if cuotas > 0:
                    update_field(self.loan_inst_amount, tot / cuotas)

            elif source in ['cuotas', 'valor_cuota']:
                # Si el usuario modifica la "Cantidad de Cuotas" o el "Valor Exacto de Cuota"
                if self.loan_inst_amount.text():
                    val_cuota = float(self.loan_inst_amount.text().replace(',', '.') or 0)
                    if cuotas > 0:
                        tot = val_cuota * cuotas
                        inte = tot - cap
                        update_field(self.loan_amount, tot)
                        update_field(self.loan_interest, inte)
                else:
                    # Si no hay valor de cuota, simplemente recalcular la cuota en base al Total actual
                    tot = float(self.loan_amount.text().replace(',', '.') or 0)
                    if cuotas > 0:
                        update_field(self.loan_inst_amount, tot / cuotas)
        except:
            pass

    def save_loan(self):
        try:
            self.btn_loan.setEnabled(False)
            name = self.loan_name.text()
            capital = float(self.loan_capital.text().replace(',', '.') or 0)
            interest = float(self.loan_interest.text().replace(',', '.') or 0)
            amount = float(self.loan_amount.text().replace(',', '.'))
            inst = int(self.loan_inst.text())
            cat = self.loan_cat.currentText()
            first_date = self.loan_first_date.date().toString("yyyy-MM-dd")
            
            if not name or amount <= 0 or inst <= 0: raise ValueError
            self.db.add_loan(name, amount, capital, interest, cat, inst, first_date)
            self.loan_name.clear(); self.loan_amount.clear(); self.loan_inst.clear()
            self.loan_capital.clear(); self.loan_interest.clear(); self.loan_inst_amount.clear()
            self.load_all_data()
            self.status_bar.showMessage(f"Préstamo '{name}' creado con éxito", 5000)
            QMessageBox.information(self, "Éxito", "Préstamo creado con sus cuotas mensuales.")
        except ValueError:
            QMessageBox.warning(self, "Error de Datos", "Por favor, ingrese un monto y cantidad de cuotas válidos.")
        except Exception as e:
            QMessageBox.critical(self, "Error del Sistema", f"No se pudo crear el préstamo: {str(e)}")
        finally:
            self.btn_loan.setEnabled(True)

    def save_check(self):
        try:
            bank = self.check_bank.text()
            num = self.check_num.text()
            amt = float(self.check_amt.text().replace(',', '.'))
            date = self.check_date.date().toString("yyyy-MM-dd")
            recp = self.check_recp.text()
            if not bank or amt <= 0: raise ValueError
            self.db.add_check(bank, num, amt, date, recp)
            self.check_bank.clear(); self.check_num.clear(); self.check_amt.clear(); self.check_recp.clear()
            self.load_all_data()
        except: QMessageBox.warning(self, "Error", "Monto o datos inválidos")

    def save_general_debt(self):
        try:
            name = self.debt_name.text()
            cat = self.debt_cat.currentText()
            amt = float(self.debt_amt.text().replace(',', '.'))
            date = self.debt_date.date().toString("yyyy-MM-dd")
            if not name or amt <= 0: raise ValueError
            self.db.add_general_debt(name, cat, amt, date)
            self.debt_name.clear(); self.debt_amt.clear()
            self.load_all_data()
        except: QMessageBox.warning(self, "Error", "Monto o datos inválidos")

    def pay_installment_ui(self, id):
        reply = QMessageBox.question(self, "Confirmar Pago", "¿Marcar esta cuota como pagada?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.db.pay_installment(id)
                self.load_all_data()
                QMessageBox.information(self, "Éxito", "Cuota marcada como pagada.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo procesar el pago: {e}")

    def pay_check_ui(self, id):
        reply = QMessageBox.question(self, "Confirmar Pago", "¿Marcar este cheque como cobrado?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.db.pay_check(id)
                self.load_all_data()
                QMessageBox.information(self, "Éxito", "Cheque marcado como cobrado.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo procesar el pago: {e}")

    def pay_debt_ui(self, id):
        reply = QMessageBox.question(self, "Confirmar Pago", "¿Marcar esta deuda como pagada?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.db.pay_general_debt(id)
                self.load_all_data()
                QMessageBox.information(self, "Éxito", "Deuda marcada como pagada.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo procesar el pago: {e}")

    def init_central_payments_tab(self):
        self.tab_central_payments = QWidget()
        layout = QVBoxLayout(self.tab_central_payments)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("💰 PANEL DE PAGOS CENTRALIZADO")
        title.setStyleSheet("font-size: 24px; font-weight: 900; color: #6366f1; margin-bottom: 10px;")
        layout.addWidget(title)
        
        self.central_pay_table = QTableWidget()
        self.central_pay_table.setColumnCount(5)
        self.central_pay_table.setHorizontalHeaderLabels(["Referencia/Entidad", "Tipo de Deuda", "Vencimiento", "Monto", "Acción"])
        self.central_pay_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.central_pay_table)
        self.stack.addWidget(self.tab_central_payments)

    def update_central_payments_table(self):
        self.central_pay_table.setRowCount(0)
        # 1. Installments
        for i in self.db.get_installments():
            r = self.central_pay_table.rowCount(); self.central_pay_table.insertRow(r)
            self.central_pay_table.setItem(r, 0, QTableWidgetItem(f"{i['name']} (Cuota {i['number']})"))
            self.central_pay_table.setItem(r, 1, QTableWidgetItem("PRÉSTAMO"))
            self.central_pay_table.setItem(r, 2, QTableWidgetItem(i['due_date']))
            self.central_pay_table.setItem(r, 3, QTableWidgetItem(f"${i['amount']:,.2f}"))
            btn = QPushButton("PAGAR"); btn.clicked.connect(lambda ch, id=i['id']: self.pay_installment_ui(id))
            self.central_pay_table.setCellWidget(r, 4, btn)

        # 2. Checks
        for c in self.db.get_checks():
            if c['status'] == 'paid': continue
            r = self.central_pay_table.rowCount(); self.central_pay_table.insertRow(r)
            self.central_pay_table.setItem(r, 0, QTableWidgetItem(f"{c['bank']} - Ch {c['number']}"))
            self.central_pay_table.setItem(r, 1, QTableWidgetItem("CHEQUE"))
            self.central_pay_table.setItem(r, 2, QTableWidgetItem(c['due_date']))
            self.central_pay_table.setItem(r, 3, QTableWidgetItem(f"${c['amount']:,.2f}"))
            btn = QPushButton("PAGAR"); btn.clicked.connect(lambda ch, id=c['id']: self.pay_check_ui(id))
            self.central_pay_table.setCellWidget(r, 4, btn)

        # 3. General Debts
        for d in self.db.get_general_debts():
            r = self.central_pay_table.rowCount(); self.central_pay_table.insertRow(r)
            self.central_pay_table.setItem(r, 0, QTableWidgetItem(d['name']))
            self.central_pay_table.setItem(r, 1, QTableWidgetItem(d['category'].upper()))
            self.central_pay_table.setItem(r, 2, QTableWidgetItem(d['due_date']))
            self.central_pay_table.setItem(r, 3, QTableWidgetItem(f"${d['amount']:,.2f}"))
            btn = QPushButton("PAGAR"); btn.clicked.connect(lambda ch, id=d['id']: self.pay_debt_ui(id))
            self.central_pay_table.setCellWidget(r, 4, btn)



    def edit_installment_date_ui(self, id, current_date):
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Vencimiento")
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        layout = QVBoxLayout(dialog)
        
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.fromString(current_date, "yyyy-MM-dd"))
        layout.addWidget(QLabel("Nueva Fecha de Vencimiento:"))
        layout.addWidget(date_edit)
        
        btn_save = QPushButton("Guardar")
        btn_save.clicked.connect(dialog.accept)
        layout.addWidget(btn_save)
        
        if dialog.exec_() == QDialog.Accepted:
            new_date = date_edit.date().toString("yyyy-MM-dd")
            try:
                self.db.update_installment_date(id, new_date)
                self.load_all_data()
                QMessageBox.information(self, "Éxito", "Fecha de vencimiento actualizada.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar la fecha: {e}")

    def pay_installment_dialog(self, id, table):
        self.db.pay_installment(id)
        self.load_all_data()
        self.refresh_dialog_table("loans", table)

    def pay_check_dialog(self, id, table):
        self.db.pay_check(id)
        self.load_all_data()
        self.refresh_dialog_table("checks", table)

    def pay_debt_dialog(self, id, table):
        self.db.pay_general_debt(id)
        self.load_all_data()
        # Need to know if it's cards or prov
        # But for refresh we can just use the dialog title or a flag
        # Let's assume it refreshes the active dialog
        self.refresh_dialog_table("cards", table) # This is a simplification

    def save_income(self):
        try:
            date = self.inc_date.date().toString("yyyy-MM-dd")
            source = self.inc_source.currentText()
            amount = float(self.inc_amount.text().replace(',', '.'))
            desc = self.inc_desc.text()
            if amount <= 0: raise ValueError
            self.db.add_income(date, amount, desc, source)
            self.inc_amount.clear(); self.inc_desc.clear()
            self.load_all_data()
        except: QMessageBox.warning(self, "Error", "Monto o datos inválidos")

    def delete_income_ui(self, id):
        reply = QMessageBox.question(self, "Confirmar", "¿Eliminar este registro de ingreso?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_income(id)
            self.load_all_data()

    def run_backup(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Backup", f"backup_contable_{datetime.date.today()}.db", "SQLite DB (*.db)")
        if file_path:
            if self.db.backup_database(file_path):
                self.status_bar.showMessage("Copia de seguridad creada correctamente", 5000)
                QMessageBox.information(self, "Éxito", "Copia de seguridad creada correctamente.")
            else:
                self.status_bar.showMessage("Error al crear backup", 5000)
                QMessageBox.critical(self, "Error", "No se pudo crear el backup.")

    def export_data_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar a Excel (CSV)", f"reporte_contable_{self.month_sel.currentText()}_{self.year_sel.currentText()}.csv", "CSV Files (*.csv)")
        if file_path:
            try:
                m = self.month_sel.currentIndex() + 1
                y = int(self.year_sel.currentText())
                expenses = self.db.get_expenses() # Or filter by period if desired
                income = self.db.get_income(m, y)
                
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["--- REPORTE CONTABLE ---"])
                    writer.writerow(["Periodo", f"{self.month_sel.currentText()} {y}"])
                    writer.writerow([])
                    writer.writerow(["INGRESOS"])
                    writer.writerow(["Fecha", "Origen", "Descripción", "Monto"])
                    for i in income: writer.writerow([i[1], i[4], i[3], i[2]])
                    
                    writer.writerow([])
                    writer.writerow(["EGRESOS"])
                    writer.writerow(["Fecha", "Tipo", "Categoría", "Descripción", "Monto"])
                    for e in expenses: 
                        if e[1].startswith(f"{y}-{m:02d}"):
                            writer.writerow([e[1], e[5], e[2], e[4], e[3]])
                
                self.status_bar.showMessage("Datos exportados correctamente", 5000)
                QMessageBox.information(self, "Éxito", "Datos exportados correctamente.")
            except Exception as e:
                self.status_bar.showMessage("Error al exportar datos", 5000)
                QMessageBox.critical(self, "Error", f"Fallo al exportar: {str(e)}")

    def load_all_data(self):
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        stats = self.db.get_stats(m, y)
        
        # Get previous month stats for Trends
        pm = m - 1 if m > 1 else 12
        py = y if m > 1 else y - 1
        prev_stats = self.db.get_stats(pm, py)
        
        # Update Trends
        self.update_trend("income", stats['total_income'], prev_stats['total_income'])
        self.update_trend("expenses", stats['total_expenses'], prev_stats['total_expenses'])
        self.update_trend("balance", stats['balance'], prev_stats['balance'])
        
        # No calculamos health_score en perfil Sucursal
        
        # Dashboard Totals
        if "income" in self.stat_labels: self.stat_labels["income"].setText(f"${stats['total_income']:,.2f}")
        if "expenses" in self.stat_labels: self.stat_labels["expenses"].setText(f"${stats['total_expenses']:,.2f}")
        
        # Balance Neto Styling
        if "balance" in self.stat_labels:
            bal_lbl = self.stat_labels["balance"]
            bal_lbl.setText(f"${stats['balance']:,.2f}")
            if stats['balance'] >= 0:
                bal_lbl.setStyleSheet("color: #10b981;")
            else:
                bal_lbl.setStyleSheet("color: #ef4444;")

        if "fixed" in self.stat_labels: self.stat_labels["fixed"].setText(f"${stats['fixed_expenses']:,.2f}")
        if "variable" in self.stat_labels: self.stat_labels["variable"].setText(f"${stats['variable_expenses']:,.2f}")
        
        # Dashboard Balances (Global)
        bals = stats['balances']
        if "loans" in self.stat_labels: self.stat_labels["loans"].setText(f"${bals['Préstamos']:,.2f}")
        if "checks" in self.stat_labels: self.stat_labels["checks"].setText(f"${bals['Cheques']:,.2f}")
        if "cards" in self.stat_labels: self.stat_labels["cards"].setText(f"${bals['Tarjetas']:,.2f}")
        if "prov" in self.stat_labels: self.stat_labels["prov"].setText(f"${bals['Proveedores']:,.2f}")

        # --- UPDATE PURE ACCOUNTING CARDS ---
        pure_stats = self.db.get_pure_accounting_stats()
        
        if hasattr(self, 'card_pure_day'):
            day_net = pure_stats['day']['net']
            self.stat_labels["pure_day"].setText(f"${day_net:,.2f}")
            self.stat_labels["pure_day"].setStyleSheet(f"color: {'#38bdf8' if day_net >= 0 else '#ef4444'}; font-size: 28px; font-weight: 900;")
            self.stat_trends["pure_day"].setText(f"Ing: ${pure_stats['day']['inc']:,.0f}")
            
        if hasattr(self, 'card_pure_month'):
            month_net = pure_stats['month']['net']
            self.stat_labels["pure_month"].setText(f"${month_net:,.2f}")
            self.stat_labels["pure_month"].setStyleSheet(f"color: {'#10b981' if month_net >= 0 else '#ef4444'}; font-size: 28px; font-weight: 900;")
            self.stat_trends["pure_month"].setText(f"Ing: ${pure_stats['month']['inc']:,.0f}")
            
        if hasattr(self, 'card_pure_year'):
            year_net = pure_stats['year']['net']
            self.stat_labels["pure_year"].setText(f"${year_net:,.2f}")
            self.stat_labels["pure_year"].setStyleSheet(f"color: {'#8b5cf6' if year_net >= 0 else '#ef4444'}; font-size: 28px; font-weight: 900;")
            self.stat_trends["pure_year"].setText(f"Ing: ${pure_stats['year']['inc']:,.0f}")

        # Dashboard Analysis
        total = stats['total_expenses']
        if total > 0:
            fixed_p = int((stats['fixed_expenses'] / total) * 100)
            var_p = int((stats['variable_expenses'] / total) * 100)
            self.fixed_percent_lbl.setText(f"Egresos Fijos: {fixed_p}%")
            self.fixed_progress.setValue(fixed_p)
            self.var_percent_lbl.setText(f"Egresos Variables: {var_p}%")
            self.var_progress.setValue(var_p)
        else:
            self.fixed_percent_lbl.setText("Fijos: 0%")
            self.fixed_progress.setValue(0)
            self.var_percent_lbl.setText("Variables: 0%")
            self.var_progress.setValue(0)
            
        total_inc = stats['total_income']
        total_exp = stats['total_expenses']
        
        if hasattr(self, 'alert_text'):
            # 1. Alertas
            today = datetime.date.today()
            upcoming_debts = [d for d in self.db.get_general_debts() if d[5] != 'paid']
            upcoming_total = 0
            count = 0
            for d in upcoming_debts:
                try:
                    due = datetime.datetime.strptime(d[4], "%Y-%m-%d").date()
                    if 0 <= (due - today).days <= 5:
                        upcoming_total += d[3] - d[7]
                        count += 1
                except: pass
            
            if count > 0:
                self.alert_text.setText(f"⚠️ Tienes {count} obligaciones venciendo en los próximos 5 días por un total de ${upcoming_total:,.2f}.")
                self.alert_text.setStyleSheet("color: #fca5a5; font-size: 13px;")
            else:
                self.alert_text.setText("✅ Todo al día. No hay vencimientos críticos cercanos.")
                self.alert_text.setStyleSheet("color: #86efac; font-size: 13px;")
                
            # 2. Termómetro
            if total_inc > 0:
                compromiso = (total_exp / total_inc) * 100
                self.debt_text.setText(f"De cada $100 que ingresaron este mes, ${compromiso:,.2f} ya están comprometidos en deudas o gastos.")
                self.debt_progress.setValue(min(100, int(compromiso)))
                color = "#ef4444" if compromiso > 80 else "#f59e0b" if compromiso > 50 else "#10b981"
                self.debt_progress.setStyleSheet(f"QProgressBar {{ background: #1e293b; border-radius: 5px; border: none; }} QProgressBar::chunk {{ background-color: {color}; border-radius: 5px; }}")
            else:
                self.debt_text.setText("Sin ingresos registrados aún este mes.")
                self.debt_progress.setValue(0)
                
            # 3. Meta (Simulada para Nivel 4)
            # Asumimos una meta dinámica de ingresos basada en el mes pasado + 10%
            meta = prev_stats['total_income'] * 1.1 if prev_stats['total_income'] > 0 else 1000000
            progreso = (total_inc / meta) * 100 if meta > 0 else 0
            self.goal_text.setText(f"Meta sugerida: ${meta:,.2f}\nLogrado: ${total_inc:,.2f}")
            self.goal_progress.setValue(min(100, int(progreso)))
        
        # Update Audit Table (Admin only)
        if self.role == "admin":
            self.update_audit_table()
            self.liability_progress.setValue(100)
            self.progress_label.setText("Panel Global de Administración")
        else:
            self.liability_progress.setValue(100)
            self.progress_label.setText("Sin compromisos financieros este mes.")

        # Dashboard Categories List (Top 5)
        # Clear previous items
        while self.cat_list_layout.count():
            item = self.cat_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for cat, amount in stats['categories'][:5]:
            item_frame = QFrame()
            item_frame.setStyleSheet("background: transparent; border-bottom: 1px solid #1f2937;")
            item_layout = QHBoxLayout(item_frame)
            item_layout.setContentsMargins(0, 5, 0, 5)
            
            lbl_cat = QLabel(cat)
            lbl_cat.setStyleSheet("color: #94a3b8; font-weight: 600;")
            lbl_amt = QLabel(f"${amount:,.2f}")
            lbl_amt.setStyleSheet("color: #f9fafb; font-weight: 800;")
            lbl_amt.setAlignment(Qt.AlignRight)
            
            item_layout.addWidget(lbl_cat)
            item_layout.addWidget(lbl_amt)
            self.cat_list_layout.addWidget(item_frame)

        # Lock/Unlock Logic based on Period
        today = datetime.date.today()
        is_past = (y < today.year) or (y == today.year and m < today.month)
        
        self.set_editing_enabled(not is_past)
        
        if is_past:
            self.lock_label.setText("🔒")
            self.lock_label.setToolTip("Periodo cerrado (Solo lectura)")
            self.btn_unlock.setVisible(True)
            self.status_bar.showMessage(f"Viendo periodo CERRADO: {self.month_sel.currentText()} {y}", 5000)
        else:
            self.lock_label.setText("🔓")
            self.lock_label.setToolTip("Periodo abierto")
            self.btn_unlock.setVisible(False)
            
        # Update Other Tables
        self.update_income_table()
        self.update_expenses_table()
        self.update_prov_table()
        self.update_loans_table()
        self.update_checks_table()
        self.update_debts_table()
        self.update_fixed_costs_table()
        self.update_investments_table()
        self.update_history_table()
        # self.update_stock_table() # Eliminado
        self.update_ai_insights()

        
        # Si somos el admin, actualizamos los datos del panel principal de administrador
        if self.role == "admin":
            self.update_admin_panel() 
            if hasattr(self, 'update_admin_payments_table'):
                self.update_admin_payments_table()
                
        # ACTUALIZAR EL GRÁFICO DE VELAS
        if hasattr(self, 'update_dashboard_chart'):
            self.update_dashboard_chart()

    def update_trend(self, key, current, previous):
        """Dibuja las flechitas verdes o rojas con estilo premium."""
        if key not in self.stat_trends: return
        label = self.stat_trends[key]
        if previous == 0:
            label.setText("NUEVO")
            label.setStyleSheet("background: rgba(148, 163, 184, 0.1); color: #94a3b8; padding: 4px 10px; border-radius: 8px;")
            return
            
        diff = ((current - previous) / previous) * 100
        if diff >= 0:
            label.setText(f"▲ {diff:,.1f}%")
            label.setStyleSheet("background: rgba(16, 185, 129, 0.15); color: #10b981; padding: 4px 10px; border-radius: 8px;")
        else:
            label.setText(f"▼ {abs(diff):,.1f}%")
            label.setStyleSheet("background: rgba(239, 68, 68, 0.15); color: #ef4444; padding: 4px 10px; border-radius: 8px;")

    def on_global_search(self, text):
        # Apply search filter to the current active module
        idx = self.stack.currentIndex()
        if idx == 2: # Income
            self.update_income_table(text)
        elif idx == 3: # Expenses
            self.update_expenses_table(text)
        elif idx == 7: # History
            self.history_search.setText(text)
        elif idx == 13: # Admin - Se corrige el índice para la pestaña del administrador
            # Cuando el administrador busca, actualizamos las tarjetas de las empresas
            self.update_admin_panel(text)
        elif idx == 14: # Admin Payments
            if hasattr(self, 'admin_pay_search'):
                self.admin_pay_search.setText(text)

    def set_editing_enabled(self, enabled):
        # List of widgets to enable/disable
        # Income
        if hasattr(self, 'inc_amount'):
            self.inc_amount.setEnabled(enabled)
            self.inc_desc.setEnabled(enabled)
            # Find and disable save button in income tab
            for btn in self.tab_income.findChildren(QPushButton):
                if "Guardar" in btn.text(): btn.setEnabled(enabled)
        
        # Expenses
        if hasattr(self, 'exp_amount'):
            self.exp_amount.setEnabled(enabled)
            for btn in self.tab_expenses.findChildren(QPushButton):
                if "Guardar" in btn.text(): btn.setEnabled(enabled)
                
        # Fixed Costs
        if hasattr(self, 'tab_fixed'):
            for btn in self.tab_fixed.findChildren(QPushButton):
                btn.setEnabled(enabled)

    def manual_unlock(self):
        password, ok = QInputDialog.getText(self, "Acceso Restringido", 
                                          "Ingrese la contraseña de administrador para desbloquear edición histórica:",
                                          QLineEdit.Password)
        if ok and password == Config.ADMIN_PASSWORD:
            self.set_editing_enabled(True)
            self.lock_label.setText("🔓 (FORZADO)")
            self.btn_unlock.setVisible(False)
            self.status_bar.showMessage("Edición HISTÓRICA habilitada.", 5000)
            QMessageBox.information(self, "Acceso Concedido", "El periodo ha sido desbloqueado para edición.")
        elif ok:
            QMessageBox.critical(self, "Acceso Denegado", "Contraseña incorrecta. El periodo permanece bloqueado.")

    def export_advanced_report(self):
        """Genera un reporte CSV profesional con totales y balance final."""
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        stats = self.db.get_stats(m, y)
        
        comp_name = self.company_name if self.company_name else 'Admin'
        path, _ = QFileDialog.getSaveFileName(self, "Exportar Reporte Pro", 
                                            f"Reporte_{comp_name}_{y}_{m:02d}.csv", "CSV (*.csv)")
        if not path: return
        
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["REPORTE FINANCIERO PROFESIONAL", self.company_name.upper()])
                writer.writerow(["Periodo:", f"{m:02d}/{y}"])
                writer.writerow([])
                writer.writerow(["RESUMEN EJECUTIVO"])
                writer.writerow(["Ingresos Totales", f"{stats['total_income']:.2f}"])
                writer.writerow(["Egresos Totales", f"{stats['total_expenses']:.2f}"])
                writer.writerow(["Balance Neto", f"{stats['balance']:.2f}"])
                writer.writerow([])
                writer.writerow(["DETALLE DE MOVIMIENTOS"])
                writer.writerow(["Fecha", "Tipo", "Categoría", "Descripción", "Monto"])
                
                movements = self.db.get_all_movements(m, y)
                for mov in movements:
                    writer.writerow([mov[0], mov[1], mov[2], mov[3], f"{mov[4]:.2f}"])
            
            QMessageBox.information(self, "Reporte Generado", "El reporte se ha exportado con éxito.")
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"No se pudo generar el archivo: {e}")

    def init_ai_tab(self):
        self.tab_ai = QWidget()
        layout = QVBoxLayout(self.tab_ai)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Header IA Estilo Premium
        header = QFrame()
        header.setFixedHeight(120)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e1b4b, stop:1 #312e81); 
                border-radius: 20px; 
                border: 1px solid #4338ca;
            }
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(25, 0, 25, 0)
        
        ai_icon = QLabel("🧠")
        ai_icon.setStyleSheet("font-size: 50px; background: transparent;")
        h_layout.addWidget(ai_icon)
        
        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignCenter)
        title = QLabel("ORÁCULO FINANCIERO IA")
        title.setStyleSheet("font-size: 26px; font-weight: 900; color: white; background: transparent; letter-spacing: 2px;")
        sub = QLabel("MENTORÍA PARA EL CRECIMIENTO ECONÓMICO Y SALUD FINANCIERA")
        sub.setStyleSheet("color: #a5b4fc; font-weight: 700; font-size: 10px; background: transparent; letter-spacing: 1px;")
        text_layout.addWidget(title); text_layout.addWidget(sub)
        h_layout.addLayout(text_layout)
        h_layout.addStretch()
        
        # Botón de "Consultar ahora"
        btn_audit = QPushButton("🔍 Auditar Estrategia")
        btn_audit.setFixedWidth(180)
        btn_audit.setStyleSheet("background: #10b981; color: white; padding: 10px; font-weight: bold; border-radius: 10px;")
        btn_audit.clicked.connect(self.run_proactive_audit)
        h_layout.addWidget(btn_audit)
        
        btn_ask = QPushButton("Nueva Consulta")
        btn_ask.setFixedWidth(140)
        
        layout.addWidget(header)
        
        main_content = QHBoxLayout()
        
        # Left Side: Insights Feed
        feed_container = QVBoxLayout()
        feed_container.addWidget(QLabel("📢 INSIGHTS Y ALERTAS DE LA RED"))
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        self.ai_container = QWidget()
        self.ai_layout = QVBoxLayout(self.ai_container)
        self.ai_layout.setSpacing(15)
        self.ai_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.ai_container)
        feed_container.addWidget(scroll)
        main_content.addLayout(feed_container, 2)
        
        # Right Side: Mentor / Chat Area
        self.mentor_container = QFrame()
        self.mentor_container.setObjectName("Card")
        self.mentor_container.setStyleSheet("background-color: #0f172a; border: 1px solid #1e293b;")
        mentor_layout = QVBoxLayout(self.mentor_container)
        
        mentor_header = QHBoxLayout()
        mentor_title = QLabel("🤖 MENTOR ESTRATÉGICO")
        mentor_title.setStyleSheet("font-weight: 900; color: #6366f1; font-size: 14px;")
        mentor_header.addWidget(mentor_title)
        
        self.voice_btn = QPushButton("🔊")
        self.voice_btn.setFixedSize(30, 30)
        self.voice_btn.setStyleSheet("background: transparent; font-size: 16px; border: none;")
        self.voice_btn.setCheckable(True)
        self.voice_btn.setChecked(True)
        self.voice_btn.clicked.connect(self.toggle_voice)
        mentor_header.addWidget(self.voice_btn)
        
        status_dot = QLabel("● Online")
        status_dot.setStyleSheet("color: #10b981; font-weight: bold; font-size: 10px;")
        mentor_header.addWidget(status_dot)
        mentor_header.addStretch()
        mentor_layout.addLayout(mentor_header)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            background: #030712; 
            color: #e2e8f0; 
            border: 1px solid #1f2937; 
            padding: 10px; 
            font-size: 13px; 
            border-radius: 8px;
        """)
        mentor_layout.addWidget(self.chat_history)
        
        input_row = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Escribe tu consulta aquí...")
        self.chat_input.setStyleSheet("padding: 10px; background: #1e293b; color: white; border: 1px solid #334155; border-radius: 8px;")
        self.chat_input.returnPressed.connect(self.send_mentor_message)
        
        btn_send = QPushButton("⚡")
        btn_send.setFixedSize(40, 40)
        btn_send.setStyleSheet("background: #6366f1; color: white; font-weight: bold; border-radius: 20px;")
        btn_send.clicked.connect(self.send_mentor_message)
        
        input_row.addWidget(self.chat_input)
        input_row.addWidget(btn_send)
        mentor_layout.addLayout(input_row)
        
        # Stats de la IA
        self.ai_health_lbl = QLabel("Estado de la Red: Calculando...")
        self.ai_health_lbl.setStyleSheet("font-weight: bold; color: #10b981; margin-top: 5px;")
        mentor_layout.addWidget(self.ai_health_lbl)
        
        main_content.addWidget(self.mentor_container, 1)
        
        layout.addLayout(main_content)
        
        # Mensaje inicial del mentor
        self.chat_history.append("<b style='color: #6366f1;'>Mentor:</b> Hola. Soy tu consultor estratégico. Analizo tus números en tiempo real para ayudarte a desendeudarte y escalar tu negocio. ¿En qué área nos enfocamos hoy?")
        
        self.stack.addWidget(self.tab_ai)

    def init_reports_tab(self):
        self.tab_reports = QWidget()
        layout = QVBoxLayout(self.tab_reports)
        
        container = QFrame()
        container.setObjectName("Card")
        vbox = QVBoxLayout(container)
        
        title = QLabel("GENERACIÓN DE REPORTES PDF")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        vbox.addWidget(title)
        vbox.addSpacing(20)
        vbox.addWidget(QLabel("Selecciona esta opción para generar reportes mensuales en PDF."))
        vbox.addWidget(QLabel("Se crearán dos archivos en tu Escritorio dentro de la carpeta 'Reportes PunPro':\n1. Libro Contable Completo (Para tu control detallado)\n2. Reporte Gerencial / Jefe (Resumen y retiros)"))
        
        vbox.addStretch()
        
        btn_generate = QPushButton("Generar Reportes PDF del Mes Actual")
        btn_generate.setStyleSheet("background-color: #3b82f6; font-size: 16px; padding: 15px; font-weight: bold;")
        btn_generate.clicked.connect(self.generate_reports_pdf)
        vbox.addWidget(btn_generate)
        
        layout.addWidget(container)
        self.stack.addWidget(self.tab_reports)

    def update_ai_insights(self):
        # Clear previous insights
        while self.ai_layout.count():
            item = self.ai_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        
        insights = []
        
        if self.role == "admin":
            # --- GLOBAL ANTI-FRAUD SCANNER ---
            db_files = [f for f in glob.glob("*.db") if not f.startswith("backup_") and f != "database.db"]
            for db_f in db_files:
                name = db_f.replace(".db", "").upper()
                tdb = Database(db_f)
                stats = tdb.get_stats(m, y)
                
                # Regla 1: Gastos Variables extremadamente altos vs Ingresos
                if stats['total_income'] > 0 and stats['variable_expenses'] > stats['total_income'] * 0.8:
                    insights.append((f"🚨 Riesgo de Fuga en {name}", f"Los gastos variables superan el 80% de los ingresos. Revisa posibles compras no justificadas o fuga de inventario.", "#ef4444"))
                    
                # Regla 2: Días en Cero (Simplificado a fin de mes)
                if stats['total_income'] == 0 and stats['total_expenses'] > 0:
                    insights.append((f"🕵️‍♂️ Anomalía Detectada: {name}", f"La sucursal reporta gastos por ${stats['total_expenses']:,.2f} pero CERO ingresos este mes.", "#f59e0b"))
                    
                # Regla 3: Excelencia a Replicar
                if stats['total_income'] > 0 and stats['balance'] > stats['total_income'] * 0.4:
                    insights.append((f"🏆 Rendimiento Extraordinario: {name}", f"Margen neto superior al 40%. Evalúa replicar las prácticas operativas de esta sucursal.", "#10b981"))
            
            if not insights:
                insights.append(("✅ Red Segura y Operativa", "El motor Anti-Fraude no detectó anomalías contables graves ni riesgos de liquidez en las sucursales auditadas.", "#3b82f6"))
                
        else:
            # --- BRANCH AI LOGIC ---
            stats = self.db.get_stats(m, y)
            
            # 1. Performance Insight
            if stats['total_income'] > 0:
                margin = (stats['balance'] / stats['total_income']) * 100
                if margin > 30:
                    insights.append(("✨ Excelente Rentabilidad", f"Tu margen neto es del {margin:.1f}%. El negocio está en una zona muy saludable.", "#10b981"))
                elif margin > 10:
                    insights.append(("📈 Crecimiento Estable", f"Margen del {margin:.1f}%. Buen ritmo, pero revisa si puedes optimizar gastos variables.", "#6366f1"))
                else:
                    insights.append(("⚠️ Margen Ajustado", f"Tu utilidad es solo del {margin:.1f}%. Considera revisar precios o reducir costos fijos.", "#f59e0b"))
            
            # 2. Anomaly Detection (Fixed vs Variable)
            if stats['total_expenses'] > 0:
                var_p = (stats['variable_expenses'] / stats['total_expenses']) * 100
                if var_p > 60:
                    insights.append(("🔍 Alerta de Gastos Variables", f"Los gastos variables representan el {var_p:.1f}% de tus egresos. Esto indica una alta dependencia de compras diarias.", "#ef4444"))
    
            # 3. Liquidity Check
            pending_total = sum(i[3] for i in self.db.get_installments() if str(i[4]).startswith(f"{y}-{m:02d}"))
            if pending_total > stats['total_income'] * 0.5:
                 insights.append(("🚨 Riesgo de Liquidez", f"Tienes cuotas pendientes por ${pending_total:,.2f} que superan el 50% de tus ingresos. ¡Cuidado con el flujo de caja!", "#ef4444"))
    
            # 4. Projections & Bonus
            day_of_month = datetime.date.today().day if m == datetime.date.today().month else 30
            daily_avg = stats['total_income'] / day_of_month if day_of_month > 0 else 0
            projection = daily_avg * 30
            comp_name = self.company_name.upper() if self.company_name else 'la red'
            insights.append(("🔮 Proyección de Cierre", f"A este ritmo, {comp_name} cerrará el mes con un ingreso estimado de ${projection:,.2f}.", "#8b5cf6"))
            
            # 5. Calculadora de Bonos (Gamificación)
            if stats['balance'] > 500000: # Supongamos meta arbitraria
                bono = stats['balance'] * 0.02
                insights.append(("🎁 Meta de Bonificación Alcanzada", f"¡Gran trabajo! Has generado una utilidad que habilita un bono estimado de ${bono:,.2f} a repartir con tu equipo (2% de Utilidad).", "#a855f7"))

        # Render Insights
        for title, text, color in insights:
            card = QFrame()
            card.setCursor(Qt.PointingHandCursor)
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #1e293b; 
                    border-left: 6px solid {color}; 
                    border-radius: 12px; 
                    padding: 5px;
                }}
                QFrame:hover {{
                    background-color: #2d3748;
                    border-left: 8px solid {color};
                }}
            """)
            c_layout = QVBoxLayout(card)
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet(f"color: {color}; font-weight: 900; font-size: 16px; background: transparent;")
            d_lbl = QLabel(text)
            d_lbl.setStyleSheet("color: #e2e8f0; font-size: 13px; background: transparent;")
            d_lbl.setWordWrap(True)
            c_layout.addWidget(t_lbl); c_layout.addWidget(d_lbl)
            
            # Click para enseñar
            card.mousePressEvent = lambda e, t=title, tx=text: self.open_ai_teaching(f"{t}: {tx}")
            
            self.ai_layout.addWidget(card)
            
        # Actualizar estado de salud de la red en el panel de mentoría
        if self.role != "admin" and stats['total_income'] > 0:
            health = "SALUDABLE" if stats['balance'] > stats['total_income'] * 0.2 else "EN OBSERVACIÓN"
            self.ai_health_lbl.setText(f"Estado de Salud: {health} ({ (stats['balance']/stats['total_income']*100):.1f}% margen)")
            self.ai_health_lbl.setStyleSheet(f"font-weight: bold; color: {'#10b981' if health == 'SALUDABLE' else '#f59e0b'}; margin-top: 10px;")

        self.ai_layout.addStretch()

    def open_ai_teaching(self, topic):
        """Activa el panel de la IA con una 'clase' o explicación profunda del tema seleccionado."""
        self.stack.setCurrentIndex(11) # Ir a pestaña IA
        self.chat_history.append(f"\n<b style='color: #a855f7;'>Analizando: {topic}</b>")
        
        # Simular una respuesta profunda de la IA basada en el contexto del ERP
        body = ""
        if "fuga" in topic.lower() or "gasto" in topic.lower():
            body = (
                "Escucha con atención: he detectado una anomalía en tus flujos de salida. "
                "Los gastos variables están creciendo más rápido que tus ventas. Esto suele ser una 'fuga silenciosa'. "
                "Te sugiero auditar los remitos de esta semana. ¿Estamos comprando de más o a precios muy altos?"
            )
        elif "rentabilidad" in topic.lower() or "balance" in topic.lower():
            body = (
                "Tu rentabilidad es el corazón del negocio. Para escalarla, debemos proteger el margen neto. "
                "Si logras mantener tus costos fijos por debajo del 15 por ciento de tus ingresos, estarás en el top de la red. "
                "La disciplina hoy es tu libertad financiera mañana."
            )
        elif "liquidez" in topic.lower() or "deuda" in topic.lower():
            body = (
                "Hablemos de liquidez. Tienes compromisos que vencen pronto. "
                "Mi consejo táctico: no utilices el capital de trabajo para deudas de largo plazo. "
                "Mantén siempre un fondo de reserva equivalente a un mes de costos fijos."
            )
        else:
            body = (
                "Este punto es clave para tu evolución. Mi motor de IA proyecta el éxito basándose en la "
                "precisión de tus registros. Cuanto mejor alimentes el sistema, más poder tendré para proteger tu capital."
            )
            
        self.chat_history.append(f"<b style='color: #6366f1;'>Mentor:</b> {body}")
        self.ai_health_lbl.setText(f"Enseñanza activa: {topic[:30]}...")
        self.speak(body)

    def send_mentor_message(self):
        user_msg_raw = self.chat_input.text().strip()
        if not user_msg_raw: return
        user_msg = user_msg_raw.lower()
        
        self.chat_history.append(f"\n<b style='color: #e2e8f0;'>Tú:</b> {user_msg_raw}")
        self.chat_input.clear()
        
        # Lógica de respuesta del Mentor basado en palabras clave y contexto
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        
        # --- ADMIN "BOSS" LOGIC ---
        if self.role == "admin":
            db_files = [f for f in glob.glob("*.db") if not f.startswith("backup_") and f != "database.db"]
            all_stats = []
            for db_f in db_files:
                try:
                    tdb = Database(db_f)
                    all_stats.append((db_f.replace(".db", "").upper(), tdb.get_stats(m, y)))
                except: continue
            
            if "total" in user_msg or "toda la red" in user_msg or "sucursales" in user_msg:
                total_inc = sum(s[1]['total_income'] for s in all_stats)
                total_net = sum(s[1]['balance'] for s in all_stats)
                best_branch = max(all_stats, key=lambda x: x[1]['balance'])[0] if all_stats else "N/A"
                response = (
                    f"Reporte de Comandante: La red total ha generado {total_inc:,.0f} pesos este mes, con una utilidad neta consolidada de {total_net:,.0f} pesos. "
                    f"La sucursal líder actualmente es {best_branch}. Como jefe, mi recomendación es auditar por qué las demás no replican su margen."
                )
            elif "internet" in user_msg or "tendencia" in user_msg or "mercado" in user_msg:
                response = (
                    "Mentor Jefe: He analizado las tendencias del mercado global 2026. Se observa un aumento en la personalización de servicios y optimización digital. "
                    "Te sugiero revisar tu cadena de suministro para reducir costos operativos un 3 por ciento y considerar estrategias de fidelización para subir el ticket promedio."
                )
            else:
                # Fallback to normal keywords if no admin-specific command
                stats = self.db.get_stats(m, y) # This is the current context DB
                response = self.get_standard_mentor_response(user_msg, stats)
        else:
            # --- BRANCH ISOLATION LOGIC ---
            stats = self.db.get_stats(m, y)
            response = self.get_standard_mentor_response(user_msg, stats)

        def delayed_reply():
            self.chat_history.append(f"<b style='color: #6366f1;'>Mentor {'Jefe' if self.role=='admin' else ''}:</b> {response}")
            self.speak(response)
            
        QTimer.singleShot(600, delayed_reply)

    def get_standard_mentor_response(self, user_msg, stats):
        # --- CATEGORÍAS DE RESPUESTA ---
        greetings = ["hola", "buenas", "que tal", "buen dia", "saludos"]
        health_keywords = ["salud", "bien", "como vamos", "estado", "situacion"]
        insight_keywords = ["insight", "que es", "que hace", "panel", "entender"]
        debt_keywords = ["deuda", "prestamo", "debo", "pagar", "cuota"]
        cost_keywords = ["gasto", "costo", "perdi", "fuga", "egreso"]
        profit_keywords = ["gano", "ganancia", "utilidad", "balance", "cuanto", "plata", "dinero"]

        if any(w in user_msg for w in greetings):
            return random.choice([
                "¡Hola! Tu sucursal tiene un potencial enorme. ¿Qué números auditamos hoy?",
                "Buen día. Estoy listo para proteger tu capital. ¿En qué nos enfocamos?",
                "Hola. El registro diario es tu mejor arma. ¿Revisamos el balance?"
            ])
        elif any(w in user_msg for w in insight_keywords):
            return (
                "El panel de Insights es mi cerebro estratégico. Busco patrones que tú no ves, como fugas de dinero "
                "o picos de gastos. Es tu radar para no perder rentabilidad."
            )
        elif any(w in user_msg for w in debt_keywords):
            total_debt = stats['balances']['Préstamos'] + stats['balances']['Cheques']
            return f"Tu deuda en esta sucursal es de {total_debt:,.0f} pesos. Prioriza siempre el desendeudamiento para crecer con capital propio."
        elif any(w in user_msg for w in cost_keywords):
            return f"Tus gastos suman {stats['total_expenses']:,.0f} pesos. Si reducimos los variables un 5 por ciento, tu utilidad saltará de inmediato."
        elif any(w in user_msg for w in profit_keywords):
            return f"Tu utilidad neta actual es de {stats['balance']:,.0f} pesos. Es tu dinero real, libre de compromisos."
        else:
            return "Entiendo. Estoy aquí para que cada peso cuente. ¿Revisamos la proyección de cierre?"

    def toggle_voice(self):
        enabled = self.voice_btn.isChecked()
        self.voice_btn.setText("🔊" if enabled else "🔇")
        self.status_bar.showMessage(f"Voz del Mentor {'activada' if enabled else 'desactivada'}", 3000)

    def speak(self, text):
        if not self.voice_btn.isChecked(): return
        
        def run_tts():
            # Limpiar texto para lectura fluida
            clean_text = text.replace("$", "").replace("AR", "pesos").replace("%", " por ciento")
            
            # Intentar con pyttsx3 si está instalado
            if pyttsx3:
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 170)
                    engine.say(clean_text)
                    engine.runAndWait()
                    return
                except: pass
            
            # Fallback forzado a PowerShell (Nativo de Windows, siempre funciona)
            try:
                escaped = clean_text.replace('"', '""').replace("\n", " ")
                # Comando de PowerShell para sintetizar voz
                ps_command = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{escaped}')"
                subprocess.run(["powershell", "-WindowStyle", "Hidden", "-Command", ps_command], capture_output=True)
            except Exception as e:
                logger.error(f"Error en Fallback de Voz: {e}")
                
        threading.Thread(target=run_tts, daemon=True).start()

    def run_proactive_audit(self):
        """El mentor realiza un escaneo completo y 'habla' sobre el estado del negocio."""
        self.stack.setCurrentIndex(11)
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        
        self.chat_history.append(f"\n<b style='color: #10b981;'>--- INICIANDO AUDITORÍA PROACTIVA {'GLOBAL' if self.role=='admin' else 'LOCAL'} ---</b>")
        
        if self.role == "admin":
            # --- GLOBAL NETWORK AUDIT ---
            db_files = [f for f in glob.glob("*.db") if not f.startswith("backup_") and f != "database.db"]
            total_net = 0
            total_inc = 0
            branches_info = []
            for db_f in db_files:
                try:
                    tdb = Database(db_f)
                    s = tdb.get_stats(m, y)
                    total_net += s['balance']
                    total_inc += s['total_income']
                    branches_info.append((db_f.replace(".db", ""), s['balance']))
                except: continue
            
            best = max(branches_info, key=lambda x: x[1])[0] if branches_info else "N/A"
            full_report = (
                f"Comandante Jefe: He auditado las {len(db_files)} unidades de negocio activas. "
                f"La red consolidada tiene un flujo de ingresos de {total_inc:,.0f} pesos y una utilidad neta de {total_net:,.0f} pesos. "
                f"La unidad {best} es la más eficiente este mes. Te sugiero analizar sus procesos para estandarizar el éxito en toda la red."
            )
        else:
            # --- SINGLE BRANCH AUDIT ---
            stats = self.db.get_stats(m, y)
            day_of_month = datetime.date.today().day if m == datetime.date.today().month else 30
            daily_avg = stats['total_income'] / day_of_month if day_of_month > 0 else 0
            yearly_net = (stats['balance'] / day_of_month) * 365 if day_of_month > 0 else 0
            
            full_report = (
                f"Iniciando auditoría de rendimiento. Con un promedio operativo diario de {daily_avg:,.0f} pesos, "
                f"tu utilidad neta proyectada anual es de {yearly_net:,.0f} pesos. "
                f"He validado tus flujos de caja. Mantén el foco en la optimización de gastos variables para proteger tu margen."
            )
        
        def display_report():
            self.chat_history.append(f"<b style='color: #6366f1;'>Mentor Jefe:</b> {full_report}")
            self.speak(full_report)
            
        QTimer.singleShot(800, display_report)

    def update_admin_panel(self, filter_text=""):
        if self.role != "admin": return
        
        # Scan for all .db files
        db_files = [f for f in glob.glob("*.db") if not f.startswith("backup_") and f != "database.db"]
        if filter_text:
            db_files = [f for f in db_files if filter_text.lower() in f.lower()]
            
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        
        # Accumulators for Group Metrics
        total_group_inc = 0
        total_group_exp = 0
        
        # Update Matrix
        self.performance_table.setRowCount(0)
        company_data = {}
        for db_file in db_files:
            try:
                temp_db = Database(db_file)
                stats = temp_db.get_stats(m, y)
                total_group_inc += stats['total_income']
                total_group_exp += stats['total_expenses']
                
                name = db_file.replace(".db", "").upper()
                company_data[name] = stats
            except: continue
            
        sorted_companies = sorted(company_data.items(), key=lambda x: x[1]['balance'], reverse=True)
        for name, stats in sorted_companies:
            r = self.performance_table.rowCount()
            self.performance_table.insertRow(r)
            self.performance_table.setItem(r, 0, QTableWidgetItem(name))
            self.performance_table.setItem(r, 1, QTableWidgetItem(f"${stats['total_income']:,.0f}"))
            self.performance_table.setItem(r, 2, QTableWidgetItem(f"${stats['balance']:,.0f}"))
            status = "🏆 LÍDER" if r == 0 and stats['balance'] > 0 else "📈 ESTABLE" if stats['balance'] >= 0 else "🚨 CRÍTICO"
            item_status = QTableWidgetItem(status)
            item_status.setForeground(Qt.green if stats['balance'] >= 0 else Qt.red)
            self.performance_table.setItem(r, 3, item_status)

        # Clear grid and add cards
        while self.admin_grid.count():
            item = self.admin_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        row, col = 0, 0
        for name, stats in company_data.items():
            self.create_admin_company_card(name, stats, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
                
        # Update Group Metric Cards
        inc_lbl = self.card_group_income.findChild(QLabel, "StatValue") or self.card_group_income.findChild(QLabel, "value")
        if inc_lbl: inc_lbl.setText(f"${total_group_inc:,.2f}")
        exp_lbl = self.card_group_expense.findChild(QLabel, "StatValue") or self.card_group_expense.findChild(QLabel, "value")
        if exp_lbl: exp_lbl.setText(f"${total_group_exp:,.2f}")
        
        net = total_group_inc - total_group_exp
        net_lbl = self.card_group_net.findChild(QLabel, "StatValue") or self.card_group_net.findChild(QLabel, "value")
        if net_lbl:
            net_lbl.setText(f"${net:,.2f}")
            net_lbl.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {'#10b981' if net >= 0 else '#ef4444'};")

        # Update Admin Radar & Ranking
        self.update_admin_radar_ranking(company_data)
        
        # Update Comparative Chart (Top 5)
        self.admin_chart_ax.clear()
        self.admin_chart_ax.set_facecolor('#0f172a')
        
        top5 = sorted_companies[:5]
        if top5:
            names = [x[0][:10] for x in top5]
            incomes = [x[1]['total_income'] for x in top5]
            expenses = [x[1]['total_expenses'] for x in top5]
            
            x_pos = list(range(len(names)))
            width = 0.35
            
            x_incomes = [x - width/2 for x in x_pos]
            x_expenses = [x + width/2 for x in x_pos]
            
            self.admin_chart_ax.bar(x_incomes, incomes, width, label='Ingresos', color='#10b981')
            self.admin_chart_ax.bar(x_expenses, expenses, width, label='Egresos', color='#f43f5e')
            
            self.admin_chart_ax.set_xticks(x_pos)
            self.admin_chart_ax.set_xticklabels(names, color='white', rotation=10, fontsize=9)
            self.admin_chart_ax.tick_params(axis='y', colors='white')
            
            self.admin_chart_ax.spines['bottom'].set_color('#334155')
            self.admin_chart_ax.spines['top'].set_visible(False)
            self.admin_chart_ax.spines['right'].set_visible(False)
            self.admin_chart_ax.spines['left'].set_color('#334155')
            
            self.admin_chart_ax.legend(loc='upper right', facecolor='#1e293b', edgecolor='#334155', labelcolor='white')
            self.admin_chart_ax.set_title("BATALLA DE SUCURSALES (TOP 5)", color='#e0e7ff', weight='bold', pad=10)
            
        self.admin_chart_figure.tight_layout()
        self.admin_chart_canvas.draw()

    def update_admin_radar_ranking(self, company_data):
        # 1. Radar Crítico (Endeudamiento > 60%)
        while self.radar_layout.count():
            item = self.radar_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        critical_companies = []
        for name, stats in company_data.items():
            inc = stats['total_income']
            exp = stats['total_expenses']
            if inc > 0:
                ratio = (exp / inc) * 100
                if ratio > 60: critical_companies.append((name, ratio, inc, exp))
            elif exp > 0:
                critical_companies.append((name, 999, 0, exp)) # Infinite ratio
                
        critical_companies.sort(key=lambda x: x[1], reverse=True)
        
        if not critical_companies:
            lbl = QLabel("✅ Sin alertas críticas. Todas las empresas están sanas.")
            lbl.setStyleSheet("color: #10b981; font-weight: bold;")
            self.radar_layout.addWidget(lbl)
        else:
            for c in critical_companies[:3]: # Top 3 worst
                name, ratio, inc, exp = c
                lbl = QLabel(f"⚠️ {name}: Deuda al {int(ratio) if ratio != 999 else '∞'}% (Ingresó ${inc/1000:,.0f}k | Gastó ${exp/1000:,.0f}k)")
                lbl.setStyleSheet("color: #fca5a5; font-weight: 900; font-size: 11px; background: #450a0a; padding: 4px; border-radius: 4px;")
                self.radar_layout.addWidget(lbl)
                
        self.radar_layout.addStretch()

        # 2. Ranking Fuga de Capitales (Gastos)
        while self.ranking_layout.count():
            item = self.ranking_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        fuga = sorted(company_data.items(), key=lambda x: x[1]['total_expenses'], reverse=True)
        podium = ["🥇", "🥈", "🥉"]
        for i, (name, stats) in enumerate(fuga[:3]):
            if stats['total_expenses'] <= 0: continue
            lbl = QLabel(f"{podium[i] if i < 3 else '🔹'} {name}: ${stats['total_expenses']:,.2f}")
            lbl.setStyleSheet("color: #fb7185; font-size: 13px; font-weight: bold;")
            self.ranking_layout.addWidget(lbl)
            
        if sum(1 for x in fuga if x[1]['total_expenses'] > 0) == 0:
            lbl = QLabel("No hay gastos registrados en el conglomerado.")
            lbl.setStyleSheet("color: #94a3b8;")
            self.ranking_layout.addWidget(lbl)
            
        self.ranking_layout.addStretch()

        # 3. Empresa Estrella (Top Profit)
        while self.top_layout.count():
            item = self.top_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        estrellas = sorted(company_data.items(), key=lambda x: x[1]['balance'], reverse=True)
        for i, (name, stats) in enumerate(estrellas[:3]):
            if stats['balance'] <= 0: continue
            lbl = QLabel(f"{podium[i] if i < 3 else '🔹'} {name}: +${stats['balance']:,.2f}")
            lbl.setStyleSheet("color: #10b981; font-size: 13px; font-weight: bold;")
            self.top_layout.addWidget(lbl)
            
        if sum(1 for x in estrellas if x[1]['balance'] > 0) == 0:
            lbl = QLabel("Aún no hay sucursales con balance positivo.")
            lbl.setStyleSheet("color: #94a3b8;")
            self.top_layout.addWidget(lbl)
            
        self.top_layout.addStretch()

    def create_new_company_admin(self):
        name, ok = QInputDialog.getText(self, "Nueva Empresa", "Nombre de la nueva empresa:")
        if ok and name:
            safe_name = name.lower().replace(" ", "_")
            db_path = f"{safe_name}.db"
            if os.path.exists(db_path):
                QMessageBox.warning(self, "Error", "Ya existe una empresa con ese nombre.")
                return
            
            # Create the DB and init tables
            new_db = Database(db_path)
            self.status_bar.showMessage(f"Empresa '{name.upper()}' creada con éxito.", 5000)
            self.update_admin_panel()
            QMessageBox.information(self, "Éxito", f"Se ha creado la base de datos para '{name.upper()}'.\nAhora los empleados pueden seleccionarla al iniciar sesión.")

    def switch_profile_ui(self):
        reply = QMessageBox.question(self, "Cambiar Perfil", "¿Desea cerrar la sesión actual y cambiar de perfil?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.switch_requested = True
            self.close()

    def switch_company_ui(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Empresa (Base de Datos)", "", "SQLite DB (*.db)")
        if file_path:
            # Check if it's a valid DB or if it needs upgrade
            self.db = Database(file_path)
            self.company_label.setText(f"EMPRESA: {os.path.basename(file_path).replace('.db', '').upper()}")
            self.load_all_data()
            self.status_bar.showMessage(f"Empresa cambiada a: {os.path.basename(file_path)}", 5000)
        else:
            # Option to create new
            reply = QMessageBox.question(self, "Nueva Empresa", "¿Desea crear una nueva base de datos para otra empresa?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                new_path, _ = QFileDialog.getSaveFileName(self, "Crear Nueva Empresa", "nueva_empresa.db", "SQLite DB (*.db)")
                if new_path:
                    if not new_path.endswith('.db'): new_path += '.db'
                    self.db = Database(new_path)
                    self.company_label.setText(f"EMPRESA: {os.path.basename(new_path).replace('.db', '').upper()}")
                    self.load_all_data()
                    self.status_bar.showMessage(f"Nueva empresa creada: {os.path.basename(new_path)}", 5000)

    def update_history_table(self):
        self.history_table.setRowCount(0)
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        search = self.history_search.text().lower()
        
        movements = self.db.get_all_movements(m, y)
        
        for d in movements:
            # d: date, type, cat, desc, amount, id, status
            if search and not (search in str(d[2]).lower() or search in str(d[3]).lower()):
                continue
                
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            self.history_table.setItem(row, 0, QTableWidgetItem(d[0]))
            
            type_item = QTableWidgetItem(d[1])
            self.history_table.setItem(row, 1, type_item)
            
            self.history_table.setItem(row, 2, QTableWidgetItem(d[2]))
            self.history_table.setItem(row, 3, QTableWidgetItem(d[3]))
            
            amt_item = QTableWidgetItem(f"${abs(d[4]):,.2f}")
            if d[1] == 'INGRESO':
                amt_item.setForeground(Qt.darkGreen)
                type_item.setForeground(Qt.darkGreen)
            else:
                amt_item.setForeground(Qt.red)
                type_item.setForeground(Qt.red)
            self.history_table.setItem(row, 4, amt_item)
            
            # Estado Column
            status_item = QTableWidgetItem(d[6])
            if d[6] == 'Pagado': status_item.setForeground(Qt.darkGreen)
            elif d[6] == 'Pendiente': status_item.setForeground(Qt.red)
            else: status_item.setForeground(Qt.darkYellow)
            self.history_table.setItem(row, 5, status_item)

            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Eliminar este movimiento (Revertir)")
            btn_del.setStyleSheet("background-color: #ef4444; max-width: 40px;")
            btn_del.clicked.connect(lambda ch, id=d[5], t=d[1]: self.delete_movement_ui(id, t))
            btn_del.setVisible(self.role == "admin")
            self.history_table.setCellWidget(row, 6, btn_del)
            
        self.history_table.setColumnHidden(6, self.role != "admin")

    def delete_movement_ui(self, move_id, m_type):
        reply = QMessageBox.question(self, "Confirmar", "¿Desea eliminar definitivamente este movimiento del historial de la empresa?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if m_type == 'INGRESO':
                self.db.delete_income(move_id)
            else:
                self.db.delete_expense(move_id)
            self.load_all_data()

    def get_date_color_styles(self, date_str):
        """Returns (background_color, text_color) based on proximity to today."""
        try:
            today = datetime.date.today()
            due_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            diff = (due_date - today).days
            
            if diff < 0:
                return "#ef4444", "white" # Red (Overdue)
            elif diff <= 4:
                return "#f59e0b", "black" # Orange (Close)
            else:
                return "#10b981", "white" # Green (Safe)
        except:
            return "transparent", "inherit"

    def update_income_table(self):
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        data = self.db.get_income(m, y)
        self.inc_table.setRowCount(0)
        
        total_m = sum(d[2] for d in data)
        self.inc_stat_total.setText(f"${total_m:,.2f}")
        self.inc_stat_avg.setText(f"${(total_m / 30):,.2f}")
        self.inc_stat_count.setText(str(len(data)))

        for i in data:
            row = self.inc_table.rowCount()
            self.inc_table.insertRow(row)
            self.inc_table.setItem(row, 0, QTableWidgetItem(i[1]))
            self.inc_table.setItem(row, 1, QTableWidgetItem(i[4]))
            self.inc_table.setItem(row, 2, QTableWidgetItem(i[3]))
            self.inc_table.setItem(row, 3, QTableWidgetItem(f"${i[2]:,.2f}"))
            
            btn_del = QPushButton("Eliminar")
            btn_del.setStyleSheet("background-color: #ef4444; font-size: 11px;")
            btn_del.clicked.connect(lambda ch, id=i[0]: self.delete_income_ui(id))
            btn_del.setVisible(self.role == "admin")
            self.inc_table.setCellWidget(row, 4, btn_del)
        self.inc_table.setColumnHidden(4, self.role != "admin")

    def update_expenses_table(self):
        query = self.search_input.text()
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        period = f"{y}-{m:02d}"
        
        if query:
            expenses = self.db.search_expenses(query)
        else:
            expenses = self.db.get_expenses()
            
        self.exp_table.setRowCount(0)
        for e in expenses:
            # Filter by period if not searching
            if not query and not e[1].startswith(period): continue
            
            # Solo mostrar 'variable' en Gastos Diarios
            if e[5] != 'variable': continue
            
            row = self.exp_table.rowCount()
            self.exp_table.insertRow(row)
            self.exp_table.setItem(row, 0, QTableWidgetItem(e[1]))
            self.exp_table.setItem(row, 1, QTableWidgetItem(e[5].capitalize()))
            self.exp_table.setItem(row, 2, QTableWidgetItem(e[2]))
            self.exp_table.setItem(row, 3, QTableWidgetItem(e[4]))
            self.exp_table.setItem(row, 4, QTableWidgetItem(f"${e[3]:,.2f}"))
            
            btn_del = QPushButton("Eliminar")
            btn_del.setStyleSheet("background-color: #ef4444; font-size: 11px; padding: 2px;")
            btn_del.clicked.connect(lambda ch, id=e[0]: self.delete_expense_ui(id))
            btn_del.setVisible(self.role == "admin")
            self.exp_table.setCellWidget(row, 5, btn_del)
        self.exp_table.setColumnHidden(5, self.role != "admin")

    def update_prov_table(self):
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        period = f"{y}-{m:02d}"
        
        # Vamos a recolectar Gastos y Deudas del periodo que sean de Proveedores
        expenses = [e for e in self.db.get_expenses() if e[1].startswith(period) and e[2] == "Carne / Proveedores"]
        debts = [d for d in self.db.get_general_debts() if d[4].startswith(period) and d[2] == "Proveedor"]
        
        # Combine
        combined = []
        
        def parse_desc(desc):
            lines = desc.split('\n')
            prov = "Desconocido"
            mercaderia = "General"
            cantidad = "-"
            detalle_pesos = "-"
            total_u = "-"
            precio_u = "-"
            
            for line in lines:
                if line.startswith("Proveedor: "):
                    prov = line.replace("Proveedor: ", "")
                elif line.startswith("Mercadería: "):
                    mercaderia = line.replace("Mercadería: ", "")
                elif line.startswith("Cantidad: "):
                    cantidad = line.replace("Cantidad: ", "")
                elif line.startswith("Detalle: "):
                    det = line.replace("Detalle: ", "")
                    if "(" in det and ")" in det:
                        cantidad = det.split("(")[0].strip()
                        detalle_pesos = det.split("(")[1].replace(")", "").strip()
                    else:
                        detalle_pesos = det
                elif line.startswith("Precio Unit.: ") or line.startswith("Precio: "):
                    pu = line.split("|")[0].replace("Precio Unit.: ", "").replace("Precio: ", "").strip()
                    precio_u = pu
                    if "Total cant:" in line or "Total:" in line:
                        total_u = line.split("|")[1].replace("Total cant:", "").replace("Total:", "").strip()
                elif line.startswith("TotalU: "):
                    total_u = line.replace("TotalU: ", "")
            
            if detalle_pesos == "-" and total_u == "-":
                detalle_pesos = desc.replace('\n', ' ')
                
            return prov, mercaderia, cantidad, detalle_pesos, total_u, precio_u

        for e in expenses:
            prov, mercaderia, cantidad, detalle_pesos, total_u, precio_u = parse_desc(e[4])
            combined.append((e[1], prov, mercaderia, cantidad, detalle_pesos, total_u, precio_u, e[3], "Pagado (Contado)", e[0], "expense"))
            
        for d in debts:
            prov, mercaderia, cantidad, detalle_pesos, total_u, precio_u = parse_desc(d[1])
            combined.append((d[4], prov, mercaderia, cantidad, detalle_pesos, total_u, precio_u, d[3], "A Pagar (Deuda)", d[0], "debt"))
        
        combined.sort(key=lambda x: x[0], reverse=True)
        
        self.prov_table.setRowCount(0)
        for c in combined:
            row = self.prov_table.rowCount()
            self.prov_table.insertRow(row)
            
            date_str = c[0]
            try:
                parts = date_str.split('-')
                if len(parts) == 3:
                    date_str = f"{parts[2]}-{parts[1]}-{parts[0][2:]}"
            except: pass
            
            self.prov_table.setItem(row, 0, QTableWidgetItem(date_str))
            self.prov_table.setItem(row, 1, QTableWidgetItem(c[1]))
            self.prov_table.setItem(row, 2, QTableWidgetItem(c[2]))
            self.prov_table.setItem(row, 3, QTableWidgetItem(c[3]))
            
            det_item = QTableWidgetItem(c[4])
            self.prov_table.setItem(row, 4, det_item)
            
            self.prov_table.setItem(row, 5, QTableWidgetItem(c[5]))
            self.prov_table.setItem(row, 6, QTableWidgetItem(c[6]))
            self.prov_table.setItem(row, 7, QTableWidgetItem(f"${c[7]:,.0f}"))
            
            item_status = QTableWidgetItem(c[8])
            if "Pagado" in c[8]:
                item_status.setForeground(Qt.darkGreen)
            else:
                item_status.setForeground(Qt.red)
            self.prov_table.setItem(row, 8, item_status)
            
            # Action buttons
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)
            
            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(24, 24)
            btn_edit.setStyleSheet("background-color: transparent; border: none; font-size: 14px;")
            btn_edit.clicked.connect(lambda ch, pid=c[9], ptype=c[10]: self.edit_prov_ui(pid, ptype))
            
            btn_del = QPushButton("❌")
            btn_del.setFixedSize(24, 24)
            btn_del.setStyleSheet("background-color: transparent; border: none; font-size: 14px;")
            btn_del.clicked.connect(lambda ch, pid=c[9], ptype=c[10]: self.delete_prov_ui(pid, ptype))
            
            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_del)
            btn_widget.setVisible(self.role == "admin")
            self.prov_table.setCellWidget(row, 9, btn_widget)
            
        self.prov_table.resizeRowsToContents()
        self.prov_table.setColumnHidden(9, self.role != "admin")

    def delete_prov_ui(self, pid, ptype):
        reply = QMessageBox.question(self, "Confirmar", "¿Desea eliminar este registro de proveedor?", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if ptype == "expense":
                self.db.delete_expense(pid)
            elif ptype == "debt":
                self.db.delete_general_debt(pid)
            self.load_all_data()

    def edit_prov_ui(self, pid, ptype):
        reply = QMessageBox.question(self, "Editar Proveedor", "¿Desea eliminar este registro y volver a cargarlo?\n\n(La edición directa requiere eliminarlo primero, por seguridad contable)", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if ptype == "expense":
                self.db.delete_expense(pid)
            elif ptype == "debt":
                self.db.delete_general_debt(pid)
            self.load_all_data()
            self.stack.setCurrentIndex(3) # Go to Proveedores tab to re-enter
            
    def generate_reports_pdf(self):
        try:
            from pdf_generator import PDFReportGenerator
            m = self.month_sel.currentIndex() + 1
            y = int(self.year_sel.currentText())
            pdf_gen = PDFReportGenerator(self.db, m, y)
            f1 = pdf_gen.generate_libro()
            f2 = pdf_gen.generate_jefe()
            QMessageBox.information(self, "Éxito", f"Reportes generados con éxito en tu Escritorio.\n\nArchivos:\n- {os.path.basename(f1)}\n- {os.path.basename(f2)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Ocurrió un error al generar los PDF: {e}")

    def delete_expense_ui(self, id):
        reply = QMessageBox.question(self, "Confirmar", "¿Desea eliminar este registro de gasto?", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_expense(id)
            self.load_all_data()

    def update_loans_table(self):
        # 1. Loan Summary Table & Dashboard Stats
        loans = self.db.get_loans()
        total_global_debt = 0
        total_global_paid = 0
        
        for l in loans:
            # l schema: (id, name, total_amount, capital, interest, category, status)
            if l[6] != 'active': continue
            row = self.loan_summary_table.rowCount()
            self.loan_summary_table.insertRow(row)
            
            capital = l[3] or 0
            interest = l[4] or 0
            total_orig = l[2] or 0
            perc = (interest / capital * 100) if capital > 0 else 0
            
            # Obtener cuánto se pagó de este préstamo específico
            all_insts = self.db.get_installments() # Podríamos filtrar esto mejor en DB, pero lo haremos aquí por ahora
            loan_insts = [x for x in all_insts if x['loan_id'] == l[0]] # No, get_installments solo devuelve pendientes
            
            # Para el "Saldo Pendiente" real, sumamos todas las cuotas de este préstamo (pagadas y no)
            # Requeriría un método get_loan_status en DB. Por ahora usemos lo que tenemos.
            # Simulemos el saldo pendiente basado en las cuotas pendientes
            pending_for_this_loan = sum(x['amount'] - (x['paid_amount'] if 'paid_amount' in x.keys() else 0.0) for x in all_insts if x['loan_id'] == l[0])
            paid_for_this_loan = total_orig - pending_for_this_loan
            
            total_global_debt += pending_for_this_loan
            total_global_paid += paid_for_this_loan
            
            self.loan_summary_table.setItem(row, 0, QTableWidgetItem(l[1]))
            self.loan_summary_table.setItem(row, 1, QTableWidgetItem(f"${capital:,.2f}"))
            self.loan_summary_table.setItem(row, 2, QTableWidgetItem(f"${interest:,.2f}"))
            self.loan_summary_table.setItem(row, 3, QTableWidgetItem(f"{perc:.1f}%"))
            
            amt_item = QTableWidgetItem(f"${pending_for_this_loan:,.2f}")
            amt_item.setForeground(Qt.red if pending_for_this_loan > 0 else Qt.darkGreen)
            amt_item.setFont(QFont("Inter", 11, QFont.Bold))
            self.loan_summary_table.setItem(row, 4, amt_item)
            
            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Eliminar Préstamo Completo")
            btn_del.setStyleSheet("background-color: #ef4444; max-width: 40px;")
            btn_del.clicked.connect(lambda ch, id=l[0]: self.delete_loan_ui(id))
            btn_del.setVisible(self.role == "admin")
            self.loan_summary_table.setCellWidget(row, 5, btn_del)

        # 🏦 ACTUALIZAR DASHBOARD SUPERIOR
        self.loan_stat_total.setText(f"${total_global_debt:,.2f}")
        total_sum = total_global_debt + total_global_paid
        progress = (total_global_paid / total_sum * 100) if total_sum > 0 else 0
        self.loan_stat_progress.setText(f"{progress:.1f}%")

        # 2. Installments Table
        insts = self.db.get_installments() # pending installments sorted by date
        self.inst_table.setRowCount(0)
        
        if insts:
            self.loan_stat_next.setText(insts[0]['due_date'])
        else:
            self.loan_stat_next.setText("Al Día")

        loans_processed = set()
        for i in insts:
            loan_id = i['loan_id']
            if loan_id in loans_processed: continue
            loans_processed.add(loan_id)
            
            row = self.inst_table.rowCount()
            self.inst_table.insertRow(row)
            
            name = str(i['name'])
            num_cuota = f"CUOTA {i['number']}/{i['total_inst']}"
            
            total_inst_count = i['total_inst'] or 1
            cap_cuota = (i['capital'] or 0) / total_inst_count
            int_cuota = (i['interest'] or 0) / total_inst_count
            perc = ((i['interest'] or 0) / (i['capital'] or 1) * 100) if (i['capital'] or 0) > 0 else 0
            
            # Calcular Deuda Restante Total de este préstamo (Suma de cuotas pendientes)
            total_debt_remaining = sum(x['amount'] - (x['paid_amount'] if 'paid_amount' in x.keys() else 0.0) for x in insts if x['loan_id'] == loan_id)
            
            self.inst_table.setItem(row, 0, QTableWidgetItem(name))
            
            prog_item = QTableWidgetItem(num_cuota)
            prog_item.setTextAlignment(Qt.AlignCenter)
            prog_item.setForeground(Qt.blue)
            self.inst_table.setItem(row, 1, prog_item)
            
            self.inst_table.setItem(row, 2, QTableWidgetItem(f"${cap_cuota:,.2f}"))
            self.inst_table.setItem(row, 3, QTableWidgetItem(f"${int_cuota:,.2f}"))
            self.inst_table.setItem(row, 4, QTableWidgetItem(f"{perc:.1f}%"))
            
            paid_cur = i['paid_amount'] if 'paid_amount' in i.keys() else 0.0
            rest_cur = i['amount'] - paid_cur
            
            amt_item = QTableWidgetItem(f"${rest_cur:,.2f}")
            amt_item.setFont(QFont("Inter", 10, QFont.Bold))
            self.inst_table.setItem(row, 5, amt_item)
            
            debt_item = QTableWidgetItem(f"${total_debt_remaining:,.2f}")
            debt_item.setForeground(Qt.red)
            debt_item.setFont(QFont("Inter", 11, QFont.Bold))
            self.inst_table.setItem(row, 6, debt_item)
            
            date_str = i['due_date']
            date_item = QTableWidgetItem(date_str)
            bg, fg = self.get_date_color_styles(date_str)
            self.inst_table.setItem(row, 7, date_item)
            
            estado = "Parcial" if i['status'] == 'partial' else "Pendiente"
            status_item = QTableWidgetItem(estado)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.inst_table.setItem(row, 8, status_item)

            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(2, 2, 2, 2)
            
            btn_pay = QPushButton("PAGAR CUOTA")
            btn_pay.setStyleSheet(f"background-color: #10b981; color: white; font-weight: bold; padding: 5px; border-radius: 4px;")
            btn_pay.clicked.connect(lambda ch, id=i['id']: self.pay_installment_dialog(id))
            btn_layout.addWidget(btn_pay)
            
            act_widget = QWidget()
            act_widget.setLayout(btn_layout)
            self.inst_table.setCellWidget(row, 9, act_widget)
            
            for col in range(9):
                item = self.inst_table.item(row, col)
                if item:
                    if bg == "#ef4444": item.setForeground(Qt.red)
                    elif bg == "#f59e0b": item.setForeground(Qt.darkYellow)
                    else: item.setForeground(Qt.darkGreen)
        self.loan_summary_table.setColumnHidden(5, self.role != "admin")
        self.inst_table.setColumnHidden(9, self.role != "admin")

    def delete_loan_ui(self, loan_id):
        reply = QMessageBox.question(self, "Confirmar", "¿Desea eliminar el préstamo y todas sus cuotas?", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_loan(loan_id)
            self.load_all_data()

    def update_checks_table(self):
        checks = self.db.get_checks()
        self.check_table.setRowCount(0)
        for c in checks:
            if c[6] == 'paid': continue
            row = self.check_table.rowCount()
            self.check_table.insertRow(row)
            self.check_table.setItem(row, 0, QTableWidgetItem(c[1]))
            self.check_table.setItem(row, 1, QTableWidgetItem(c[2]))
            self.check_table.setItem(row, 2, QTableWidgetItem(c[5]))
            self.check_table.setItem(row, 3, QTableWidgetItem(f"${c[3]:,.2f}"))
            
            date_str = c[4]
            date_item = QTableWidgetItem(date_str)
            bg, fg = self.get_date_color_styles(date_str)
            self.check_table.setItem(row, 4, date_item)
            
            btn_pay = QPushButton("✅")
            btn_pay.setToolTip("Cobrado")
            btn_pay.setStyleSheet(f"background-color: {bg}; color: {fg}; font-size: 14px; font-weight: bold;")
            btn_pay.clicked.connect(lambda ch, id=c[0]: self.pay_check_ui(id))
            btn_pay.setVisible(self.role == "admin")
            self.check_table.setCellWidget(row, 5, btn_pay)
            
            # Highlight text
            for col in range(5):
                item = self.check_table.item(row, col)
                if item:
                    if bg == "#ef4444": item.setForeground(Qt.red)
                    elif bg == "#f59e0b": item.setForeground(Qt.darkYellow)
        self.check_table.setColumnHidden(5, self.role != "admin")

    def update_debts_table(self):
        debts = [d for d in self.db.get_general_debts() if d[2] not in ['Costo Fijo', 'Inversión']]
        self.debt_table.setRowCount(0)
        for d in debts:
            row = self.debt_table.rowCount()
            self.debt_table.insertRow(row)
            self.debt_table.setItem(row, 0, QTableWidgetItem(d[1]))
            self.debt_table.setItem(row, 1, QTableWidgetItem(d[2]))
            self.debt_table.setItem(row, 2, QTableWidgetItem(f"${d[3]:,.2f}"))
            
            date_str = d[4]
            date_item = QTableWidgetItem(date_str)
            bg, fg = self.get_date_color_styles(date_str)
            self.debt_table.setItem(row, 3, date_item)
            
            btn_pay = QPushButton("💰")
            btn_pay.setToolTip("Liquidar Deuda")
            btn_pay.setStyleSheet(f"background-color: {bg}; color: {fg}; font-size: 14px; font-weight: bold;")
            btn_pay.clicked.connect(lambda ch, id=d[0]: self.pay_debt_ui(id))
            btn_pay.setVisible(self.role == "admin")
            self.debt_table.setCellWidget(row, 4, btn_pay)

            # Highlight text
            for col in range(4):
                item = self.debt_table.item(row, col)
                if item:
                    if bg == "#ef4444": item.setForeground(Qt.red)
                    elif bg == "#f59e0b": item.setForeground(Qt.darkYellow)
        self.debt_table.setColumnHidden(4, self.role != "admin")

    def update_fixed_costs_table(self):
        fcs = [d for d in self.db.get_general_debts() if d[2] == 'Costo Fijo']
        self.fix_table.setRowCount(0)
        for f in fcs:
            row = self.fix_table.rowCount()
            self.fix_table.insertRow(row)
            self.fix_table.setItem(row, 0, QTableWidgetItem(f[4])) # Vencimiento
            self.fix_table.setItem(row, 1, QTableWidgetItem(f[1])) # Nombre
            self.fix_table.setItem(row, 2, QTableWidgetItem(f"${f[3]:,.2f}"))
            
            rest = f[3] - (f[6] if f[6] else 0.0)
            self.fix_table.setItem(row, 3, QTableWidgetItem(f"${rest:,.2f}"))
            
            estado = "Parcial" if f[5] == 'partial' else "Pendiente"
            if f[5] == 'paid': estado = "Pagado"
            self.fix_table.setItem(row, 4, QTableWidgetItem(estado))

            # Borrar button for company (before it's paid)
            btn_del = QPushButton("🗑️")
            btn_del.setStyleSheet("background-color: #ef4444; color: white;")
            btn_del.clicked.connect(lambda ch, id=f[0]: self.delete_pending_fix_ui(id))
            self.fix_table.setCellWidget(row, 5, btn_del)

    def delete_pending_fix_ui(self, id):
        reply = QMessageBox.question(self, "Confirmar", "¿Desea eliminar este costo fijo pendiente?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_general_debt(id)
            self.load_all_data()
        QTimer.singleShot(1200, self.auto_check_fixed_costs)

    def add_fixed_cost_config(self):
        try:
            name = self.fix_name.text()
            cat = self.fix_cat.currentText()
            amt = float(self.fix_amount.text().replace(',', '.'))
            if not name or amt <= 0: raise ValueError
            
            m = self.month_sel.currentIndex() + 1
            y = int(self.year_sel.currentText())
            month_date = f"{y}-{m:02d}-01"
            
            self.db.add_general_debt(f"Costo Fijo: {name} ({cat})", "Costo Fijo", amt, month_date)
            self.fix_name.clear(); self.fix_amount.clear()
            self.load_all_data()
            QMessageBox.information(self, "Éxito", "El Costo Fijo fue enviado a la Tesorería como pendiente de pago.")
        except: QMessageBox.warning(self, "Error", "Datos inválidos")

    def auto_check_fixed_costs(self):
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        period = f"{y}-{m:02d}"
        
        current_fcs = [d for d in self.db.get_general_debts() if d[2] == 'Costo Fijo' and d[4].startswith(period)]
        if not current_fcs:
            prev_m = m - 1 if m > 1 else 12
            prev_y = y if m > 1 else y - 1
            prev_period = f"{prev_y}-{prev_m:02d}"
            prev_fcs = [d for d in self.db.get_general_debts() if d[2] == 'Costo Fijo' and d[4].startswith(prev_period)]
            if prev_fcs:
                QTimer.singleShot(2000, lambda: ToastNotification(self, "Tienes costos fijos del mes pasado. Recuerda cargarlos este mes.", "📌", 7000))


    def apply_monthly_fixed_costs(self):
        m = self.month_sel.currentIndex() + 1
        y = int(self.year_sel.currentText())
        period = f"{y}-{m:02d}"
        
        current_fcs = [d for d in self.db.get_general_debts() if d[2] == 'Costo Fijo' and d[4].startswith(period)]
        if current_fcs:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Aviso de Duplicidad")
            msg.setText(f"Ya existen costos fijos cargados para {self.month_sel.currentText()} {y}.")
            msg.setInformativeText("¿Qué desea hacer?")
            btn_replace = msg.addButton("Reemplazar Todo", QMessageBox.ActionRole)
            btn_add = msg.addButton("Agregar (Duplicar)", QMessageBox.ActionRole)
            btn_cancel = msg.addButton("Cancelar", QMessageBox.RejectRole)
            
            msg.exec_()
            
            if msg.clickedButton() == btn_cancel: return
            if msg.clickedButton() == btn_replace:
                for f in current_fcs:
                    self.db.delete_general_debt(f[0])
            
        prev_m = m - 1 if m > 1 else 12
        prev_y = y if m > 1 else y - 1
        prev_period = f"{prev_y}-{prev_m:02d}"
        
        month_date = f"{y}-{m:02d}-01"
        added = False
        
        # Primero buscar en general_debts (el nuevo metodo)
        prev_fcs = [d for d in self.db.get_general_debts() if d[2] == 'Costo Fijo' and d[4].startswith(prev_period)]
        if prev_fcs:
            for f in prev_fcs:
                self.db.add_general_debt(f[1], "Costo Fijo", f[3], month_date)
            added = True
        else:
            # Fallback a expenses por compatibilidad hacia atrás
            prev_fcs_exp = [e for e in self.db.get_expenses() if e[5] == 'fijo' and e[1].startswith(prev_period)]
            if prev_fcs_exp:
                for f in prev_fcs_exp:
                    name = f[4].replace("Costo Fijo: ", "")
                    self.db.add_general_debt(f"Costo Fijo: {name} ({f[2]})", "Costo Fijo", f[3], month_date)
                added = True
                
        if added:
            self.load_all_data()
            QMessageBox.information(self, "Éxito", "Se han precargado los costos fijos del mes anterior y enviado a Tesorería.")
        else:
            QMessageBox.information(self, "Aviso", "No se encontraron costos fijos registrados en el mes anterior.")

    # --- MÉTODOS NIVEL 4 (INVENTARIO Y AUDITORÍA) ---
    

    def init_audit_pro_tab(self):
        self.tab_audit = QWidget()
        layout = QVBoxLayout(self.tab_audit)
        layout.addWidget(QLabel("🏢 AUDITORÍA DE SISTEMA AVANZADA - LOGS EN TIEMPO REAL"))
        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(5)
        self.audit_table.setHorizontalHeaderLabels(["Timestamp", "Usuario/Empresa", "Acción", "Tabla", "Detalles"])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.audit_table)
        self.stack.addWidget(self.tab_audit)

    def update_audit_table(self):
        if not hasattr(self, 'audit_table'): return
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM system_audit ORDER BY timestamp DESC LIMIT 100")
            data = cursor.fetchall()
            self.audit_table.setRowCount(0)
            for d in data:
                row = self.audit_table.rowCount()
                self.audit_table.insertRow(row)
                self.audit_table.setItem(row, 0, QTableWidgetItem(d['timestamp']))
                self.audit_table.setItem(row, 1, QTableWidgetItem(d['user']))
                self.audit_table.setItem(row, 2, QTableWidgetItem(d['action']))
                self.audit_table.setItem(row, 3, QTableWidgetItem(d['table_affected']))
                self.audit_table.setItem(row, 4, QTableWidgetItem(d['details']))

    # --- ADMIN LEVEL 4 TOOLS ---
    def export_matrix_csv(self):
        import csv
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Matriz de Rendimiento", "Matriz_Rendimiento.csv", "CSV (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Empresa", "Ingreso", "Balance", "Estado"])
                    for row in range(self.performance_table.rowCount()):
                        emp = self.performance_table.item(row, 0).text()
                        ing = self.performance_table.item(row, 1).text()
                        bal = self.performance_table.item(row, 2).text()
                        est = self.performance_table.item(row, 3).text()
                        writer.writerow([emp, ing, bal, est])
                QMessageBox.information(self, "Éxito", "Matriz exportada correctamente.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo exportar: {e}")

    def show_transfer_dialog(self):
        db_files = [f for f in glob.glob("*.db") if not f.startswith("backup_") and f != "database.db"]
        if len(db_files) < 2:
            QMessageBox.warning(self, "Error", "Se necesitan al menos 2 empresas para realizar transferencias.")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Préstamo / Transferencia entre Sucursales")
        dialog.setStyleSheet(STYLE_SHEET)
        layout = QFormLayout(dialog)
        
        cb_origen = QComboBox()
        cb_destino = QComboBox()
        for f in db_files:
            name = f.replace(".db", "").upper()
            cb_origen.addItem(name, f)
            cb_destino.addItem(name, f)
            
        amt_input = QLineEdit()
        desc_input = QLineEdit("Préstamo interno inter-sucursal")
        
        layout.addRow("Origen (Envía):", cb_origen)
        layout.addRow("Destino (Recibe):", cb_destino)
        layout.addRow("Monto ($):", amt_input)
        layout.addRow("Descripción:", desc_input)
        
        btn_save = QPushButton("Ejecutar Transferencia")
        btn_save.setStyleSheet("background-color: #6366f1; font-weight: bold; padding: 10px;")
        btn_save.clicked.connect(dialog.accept)
        layout.addRow(btn_save)
        
        if dialog.exec_() == QDialog.Accepted:
            if cb_origen.currentText() == cb_destino.currentText():
                QMessageBox.warning(self, "Error", "El Origen y Destino deben ser distintos.")
                return
            try:
                amount = float(amt_input.text().replace(',', '.'))
                if amount <= 0: raise ValueError
                
                db_o = Database(cb_origen.currentData())
                db_d = Database(cb_destino.currentData())
                date_str = datetime.date.today().isoformat()
                
                # Egresar del Origen (Como costo/préstamo)
                db_o.add_expense(date_str, 'Préstamo Interno', amount, f"Transferencia hacia {cb_destino.currentText()} - {desc_input.text()}", 'fixed')
                
                # Ingresar al Destino
                db_d.add_income(date_str, amount, f"Transferencia desde {cb_origen.currentText()} - {desc_input.text()}", 'Préstamo Interno')
                
                QMessageBox.information(self, "Éxito", "¡Transferencia procesada correctamente!\n\nAmbas bases de datos han sido actualizadas.")
                self.load_all_data()
            except Exception as e:
                QMessageBox.warning(self, "Error", "Ocurrió un error. Verifique que el monto sea un número válido.")

    def close_month_global(self):
        reply = QMessageBox.question(self, "Confirmar Cierre", "¿Guardar estado actual de todas las empresas como Cierre Histórico en la base central (database.db)?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            m = self.month_sel.currentIndex() + 1
            y = int(self.year_sel.currentText())
            try:
                import sqlite3
                conn = sqlite3.connect("database.db")
                c = conn.cursor()
                c.execute('''CREATE TABLE IF NOT EXISTS global_history (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                year INTEGER, month INTEGER, company TEXT,
                                income REAL, balance REAL, status TEXT, date_closed TEXT
                             )''')
                
                c.execute("SELECT COUNT(*) FROM global_history WHERE year=? AND month=?", (y, m))
                if c.fetchone()[0] > 0:
                    reply_override = QMessageBox.question(self, "Aviso", f"Ya existe un cierre para el mes {m}/{y}. ¿Desea sobrescribirlo?", QMessageBox.Yes | QMessageBox.No)
                    if reply_override != QMessageBox.Yes:
                        conn.close()
                        return
                    c.execute("DELETE FROM global_history WHERE year=? AND month=?", (y, m))
                
                date_closed = datetime.date.today().isoformat()
                for row in range(self.performance_table.rowCount()):
                    emp = self.performance_table.item(row, 0).text()
                    ing_str = self.performance_table.item(row, 1).text().replace('$', '').replace(',', '')
                    bal_str = self.performance_table.item(row, 2).text().replace('$', '').replace(',', '')
                    est = self.performance_table.item(row, 3).text()
                    
                    c.execute("INSERT INTO global_history (year, month, company, income, balance, status, date_closed) VALUES (?,?,?,?,?,?,?)",
                              (y, m, emp, float(ing_str), float(bal_str), est, date_closed))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Éxito", f"¡Cierre del mes {m:02d}/{y} guardado exitosamente en la base de datos central!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Fallo al guardar cierre: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Flag to control if we should restart the login process
    restart_login = True
    
    while restart_login:
        login_dialog = LoginDialog()
        if login_dialog.exec_() == QDialog.Accepted:
            main_window = ButcheryAccounting(role=login_dialog.user_role, company=login_dialog.company_name)
            main_window.show()
            app.exec_() # This call blocks until main_window is closed
            
            restart_login = main_window.switch_requested # Decide whether to show login again
        else:
            restart_login = False # Login dialog was cancelled, exit application
            
    sys.exit(0) # Ensure a clean exit
