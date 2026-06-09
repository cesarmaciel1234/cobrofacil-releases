from src.utils.theme_manager import theme_manager
import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QTabWidget, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

# Imports pesados movidos al inicio para evitar crashes de Qt
import matplotlib
try:
    matplotlib.use("Qt5Agg")
except: pass

class Admin4Gastos(QWidget):
    """
    ADMIN PASO 7: CONTROL DE GASTOS (DORMIDO)
    Módulo para registrar gastos diarios (variables) y costos fijos.
    Ahora integrado con el ERP Contable para sincronización nativa,
    usando carga perezosa para inicio instantáneo.
    """
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.is_loaded = False
        self.erp_externo = None
        
        self.setStyleSheet(" font-family: 'Segoe UI';")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- PANTALLA DE CARGA (MÓDULO DORMIDO) ---
        self.loading_screen = QFrame()
        ll = QVBoxLayout(self.loading_screen)
        self.lbl_loading = QLabel("💤 Control de Gastos Dormido\nIniciando módulos...")
        self.lbl_loading.setStyleSheet(" font-size: 22px; font-weight: bold;")
        self.lbl_loading.setAlignment(Qt.AlignCenter)
        ll.addWidget(self.lbl_loading)
        
        self.main_layout.addWidget(self.loading_screen)

    def showEvent(self, event):
        super().showEvent(event)
        # Lazy Loading
        if not self.is_loaded:
            self.is_loaded = True
            QApplication.processEvents()
            QTimer.singleShot(50, self.load_heavy_modules)
            
    def cargar_datos(self):
        # Método requerido por main_window.py (Dummy porque carga en lazy load)
        pass

    def load_heavy_modules(self):
        try:
            self.lbl_loading.setText("🔌 Conectando con la contabilidad madre...")
            QApplication.processEvents()
            
            ext_path = r"C:\Users\cesar\OneDrive\Desktop\proyecto enero\negocio contable"
            if os.path.exists(ext_path):
                if ext_path not in sys.path:
                    sys.path.insert(0, ext_path)
                    
                original_cwd = os.getcwd()
                import importlib.util
                
                # ERP
                os.chdir(ext_path)
                
                db_file = os.path.join(ext_path, "database.py")
                spec_db = importlib.util.spec_from_file_location("ext_db", db_file)
                ext_db = importlib.util.module_from_spec(spec_db)
                sys.modules["ext_db"] = ext_db
                spec_db.loader.exec_module(ext_db)
                
                main_file = os.path.join(ext_path, "main.py")
                spec_main = importlib.util.spec_from_file_location("contabilidad_externa", main_file)
                contabilidad_main = importlib.util.module_from_spec(spec_main)
                sys.modules["contabilidad_externa"] = contabilidad_main
                
                old_db = sys.modules.get("database")
                sys.modules["database"] = ext_db
                
                spec_main.loader.exec_module(contabilidad_main)
                
                if old_db: sys.modules["database"] = old_db
                else: del sys.modules["database"]
                
                # Mocks de seguridad anti-bloqueo
                class DummyMsgBox:
                    @staticmethod
                    def warning(*args): pass
                    @staticmethod
                    def information(*args): pass
                    @staticmethod
                    def critical(*args): pass
                
                from PyQt5.QtCore import QTimer as RealQTimer
                contabilidad_main.QMessageBox = DummyMsgBox
                contabilidad_main.QTimer = RealQTimer
                
                company_path = os.path.join(original_cwd, "punpro")
                self.erp_externo = contabilidad_main.ButcheryAccounting(role="admin", company=company_path)
                os.chdir(original_cwd)

            self.lbl_loading.setText("✨ Renderizando interfaz...")
            QApplication.processEvents()
            self.build_final_ui()
            
            self.loading_screen.deleteLater()
            
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.lbl_loading.setText(f"❌ Error al cargar módulo:\n{str(e)}")
            self.lbl_loading.setStyleSheet(" font-size: 16px;")
            try:
                with open("error_gastos.txt", "w") as f:
                    f.write(error_msg)
            except: pass

    def build_final_ui(self):
        # --- HEADER ---
        header = QFrame()
        header.setStyleSheet(" border-bottom: 2px solid #ef4444;")
        header.setFixedHeight(80)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(25, 0, 25, 0)
        
        btn_back = QPushButton("🔙 VOLVER")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                  font-weight: 800; border-radius: 10px; 
                padding: 10px 25px; border: 1px solid #ef4444; font-size: 11px; letter-spacing: 1px;
            }
            QPushButton:hover {  color: white; }
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)
        hl.addWidget(btn_back)
        
        hl.addSpacing(20)
        lbl_title = QLabel("💸 CONTROL DE GASTOS <span style=''>2026</span>")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: 900;  letter-spacing: 1px;")
        hl.addWidget(lbl_title)
        hl.addStretch()
        self.main_layout.addWidget(header)
        
        # --- TABS ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none;  }
            QTabBar::tab {   padding: 12px 20px; font-weight: bold; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
            QTabBar::tab:selected {  color: white; }
            QTabBar::tab:hover:!selected {  }
        """)
        
        if self.erp_externo:
            try:
                import styles as ext_styles
                extra_style = ext_styles.STYLE_SHEET
            except:
                extra_style = "QFrame#Card {  border-radius: 12px; }"

            def add_ext_tab(ext_widget, name):
                if ext_widget:
                    ext_widget.setVisible(True)
                    container = QWidget()
                    container.setStyleSheet(extra_style)
                    cl = QVBoxLayout(container)
                    cl.setContentsMargins(0,0,0,0)
                    cl.addWidget(ext_widget)
                    self.tabs.addTab(container, name)

            # Extraemos las dos pestañas clave de la contabilidad madre
            add_ext_tab(getattr(self.erp_externo, 'tab_expenses', None), "📉 Gastos Diarios (Variables)")
            add_ext_tab(getattr(self.erp_externo, 'tab_fixed_costs', None), "📌 Costos Fijos")
        
        self.main_layout.addWidget(self.tabs)
