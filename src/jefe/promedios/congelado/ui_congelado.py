"""
ui_congelado.py - Interfaz de usuario para cálculo de promedios de congelados
TPV Pro 2026 · Cobro Fácil POS
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QDate
from src.contabilidad.shared_globals import PAL

class UICongelado(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tipo_promedio = "congelado"
        self._build_ui()
        self._cargar_filas_defecto()
    
    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        
        # Header con datos de compra
        header = QFrame()
        header.setStyleSheet(f"background: {PAL['surface']}; padding: 16px; border-bottom: 1px solid {PAL['border']};")
        header_lay = QHBoxLayout(header)
        
        self._input_proveedor = QLineEdit()
        self._input_proveedor.setPlaceholderText("Proveedor")
        self._input_proveedor.setFixedWidth(200)
        
        self._input_fecha = QDateEdit()
        self._input_fecha.setDate(QDate.currentDate())
        self._input_fecha.setCalendarPopup(True)
        self._input_fecha.setFixedWidth(150)
        
        header_lay.addWidget(QLabel("Proveedor:"))
        header_lay.addWidget(self._input_proveedor)
        header_lay.addWidget(QLabel("Fecha:"))
        header_lay.addWidget(self._input_fecha)
        header_lay.addStretch()
        
        # Datos de la compra
        datos_lay = QGridLayout()
        
        self._prom_kilos = QLineEdit("0")
        self._prom_kilos.setReadOnly(True)
        self._prom_kilos.setFixedWidth(100)
        
        self._prom_precio = QLineEdit("0")
        self._prom_precio.setReadOnly(True)
        self._prom_precio.setFixedWidth(100)
        
        self._prom_merma = QLineEdit("0")
        self._prom_merma.setFixedWidth(100)
        
        datos_lay.addWidget(QLabel("Kilos Totales:"), 0, 0)
        datos_lay.addWidget(self._prom_kilos, 0, 1)
        datos_lay.addWidget(QLabel("Precio por Kg:"), 0, 2)
        datos_lay.addWidget(self._prom_precio, 0, 3)
        datos_lay.addWidget(QLabel("Merma %:"), 1, 0)
        datos_lay.addWidget(self._prom_merma, 1, 1)
        
        header_lay.addLayout(datos_lay)
        lay.addWidget(header)
        
        # Tabla de cálculos
        self._prom_tabla = QTableWidget()
        self._prom_tabla.setColumnCount(12)
        self._prom_tabla.setHorizontalHeaderLabels([
            "Producto", "Kilos", "Costo $/kg", "Precio Venta", "% Ganancia",
            "P. Mayoreo", "Desde kg", "% Mayoreo", "V. Total", "V. Mayoreo", "Ganancia", "G. Mayoreo"
        ])
        self._prom_tabla.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self._prom_tabla)
        
        # Botones de acción
        btn_lay = QHBoxLayout()
        
        btn_calcular = QPushButton("Calcular Costos")
        btn_calcular.clicked.connect(self._calcular_costos)
        btn_calcular.setStyleSheet(f"background: {PAL['primary']}; color: white; padding: 8px 16px; border-radius: 8px;")
        
        btn_repartir = QPushButton("Repartir Precios")
        btn_repartir.clicked.connect(self._repartir_precios)
        btn_repartir.setStyleSheet(f"background: {PAL['success']}; color: white; padding: 8px 16px; border-radius: 8px;")
        
        btn_guardar = QPushButton("Guardar Historial")
        btn_guardar.clicked.connect(self._guardar_historial)
        btn_guardar.setStyleSheet(f"background: {PAL['warning']}; color: #0F172A; padding: 8px 16px; border-radius: 8px;")
        
        btn_lay.addWidget(btn_calcular)
        btn_lay.addWidget(btn_repartir)
        btn_lay.addWidget(btn_guardar)
        btn_lay.addStretch()
        lay.addLayout(btn_lay)
    
    def _cargar_filas_defecto(self):
        """Carga las filas por defecto para congelados"""
        productos = [
            "Pollo congelado kg",
            "Milanesa kg",
            "Nuggets kg",
            "Hamburguesa kg",
            "Papas congeladas kg",
            "Vegetales mix kg"
        ]
        
        self._prom_tabla.setRowCount(len(productos))
        
        for i, prod in enumerate(productos):
            self._prom_tabla.setItem(i, 0, QTableWidgetItem(prod))
            self._prom_tabla.setItem(i, 1, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 2, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 3, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 4, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 5, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 6, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 7, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 8, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 9, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 10, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 11, QTableWidgetItem("0"))
    
    def _calcular_costos(self):
        """Calcula el costo real por kg considerando merma usando el motor"""
        try:
            from .motor_congelado import MotorCongelado

            kilos = float(self._prom_kilos.text().replace(',', '.') or 0)
            precio = float(self._prom_precio.text().replace(',', '.') or 0)
            merma = float(self._prom_merma.text().replace(',', '.') or 0)

            if kilos == 0 or precio == 0:
                QMessageBox.warning(self, "Datos incompletos", "Ingrese kilos y precio.")
                return

            costo_real, kilos_utiles = MotorCongelado.calcular_costo_kilo(kilos, precio, merma)
            self._costo_real_kg = costo_real

            # Extraer filas de la tabla
            filas = []
            for i in range(self._prom_tabla.rowCount()):
                fila = []
                for j in range(self._prom_tabla.columnCount()):
                    item = self._prom_tabla.item(i, j)
                    fila.append(item.text() if item else "0")
                filas.append(fila)

            # Usar el motor para recalcular todas las filas
            resultado = MotorCongelado.recalcular_tabla(filas, costo_real, from_calc=True)

            # Actualizar tabla con resultados
            for i, calc in enumerate(resultado["filas"]):
                self._prom_tabla.setItem(i, 2, QTableWidgetItem(f"{calc['costo_real_kg']:.2f}"))
                self._prom_tabla.setItem(i, 3, QTableWidgetItem(f"{calc['pv']:.2f}"))
                self._prom_tabla.setItem(i, 4, QTableWidgetItem(f"{calc['pg']:.2f}"))
                self._prom_tabla.setItem(i, 5, QTableWidgetItem(f"{calc['pm']:.2f}"))
                self._prom_tabla.setItem(i, 7, QTableWidgetItem(f"{calc['pmg']:.2f}"))
                self._prom_tabla.setItem(i, 8, QTableWidgetItem(f"{calc['v_costo']:.2f}"))
                self._prom_tabla.setItem(i, 9, QTableWidgetItem(f"{calc['vn']:.2f}"))
                self._prom_tabla.setItem(i, 10, QTableWidgetItem(f"{calc['vo']:.2f}"))
                self._prom_tabla.setItem(i, 11, QTableWidgetItem(f"{calc['gn']:.2f}"))
                self._prom_tabla.setItem(i, 12, QTableWidgetItem(f"{calc['go']:.2f}"))

            QMessageBox.information(self, "Cálculo completado", f"Costo real por kg: ${costo_real:.2f}\nKilos útiles: {kilos_utiles:.2f}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en cálculo: {e}")

    def _repartir_precios(self):
        """Reparte los precios basándose en el % de ganancia usando el motor"""
        try:
            from .motor_congelado import MotorCongelado

            if not hasattr(self, '_costo_real_kg'):
                QMessageBox.warning(self, "Error", "Primero calcule los costos.")
                return

            # Extraer filas de la tabla
            filas = []
            for i in range(self._prom_tabla.rowCount()):
                fila = []
                for j in range(self._prom_tabla.columnCount()):
                    item = self._prom_tabla.item(i, j)
                    fila.append(item.text() if item else "0")
                filas.append(fila)

            # Usar el motor para recalcular todas las filas
            resultado = MotorCongelado.recalcular_tabla(filas, self._costo_real_kg, from_calc=True)

            # Actualizar tabla con resultados
            for i, calc in enumerate(resultado["filas"]):
                self._prom_tabla.setItem(i, 3, QTableWidgetItem(f"{calc['pv']:.2f}"))
                self._prom_tabla.setItem(i, 4, QTableWidgetItem(f"{calc['pg']:.2f}"))
                self._prom_tabla.setItem(i, 5, QTableWidgetItem(f"{calc['pm']:.2f}"))
                self._prom_tabla.setItem(i, 7, QTableWidgetItem(f"{calc['pmg']:.2f}"))
                self._prom_tabla.setItem(i, 8, QTableWidgetItem(f"{calc['v_costo']:.2f}"))
                self._prom_tabla.setItem(i, 9, QTableWidgetItem(f"{calc['vn']:.2f}"))
                self._prom_tabla.setItem(i, 10, QTableWidgetItem(f"{calc['vo']:.2f}"))
                self._prom_tabla.setItem(i, 11, QTableWidgetItem(f"{calc['gn']:.2f}"))
                self._prom_tabla.setItem(i, 12, QTableWidgetItem(f"{calc['go']:.2f}"))

            QMessageBox.information(self, "Precios repartidos", "Los precios de venta han sido actualizados.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error repartiendo precios: {e}")
    
    def _guardar_historial(self):
        """Guarda el estado actual en el historial"""
        try:
            from src.jefe.promedios.motor_global_promedios import MotorPromedios
            from src.base_de_datos.database import DatabaseManager
            
            db = DatabaseManager()
            estado = self.get_state()
            
            exito = MotorPromedios.guardar_historial(
                db, self._tipo_promedio, estado,
                self._input_proveedor.text(),
                self._input_fecha.date().toString("yyyy-MM-dd")
            )
            
            if exito:
                QMessageBox.information(self, "Guardado", "Historial guardado exitosamente.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo guardar el historial.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando historial: {e}")
    
    def get_state(self):
        """Retorna el estado actual para sincronización"""
        filas = []
        for i in range(self._prom_tabla.rowCount()):
            fila = []
            for j in range(self._prom_tabla.columnCount()):
                item = self._prom_tabla.item(i, j)
                fila.append(item.text() if item else "0")
            filas.append(fila)
        
        return {
            "kilos": self._prom_kilos.text(),
            "precio": self._prom_precio.text(),
            "merma": self._prom_merma.text(),
            "filas": filas
        }
    
    def redondear(self):
        """Redondea precios a múltiplos de 50"""
        for i in range(self._prom_tabla.rowCount()):
            item_precio = self._prom_tabla.item(i, 3)
            if item_precio:
                precio = float(item_precio.text().replace(',', '.') or 0)
                precio_redondeado = round(precio / 50) * 50
                self._prom_tabla.setItem(i, 3, QTableWidgetItem(f"{precio_redondeado:.2f}"))
