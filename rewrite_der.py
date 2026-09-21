import codecs

path = 'src/admin/nexus_admin/vistas/componentes/nexus_panel_der.py'
with codecs.open(path, 'r', 'utf-8', errors='ignore') as f:
    der = f.read()

# I am completely redesigning how _cargar_siguiente_pagina and the EN VIVO tab works
replacement_imports = '''import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFrame, QMessageBox, QFileDialog, QStackedWidget,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from datetime import datetime
from src.base_de_datos.database import db_manager

class CyberFeedItem(QFrame):
    def __init__(self, pc, fecha, tipo, usuario, obs):
        super().__init__()
        self.setStyleSheet("""
            CyberFeedItem {
                background-color: #0F172A; 
                border: 1px solid #1E293B; 
                border-radius: 8px; 
                margin-bottom: 5px;
            }
            CyberFeedItem:hover {
                background-color: #1E293B;
                border: 1px solid #38BDF8;
            }
        """)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)
        
        # TITLE ROW
        t_lay = QHBoxLayout()
        t_lay.setContentsMargins(0,0,0,0)
        
        icon = "\U0001F4DD" # memo
        color = "#38BDF8"
        if "SEGURIDAD" in tipo.upper() or "ALERTA" in tipo.upper():
            icon = "\U0001F6A8" # sirena
            color = "#EF4444"
        elif "INTERVENCION" in tipo.upper():
            icon = "\U0001F527" # llave inglesa
            color = "#F59E0B"
        elif "APERTURA" in tipo.upper():
            icon = "\U0001F511" # llave
            color = "#8B5CF6"
        elif "CIERRE" in tipo.upper():
            icon = "\U0001F3C1" # bandera
            color = "#10B981"
        elif "VENTA" in tipo.upper():
            icon = "\U0001F4B5" # billete
            color = "#10B981"
            
        lbl_title = QLabel(f"<b><span style='color: {color}; font-size: 14px;'>{icon} [{pc}] {tipo}</span></b>")
        lbl_title.setTextFormat(Qt.TextFormat.RichText)
        
        try:
            time_str = str(fecha)[5:16]
        except:
            time_str = str(fecha)
            
        lbl_time = QLabel(f"<span style='color: #64748B; font-size: 11px;'>{time_str}</span>")
        lbl_time.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        t_lay.addWidget(lbl_title, 1)
        t_lay.addWidget(lbl_time)
        
        # DESCRIPTION ROW
        lbl_desc = QLabel(f"<span style='color: #94A3B8; font-size: 12px; font-style: italic;'><b>Usuario:</b> {usuario} &nbsp;//&nbsp; <b>Detalle:</b> {obs}</span>")
        lbl_desc.setWordWrap(True)
        lbl_desc.setTextFormat(Qt.TextFormat.RichText)
        lbl_desc.setContentsMargins(25, 0, 0, 0) # Identacion
        
        lay.addLayout(t_lay)
        lay.addWidget(lbl_desc)

class NexusPanelDer(QFrame):
'''

der = der.replace('import os\nfrom PyQt6.QtWidgets import (\n    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,\n    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,\n    QAbstractItemView, QFrame, QMessageBox, QFileDialog, QStackedWidget\n)\nfrom PyQt6.QtCore import Qt\nfrom PyQt6.QtGui import QColor, QFont\nfrom datetime import datetime\nfrom src.base_de_datos.database import db_manager\n\nclass NexusPanelDer(QFrame):', replacement_imports)

# Replace table definition with feed container
old_table_def = '''        self.tabla_eventos = QTableWidget()
        self.tabla_eventos.setColumnCount(5)
        self.tabla_eventos.setHorizontalHeaderLabels(["\U0001F4BB PC", "\U0001F4C5 FECHA / HORA", "\U0001F6A8 EVENTO DE AUDITORA", "\U0001F464 USUARIO", "\U0001F4DD DETALLE / OBSERVACIONES"])
        self.tabla_eventos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_eventos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_eventos.verticalHeader().setVisible(False)
        header = self.tabla_eventos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tabla_eventos.verticalScrollBar().valueChanged.connect(self._al_hacer_scroll)
        
        layout_inf.addWidget(self.tabla_eventos)'''

new_feed_def = '''        self.scroll_eventos = QScrollArea()
        self.scroll_eventos.setWidgetResizable(True)
        self.scroll_eventos.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#feed_container { background: transparent; }")
        
        self.feed_container = QWidget()
        self.feed_container.setObjectName("feed_container")
        self.feed_layout = QVBoxLayout(self.feed_container)
        self.feed_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.feed_layout.setContentsMargins(5, 5, 5, 5)
        
        self.scroll_eventos.setWidget(self.feed_container)
        self.scroll_eventos.verticalScrollBar().valueChanged.connect(self._al_hacer_scroll)
        
        layout_inf.addWidget(self.scroll_eventos)'''

# Sometimes there are strange chars, let's just do a manual find and replace that avoids exact match
import re
der = re.sub(r'self\.tabla_eventos = QTableWidget\(\).*?layout_inf\.addWidget\(self\.tabla_eventos\)', new_feed_def, der, flags=re.DOTALL)


# Replace setRowCount(0)
der = re.sub(r'self\.tabla_eventos\.setRowCount\(0\)', 
'''while self.feed_layout.count():
            item = self.feed_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()''', der)


# Replace _cargar_siguiente_pagina
old_cargar = '''    def _cargar_siguiente_pagina(self):
        current_rows = self.tabla_eventos.rowCount()'''
        
new_cargar = '''    def _cargar_siguiente_pagina(self):
        current_rows = self.feed_layout.count()
        if current_rows >= self.total_logs_count:
            return
            
        q_paginated = f"{self.active_query} LIMIT 50 OFFSET {self.offset}"
        try:
            from src.cerebro_global.nexus_cerebro import CerebroNexus
            page_logs = CerebroNexus.ejecutar_query(q_paginated, tuple(self.active_params)) or []
        except Exception as e:
            print(f"Error cargando pagina de auditoria: {e}")
            return
            
        if not page_logs:
            return

        for r in page_logs:
            tipo = str(r['tipo']).upper()
            obs = str(r['observaciones'] or '')
            usuario = str(r['usuario'] or '').upper()
            try:
                c_id = int(r['caja_id']) if r['caja_id'] is not None else 1
            except:
                c_id = 1
            pc_name = f"CAJA-{c_id}"
            
            feed_item = CyberFeedItem(pc_name, r['fecha'], tipo, usuario, obs)
            self.feed_layout.addWidget(feed_item)

        self.offset += 50
        
    def _al_hacer_scroll_old(self): pass'''

der = re.sub(r'def _cargar_siguiente_pagina\(self\):.*?self\.offset \+= 50', new_cargar, der, flags=re.DOTALL)

# Fix scroll logic
der = der.replace('bar = self.tabla_eventos.verticalScrollBar()', 'bar = self.scroll_eventos.verticalScrollBar()')

# Theme update fix
der = re.sub(r'if hasattr\(self, \'tabla_eventos\'\):.*?self\.tabla_eventos\.setStyleSheet\(table_css\)', '', der, flags=re.DOTALL)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(der)
