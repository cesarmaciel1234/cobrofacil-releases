import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QWidget, QAbstractItemView,
    QSpinBox, QDoubleSpinBox, QInputDialog
)
from PyQt6.QtCore import Qt
from src.motor_descuentos.cerebro.motor_combos import MotorCombos

class DialogoCombos(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎁 Gestión de Combos")
        self.resize(800, 600)
        self.setStyleSheet("""
            QDialog { background-color: #F8FAFC; }
            QPushButton { 
                background: #3B82F6; color: white; font-weight: bold; border-radius: 6px; padding: 8px 15px; 
            }
            QPushButton:hover { background: #2563EB; }
            QPushButton#btnEliminar { background: #EF4444; }
            QPushButton#btnEliminar:hover { background: #DC2626; }
            QTableWidget { background: white; border: 1px solid #E2E8F0; border-radius: 6px; }
            QHeaderView::section { background: #F1F5F9; font-weight: bold; padding: 5px; border: none; }
        """)
        
        self._setup_ui()
        self._cargar_combos()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(15)
        
        # Header
        hl = QHBoxLayout()
        tit = QLabel("Combos Activos")
        tit.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        hl.addWidget(tit)
        hl.addStretch()
        
        btn_nuevo = QPushButton("➕ Crear Nuevo Combo")
        btn_nuevo.clicked.connect(self._crear_combo)
        hl.addWidget(btn_nuevo)
        root.addLayout(hl)
        
        # Table
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre del Combo", "Precio Final", "Productos"])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        root.addWidget(self.tabla)
        
        # Botones inferiores
        hl2 = QHBoxLayout()
        btn_eliminar = QPushButton("🗑️ Eliminar Seleccionado")
        btn_eliminar.setObjectName("btnEliminar")
        btn_eliminar.clicked.connect(self._eliminar_combo)
        hl2.addWidget(btn_eliminar)
        hl2.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setStyleSheet("background: #64748B;")
        btn_cerrar.clicked.connect(self.close)
        hl2.addWidget(btn_cerrar)
        root.addLayout(hl2)

    def _cargar_combos(self):
        self.tabla.setRowCount(0)
        try:
            motor = MotorCombos()
            res = motor.obtener_combos()
            if res:
                for row in res:
                    r = self.tabla.rowCount()
                    self.tabla.insertRow(r)
                    
                    id_c = str(row.get('id', ''))
                    nom = str(row.get('nombre', ''))
                    prec = float(row.get('precio_combo', 0.0))
                    prod_str = str(row.get('productos_json', '[]'))
                    
                    try:
                        prods = json.loads(prod_str)
                        detalles = ", ".join([f"{p['cantidad']}x {p['nombre']}" for p in prods])
                    except:
                        detalles = "Error leyendo productos"

                    self.tabla.setItem(r, 0, QTableWidgetItem(id_c))
                    self.tabla.setItem(r, 1, QTableWidgetItem(nom))
                    self.tabla.setItem(r, 2, QTableWidgetItem(f"${prec:,.2f}"))
                    self.tabla.setItem(r, 3, QTableWidgetItem(detalles))
        except Exception as e:
            print("Error cargando combos:", e)

    def _crear_combo(self):
        dlg = CreadorComboDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._cargar_combos()

    def _eliminar_combo(self):
        row = self.tabla.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un combo para eliminar.")
            return
            
        id_c = self.tabla.item(row, 0).text()
        nombre = self.tabla.item(row, 1).text()
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar el combo '{nombre}'?") == QMessageBox.StandardButton.Yes:
            if MotorCombos().eliminar_combo(id_c):
                self._cargar_combos()


class CreadorComboDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Combo")
        self.resize(600, 500)
        self.productos_agregados = [] # list of dicts: id_producto, nombre, cantidad
        
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLineEdit, QSpinBox, QDoubleSpinBox { padding: 6px; border: 1px solid #CBD5E1; border-radius: 4px; }
            QPushButton { background: #10B981; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; }
            QPushButton:hover { background: #059669; }
        """)
        
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        
        # Nombre Combo
        hl1 = QHBoxLayout()
        hl1.addWidget(QLabel("Nombre del Combo:"))
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Combo Asado Familiar")
        hl1.addWidget(self.txt_nombre, 1)
        root.addLayout(hl1)
        
        # Buscador producto
        hl2 = QHBoxLayout()
        hl2.addWidget(QLabel("Agregar Producto (ID o Nombre):"))
        self.txt_buscar = QLineEdit()
        self.txt_buscar.returnPressed.connect(self._buscar_y_agregar)
        hl2.addWidget(self.txt_buscar, 1)
        btn_add = QPushButton("Buscar")
        btn_add.clicked.connect(self._buscar_y_agregar)
        hl2.addWidget(btn_add)
        root.addLayout(hl2)
        
        # Tabla productos
        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre Producto", "Cantidad Requerida"])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        root.addWidget(self.tabla)
        
        # Precio final
        hl3 = QHBoxLayout()
        hl3.addStretch()
        hl3.addWidget(QLabel("Precio Especial del Combo: $"))
        self.spn_precio = QDoubleSpinBox()
        self.spn_precio.setMaximum(9999999)
        self.spn_precio.setDecimals(2)
        hl3.addWidget(self.spn_precio)
        root.addLayout(hl3)
        
        # Botones
        hl4 = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("background: #94A3B8;")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾 Guardar Combo")
        btn_save.clicked.connect(self._guardar)
        hl4.addStretch()
        hl4.addWidget(btn_cancel)
        hl4.addWidget(btn_save)
        root.addLayout(hl4)

    def _buscar_y_agregar(self):
        termino = self.txt_buscar.text().strip()
        if not termino: return
        
        res = MotorCombos().buscar_productos(termino)
        
        if not res:
            QMessageBox.warning(self, "No encontrado", "No se encontró el producto.")
            return
            
        if len(res) == 1:
            self._seleccionar_producto(res[0])
        else:
            # simple dialog to pick if multiple
            nombres = [str(r.get('nombre', '')) for r in res]
            item, ok = QInputDialog.getItem(self, "Seleccionar", "Varios encontrados. Elija uno:", nombres, 0, False)
            if ok and item:
                idx = nombres.index(item)
                self._seleccionar_producto(res[idx])

    def _seleccionar_producto(self, prod):
        id_p = str(prod.get('id', ''))
        nom = str(prod.get('nombre', ''))
        
        cant, ok = QInputDialog.getDouble(self, "Cantidad", f"¿Qué cantidad de '{nom}' requiere este combo?", 1.0, 0.01, 999, 2)
        if ok and cant > 0:
            self.productos_agregados.append({"id_producto": id_p, "nombre": nom, "cantidad": cant})
            self._actualizar_tabla()
            self.txt_buscar.clear()

    def _actualizar_tabla(self):
        self.tabla.setRowCount(0)
        for p in self.productos_agregados:
            r = self.tabla.rowCount()
            self.tabla.insertRow(r)
            self.tabla.setItem(r, 0, QTableWidgetItem(p["id_producto"]))
            self.tabla.setItem(r, 1, QTableWidgetItem(p["nombre"]))
            self.tabla.setItem(r, 2, QTableWidgetItem(str(p["cantidad"])))

    def _guardar(self):
        nom = self.txt_nombre.text().strip()
        prec = self.spn_precio.value()
        
        if not nom:
            QMessageBox.warning(self, "Error", "Debe ingresar un nombre.")
            return
        if not self.productos_agregados:
            QMessageBox.warning(self, "Error", "Debe agregar al menos un producto al combo.")
            return
        if prec <= 0:
            QMessageBox.warning(self, "Error", "El precio del combo debe ser mayor a 0.")
            return
            
        if MotorCombos().guardar_combo(nom, prec, self.productos_agregados):
            QMessageBox.information(self, "Éxito", "Combo guardado correctamente.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "No se pudo guardar el combo.")
