from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QPushButton, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QTreeWidget, QTreeWidgetItem, QSplitter,
    QComboBox, QCheckBox, QStackedWidget, QFileDialog, QGridLayout,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QColor, QFont, QBrush

# Removed db_manager import


class DialogoProducto(QDialog):
    def __init__(self, datos=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 " + ("Editar Producto" if datos else "Nuevo Producto"))
        self.setFixedSize(780, 680)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        self._id = dict(datos).get('id') if datos else None
        self._cant_oferta = dict(datos).get('cant_oferta', 0.0) if datos else 0.0
        self._precio_oferta = dict(datos).get('precio_oferta', 0.0) if datos else 0.0
        self.setup_ui(datos)

    def setup_ui(self, datos):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(30, 30, 30, 30)
        main_lay.setSpacing(20)

        # --- HEADER ---
        lbl_tit = QLabel("💎 Ficha de Producto 2026")
        lbl_tit.setStyleSheet("font-size: 24px; font-weight: bold; ")
        main_lay.addWidget(lbl_tit)

        # --- SECCIÓN: CÓDIGO DE BARRAS (ALTA VISIBILIDAD) ---
        barcode_frame = QFrame()
        barcode_frame.setStyleSheet("background: white; border-radius: 16px; border: 1px solid #CBD5E1;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        barcode_frame.setGraphicsEffect(shadow)
        
        bar_lay = QVBoxLayout(barcode_frame)
        bar_lay.setContentsMargins(20, 15, 20, 15)
        
        lbl_bc = QLabel("CÓDIGO DE BARRAS / PLU:")
        lbl_bc.setStyleSheet("font-weight: bold; font-size: 11px; border: none; color: #64748B;")
        self.txt_codigo = QLineEdit(dict(datos).get('codigo', '') if datos else '')
        self.txt_codigo.setPlaceholderText("Escanea o escribe el código...")
        self.txt_codigo.setStyleSheet("""
            QLineEdit { 
                background: #F8FAFC; border: 2px solid transparent; border-bottom: 2px solid #CBD5E1; border-radius: 8px; 
                padding: 15px; font-size: 24px; font-weight: 900;  
                font-family: 'Consolas', monospace; color: #1E3A8A;
            }
            QLineEdit:focus {
                background: white;
                border: 2px solid #3B82F6;
            }
        """)
        bar_lay.addWidget(lbl_bc)
        bar_lay.addWidget(self.txt_codigo)
        main_lay.addWidget(barcode_frame)

        # --- CUERPO EN DOS COLUMNAS ---
        grid = QGridLayout()
        grid.setSpacing(20)

        # Columna 1: Info Básica
        self.txt_nombre = QLineEdit(dict(datos).get('nombre', '') if datos else '')
        self.txt_nombre.setPlaceholderText("Nombre descriptivo...")
        self.add_field(grid, "Nombre del Producto *:", self.txt_nombre, 0, 0)

        self.cmb_cat = QComboBox()
        self.cmb_cat.setEditable(True)
        try:
            from src.motor_inventario.motor_departamentos import MotorDepartamentos
            motor_dep = MotorDepartamentos()
            cats = motor_dep.obtener_categorias()
            cats_names = [c['nombre'] for c in cats] if cats else []
            self.cmb_cat.addItems(cats_names)
        except: pass
        
        idx_cat = self.cmb_cat.findText(dict(datos).get('categoria', 'GENERAL') if datos else 'GENERAL')
        if idx_cat >= 0: self.cmb_cat.setCurrentIndex(idx_cat)

        v_cat = QVBoxLayout()
        lbl_cat = QLabel("Departamento (Mercadería):")
        lbl_cat.setStyleSheet("font-weight: bold;  font-size: 12px;")
        v_cat.addWidget(lbl_cat)
        v_cat.addWidget(self.cmb_cat)
        grid.addLayout(v_cat, 1, 0)

        self.cmb_depto = QComboBox()
        self.cmb_depto.addItem("")
        try:
            from src.motor_inventario.motor_departamentos import MotorDepartamentos
            motor_dep = MotorDepartamentos()
            deps = motor_dep.obtener_departamentos()
            deps_names = [d['nombre'] for d in deps] if deps else []
            self.cmb_depto.addItems(deps_names)
        except: pass

        v_depto = QVBoxLayout()
        lbl_depto = QLabel("Impuesto (Departamento Fiscal):")
        lbl_depto.setStyleSheet("font-weight: bold;  font-size: 12px;")
        v_depto.addWidget(lbl_depto)
        v_depto.addWidget(self.cmb_depto)
        
        self.lbl_iva_info = QLabel("ℹ️ IVA Aplicado: 21.0% (tasa general)")
        self.lbl_iva_info.setStyleSheet(" font-size: 11px; font-weight: bold; margin-top: 2px;")
        v_depto.addWidget(self.lbl_iva_info)
        grid.addLayout(v_depto, 2, 0)
        
        self.cmb_depto.currentIndexChanged.connect(self._actualizar_info_iva)

        depto_actual = dict(datos).get('departamento', '') if datos else ''
        idx_dep = self.cmb_depto.findText(depto_actual)
        if idx_dep >= 0: 
            self.cmb_depto.setCurrentIndex(idx_dep)
        else:
            self._actualizar_info_iva()

        self.cmb_uni = QComboBox()
        self.cmb_uni.addItems(['UN','KG','LT','MT','CJ'])
        idx = self.cmb_uni.findText(dict(datos).get('unidad', 'UN') if datos else 'UN')
        if idx >= 0: self.cmb_uni.setCurrentIndex(idx)
        self.add_field(grid, "Unidad de Medida:", self.cmb_uni, 3, 0)

        self.chk_pes = QCheckBox("Es pesable / fraccionable (Balanza)")
        self.chk_pes.setChecked(bool(dict(datos).get('es_pesable', 0)) if datos else False)
        self.chk_pes.setStyleSheet("font-weight: bold;  margin-top: 10px;")
        grid.addWidget(self.chk_pes, 4, 0)

        # Tarjeta Finanzas (Derecha)
        price_card = QFrame()
        price_card.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 16px; padding: 15px;")
        
        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(20)
        shadow2.setColor(QColor(0, 0, 0, 15))
        shadow2.setOffset(0, 4)
        price_card.setGraphicsEffect(shadow2)
        
        p_lay = QFormLayout(price_card)
        p_lay.setSpacing(12)

        self.txt_costo = self.create_price_input(str(dict(datos).get('costo', '0.00')) if datos else '0.00')
        self.txt_precio = self.create_price_input(str(dict(datos).get('precio', '0.00')) if datos else '0.00', bold=True)
        self.txt_mayoreo = self.create_price_input(str(dict(datos).get('precio_mayoreo', '0.00')) if datos else '0.00')
        
        p_lay.addRow(QLabel("Costo Compra ($):"), self.txt_costo)
        p_lay.addRow(QLabel("Precio Venta ($) *:"), self.txt_precio)
        p_lay.addRow(QLabel("Precio Mayoreo ($):"), self.txt_mayoreo)
        
        grid.addWidget(price_card, 0, 1, 3, 1)

        # Stock Info
        stock_lay = QHBoxLayout()
        self.txt_stock = self.create_price_input(str(dict(datos).get('stock', '0')) if datos else '0')
        self.txt_min = self.create_price_input(str(dict(datos).get('stock_minimo', '0')) if datos else '0')
        self.txt_max = self.create_price_input(str(dict(datos).get('stock_maximo', '0')) if datos else '0')
        
        v_stock = QVBoxLayout(); v_stock.addWidget(QLabel("Stock Act.")); v_stock.addWidget(self.txt_stock)
        v_min = QVBoxLayout(); v_min.addWidget(QLabel("Min.")); v_min.addWidget(self.txt_min)
        v_max = QVBoxLayout(); v_max.addWidget(QLabel("Max.")); v_max.addWidget(self.txt_max)
        
        stock_lay.addLayout(v_stock); stock_lay.addLayout(v_min); stock_lay.addLayout(v_max)
        grid.addLayout(stock_lay, 3, 1, 2, 1)

        main_lay.addLayout(grid)

        # --- BOTONES DE ACCIÓN ---
        main_lay.addStretch()
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("padding: 15px; border-radius: 10px; font-weight: bold; font-size: 14px; background: #F1F5F9; color: #475569;")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 Guardar Producto")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2563EB; color: white; border: none; 
                border-radius: 10px; padding: 15px 30px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:pressed { background-color: #1E40AF; }
        """)
        btn_save.clicked.connect(self._ok)

        h_btns.addWidget(btn_cancel)
        h_btns.addStretch()
        h_btns.addWidget(btn_save)
        main_lay.addLayout(h_btns)

    def add_field(self, grid, label, widget, row, col):
        v = QVBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("font-weight: bold;  font-size: 12px;")
        v.addWidget(lbl)
        v.addWidget(widget)
        grid.addLayout(v, row, col)

    def create_price_input(self, val, bold=False):
        inp = QLineEdit(val)
        weight = "900" if bold else "normal"
        color = "#1E40AF" if bold else "#1E293B"
        inp.setStyleSheet(f"""
            QLineEdit {{
                background: #F1F5F9; 
                border: 2px solid transparent; 
                border-radius: 8px; 
                padding: 10px; 
                font-size: 16px;
                font-weight: {weight}; 
                color: {color};
            }}
            QLineEdit:focus {{
                background: white;
                border: 2px solid #3B82F6;
            }}
        """)
        return inp

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.focusNextChild()
        else:
            super().keyPressEvent(event)

    def _ok(self):
        nom = self.txt_nombre.text().strip()
        cod = self.txt_codigo.text().strip()
        
        if not nom:
            QMessageBox.warning(self, "Requerido", "El nombre es obligatorio.")
            return

        from src.motor_inventario.motor_catalogo import MotorCatalogo
        if cod and MotorCatalogo().verificar_codigo_existe(cod, self._id):
            ans = QMessageBox.question(
                self, "Código Duplicado",
                f"⚠️ Atención: El código de barras '{cod}' ya está asignado a otro producto.\n\n¿Deseas guardarlo de todos modos?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if ans == QMessageBox.No:
                return

        if MotorCatalogo().verificar_nombre_existe(nom, self._id):
            ans = QMessageBox.question(
                self, "Nombre Duplicado",
                f"⚠️ Atención: Ya existe un producto con el nombre '{nom}'.\n\n¿Deseas registrar este duplicado de todos modos?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if ans == QMessageBox.No:
                return

        self.accept()

    def _actualizar_info_iva(self):
        dep = self.cmb_depto.currentText().strip()
        from src.config import config
        iva_gen = float(config.get("tax_percentage", 21.0))
        if not dep:
            self.lbl_iva_info.setText(f"ℹ️ IVA Aplicado: {iva_gen:.1f}% (tasa general)")
            return
            
        try:
            from src.motor_inventario.motor_departamentos import MotorDepartamentos
            iva_val = MotorDepartamentos().obtener_iva_departamento(dep)
            if iva_val is not None:
                self.lbl_iva_info.setText(f"ℹ️ IVA Aplicado: {iva_val:.1f}% (por departamento)")
            else:
                self.lbl_iva_info.setText(f"ℹ️ IVA Aplicado: {iva_gen:.1f}% (tasa general)")
        except Exception:
            self.lbl_iva_info.setText(f"ℹ️ IVA Aplicado: {iva_gen:.1f}% (tasa general)")


    def get_data(self):
        def parse_f(txt):
            try: return float(txt.replace(',','.'))
            except: return 0.0
        return {
            'id':self._id, 'codigo':self.txt_codigo.text().strip() or None,
            'nombre':self.txt_nombre.text().strip(),
            'precio':parse_f(self.txt_precio.text()),
            'precio_mayoreo':parse_f(self.txt_mayoreo.text()),
            'cant_oferta': self._cant_oferta,
            'precio_oferta': self._precio_oferta,
            'costo':parse_f(self.txt_costo.text()),
            'stock':parse_f(self.txt_stock.text()),
            'stock_minimo':parse_f(self.txt_min.text()),
            'stock_maximo':parse_f(self.txt_max.text()),
            'departamento':self.cmb_depto.currentText().strip() or None,
            'categoria':self.cmb_cat.currentText().strip() or 'GENERAL',
            'unidad':self.cmb_uni.currentText(),
            'es_pesable':1 if self.chk_pes.isChecked() else 0,
        }


# ── Panel Departamentos (Totalmente unificado a Tema Claro) ──
