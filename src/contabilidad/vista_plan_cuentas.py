from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from src.contabilidad.shared_globals import *

class VistaPlanCuentasMixin:
    def _build_tab_plan_cuentas(self):
        lay, _ = self._page()
        
        lay.addWidget(section_title("📑  Plan de Cuentas Contable"))
        
        # Toolbar
        toolbar = QHBoxLayout()
        btn_cargar = btn_primary("📥 Cargar Plan por Defecto")
        btn_cargar.clicked.connect(self._cargar_plan_cuentas_defecto)
        toolbar.addWidget(btn_cargar)
        toolbar.addStretch()
        lay.addLayout(toolbar)
        
        lay.addSpacing(15)
        
        # Tabla de cuentas
        self._tbl_plan_cuentas = build_table(["Código", "Nombre", "Tipo", "Nivel", "Padre"])
        lay.addWidget(self._tbl_plan_cuentas)
        lay.addStretch()
    
    def _load_plan_cuentas(self):
        if not self._db:
            return
        
        try:
            if self._db.is_enterprise_mode():
                cuentas = self._db.get_plan_cuentas()
                self._tbl_plan_cuentas.setRowCount(0)
                
                for cuenta in cuentas:
                    r = self._tbl_plan_cuentas.rowCount()
                    self._tbl_plan_cuentas.insertRow(r)
                    
                    vals = [
                        cuenta.get('codigo', ''),
                        cuenta.get('nombre', ''),
                        cuenta.get('tipo', ''),
                        cuenta.get('nivel', ''),
                        cuenta.get('padre', '')
                    ]
                    
                    for c, v in enumerate(vals):
                        item = QTableWidgetItem(str(v))
                        self._tbl_plan_cuentas.setItem(r, c, item)
            else:
                QMessageBox.warning(self, "Modo Enterprise", 
                    "El modo enterprise no está activado. Active los motores contables para usar el plan de cuentas.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando plan de cuentas: {e}")
    
    def _cargar_plan_cuentas_defecto(self):
        if not self._db:
            return
        
        try:
            if self._db.is_enterprise_mode():
                self._db.cargar_plan_cuentas_defecto()
                QMessageBox.information(self, "Éxito", "Plan de cuentas por defecto cargado")
                self._load_plan_cuentas()
            else:
                QMessageBox.warning(self, "Modo Enterprise", 
                    "El modo enterprise no está activado.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando plan: {e}")
