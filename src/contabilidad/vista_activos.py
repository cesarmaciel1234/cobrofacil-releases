from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from src.contabilidad.shared_globals import *

class VistaActivosMixin:
    def _build_tab_activos(self):
        lay, _ = self._page()
        
        lay.addWidget(section_title("🏢  Activos Fijos"))
        
        # Toolbar
        toolbar = QHBoxLayout()
        btn_nuevo = btn_primary("➕ Nuevo Activo")
        btn_nuevo.clicked.connect(self._nuevo_activo)
        btn_depreciar = btn_primary("📉 Calcular Depreciación")
        btn_depreciar.clicked.connect(self._calcular_depreciacion)
        btn_reporte = btn_primary("📊 Reporte Activos")
        btn_reporte.clicked.connect(self._reporte_activos)
        
        toolbar.addWidget(btn_nuevo)
        toolbar.addWidget(btn_depreciar)
        toolbar.addWidget(btn_reporte)
        toolbar.addStretch()
        lay.addLayout(toolbar)
        
        lay.addSpacing(15)
        
        # Tabla de activos
        self._tbl_activos = build_table(["Código", "Nombre", "Costo", "Valor en Libros", "Vida Útil", "Estado"])
        lay.addWidget(self._tbl_activos)
        lay.addStretch()
    
    def _load_activos(self):
        if not self._db:
            return
        
        try:
            if self._db.is_enterprise_mode():
                from src.contabilidad.motor_depreciacion import MotorDepreciacion
                motor = MotorDepreciacion(self._db.db_name)
                activos = motor.listar_activos()
                
                self._tbl_activos.setRowCount(0)
                for activo in activos:
                    r = self._tbl_activos.rowCount()
                    self._tbl_activos.insertRow(r)
                    
                    vals = [
                        activo.get('codigo', ''),
                        activo.get('nombre', ''),
                        f"${activo.get('costo', 0):,.2f}",
                        f"${activo.get('valor_en_libros', 0):,.2f}",
                        f"{activo.get('vida_util_anios', 0)} años",
                        activo.get('estado', '')
                    ]
                    
                    for c, v in enumerate(vals):
                        item = QTableWidgetItem(str(v))
                        self._tbl_activos.setItem(r, c, item)
            else:
                QMessageBox.warning(self, "Modo Enterprise", 
                    "El modo enterprise no está activado.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando activos: {e}")
    
    def _nuevo_activo(self):
        if not self._db or not self._db.is_enterprise_mode():
            QMessageBox.warning(self, "Modo Enterprise", "El modo enterprise no está activado.")
            return
        
        # Diálogo simplificado para crear activo
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Activo Fijo")
        dialog.setFixedWidth(500)
        
        layout = QFormLayout(dialog)
        
        codigo = QLineEdit()
        nombre = QLineEdit()
        costo = QLineEdit()
        vida_util = QSpinBox()
        vida_util.setRange(1, 50)
        vida_util.setValue(5)
        
        layout.addRow("Código:", codigo)
        layout.addRow("Nombre:", nombre)
        layout.addRow("Costo:", costo)
        layout.addRow("Vida Útil (años):", vida_util)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addRow(btns)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                from src.contabilidad.motor_depreciacion import MotorDepreciacion, MetodoDepreciacion
                from datetime import date
                
                motor = MotorDepreciacion(self._db.db_name)
                
                exito, msg, activo_id = motor.registrar_activo_fijo(
                    codigo=codigo.text(),
                    nombre=nombre.text(),
                    cuenta_activo="1.2.01.03",  # Maquinaria por defecto
                    cuenta_depreciacion="1.2.02.01",
                    cuenta_gasto="5.1.05.01",
                    costo=float(costo.text()),
                    fecha_adquisicion=date.today(),
                    vida_util_anios=vida_util.value(),
                    metodo=MetodoDepreciacion.LINEAL
                )
                
                if exito:
                    QMessageBox.information(self, "Éxito", msg)
                    self._load_activos()
                else:
                    QMessageBox.warning(self, "Error", msg)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error: {e}")
    
    def _calcular_depreciacion(self):
        if not self._db or not self._db.is_enterprise_mode():
            QMessageBox.warning(self, "Modo Enterprise", "El modo enterprise no está activado.")
            return
        
        try:
            from datetime import date
            periodo = date.today().strftime("%Y-%m")
            
            from src.contabilidad.motor_depreciacion import MotorDepreciacion
            motor = MotorDepreciacion(self._db.db_name)
            
            exito, msg, activos = motor.generar_depreciacion_periodo(periodo)
            
            if exito:
                QMessageBox.information(self, "Depreciación", 
                    f"Depreciaciones generadas para {len(activos)} activos.")
                self._load_activos()
            else:
                QMessageBox.warning(self, "Error", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {e}")
    
    def _reporte_activos(self):
        if not self._db or not self._db.is_enterprise_mode():
            QMessageBox.warning(self, "Modo Enterprise", "El modo enterprise no está activado.")
            return
        
        try:
            from src.contabilidad.motor_depreciacion import MotorDepreciacion
            motor = MotorDepreciacion(self._db.db_name)
            reporte = motor.obtener_reporte_activos()
            
            msg = f"Reporte de Activos Fijos\n\n"
            msg += f"Cantidad de Activos: {reporte.get('cantidad_activos', 0)}\n"
            msg += f"Costo Total: ${reporte.get('total_costo', 0):,.2f}\n"
            msg += f"Depreciación Acumulada: ${reporte.get('total_depreciacion_acumulada', 0):,.2f}\n"
            msg += f"Valor en Libros Total: ${reporte.get('total_valor_en_libros', 0):,.2f}"
            
            QMessageBox.information(self, "Reporte de Activos", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {e}")
