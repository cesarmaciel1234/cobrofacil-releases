from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from src.contabilidad.shared_globals import *

class VistaAsientosMixin:
    def _build_tab_asientos(self):
        lay, _ = self._page()
        
        lay.addWidget(section_title("📝  Asientos Contables"))
        
        # Toolbar
        toolbar = QHBoxLayout()
        btn_balance = btn_primary("📊 Balance de Comprobación")
        btn_balance.clicked.connect(self._mostrar_balance_comprobacion)
        btn_balance_gen = btn_primary("🏛️ Balance General")
        btn_balance_gen.clicked.connect(self._mostrar_balance_general)
        btn_py = btn_primary("📈 Estado de Resultados")
        btn_py.clicked.connect(self._mostrar_estado_resultados)
        
        toolbar.addWidget(btn_balance)
        toolbar.addWidget(btn_balance_gen)
        toolbar.addWidget(btn_py)
        toolbar.addStretch()
        lay.addLayout(toolbar)
        
        lay.addSpacing(15)
        
        # Tabla de asientos
        self._tbl_asientos = build_table(["Número", "Fecha", "Tipo", "Descripción", "Estado", "Usuario"])
        lay.addWidget(self._tbl_asientos)
        lay.addStretch()
    
    def _load_asientos(self):
        if not self._db:
            return
        
        try:
            if self._db.is_enterprise_mode():
                from datetime import date
                desde = date.today().replace(day=1)
                hasta = date.today()
                
                mayor = self._db.get_mayor_general(desde=desde, hasta=hasta)
                
                self._tbl_asientos.setRowCount(0)
                for fila in mayor:
                    r = self._tbl_asientos.rowCount()
                    self._tbl_asientos.insertRow(r)
                    
                    vals = [
                        fila.get('numero', ''),
                        fila.get('fecha', ''),
                        fila.get('tipo', ''),
                        fila.get('descripcion', ''),
                        fila.get('estado', ''),
                        fila.get('usuario', '')
                    ]
                    
                    for c, v in enumerate(vals):
                        item = QTableWidgetItem(str(v))
                        self._tbl_asientos.setItem(r, c, item)
            else:
                QMessageBox.warning(self, "Modo Enterprise", 
                    "El modo enterprise no está activado.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando asientos: {e}")
    
    def _mostrar_balance_comprobacion(self):
        if not self._db or not self._db.is_enterprise_mode():
            QMessageBox.warning(self, "Modo Enterprise", "El modo enterprise no está activado.")
            return
        
        try:
            from datetime import date
            fecha = date.today()
            balance = self._db.get_balance_general(fecha)
            
            msg = f"Balance de Comprobación al {fecha}\n\n"
            msg += f"Total Debe: ${balance.get('total_debe', 0):,.2f}\n"
            msg += f"Total Haber: ${balance.get('total_haber', 0):,.2f}\n"
            msg += f"Cuadra: {'Sí' if balance.get('cuadra', False) else 'No'}"
            
            QMessageBox.information(self, "Balance de Comprobación", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {e}")
    
    def _mostrar_balance_general(self):
        if not self._db or not self._db.is_enterprise_mode():
            QMessageBox.warning(self, "Modo Enterprise", "El modo enterprise no está activado.")
            return
        
        try:
            from datetime import date
            fecha = date.today()
            balance = self._db.get_balance_general(fecha)
            
            msg = f"Balance General al {fecha}\n\n"
            msg += f"Total Activos: ${balance.get('total_activos', 0):,.2f}\n"
            msg += f"Total Pasivos: ${balance.get('total_pasivos', 0):,.2f}\n"
            msg += f"Total Patrimonio: ${balance.get('total_patrimonio', 0):,.2f}\n"
            msg += f"Cuadra: {'Sí' if balance.get('cuadra', False) else 'No'}"
            
            QMessageBox.information(self, "Balance General", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {e}")
    
    def _mostrar_estado_resultados(self):
        if not self._db or not self._db.is_enterprise_mode():
            QMessageBox.warning(self, "Modo Enterprise", "El modo enterprise no está activado.")
            return
        
        try:
            from datetime import date
            desde = date.today().replace(day=1)
            hasta = date.today()
            
            er = self._db.get_estado_resultados(desde, hasta)
            
            msg = f"Estado de Resultados ({desde} a {hasta})\n\n"
            msg += f"Total Ingresos: ${er.get('total_ingresos', 0):,.2f}\n"
            msg += f"Total Gastos: ${er.get('total_gastos', 0):,.2f}\n"
            msg += f"Resultado Neto: ${er.get('resultado_neto', 0):,.2f}"
            
            QMessageBox.information(self, "Estado de Resultados", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {e}")
