import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QLineEdit, QFormLayout, QDialog, QMessageBox, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

try:
    from src.database import db_manager
except ImportError:
    from database import db_manager

class Admin11Proveedores(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        self.setStyleSheet("background-color: #f8fafc; font-family: 'Segoe UI';")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("background: white; border-bottom: 1px solid #e2e8f0;")
        header.setFixedHeight(70)
        hl = QHBoxLayout(header)
        btn_back = QPushButton("🔙 VOLVER")
        btn_back.setStyleSheet("background: #f1f5f9; font-weight: bold; border-radius: 10px; padding: 10px 20px;")
        btn_back.clicked.connect(self.request_dashboard.emit)
        hl.addWidget(btn_back)
        hl.addWidget(QLabel("🚚 GESTIÓN DE COMPRAS Y PROVEEDORES", styleSheet="font-size: 18px; font-weight: 900; color: #0f172a;"))
        hl.addStretch()
        
        btn_new = QPushButton("+ NUEVA ORDEN DE COMPRA")
        btn_new.setStyleSheet("background: #6366f1; color: white; font-weight: bold; border-radius: 10px; padding: 10px 20px;")
        btn_new.clicked.connect(self.abrir_dialogo_compra)
        hl.addWidget(btn_new)
        self.main_layout.addWidget(header)
        
        # Content
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(30, 30, 30, 30)
        cl.setSpacing(20)
        
        # Stats Row
        stats_row = QHBoxLayout()
        self.stat_compras = self.create_stat_card("COMPRAS MES", "$ 0.00", "#6366f1")
        self.stat_pendientes = self.create_stat_card("PENDIENTES PAGO", "$ 0.00", "#f43f5e")
        stats_row.addWidget(self.stat_compras)
        stats_row.addWidget(self.stat_pendientes)
        cl.addLayout(stats_row)
        
        # Table
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Proveedor", "Mercadería", "Cant.", "Precio U.", "Total", "Estado"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setStyleSheet("""
            QTableWidget { background: white; border-radius: 15px; border: 1px solid #e2e8f0; gridline-color: #f1f5f9; }
            QHeaderView::section { background: #f8fafc; padding: 10px; font-weight: bold; border: none; border-bottom: 1px solid #e2e8f0; }
        """)
        cl.addWidget(self.tabla)
        
        self.main_layout.addWidget(content)

    def create_stat_card(self, title, val, color):
        card = QFrame()
        card.setStyleSheet(f"background: white; border-radius: 15px; border-left: 5px solid {color}; border: 1px solid #e2e8f0;")
        l = QVBoxLayout(card)
        l.addWidget(QLabel(title, styleSheet="color: #64748b; font-size: 11px; font-weight: bold;"))
        lbl_val = QLabel(val)
        lbl_val.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: 900;")
        l.addWidget(lbl_val)
        card.val_label = lbl_val
        return card

    def cargar_datos(self):
        # Asegurar columna 'status' en tabla 'gastos' si no existe
        def add_col_safe(table, col, type):
            try:
                res = db_manager.execute_query(f"PRAGMA table_info({table})")
                cols = [c[1] for c in res] if res else []
                if col not in cols:
                    db_manager.execute_non_query(f"ALTER TABLE {table} ADD COLUMN {col} {type}")
            except: pass
            
        add_col_safe('gastos', 'status', "TEXT DEFAULT 'Pagado'")
        
        # En el proyecto PunPro real, los proveedores se guardan en la tabla 'gastos' con categoría 'Mercadería'
        query = "SELECT fecha, descripcion, monto, status FROM gastos WHERE categoria = 'Mercadería / Stock' ORDER BY fecha DESC LIMIT 50"
        res = db_manager.execute_query(query)
        if res is None: res = [] # Prevenir TypeError
        
        self.tabla.setRowCount(0)
        total_mes = 0
        total_deuda = 0
        
        for r in res:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(str(r['fecha'])))
            self.tabla.setItem(row, 1, QTableWidgetItem("Proveedor General")) 
            self.tabla.setItem(row, 2, QTableWidgetItem(r['descripcion']))
            self.tabla.setItem(row, 5, QTableWidgetItem(f"$ {r['monto']:,.2f}"))
            
            status = r['status'] if 'status' in r else "Pagado"
            it_status = QTableWidgetItem(status)
            if status == "Pendiente": 
                it_status.setForeground(QColor("#f43f5e"))
                total_deuda += r['monto']
            else: 
                it_status.setForeground(QColor("#10b981"))
            self.tabla.setItem(row, 6, it_status)
            
            total_mes += r['monto']
            
        self.stat_compras.val_label.setText(f"$ {total_mes:,.2f}")
        self.stat_pendientes.val_label.setText(f"$ {total_deuda:,.2f}")

    def abrir_dialogo_compra(self, ai_data=None):
        dlg = QDialog(self)
        dlg.setWindowTitle("Nueva Orden de Compra")
        dlg.setFixedWidth(400)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        
        cb_prov = QComboBox()
        cb_prov.addItems(["Systel S.A.", "Distribuidora Carne", "Frigorífico Central", "Otros"])
        
        txt_desc = QLineEdit()
        txt_amount = QLineEdit()
        
        if ai_data:
            txt_desc.setText(ai_data.get('details', ''))
            txt_amount.setText(str(ai_data.get('amount', '')))
            
        form.addRow("Proveedor:", cb_prov)
        form.addRow("Detalle / PLUs:", txt_desc)
        form.addRow("Importe Total $:", txt_amount)
        layout.addLayout(form)
        
        btn_save = QPushButton("REGISTRAR COMPRA")
        btn_save.setStyleSheet("background: #10b981; color: white; font-weight: bold; padding: 10px;")
        btn_save.clicked.connect(lambda: self.guardar_compra(dlg, cb_prov.currentText(), txt_desc.text(), txt_amount.text()))
        layout.addWidget(btn_save)
        
        dlg.exec_()

    def guardar_compra(self, dlg, prov, desc, amount):
        try:
            val = float(amount)
            # Guardar en la base de datos de PunPro
            query = "INSERT INTO gastos (fecha, categoria, descripcion, monto, status, usuario) VALUES (date('now'), 'Mercadería / Stock', ?, ?, 'Pendiente', 'admin')"
            db_manager.execute_non_query(query, (f"{prov}: {desc}", val))
            QMessageBox.information(self, "Éxito", "Orden de compra registrada y enviada a Contabilidad.")
            dlg.accept()
            self.cargar_datos()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar: {e}")

    def auto_import_ai(self, list_of_items):
        """Metodo Nivel 5 para recibir datos de la IA Boss."""
        summary = "Pedido sugerido por IA: " + ", ".join(list_of_items)
        self.abrir_dialogo_compra({'details': summary, 'amount': 0})
