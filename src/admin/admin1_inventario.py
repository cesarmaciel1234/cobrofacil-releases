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

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

STYLE = """
QWidget {
    font-family: 'Inter', 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
    font-size: 13px;
    background-color: #F8FAFC;
    color: #334155;
}
QFrame#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F1F5F9, stop:1 #E2E8F0);
    border-bottom: 2px solid #CBD5E1;
    border-radius: 12px;
}
QLabel#titulo {
    color: #0F172A;
    background: transparent;
    font-size: 22px;
    font-weight: 900;
    letter-spacing: 1px;
}
QPushButton {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #F1F5F9;
    border-color: #94A3B8;
    color: #0F172A;
}
QPushButton#blue {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
}
QPushButton#blue:hover {
    background-color: #1D4ED8;
    color: #FFFFFF;
}
QPushButton#danger {
    background-color: #FFFFFF;
    color: #DC2626;
    border: 1px solid #FECACA;
}
QPushButton#danger:hover {
    background-color: #FEF2F2;
    color: #B91C1C;
    border: 1px solid #FCA5A5;
}
QPushButton#gray {
    background-color: #FFFFFF;
    color: #475569;
    border: 1px solid #E2E8F0;
}
QPushButton#gray:hover {
    background-color: #F1F5F9;
}
QLineEdit, QComboBox {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
}
QLineEdit:focus, QComboBox:focus {
    border: 2px solid #3B82F6;
    background-color: #FFFFFF;
}
QTreeWidget, QTableWidget {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #E2E8F0;
    gridline-color: #F1F5F9;
    selection-background-color: #EFF6FF;
    selection-color: #1D4ED8;
    border-radius: 12px;
    alternate-background-color: #F8FAFC;
}
QHeaderView::section {
    background-color: #F8FAFC;
    color: #64748B;
    font-weight: 800;
    padding: 15px 12px;
    border: none;
    border-bottom: 2px solid #E2E8F0;
    font-size: 11px;
    text-transform: uppercase;
}
QScrollBar:vertical {
    border: none;
    background: #F1F5F9;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #CBD5E1;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""


# ── Diálogo Producto 2026 ──────────────────────────────────
class DialogoProducto(QDialog):
    def __init__(self, datos=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 " + ("Editar Producto" if datos else "Nuevo Producto"))
        self.setFixedSize(780, 680)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        self._id = datos.get('id') if datos else None
        self._cant_oferta = datos.get('cant_oferta', 0.0) if datos else 0.0
        self._precio_oferta = datos.get('precio_oferta', 0.0) if datos else 0.0
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
        self.txt_codigo = QLineEdit(datos.get('codigo', '') if datos else '')
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
        self.txt_nombre = QLineEdit(datos.get('nombre', '') if datos else '')
        self.txt_nombre.setPlaceholderText("Nombre descriptivo...")
        self.add_field(grid, "Nombre del Producto *:", self.txt_nombre, 0, 0)

        self.cmb_cat = QComboBox()
        self.cmb_cat.setEditable(True)
        try:
            cats = db_manager.execute_query("SELECT nombre FROM categorias ORDER BY nombre") or []
            existentes_cat = set(["GENERAL"])
            self.cmb_cat.addItem("GENERAL")
            for c in cats:
                if c['nombre'].upper() != "GENERAL":
                    self.cmb_cat.addItem(c['nombre'])
                    existentes_cat.add(c['nombre'])
            cats_prod = db_manager.execute_query("SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL AND categoria != '' ORDER BY categoria") or []
            for cp in cats_prod:
                if cp['categoria'] not in existentes_cat:
                    self.cmb_cat.addItem(cp['categoria'])
                    existentes_cat.add(cp['categoria'])
        except: pass
        
        idx_cat = self.cmb_cat.findText(datos.get('categoria', 'GENERAL') if datos else 'GENERAL')
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
            deps = db_manager.execute_query("SELECT nombre FROM departamentos ORDER BY nombre") or []
            existentes = set([""])
            for d in deps:
                self.cmb_depto.addItem(d['nombre'])
                existentes.add(d['nombre'])
            
            deps_prod = db_manager.execute_query("SELECT DISTINCT departamento FROM productos WHERE departamento IS NOT NULL AND departamento != '' ORDER BY departamento") or []
            for dp in deps_prod:
                if dp['departamento'] not in existentes:
                    self.cmb_depto.addItem(dp['departamento'])
                    existentes.add(dp['departamento'])
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

        depto_actual = datos.get('departamento', '') if datos else ''
        idx_dep = self.cmb_depto.findText(depto_actual)
        if idx_dep >= 0: 
            self.cmb_depto.setCurrentIndex(idx_dep)
        else:
            self._actualizar_info_iva()

        self.cmb_uni = QComboBox()
        self.cmb_uni.addItems(['UN','KG','LT','MT','CJ'])
        idx = self.cmb_uni.findText(datos.get('unidad', 'UN') if datos else 'UN')
        if idx >= 0: self.cmb_uni.setCurrentIndex(idx)
        self.add_field(grid, "Unidad de Medida:", self.cmb_uni, 3, 0)

        self.chk_pes = QCheckBox("Es pesable / fraccionable (Balanza)")
        self.chk_pes.setChecked(bool(datos.get('es_pesable', 0)) if datos else False)
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

        self.txt_costo = self.create_price_input(str(datos.get('costo', '0.00')) if datos else '0.00')
        self.txt_precio = self.create_price_input(str(datos.get('precio', '0.00')) if datos else '0.00', bold=True)
        self.txt_mayoreo = self.create_price_input(str(datos.get('precio_mayoreo', '0.00')) if datos else '0.00')
        
        p_lay.addRow(QLabel("Costo Compra ($):"), self.txt_costo)
        p_lay.addRow(QLabel("Precio Venta ($) *:"), self.txt_precio)
        p_lay.addRow(QLabel("Precio Mayoreo ($):"), self.txt_mayoreo)
        
        grid.addWidget(price_card, 0, 1, 3, 1)

        # Stock Info
        stock_lay = QHBoxLayout()
        self.txt_stock = self.create_price_input(str(datos.get('stock', '0')) if datos else '0')
        self.txt_min = self.create_price_input(str(datos.get('stock_minimo', '0')) if datos else '0')
        self.txt_max = self.create_price_input(str(datos.get('stock_maximo', '0')) if datos else '0')
        
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

        # Advertencia de Código Duplicado
        if cod:
            try:
                res = db_manager.execute_query("SELECT id FROM productos WHERE codigo=?", (cod,))
                if res and len(res) > 0:
                    if self._id is None or res[0]['id'] != self._id:
                        ans = QMessageBox.question(
                            self, "Código Duplicado",
                            f"⚠️ Atención: El código de barras '{cod}' ya está asignado a otro producto.\n\n¿Deseas guardarlo de todos modos?",
                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                        )
                        if ans == QMessageBox.No:
                            return
            except: pass

        # Advertencia de Nombre Duplicado
        try:
            # Búsqueda que ignora mayúsculas/minúsculas
            res_nom = db_manager.execute_query("SELECT id FROM productos WHERE LOWER(nombre) = LOWER(?)", (nom,))
            if res_nom and len(res_nom) > 0:
                if self._id is None or res_nom[0]['id'] != self._id:
                    ans = QMessageBox.question(
                        self, "Nombre Duplicado",
                        f"⚠️ Atención: Ya existe un producto con el nombre '{nom}'.\n\n¿Deseas registrar este duplicado de todos modos?",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                    )
                    if ans == QMessageBox.No:
                        return
        except: pass

        self.accept()

    def _actualizar_info_iva(self):
        dep = self.cmb_depto.currentText().strip()
        from src.admin.admin5_configuracion import config
        iva_gen = float(config.get("tax_percentage", 21.0))
        if not dep:
            self.lbl_iva_info.setText(f"ℹ️ IVA Aplicado: {iva_gen:.1f}% (tasa general)")
            return
            
        try:
            res = db_manager.execute_query("SELECT iva FROM departamentos WHERE UPPER(nombre) = UPPER(?)", (dep,))
            if res and res[0]['iva'] is not None:
                self.lbl_iva_info.setText(f"ℹ️ IVA Aplicado: {res[0]['iva']:.1f}% (por departamento)")
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
class PanelDepartamentos(QWidget):
    departamentos_cambiados = pyqtSignal()
    volver = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._modo_edicion = None
        self._setup_ui()
        self._cargar()

    def _setup_ui(self):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # Toolbar contextual clara integrada (sin barra negra duplicada)
        tb = QFrame(); tb.setFixedHeight(50)
        tb.setStyleSheet("QFrame{background: white; border-bottom: 1px solid #cbd5e1;}")
        tl = QHBoxLayout(tb); tl.setContentsMargins(15,5,15,5); tl.setSpacing(10)
        btn_volver = QPushButton("⬅ Volver al Catálogo"); btn_volver.setObjectName("gray")
        btn_volver.clicked.connect(self.volver.emit)
        self.btn_nuevo_dep = QPushButton("📁 Limpiar Formulario")
        self.btn_nuevo_dep.clicked.connect(self._iniciar_nuevo)
        self.btn_elim_dep  = QPushButton("✖ Eliminar Seleccionado"); self.btn_elim_dep.setObjectName("danger")
        self.btn_elim_dep.clicked.connect(self._eliminar)
        for w in [btn_volver, self.btn_nuevo_dep, self.btn_elim_dep]: tl.addWidget(w)
        tl.addStretch()
        root.addWidget(tb)

        sp = QSplitter(Qt.Horizontal)

        # Árbol izquierdo
        left = QWidget(); ll = QVBoxLayout(left); ll.setContentsMargins(15,15,15,15); ll.setSpacing(10)
        lbl = QLabel("DEPARTAMENTOS (CATEGORÍAS DE IMPUESTOS)")
        lbl.setStyleSheet("font-weight: 900;  font-size: 13px;")
        self.txt_buscar = QLineEdit(); self.txt_buscar.setPlaceholderText("🔍 Buscar depto o categoría...")
        self.txt_buscar.textChanged.connect(lambda t: self._cargar(t))
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Depto / Categoría", "IVA (%)"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.itemClicked.connect(self._seleccionar)
        ll.addWidget(lbl); ll.addWidget(self.txt_buscar); ll.addWidget(self.tree)
        sp.addWidget(left)

        # Formulario derecho flotante
        right = QWidget()
        rl_main = QVBoxLayout(right)
        rl_main.setContentsMargins(20, 20, 20, 20)
        
        form_card = QFrame()
        form_card.setStyleSheet("background: white; border: 1px solid #E2E8F0; border-radius: 12px;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        form_card.setGraphicsEffect(shadow)
        
        rl = QVBoxLayout(form_card)
        rl.setContentsMargins(20, 20, 20, 20)
        rl.setSpacing(15)
        
        self.lbl_titulo_form = QLabel("NUEVO DEPARTAMENTO E IMPUESTOS")
        self.lbl_titulo_form.setStyleSheet("font-weight: 900; font-size: 15px; border: none;")
        
        lbl_n = QLabel("Nombre de la categoría/departamento:")
        lbl_n.setStyleSheet("font-weight: bold; border: none;")
        self.txt_nombre_dep = QLineEdit()
        self.txt_nombre_dep.setStyleSheet("border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px; background: #F8FAFC; font-size: 14px; font-weight: bold;")
        
        lbl_iva = QLabel("Tasa de IVA (%):")
        lbl_iva.setStyleSheet("font-weight: bold; border: none;")
        self.txt_iva_dep = QLineEdit("21.0")
        self.txt_iva_dep.setStyleSheet("border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px; background: #F8FAFC; font-size: 14px; font-weight: bold;")
        
        bx2 = QHBoxLayout()
        self.btn_guardar_dep = QPushButton("✔ Guardar Configuración")
        self.btn_guardar_dep.setObjectName("blue")
        self.btn_cancelar_dep = QPushButton("✖ Cancelar")
        self.btn_cancelar_dep.setObjectName("gray")
        self.btn_guardar_dep.clicked.connect(self._guardar)
        self.btn_cancelar_dep.clicked.connect(self._iniciar_nuevo)
        
        bx2.addWidget(self.btn_guardar_dep)
        bx2.addWidget(self.btn_cancelar_dep)
        
        rl.addWidget(self.lbl_titulo_form)
        rl.addWidget(lbl_n)
        rl.addWidget(self.txt_nombre_dep)
        rl.addWidget(lbl_iva)
        rl.addWidget(self.txt_iva_dep)
        rl.addLayout(bx2)
        rl.addStretch()
        
        rl_main.addWidget(form_card)
        sp.addWidget(right)
        sp.setSizes([350, 650])
        root.addWidget(sp)

    def _cargar(self, filtro=''):
        try:
            insert_kw = "INSERT IGNORE INTO" if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb" else "INSERT OR IGNORE INTO"
            db_manager.execute_non_query("CREATE TABLE IF NOT EXISTS departamentos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL, iva REAL DEFAULT 21.0)")
            db_manager.execute_non_query(f"{insert_kw} departamentos (nombre) SELECT DISTINCT departamento FROM productos WHERE departamento IS NOT NULL AND departamento != ''")
        except: pass

        self.tree.clear()
        sd = QTreeWidgetItem(self.tree, ["- Sin Departamento -", "—"])
        sd.setData(0, Qt.UserRole, -1)
        rows = db_manager.execute_query("SELECT id,nombre,iva FROM departamentos ORDER BY nombre") or []
        for r in rows:
            if filtro and filtro.lower() not in r['nombre'].lower(): continue
            it = QTreeWidgetItem(self.tree, [r['nombre'], f"{r['iva']:.1f}%"])
            it.setData(0, Qt.UserRole, r['id'])

    def _iniciar_nuevo(self):
        self._modo_edicion = None
        self.lbl_titulo_form.setText("NUEVO DEPARTAMENTO E IMPUESTOS")
        self.txt_nombre_dep.clear()
        self.txt_iva_dep.setText("21.0")
        self.txt_nombre_dep.setFocus()

    def _seleccionar(self, item, _):
        id_dep = item.data(0, Qt.UserRole)
        if id_dep and id_dep != -1:
            self._modo_edicion = id_dep
            self.lbl_titulo_form.setText("EDITAR DEPARTAMENTO E IMPUESTOS")
            self.txt_nombre_dep.setText(item.text(0))
            try:
                res = db_manager.execute_query("SELECT iva FROM departamentos WHERE id = ?", (id_dep,))
                if res and res[0]['iva'] is not None:
                    self.txt_iva_dep.setText(f"{res[0]['iva']:.1f}")
                else:
                    self.txt_iva_dep.setText("21.0")
            except:
                self.txt_iva_dep.setText("21.0")
        else:
            self._iniciar_nuevo()

    def _guardar(self):
        nombre = self.txt_nombre_dep.text().strip()
        if not nombre: QMessageBox.warning(self,"Requerido","Ingresá un nombre."); return
        try:
            iva_val = float(self.txt_iva_dep.text().strip())
            if iva_val < 0: raise ValueError()
        except:
            QMessageBox.warning(self, "Error", "La tasa de IVA debe ser un número positivo."); return

        if self._modo_edicion:
            ok = db_manager.execute_non_query("UPDATE departamentos SET nombre=?, iva=? WHERE id=?",(nombre,iva_val,self._modo_edicion))
        else:
            # Verificar si el departamento ya existe antes de insertar
            existe = db_manager.execute_query("SELECT id FROM departamentos WHERE nombre = ?", (nombre,))
            if existe:
                QMessageBox.warning(self, "Duplicado", f"El departamento '{nombre}' ya existe.")
                return
            ok = db_manager.execute_non_query("INSERT INTO departamentos (nombre, iva) VALUES (?, ?)", (nombre, iva_val))
        if ok:
            self._cargar(); self.departamentos_cambiados.emit(); self._iniciar_nuevo()
        else:
            QMessageBox.warning(self,"Error","No se pudo guardar.")

    def _eliminar(self):
        item = self.tree.currentItem()
        if not item: return
        id_dep = item.data(0, Qt.UserRole)
        if not id_dep or id_dep == -1: return
        nombre_depto = item.text(0)
        if QMessageBox.question(self,"Confirmar",f"¿Eliminar '{nombre_depto}'?",
                                QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            # Limpiar productos huérfanos antes de eliminar el departamento
            db_manager.execute_non_query(
                "UPDATE productos SET departamento = '' WHERE departamento = ?",
                (nombre_depto,)
            )
            db_manager.execute_non_query("DELETE FROM departamentos WHERE id=?",(id_dep,))
            self._cargar(); self.departamentos_cambiados.emit()


# ── Panel Categorias (Departamentos de Mercadería) ──
class PanelCategorias(QWidget):
    categorias_cambiadas = pyqtSignal()
    volver = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._modo_edicion = None
        self._setup_ui()
        self._cargar()

    def _setup_ui(self):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        tb = QFrame(); tb.setFixedHeight(50)
        tb.setStyleSheet("QFrame{background: white; border-bottom: 1px solid #cbd5e1;}")
        tl = QHBoxLayout(tb); tl.setContentsMargins(15,5,15,5); tl.setSpacing(10)
        btn_volver = QPushButton("⬅ Volver al Catálogo"); btn_volver.setObjectName("gray")
        btn_volver.clicked.connect(self.volver.emit)
        tl.addWidget(btn_volver); tl.addStretch()
        root.addWidget(tb)

        content = QWidget(); cl = QVBoxLayout(content); cl.setContentsMargins(20,20,20,20); cl.setSpacing(20)
        lbl = QLabel("DEPARTAMENTOS DE MERCADERÍA")
        lbl.setStyleSheet("font-size:18px; font-weight:800; ")
        cl.addWidget(lbl)

        grid = QGridLayout()
        # Formulario
        form_frame = QFrame()
        form_frame.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E2E8F0;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        form_frame.setGraphicsEffect(shadow)
        
        form_lay = QVBoxLayout(form_frame)
        form_lay.setContentsMargins(20, 20, 20, 20)
        form_lay.setSpacing(15)
        
        self.lbl_titulo_form = QLabel("NUEVO DEPARTAMENTO")
        self.lbl_titulo_form.setStyleSheet("font-weight: 800; font-size: 14px; border: none;")
        form_lay.addWidget(self.lbl_titulo_form)
        
        lbl_n = QLabel("Nombre del departamento:")
        lbl_n.setStyleSheet("border: none; font-weight: bold;")
        self.txt_nombre_cat = QLineEdit()
        self.txt_nombre_cat.setPlaceholderText("Ej. Lácteos, Bebidas, Almacén...")
        self.txt_nombre_cat.setStyleSheet("padding: 12px; border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC;")
        form_lay.addWidget(lbl_n)
        form_lay.addWidget(self.txt_nombre_cat)

        h_btn = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar"); btn_cancelar.setObjectName("gray")
        btn_cancelar.clicked.connect(self._iniciar_nuevo)
        btn_guardar = QPushButton("Guardar Departamento"); btn_guardar.setObjectName("blue")
        btn_guardar.clicked.connect(self._guardar)
        h_btn.addWidget(btn_cancelar); h_btn.addWidget(btn_guardar)
        form_lay.addLayout(h_btn); form_lay.addStretch()
        grid.addWidget(form_frame, 0, 0)

        # Lista
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Nombre del Departamento", "ID"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setStyleSheet("QTreeWidget { background: white; border: 1px solid #E2E8F0; border-radius: 8px; font-size: 13px; }")
        grid.addWidget(self.tree, 0, 1)

        h_actions = QHBoxLayout()
        btn_editar = QPushButton("Editar Seleccionado"); btn_editar.setObjectName("gray")
        btn_editar.clicked.connect(self._cargar_para_edicion)
        btn_elim = QPushButton("Eliminar Seleccionado"); btn_elim.setObjectName("danger")
        btn_elim.clicked.connect(self._eliminar)
        h_actions.addWidget(btn_editar); h_actions.addWidget(btn_elim); h_actions.addStretch()
        cl.addLayout(grid)
        cl.addLayout(h_actions)
        root.addWidget(content)

    def _cargar(self):
        try:
            insert_kw = "INSERT IGNORE INTO" if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb" else "INSERT OR IGNORE INTO"
            db_manager.execute_non_query("CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL)")
            db_manager.execute_non_query(f"{insert_kw} categorias (nombre) SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL AND categoria != ''")
        except: pass

        self.tree.clear()
        sd = QTreeWidgetItem(self.tree, ["- Sin Departamento -", "—"])
        sd.setForeground(0, QBrush(QColor("#64748b")))
        rows = db_manager.execute_query("SELECT id, nombre FROM categorias ORDER BY nombre") or []
        for r in rows:
            it = QTreeWidgetItem(self.tree, [r['nombre'], str(r['id'])])
            it.setData(0, Qt.UserRole, r['id'])

    def _iniciar_nuevo(self):
        self._modo_edicion = None
        self.txt_nombre_cat.clear()
        self.lbl_titulo_form.setText("NUEVO DEPARTAMENTO")

    def _cargar_para_edicion(self):
        item = self.tree.currentItem()
        if not item: return
        id_cat = item.data(0, Qt.UserRole)
        if not id_cat or id_cat == -1: return
        self._modo_edicion = id_cat
        self.txt_nombre_cat.setText(item.text(0))
        self.lbl_titulo_form.setText("EDITAR DEPARTAMENTO")

    def _guardar(self):
        nombre = self.txt_nombre_cat.text().strip()
        if not nombre: QMessageBox.warning(self,"Requerido","Ingresá un nombre."); return
        if self._modo_edicion:
            ok = db_manager.execute_non_query("UPDATE categorias SET nombre=? WHERE id=?",(nombre,self._modo_edicion))
        else:
            existe = db_manager.execute_query("SELECT id FROM categorias WHERE nombre = ?", (nombre,))
            if existe:
                QMessageBox.warning(self, "Duplicado", f"El departamento '{nombre}' ya existe.")
                return
            ok = db_manager.execute_non_query("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
        if ok:
            self._cargar(); self.categorias_cambiadas.emit(); self._iniciar_nuevo()
        else:
            QMessageBox.warning(self,"Error","No se pudo guardar.")

    def _eliminar(self):
        item = self.tree.currentItem()
        if not item: return
        id_cat = item.data(0, Qt.UserRole)
        if not id_cat or id_cat == -1: return
        nombre_cat = item.text(0)
        if QMessageBox.question(self,"Confirmar",f"¿Eliminar '{nombre_cat}'?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            db_manager.execute_non_query("UPDATE productos SET categoria = 'GENERAL' WHERE categoria = ?", (nombre_cat,))
            db_manager.execute_non_query("DELETE FROM categorias WHERE id=?",(id_cat,))
            self._cargar(); self.categorias_cambiadas.emit()

# ── Catálogo de Productos ────────────────────────────────
class CatalogoProductos(QWidget):
    volver = pyqtSignal()

    HEADERS = ["", "Código", "Descripción del Producto", "Departamento", "IVA (%)",
               "Costo", "P. Venta", "Regla Promo", "Of. Relámpago", "Of. Promedio", "Existencia",
               "Inv. Mínimo", "Inv. Máximo", "Tipo de Venta"]

    DEPTO_COLORS = [
        "#FFFFFF", "#F8FAFC", "#F0F9FF", "#ECFDF5",
        "#FFFBEB", "#FFF1F2", "#F5F3FF", "#FDF4FF",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._depto_color_map = {}
        self.all_rows = []
        self.loaded_count = 0
        self._setup_ui()
        self._cargar_deptos()
        self.cargar_datos()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(8)
        self.setStyleSheet("background-color: #F8FAFC;")

        from src.config import config
        from src.shared.urgencia_stock_banner import UrgenciaStockBanner

        self._urgencia_banner = UrgenciaStockBanner(self)
        root.addWidget(self._urgencia_banner)

        # ── Barra de filtros ─────────────────────────────
        fb = QFrame(); fb.setFixedHeight(60)
        fb.setStyleSheet("QFrame { background: #FFFFFF; border-bottom: 1px solid #E2E8F0; }")
        fl = QHBoxLayout(fb); fl.setContentsMargins(15, 6, 15, 6); fl.setSpacing(12)
        
        ico_search = QLabel("🔍")
        ico_search.setStyleSheet(" font-size: 16px; background: transparent;")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre, código o ID...")
        self.txt_buscar.setMinimumWidth(350)
        
        # Debounce timer para búsqueda rápida sin lag
        from PyQt6.QtCore import QTimer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.cargar_datos)
        self.txt_buscar.textChanged.connect(lambda: self.search_timer.start(300))

        lbl_dep = QLabel("FILTRAR POR DEPARTAMENTO:")
        lbl_dep.setStyleSheet("font-weight:800;font-size:10px;letter-spacing:1px; background: transparent;")
        self.cmb_depto = QComboBox()
        self.cmb_depto.setMinimumWidth(200)
        self.cmb_depto.currentIndexChanged.connect(self.cargar_datos)

        fl.addWidget(ico_search)
        fl.addWidget(self.txt_buscar)
        fl.addSpacing(15)
        fl.addWidget(lbl_dep); fl.addWidget(self.cmb_depto)
        fl.addSpacing(20)

        self.chk_venta_sin_stock = QCheckBox("🚨 Urgencia: vender sin stock")
        self.chk_venta_sin_stock.setToolTip(
            "Solo para emergencias. El cajero podrá vender aunque no haya existencia "
            "y se mostrará una alerta parpadeante mientras esté activo."
        )
        self.chk_venta_sin_stock.setStyleSheet(
            "QCheckBox { font-weight: 800; color: #B91C1C; padding: 4px 8px; "
            "border: 1px solid #FECACA; border-radius: 6px; background: #FFF7ED; }"
            "QCheckBox::indicator { width: 18px; height: 18px; }"
        )
        self.chk_venta_sin_stock.setChecked(bool(config.get("opt_stock_negativo", False)))
        self.chk_venta_sin_stock.toggled.connect(self._toggle_venta_sin_stock)
        fl.addWidget(self.chk_venta_sin_stock)

        fl.addStretch()
        root.addWidget(fb)

        self._sync_urgencia_banner()

        # ── Tabla ────────────────────────────────────────
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(self.HEADERS))
        self.tabla.setHorizontalHeaderLabels(self.HEADERS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setAlternatingRowColors(False)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setShowGrid(False)
        self.tabla.setStyleSheet("""
            QTableWidget {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                gridline-color: transparent;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px 10px;
                color: #0F172A;
                border-bottom: 1px solid #F1F5F9;
            }
            QTableWidget::item:hover {
                background-color: #F1F5F9;
            }
            QTableWidget::item:selected {
                background-color: #EFF6FF;
                color: #1D4ED8;
                border-bottom: 2px solid #3B82F6;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #64748B;
                font-weight: 900;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """)
        # Agregamos el ancho de "Regla Promo" (110) para tener 14 columnas
        col_widths = [28, 100, -1, 130, 70, 80, 80, 110, 95, 95, 80, 80, 80, 90]
        hh = self.tabla.horizontalHeader()
        for i, w in enumerate(col_widths):
            if w == -1:
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Fixed)
                self.tabla.setColumnWidth(i, w)

        self.tabla.verticalHeader().setDefaultSectionSize(40)
        self.tabla.doubleClicked.connect(self._modificar_seleccionado)
        root.addWidget(self.tabla)

        # ── Footer ───────────────────────────────────────
        ft = QFrame(); ft.setFixedHeight(38)
        ft.setStyleSheet("QFrame { background: #FFFFFF; border-top: 1px solid #E2E8F0; }")
        fl2 = QHBoxLayout(ft); fl2.setContentsMargins(12, 0, 12, 0)
        self.lbl_total   = QLabel("0 productos")
        self.lbl_stock0  = QLabel("")
        self.lbl_sel     = QLabel("")
        for lbl in [self.lbl_total, self.lbl_stock0, self.lbl_sel]:
            lbl.setStyleSheet("font-size:11px; background: transparent;")
        fl2.addWidget(self.lbl_total)
        fl2.addSpacing(20); fl2.addWidget(self.lbl_stock0)
        fl2.addStretch();   fl2.addWidget(self.lbl_sel)
        root.addWidget(ft)

        self.tabla.itemSelectionChanged.connect(self._actualizar_sel)
        self.tabla.verticalScrollBar().valueChanged.connect(self._al_hacer_scroll)

    def _apply_catalogo_theme(self):
        """Mantiene tabla y filtros en modo claro aunque theme_manager reaplique estilos."""
        self.setStyleSheet("background-color: #F8FAFC;")
        if hasattr(self, "tabla"):
            self.tabla.setStyleSheet("""
                QTableWidget {
                    background: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 12px;
                    gridline-color: transparent;
                    outline: none;
                }
                QTableWidget::item {
                    padding: 8px 10px;
                    color: #0F172A;
                    border-bottom: 1px solid #F1F5F9;
                }
                QTableWidget::item:hover {
                    background-color: #F1F5F9;
                }
                QTableWidget::item:selected {
                    background-color: #EFF6FF;
                    color: #1D4ED8;
                    border-bottom: 2px solid #3B82F6;
                }
                QHeaderView::section {
                    background-color: #F8FAFC;
                    color: #64748B;
                    font-weight: 900;
                    padding: 12px 8px;
                    border: none;
                    border-bottom: 2px solid #E2E8F0;
                    font-size: 11px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
            """)
        if hasattr(self, "txt_buscar"):
            self.txt_buscar.setStyleSheet(
                "QLineEdit { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; "
                "border-radius: 8px; padding: 10px 14px; font-size: 13px; }"
                "QLineEdit:focus { border: 2px solid #3B82F6; }"
            )
        if hasattr(self, "cmb_depto"):
            self.cmb_depto.setStyleSheet(
                "QComboBox { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; "
                "border-radius: 8px; padding: 8px 12px; }"
                "QComboBox:focus { border: 2px solid #3B82F6; }"
            )

    def _sync_urgencia_banner(self):
        activo = bool(self.chk_venta_sin_stock.isChecked())
        self._urgencia_banner.set_active(activo)
        self.chk_venta_sin_stock.setStyleSheet(
            "QCheckBox { font-weight: 800; color: #B91C1C; padding: 4px 8px; "
            "border: 2px solid #DC2626; border-radius: 6px; background: #FEE2E2; }"
            "QCheckBox::indicator { width: 18px; height: 18px; }"
            if activo
            else "QCheckBox { font-weight: 800; color: #B91C1C; padding: 4px 8px; "
            "border: 1px solid #FECACA; border-radius: 6px; background: #FFF7ED; }"
            "QCheckBox::indicator { width: 18px; height: 18px; }"
        )

    def _toggle_venta_sin_stock(self, checked: bool):
        from src.config import config

        if checked:
            r = QMessageBox.warning(
                self,
                "Modo urgencia — vender sin stock",
                "Estás activando una excepción a las reglas de inventario.\n\n"
                "• El cajero podrá vender productos sin existencia.\n"
                "• Habrá una alerta PARPADEANTE en inventario y en el terminal.\n\n"
                "Desactivalo cuando termine la urgencia.",
                QMessageBox.Ok | QMessageBox.Cancel,
                QMessageBox.Cancel,
            )
            if r != QMessageBox.Ok:
                self.chk_venta_sin_stock.blockSignals(True)
                self.chk_venta_sin_stock.setChecked(False)
                self.chk_venta_sin_stock.blockSignals(False)
                self._sync_urgencia_banner()
                return

        config.set("opt_stock_negativo", bool(checked))
        self._sync_urgencia_banner()

    def showEvent(self, event):
        super().showEvent(event)
        from src.config import config

        self.chk_venta_sin_stock.blockSignals(True)
        self.chk_venta_sin_stock.setChecked(bool(config.get("opt_stock_negativo", False)))
        self.chk_venta_sin_stock.blockSignals(False)
        self._sync_urgencia_banner()

    def _cargar_deptos(self):
        self.cmb_depto.blockSignals(True)
        self.cmb_depto.clear()
        self.cmb_depto.addItem("— Todas las categorías —", None)
        try:
            cats = db_manager.execute_query(
                "SELECT DISTINCT categoria FROM productos "
                "WHERE categoria IS NOT NULL ORDER BY categoria"
            ) or []
            for r in cats:
                cat = r['categoria']
                if cat and cat.upper() != "GENERAL":
                    self.cmb_depto.addItem(cat, cat)
        except: pass
        self.cmb_depto.blockSignals(False)

    def cargar_datos(self):
        buscar = self.txt_buscar.text().strip()
        depto  = self.cmb_depto.currentData()

        q = "SELECT p.*, d.iva AS depto_iva FROM productos p LEFT JOIN departamentos d ON UPPER(p.departamento) = UPPER(d.nombre) WHERE 1=1"
        p = []
        if buscar:
            q += " AND (p.nombre LIKE ? OR CAST(p.id AS TEXT) LIKE ? OR COALESCE(p.codigo,'') LIKE ?)"
            p += [f"%{buscar}%"] * 3
        if depto:
            q += " AND p.departamento=?"
            p.append(depto)
        q += " ORDER BY p.departamento, p.nombre"
        # q += " LIMIT 5000"  # Removido para permitir carga completa con paginación diferida

        self.all_rows = db_manager.execute_query(q, tuple(p)) or []
        self._depto_color_map = {}
        self.loaded_count = 0
        self.tabla.setRowCount(0)
        
        # Cargar la primera página
        self._cargar_siguiente_pagina()

        # Calcular stock crítico de forma rápida de la memoria sin trabar la UI
        sin_stock = sum(1 for r in self.all_rows if (r['stock'] or 0.0) <= 0)

        n = len(self.all_rows)
        self.lbl_total.setText(f"📦 {n} PRODUCTOS EN INVENTARIO")
        self.lbl_total.setStyleSheet(" font-weight: 800; background: transparent;")
        self.lbl_stock0.setText(
            f"⚠️ Stock Crítico: {sin_stock}" if sin_stock else "✅ Stock Saludable"
        )
        self.lbl_stock0.setStyleSheet(
            f"color:{'#ef4444' if sin_stock else '#10b981'}; font-size:11px; font-weight:bold; background: transparent;"
        )

    def _cargar_siguiente_pagina(self):
        if getattr(self, '_loading_page', False):
            return
        self._loading_page = True
        try:
            if self.loaded_count >= len(self.all_rows):
                return
                
            inicio = self.loaded_count
            fin = min(inicio + 50, len(self.all_rows))
            
            self.tabla.blockSignals(True)
            self.tabla.setRowCount(fin)
            
            for i in range(inicio, fin):
                r = self.all_rows[i]
                dep   = r['departamento'] or ''
                stock = r['stock'] or 0.0
                uni   = (r['unidad'] or 'UN').upper()
                tipo  = "KILO" if uni == 'KG' else "UNIDAD"
                
                depto_iva = None
                try:
                    depto_iva = r['depto_iva']
                except (IndexError, KeyError, TypeError):
                    pass
                    
                if depto_iva is None:
                    from src.admin.admin5_configuracion import config
                    depto_iva = float(config.get("tax_percentage", 21.0))
                else:
                    depto_iva = float(depto_iva)

                dep_key = (dep or "GENERAL").upper()
                if dep_key not in self._depto_color_map:
                    idx = len(self._depto_color_map) % len(self.DEPTO_COLORS)
                    self._depto_color_map[dep_key] = self.DEPTO_COLORS[idx]
                base_hex = self._depto_color_map[dep_key]
                if i % 2 == 1 and base_hex == "#FFFFFF":
                    base_hex = "#F8FAFC"
                row_bg = QColor(base_hex)
                chk = QTableWidgetItem()
                chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                chk.setCheckState(Qt.Unchecked)
                chk.setBackground(row_bg)
                self.tabla.setItem(i, 0, chk)

                vals = [
                    (str(r['id']),       Qt.AlignRight),
                    (r['nombre'] or '',  Qt.AlignLeft),
                    (dep,                Qt.AlignLeft),
                    (f"{depto_iva:.1f}%", Qt.AlignCenter),
                    (f"${r['costo']:.2f}", Qt.AlignRight),
                    (f"${r['precio']:.2f}", Qt.AlignRight),
                    (f"{r['cant_oferta']:g} x ${r['precio_oferta']:.2f}" if r.get('precio_oferta') else "-", Qt.AlignCenter),
                    (f"${r['precio_oferta_relampago']:.2f}" if r.get('precio_oferta_relampago') else "-", Qt.AlignCenter),
                    (f"${r['precio_oferta_promedio']:.2f}" if r.get('precio_oferta_promedio') else "-", Qt.AlignCenter),
                    (f"{stock:.2f}",     Qt.AlignRight),
                    (f"{r['stock_minimo'] or 0:.2f}", Qt.AlignCenter),
                    (f"{r['stock_maximo'] or 0:.2f}", Qt.AlignCenter),
                    (tipo,               Qt.AlignCenter),
                ]

                for j, (v, align) in enumerate(vals, 1):
                    it = QTableWidgetItem(v)
                    it.setTextAlignment(Qt.AlignVCenter | align)
                    it.setBackground(row_bg)
                    it.setForeground(QColor("#0F172A"))

                    if j == 7 or j == 8:  # Resaltar si hay oferta
                        if v != "-":
                            it.setForeground(QColor("#EA580C"))
                            it.setFont(QFont("Segoe UI", 9, QFont.Bold))

                    if j == 9: # Stock
                        if stock <= 0:
                            it.setForeground(QColor("#DC2626"))
                            it.setBackground(QColor("#FEF2F2"))
                        elif stock < 5:
                            it.setForeground(QColor("#D97706"))
                            it.setBackground(QColor("#FFFBEB"))
                        else:
                            it.setForeground(QColor("#059669"))

                    if j == 12: # Tipo
                        it.setForeground(QColor("#2563EB"))
                        it.setFont(QFont("Segoe UI", 9, QFont.Bold))

                    self.tabla.setItem(i, j, it)
                    
            self.loaded_count = fin
        finally:
            self.tabla.blockSignals(False)
            self._loading_page = False

    def _al_hacer_scroll(self, value):
        bar = self.tabla.verticalScrollBar()
        if bar.maximum() > 0 and value >= bar.maximum() - 15:
            self._cargar_siguiente_pagina()

    def _actualizar_sel(self):
        sel = len(self.tabla.selectedItems()) // len(self.HEADERS)
        self.lbl_sel.setText(f"Seleccionados: {sel}" if sel else "")

    def _modificar_seleccionado(self, *args, **kwargs):
        row = self.tabla.currentRow()
        if row == -1:
            QMessageBox.information(self, "Selección", "Seleccioná un producto primero.")
            return
        item_id = self.tabla.item(row, 1)
        if not item_id:
            return
        id_p = item_id.text()
        rows = db_manager.execute_query("SELECT * FROM productos WHERE id=?", (id_p,)) or []
        if not rows: 
            return
        r = rows[0]
        def get_val(col, default=0.0):
            try: 
                return r[col] if r[col] is not None else default
            except: 
                return default

        datos = {
            'id': r['id'], 
            'codigo': r['codigo'] or '', 
            'nombre': r['nombre'] or '',
            'precio': r['precio'] if r['precio'] is not None else 0.0, 
            'precio_mayoreo': r['precio_mayoreo'] if r['precio_mayoreo'] is not None else 0.0,
            'cant_oferta': get_val('cant_oferta', 0.0), 
            'precio_oferta': get_val('precio_oferta', 0.0),
            'costo': r['costo'] if r['costo'] is not None else 0.0, 
            'stock': r['stock'] if r['stock'] is not None else 0.0,
            'stock_minimo': r['stock_minimo'] if r['stock_minimo'] is not None else 0.0, 
            'stock_maximo': r['stock_maximo'] if r['stock_maximo'] is not None else 0.0,
            'unidad': r['unidad'] or 'UN', 
            'es_pesable': r['es_pesable'] if r['es_pesable'] is not None else 0,
            'departamento': r['departamento'] or '', 
            'categoria': r['categoria'] or 'GENERAL'
        }
        dlg = DialogoProducto(datos, self)
        if qt_exec(dlg):
            d = dlg.get_data()
            ok = db_manager.execute_non_query(
                "UPDATE productos SET codigo=?,nombre=?,precio=?,precio_mayoreo=?,cant_oferta=?,precio_oferta=?,costo=?,stock=?,"
                "stock_minimo=?,stock_maximo=?,unidad=?,es_pesable=?,departamento=?,categoria=? WHERE id=?",
                (d['codigo'], d['nombre'], d['precio'], d['precio_mayoreo'], d['cant_oferta'], d['precio_oferta'], d['costo'], d['stock'],
                 d['stock_minimo'], d['stock_maximo'], d['unidad'], d['es_pesable'], d['departamento'], d['categoria'], d['id']))
            if ok:
                self._cargar_deptos()
                self.cargar_datos()
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar el producto. Verifique los campos ingresados o si el código ya existe.")

    def _exportar(self):
        from datetime import datetime
        nombre_def = f"productos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exportar productos", nombre_def,
            "Excel (*.xlsx);;Todos los archivos (*)")
        if not filepath: return
        
        # Inyectar trabajador en segundo plano
        class WorkerExport(QThread):
            finished = pyqtSignal(bool, str)
            def __init__(self, path):
                super().__init__()
                self.path = path
            def run(self):
                from src.admin.admin_importexport import exportar_excel
                ok, msg = exportar_excel(self.path)
                self.finished.emit(ok, msg)
                
        self._btn_sender = self.sender() # Identifica qué botón presiono
        if self._btn_sender:
            self._old_text = self._btn_sender.text()
            self._btn_sender.setText("⏳ CARGANDO...")
            self._btn_sender.setEnabled(False)
            
        self._worker_exp = WorkerExport(filepath)
        def on_fin(ok, msg):
            if self._btn_sender:
                self._btn_sender.setText(self._old_text)
                self._btn_sender.setEnabled(True)
            (QMessageBox.information if ok else QMessageBox.critical)(
                self, "Exportación" + (" exitosa" if ok else " fallida"), msg)
        self._worker_exp.finished.connect(on_fin)
        self._worker_exp.start()

    def _descargar_precarga(self):
        respuesta = QMessageBox.question(
            self, "Precarga desde la Nube",
            "¿Deseas descargar y sumar ~12,800 productos precargados desde la nube a tu base de datos?\n(Esto tomará un par de segundos)",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if respuesta != QMessageBox.Yes: return

        class WorkerPrecarga(QThread):
            finished = pyqtSignal(bool, str)
            def run(self):
                import urllib.request
                import json
                
                url = "https://firebasestorage.googleapis.com/v0/b/cajafacil-pro-updates.firebasestorage.app/o/inventario_precargado.json?alt=media"
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=15) as response:
                        data = json.loads(response.read().decode('utf-8'))
                        
                    if not data:
                        self.finished.emit(False, "El archivo JSON está vacío.")
                        return
                    
                    # Load existing barcodes to prevent duplicates
                    existing_res = db_manager.execute_query("SELECT codigo FROM productos WHERE codigo IS NOT NULL AND codigo != ''")
                    existing_codes = set(str(row['codigo']).strip() for row in (existing_res or []))
                    
                    # Preparar lista para inserción masiva
                    values = []
                    for item in data:
                        codigo = str(item.get("codigo", "") or "").strip()
                        nombre = str(item.get("descripcion", "") or "").strip()
                        if not codigo or not nombre:
                            continue
                        if codigo in existing_codes:
                            continue # Skip items we already have!
                            
                        values.append((
                            codigo,
                            nombre,
                            float(item.get("precio_venta") or 0.0),
                            float(item.get("precio_costo") or 0.0),
                            float(item.get("precio_mayoreo") or 0.0),
                            str(item.get("departamento", "GENERAL") or "GENERAL"),
                            float(item.get("stock") or 0.0),
                            float(item.get("stock_minimo") or 0.0),
                            float(item.get("stock_maximo") or 0.0),
                            1 if str(item.get("tipo_venta", "")).strip().lower() in ("granel", "a granel") else 0
                        ))
                        # Add to existing so we don't insert duplicate barcodes from the JSON itself
                        existing_codes.add(codigo)
                    
                    if not values:
                        self.finished.emit(True, "Tu inventario ya está actualizado. No se encontraron productos nuevos en la nube.")
                        return

                    # Inserción masiva usando executemany con sintaxis compatible
                    insert_keyword = "INSERT IGNORE INTO" if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb" else "INSERT OR IGNORE INTO"
                    query = f"""
                        {insert_keyword} productos (
                            codigo, nombre, precio, costo, precio_mayoreo,
                            departamento, stock, stock_minimo, stock_maximo, es_pesable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    db_manager.execute_many(query, values)
                    self.finished.emit(True, f"Se insertaron {len(values)} productos nuevos exitosamente.")
                except Exception as e:
                    self.finished.emit(False, str(e))

        self._btn_sender_pre = self.sender()
        if self._btn_sender_pre:
            self._old_text_pre = self._btn_sender_pre.text()
            self._btn_sender_pre.setText("⏳ DESCARGANDO...")
            self._btn_sender_pre.setEnabled(False)

        self._worker_pre = WorkerPrecarga()
        def on_fin_pre(ok, msg):
            if self._btn_sender_pre:
                self._btn_sender_pre.setText(self._old_text_pre)
                self._btn_sender_pre.setEnabled(True)
            (QMessageBox.information if ok else QMessageBox.critical)(
                self, "Precarga Nube" + (" completada" if ok else " fallida"), msg)
            if ok:
                self.txt_buscar.clear()
                self.cargar_datos()

        self._worker_pre.finished.connect(on_fin_pre)
        self._worker_pre.start()

    def _unificar_duplicados(self):
        respuesta = QMessageBox.question(
            self, "Unificar Duplicados",
            "¿Deseas buscar y unificar automáticamente todos los productos repetidos (con el mismo código)?\n\nEl sistema acumulará el stock en el producto principal y eliminará las copias vacías o basura.\nEste proceso no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if respuesta != QMessageBox.Yes: return
        
        from src.utils.db import db_manager
        
        # 1. Obtener todos los productos
        res = db_manager.execute_query("SELECT id, codigo, nombre, precio, stock FROM productos WHERE codigo IS NOT NULL AND codigo != ''")
        if not res: return
        
        # 2. Agrupar por código
        por_codigo = {}
        for p in res:
            cod = str(p['codigo']).strip()
            if not cod: continue
            if cod not in por_codigo:
                por_codigo[cod] = []
            por_codigo[cod].append(p)
            
        unificados = 0
        eliminados = 0
        
        for cod, lista in por_codigo.items():
            if len(lista) > 1:
                # Elegir el principal (el que tenga mayor precio, luego mayor stock)
                lista.sort(key=lambda x: (float(x['precio'] or 0), float(x['stock'] or 0)), reverse=True)
                principal = lista[0]
                clones = lista[1:]
                
                stock_acumulado = float(principal['stock'] or 0)
                ids_a_borrar = []
                for clon in clones:
                    stock_acumulado += float(clon['stock'] or 0)
                    ids_a_borrar.append(clon['id'])
                    
                if ids_a_borrar:
                    # Actualizar stock del principal
                    db_manager.execute_query("UPDATE productos SET stock = ? WHERE id = ?", (stock_acumulado, principal['id']))
                    # Actualizar referencias en detalles_ventas (por si acaso usaban el ID del clon)
                    for cid in ids_a_borrar:
                        db_manager.execute_query("UPDATE detalles_ventas SET id_producto = ? WHERE id_producto = ?", (str(principal['id']), str(cid)))
                        db_manager.execute_query("DELETE FROM productos WHERE id = ?", (cid,))
                        eliminados += 1
                unificados += 1
                
        QMessageBox.information(self, "Unificación Completada", f"Se unificaron {unificados} códigos distintos.\nSe eliminaron {eliminados} productos duplicados (clones) de la base de datos.")
        self.txt_buscar.clear()
        self.cargar_datos()

    def _importar(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Importar productos", "",
            "Excel (*.xlsx *.xls);;Todos los archivos (*)")
        if not filepath: return

        class WorkerImport(QThread):
            finished = pyqtSignal(bool, str)
            def __init__(self, path):
                super().__init__()
                self.path = path
            def run(self):
                from src.admin.admin_importexport import importar_excel
                ok, msg = importar_excel(self.path)
                self.finished.emit(ok, msg)

        self._btn_sender_imp = self.sender()
        if self._btn_sender_imp:
            self._old_text_imp = self._btn_sender_imp.text()
            self._btn_sender_imp.setText("⏳ CARGANDO...")
            self._btn_sender_imp.setEnabled(False)

        self._worker_imp = WorkerImport(filepath)
        def on_fin_imp(ok, msg):
            if self._btn_sender_imp:
                self._btn_sender_imp.setText(self._old_text_imp)
                self._btn_sender_imp.setEnabled(True)
            (QMessageBox.information if ok else QMessageBox.critical)(
                self, "Importación" + (" completada" if ok else " fallida"), msg)
            if ok:
                self._cargar_deptos(); self.cargar_datos()
        self._worker_imp.finished.connect(on_fin_imp)
        self._worker_imp.start()

# ── Pantalla principal Inventario ─────────────────────────
class Admin1Inventario(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._apply_inventario_theme()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_inventario_theme()

    def _apply_inventario_theme(self):
        """Reaplica tema claro tras theme_manager (se ejecuta al lazy-load)."""
        self.setStyleSheet(STYLE)
        if hasattr(self, "catalogo"):
            self.catalogo._apply_catalogo_theme()

    def _setup_ui(self):
        self.setStyleSheet(STYLE)
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # Header Elite Blue (Cajero Style unificado sin recuadro blanco)
        hdr = QFrame(); hdr.setObjectName("header"); hdr.setFixedHeight(85)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(25,0,25,0)
        
        btn_back = QPushButton("🔙 VOLVER AL PANEL")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                background: #FFFFFF; color: #0F172A; font-weight: 800; border-radius: 10px;
                padding: 10px 25px; border: 1px solid #CBD5E1; font-size: 11px; letter-spacing: 1px;
            }
            QPushButton:hover { background: #EFF6FF; border-color: #3B82F6; color: #1D4ED8; }
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)
        hl.addWidget(btn_back)
        
        hl.addSpacing(20)
        tit = QLabel("📦 GESTIÓN DE INVENTARIO <span style='color:#64748B;'>2026</span>")
        tit.setObjectName("titulo")
        tit.setStyleSheet("background: transparent;")
        hl.addWidget(tit); hl.addStretch()
        root.addWidget(hdr)

        # Toolbar superior
        self.toolbar = QFrame(); self.toolbar.setFixedHeight(70)
        self.toolbar.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        tl = QHBoxLayout(self.toolbar); tl.setContentsMargins(25,0,25,0); tl.setSpacing(12)
        self.btn_nuevo    = QPushButton("➕ NUEVO PRODUCTO")
        self.btn_nuevo.clicked.connect(self._nuevo)
        self.btn_modif    = QPushButton("✏️ MODIFICAR")
        self.btn_modif.clicked.connect(lambda: self.catalogo._modificar_seleccionado())
        self.btn_eliminar = QPushButton("🗑️ ELIMINAR")
        self.btn_eliminar.setObjectName("danger")
        self.btn_eliminar.clicked.connect(self._borrar_desde_catalogo)
        
        self.btn_importar = QPushButton("📥 IMPORTAR EXCEL")
        self.btn_importar.clicked.connect(lambda: self.catalogo._importar())
        self.btn_exportar = QPushButton("📤 EXPORTAR EXCEL")
        self.btn_exportar.clicked.connect(lambda: self.catalogo._exportar())
        self.btn_precarga = QPushButton("📦 PRECARGA NUBE")
        self.btn_precarga.clicked.connect(lambda: self.catalogo._descargar_precarga())
        self.btn_unificar = QPushButton("🧹 UNIFICAR DUPLICADOS")
        self.btn_unificar.setObjectName("blue")
        self.btn_unificar.clicked.connect(lambda: self.catalogo._unificar_duplicados())
        
        self.btn_categorias = QPushButton("📁 DEPARTAMENTOS")
        self.btn_categorias.clicked.connect(self._mostrar_categorias)
        
        self.btn_deptos   = QPushButton("⚖️ DEP. IMPUESTOS")
        self.btn_deptos.clicked.connect(self._mostrar_departamentos)
        
        self.btn_catalogo = QPushButton("📰 CATÁLOGO PDF")
        self.btn_catalogo.setObjectName("blue")
        self.btn_catalogo.clicked.connect(self._dialogo_catalogo_pdf)
        
        for b in [self.btn_nuevo, self.btn_modif, self.btn_eliminar, self.btn_importar, self.btn_exportar, self.btn_precarga, self.btn_unificar, self.btn_categorias, self.btn_deptos, self.btn_catalogo]:
            tl.addWidget(b)
        tl.addStretch()
        root.addWidget(self.toolbar)

        self.stack = QStackedWidget()

        self.catalogo = CatalogoProductos()

        self.panel_deptos = PanelDepartamentos()
        self.panel_deptos.volver.connect(self._volver_catalogo)
        self.panel_deptos.departamentos_cambiados.connect(self.catalogo._cargar_deptos)
        self.panel_deptos.departamentos_cambiados.connect(self.catalogo.cargar_datos)

        self.panel_categorias = PanelCategorias()
        self.panel_categorias.volver.connect(self._volver_catalogo)
        self.panel_categorias.categorias_cambiadas.connect(self.catalogo._cargar_deptos)
        self.panel_categorias.categorias_cambiadas.connect(self.catalogo.cargar_datos)

        self.stack.addWidget(self.catalogo)         # 0
        self.stack.addWidget(self.panel_deptos)     # 1
        self.stack.addWidget(self.panel_categorias) # 2

        self.stack.setCurrentIndex(0)
        root.addWidget(self.stack)
        
        # Sincronización en Tiempo Real (Solo para Modo Espectador / Red)
        from src.config import config
        from PyQt6.QtCore import QTimer
        db_path = config.get("db_path", "")
        if db_path and db_path != "":
            self.sync_timer = QTimer(self)
            self.sync_timer.timeout.connect(self.sincronizacion_silenciosa)
            self.sync_timer.start(5000) # Cada 5 segundos

    def sincronizacion_silenciosa(self):
        if not self.isVisible(): return
        if self.stack.currentIndex() != 0: return
        if self.catalogo.txt_buscar.hasFocus(): return
        
        bar = self.catalogo.tabla.verticalScrollBar()
        scroll_pos = bar.value() if bar else 0
        target_count = self.catalogo.loaded_count # Cuántos registros ya cargó el usuario con scroll
        
        self.cargar_datos()
        
        # Forzar recarga de las páginas que ya tenía scrolleadas
        if target_count > 50:
            while self.catalogo.loaded_count < target_count and self.catalogo.loaded_count < len(self.catalogo.all_rows):
                self.catalogo._cargar_siguiente_pagina()
        
        if bar:
            bar.setValue(scroll_pos)

    def _mostrar_departamentos(self, *args, **kwargs):
        self.toolbar.setVisible(False) # Elimina los botones duplicados de la vista principal
        self.stack.setCurrentIndex(1)

    def _mostrar_categorias(self, *args, **kwargs):
        self.toolbar.setVisible(False)
        self.stack.setCurrentIndex(2)

    def _volver_catalogo(self):
        self.toolbar.setVisible(True)  # Restaura la botonera al regresar
        self.stack.setCurrentIndex(0)

    def _dialogo_catalogo_pdf(self):
        visible_rows = []
        checked_rows = []
        for i in range(self.catalogo.tabla.rowCount()):
            if not self.catalogo.tabla.isRowHidden(i):
                it = self.catalogo.tabla.item(i, 0)
                id_p = self.catalogo.tabla.item(i, 1).text()
                
                # Find the row data
                row_data = None
                for r in self.catalogo.all_rows:
                    if str(r['id']) == id_p:
                        row_data = r
                        break
                        
                if row_data:
                    visible_rows.append(row_data)
                    if it and it.checkState() == Qt.Checked:
                        checked_rows.append(row_data)

        total_filtered = len(visible_rows)
        has_checked = len(checked_rows) > 0

        dlg = QDialog(self)
        dlg.setWindowTitle("Exportar Catálogo / Lista de Precios")
        dlg.setFixedSize(500, 420)
        dlg.setStyleSheet("""
            QDialog { background: white;  font-family: 'Segoe UI'; font-size: 13px; }
            QPushButton {  background-color: #3b82f6; color: white; font-weight: bold; padding: 10px; border-radius: 6px; border: none; font-size: 12px; }
            QPushButton:hover {  }
            QLineEdit, QComboBox, QSpinBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px;  background: white; }
            QRadioButton { spacing: 8px; font-weight: bold; }
        """)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)
        
        lbl_tit = QLabel("📰 CREAR CATÁLOGO DE PRECIOS (PDF)")
        lbl_tit.setStyleSheet(" font-size: 15px; font-weight: 900; letter-spacing: 0.5px;")
        lay.addWidget(lbl_tit)
        
        from PyQt6.QtWidgets import QFormLayout, QRadioButton, QSpinBox
        form = QFormLayout()
        form.setSpacing(10)
        
        txt_titulo = QLineEdit("CATÁLOGO DE PRODUCTOS")
        txt_titulo.setPlaceholderText("Título del catálogo...")
        txt_titulo.setMinimumWidth(260)
        
        txt_negocio = QLineEdit("MINI-SÚPER ELITE")
        try:
            from src.config import config as _cfg
            nombre_neg = _cfg.get("business_name", "")
            if nombre_neg:
                txt_negocio.setText(nombre_neg.upper())
        except:
            pass
            
        cmb_diseno = QComboBox()
        cmb_diseno.addItem("📋 Lista Compacta (Tabla formal)", "lista")
        cmb_diseno.addItem("🖼️ Folleto Gráfico (Tarjetas de producto)", "grilla")
        
        form.addRow("<b>Título Principal:</b>", txt_titulo)
        form.addRow("<b>Nombre del Negocio:</b>", txt_negocio)
        form.addRow("<b>Diseño del PDF:</b>", cmb_diseno)
        lay.addLayout(form)
        
        lay.addWidget(QLabel("<b>¿Qué productos incluir?</b>"))
        lay_inc = QVBoxLayout()
        rb_all = QRadioButton(f"Los {total_filtered} productos que estoy viendo ahora")
        rb_all.setChecked(True)
        
        rb_sel = QRadioButton(f"Solo los marcados [🗹] ({len(checked_rows)} seleccionados)")
        rb_sel.setEnabled(has_checked)
        if has_checked:
            rb_sel.setChecked(True)
            
        lay_inc.addWidget(rb_all)
        lay_inc.addWidget(rb_sel)
        lay.addLayout(lay_inc)
        
        lay_limite = QHBoxLayout()
        lay_limite.addWidget(QLabel("<b>Limitar a los primeros:</b>"))
        spin_limite = QSpinBox()
        spin_limite.setRange(1, 100000)
        spin_limite.setValue(total_filtered if total_filtered > 0 else 1)
        spin_limite.setSuffix(" productos")
        lay_limite.addWidget(spin_limite)
        lay_limite.addStretch()
        lay.addLayout(lay_limite)
        
        # Conectar cambios de radio button a spinbox
        def _update_spin():
            if rb_sel.isChecked():
                spin_limite.setValue(len(checked_rows) if len(checked_rows) > 0 else 1)
            else:
                spin_limite.setValue(total_filtered if total_filtered > 0 else 1)
        rb_all.toggled.connect(_update_spin)
        rb_sel.toggled.connect(_update_spin)
        
        btn_ok = QPushButton("✔ Generar PDF y Abrir")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(dlg.accept)
        lay.addSpacing(10)
        lay.addWidget(btn_ok)
        
        if qt_exec(dlg):
            if rb_sel.isChecked():
                productos_a_procesar = checked_rows
            else:
                productos_a_procesar = visible_rows
                
            limite = spin_limite.value()
            productos_a_procesar = productos_a_procesar[:limite]
                
            if not productos_a_procesar:
                QMessageBox.warning(self, "Aviso", "No hay productos para exportar.")
                return
                
            lote_catalogo = []
            for p in productos_a_procesar:
                # sqlite3.Row does not have .get() method, use bracket notation
                depto = p['departamento'] if 'departamento' in p.keys() and p['departamento'] is not None else ''
                uni = p['unidad'] if 'unidad' in p.keys() and p['unidad'] is not None else 'UN'
                
                lote_catalogo.append({
                    "id": str(p['id']),
                    "nombre": p['nombre'],
                    "precio": f"{p['precio']:.2f}" if p['precio'] is not None else "0.00",
                    "departamento": depto,
                    "unidad": uni
                })
                
            try:
                from src.services.etiquetas.renderer import EtiquetaRenderer, abrir_archivo_pdf
                ren = EtiquetaRenderer()
                pdf_path = ren.generar_pdf_catalogo_inventario(
                    lote_productos=lote_catalogo,
                    titulo_folleto=txt_titulo.text().strip(),
                    negocio=txt_negocio.text().strip(),
                    diseno_tipo=cmb_diseno.currentData()
                )
                abrir_archivo_pdf(pdf_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Fallo al generar catálogo PDF: {e}")

    def cargar_datos(self):
        self.catalogo._cargar_deptos()
        self.catalogo.cargar_datos()

    def _nuevo(self, *args, **kwargs):
        dlg = DialogoProducto(parent=self)
        if qt_exec(dlg):
            d = dlg.get_data()
            ok = db_manager.execute_non_query(
                "INSERT INTO productos (codigo,nombre,precio,precio_mayoreo,cant_oferta,precio_oferta,costo,stock,"
                "stock_minimo,stock_maximo,unidad,es_pesable,departamento,categoria) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (d['codigo'],d['nombre'],d['precio'],d['precio_mayoreo'],d['cant_oferta'],d['precio_oferta'],d['costo'],d['stock'],
                 d['stock_minimo'],d['stock_maximo'],d['unidad'],d['es_pesable'],d['departamento'],d['categoria']))
            if ok:
                self.catalogo._cargar_deptos(); self.catalogo.cargar_datos()
            else:
                QMessageBox.warning(self,"Error","No se pudo guardar.")

    def _borrar_desde_catalogo(self, *args, **kwargs):
        # 1. Obtener todas las filas seleccionadas por checkbox
        filas_a_borrar = []
        for i in range(self.catalogo.tabla.rowCount()):
            chk = self.catalogo.tabla.item(i, 0)
            if chk and chk.checkState() == Qt.Checked:
                filas_a_borrar.append(i)
                
        # 2. Si no hay checkboxes marcados, usar las filas seleccionadas (multiselección)
        if not filas_a_borrar:
            for item in self.catalogo.tabla.selectedItems():
                if item.row() not in filas_a_borrar:
                    filas_a_borrar.append(item.row())
                
        if not filas_a_borrar:
            QMessageBox.information(self, "Aviso", "Seleccioná al menos un producto (usando las casillas) para eliminar.")
            return
            
        nombres = []
        ids_a_borrar = []
        for row in filas_a_borrar:
            item_id = self.catalogo.tabla.item(row, 1)
            item_nom = self.catalogo.tabla.item(row, 2)
            if item_id and item_nom:
                ids_a_borrar.append(item_id.text())
                nombres.append(item_nom.text())
                
        if not ids_a_borrar:
            return
            
        mensaje = f"¿Estás seguro de eliminar {len(ids_a_borrar)} producto(s)?"
        if len(ids_a_borrar) == 1:
            mensaje = f"¿Borrar producto: {nombres[0]}?"
            
        if QMessageBox.question(self, "Confirmar Eliminación", mensaje, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            eliminados = 0
            for id_p in ids_a_borrar:
                # Borrar de la base de datos
                if db_manager.execute_non_query("DELETE FROM productos WHERE id=?", (id_p,)):
                    eliminados += 1
                    
            if eliminados > 0:
                self.catalogo._cargar_deptos()
                self.catalogo.cargar_datos()
                if len(ids_a_borrar) > 1:
                    QMessageBox.information(self, "Éxito", f"Se eliminaron {eliminados} productos correctamente.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el/los producto(s) de la base de datos.")