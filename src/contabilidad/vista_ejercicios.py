from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from src.contabilidad.shared_globals import *

class VistaEjerciciosMixin:
    def _build_tab_ejercicios(self):
        lay, _ = self._page()
        
        lay.addWidget(section_title("📅  Ejercicios Contables"))
        
        # Toolbar
        toolbar = QHBoxLayout()
        btn_crear = btn_primary("➕ Crear Ejercicio")
        btn_crear.clicked.connect(self._crear_ejercicio)
        btn_cerrar = btn_primary("🔒 Cerrar Ejercicio")
        btn_cerrar.clicked.connect(self._cerrar_ejercicio)
        btn_ver = btn_primary("👁️ Ver Balance Cierre")
        btn_ver.clicked.connect(self._ver_balance_cierre)
        
        toolbar.addWidget(btn_crear)
        toolbar.addWidget(btn_cerrar)
        toolbar.addWidget(btn_ver)
        toolbar.addStretch()
        lay.addLayout(toolbar)
        
        lay.addSpacing(15)
        
        # Tabla de ejercicios
        self._tbl_ejercicios = build_table(["Año", "Estado", "Fecha Apertura", "Fecha Cierre", "Resultado"])
        lay.addWidget(self._tbl_ejercicios)
        lay.addStretch()
    
    def _load_ejercicios(self):
        if not self._db:
            return
        
        try:
            if self._db.is_enterprise_mode():
                from src.contabilidad.motor_cierre import MotorCierre
                motor = MotorCierre(self._db.db_name)
                ejercicios = motor.listar_ejercicios()
                
                self._tbl_ejercicios.setRowCount(0)
                for ej in ejercicios:
                    r = self._tbl_ejercicios.rowCount()
                    self._tbl_ejercicios.insertRow(r)
                    
                    vals = [
                        ej.get('anio', ''),
                        ej.get('estado', ''),
                        ej.get('fecha_apertura', ''),
                        ej.get('fecha_cierre', '—'),
                        f"${ej.get('resultado_ejercicio', 0):,.2f}"
                    ]
                    
                    for c, v in enumerate(vals):
                        item = QTableWidgetItem(str(v))
                        self._tbl_ejercicios.setItem(r, c, item)
            else:
                QMessageBox.warning(self, "Modo Enterprise", 
                    "El modo enterprise no está activado.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando ejercicios: {e}")
    
    def _crear_ejercicio(self):
        if not self._db or not self._db.is_enterprise_mode():
            QMessageBox.warning(self, "Modo Enterprise", "El modo enterprise no está activado.")
            return
        
        # Diálogo para crear ejercicio
        dialog = QDialog(self)
        dialog.setWindowTitle("Crear Ejercicio Contable")
        dialog.setFixedWidth(400)
        
        layout = QFormLayout(dialog)
        
        anio = QSpinBox()
        anio.setRange(2000, 2100)
        anio.setValue(datetime.date.today().year)
        
        layout.addRow("Año:", anio)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addRow(btns)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                from src.contabilidad.motor_cierre import MotorCierre
                motor = MotorCierre(self._db.db_name)
                
                exito, msg, ejercicio_id = motor.crear_ejercicio(anio.value())
                
                if exito:
                    QMessageBox.information(self, "Éxito", msg)
                    self._load_ejercicios()
                else:
                    QMessageBox.warning(self, "Error", msg)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error: {e}")
    
    def _cerrar_ejercicio(self):
        if not self._db or not self._db.is_enterprise_mode():
            QMessageBox.warning(self, "Modo Enterprise", "El modo enterprise no está activado.")
            return
        
        # Diálogo para seleccionar año
        anio, ok = QInputDialog.getInt(self, "Cerrar Ejercicio", "Año a cerrar:", 
                                          datetime.date.today().year, 2000, 2100)
        
        if ok:
            try:
                from src.contabilidad.motor_cierre import MotorCierre
                motor = MotorCierre(self._db.db_name)
                
                respuesta = QMessageBox.question(
                    self, "Confirmar Cierre",
                    f"¿Está seguro de cerrar el ejercicio {anio}?\n\n"
                    "Esto generará:\n"
                    "- Asiento de cierre de cuentas de resultados\n"
                    "- Asiento de apertura del siguiente año\n"
                    "- El ejercicio quedará bloqueado",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if respuesta == QMessageBox.StandardButton.Yes:
                    exito, msg = motor.proceso_completo_cierre(anio, "admin")
                    
                    if exito:
                        QMessageBox.information(self, "Éxito", msg)
                        self._load_ejercicios()
                    else:
                        QMessageBox.warning(self, "Error", msg)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error: {e}")
    
    def _ver_balance_cierre(self):
        if not self._db or not self._db.is_enterprise_mode():
            QMessageBox.warning(self, "Modo Enterprise", "El modo enterprise no está activado.")
            return
        
        # Diálogo para seleccionar año
        anio, ok = QInputDialog.getInt(self, "Ver Balance Cierre", "Año:", 
                                          datetime.date.today().year, 2000, 2100)
        
        if ok:
            try:
                from src.contabilidad.motor_cierre import MotorCierre
                motor = MotorCierre(self._db.db_name)
                balance = motor.obtener_balance_cierre(anio)
                
                if "error" in balance:
                    QMessageBox.warning(self, "Error", balance["error"])
                    return
                
                msg = f"Balance de Cierre - Ejercicio {anio}\n\n"
                
                if "balance_general" in balance:
                    bg = balance["balance_general"]
                    msg += "BALANCE GENERAL:\n"
                    msg += f"  Total Activos: ${bg.get('total_activos', 0):,.2f}\n"
                    msg += f"  Total Pasivos: ${bg.get('total_pasivos', 0):,.2f}\n"
                    msg += f"  Total Patrimonio: ${bg.get('total_patrimonio', 0):,.2f}\n\n"
                
                if "estado_resultados" in balance:
                    er = balance["estado_resultados"]
                    msg += "ESTADO DE RESULTADOS:\n"
                    msg += f"  Total Ingresos: ${er.get('total_ingresos', 0):,.2f}\n"
                    msg += f"  Total Gastos: ${er.get('total_gastos', 0):,.2f}\n"
                    msg += f"  Resultado Neto: ${er.get('resultado_neto', 0):,.2f}"
                
                QMessageBox.information(self, "Balance de Cierre", msg)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error: {e}")
