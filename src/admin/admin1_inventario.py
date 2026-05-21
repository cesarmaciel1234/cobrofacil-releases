from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QPushButton, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QTreeWidget, QTreeWidgetItem, QSplitter,
    QComboBox, QCheckBox, QStackedWidget, QFileDialog, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QColor, QFont

try:
    from src.database import db_manager
except ImportError:
    from database import db_manager

STYLE = """
QWidget {
    background-color: #F8FAFC;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 13px;
    color: #1e293b;
}
QFrame#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E3A8A, stop:1 #3B82F6);
    border-bottom: 2px solid #0f172a;
    border-radius: 10px;
}
QLabel#titulo {
    color: white;
    background: transparent;
    font-size: 20px;
    font-weight: 900;
    letter-spacing: 1px;
}
QPushButton {
    background-color: white;
    color: #1e3a8a;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 11px;
}
QPushButton:hover {
    background-color: #3b82f6;
    color: white;
    border-color: #3b82f6;
}
QPushButton#danger {
    background-color: #fef2f2;
    color: #ef4444;
    border: 1px solid #fecaca;
}
QPushButton#danger:hover {
    background-color: #ef4444;
    color: white;
}
QPushButton#gray {
    background-color: #f1f5f9;
    color: #64748b;
    border: 1px solid #e2e8f0;
}
QPushButton#gray:hover {
    background-color: #e2e8f0;
    color: #0f172a;
}
QLineEdit, QComboBox {
    background-color: white;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 12px;
}
QLineEdit:focus {
    border: 2px solid #3b82f6;
}
QTreeWidget, QTableWidget {
    background-color: white;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    gridline-color: #f1f5f9;
    selection-background-color: #FDE047;
    selection-color: #0f172a;
    border-radius: 8px;
}
QHeaderView::section {
    background-color: white;
    color: #64748b;
    font-weight: 800;
    padding: 12px;
    border: none;
    border-bottom: 2px solid #e2e8f0;
    font-size: 11px;
    text-transform: uppercase;
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

    def keyPressEvent(self, event):
        from PyQt5.QtWidgets import QPushButton
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if isinstance(self.focusWidget(), QPushButton):
                super().keyPressEvent(event)
            else:
                self.focusNextChild()
        else:
            super().keyPressEvent(event)

    def setup_ui(self, datos):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(30, 30, 30, 30)
        main_lay.setSpacing(20)

        # --- HEADER ---
        lbl_tit = QLabel("💎 Ficha de Producto 2026")
        lbl_tit.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E3A8A;")
        main_lay.addWidget(lbl_tit)

        # --- SECCIÓN: CÓDIGO DE BARRAS (ALTA VISIBILIDAD) ---
        barcode_frame = QFrame()
        barcode_frame.setStyleSheet("background: #F1F5F9; border-radius: 12px; border: 1px solid #CBD5E1;")
        bar_lay = QVBoxLayout(barcode_frame)
        bar_lay.setContentsMargins(20, 15, 20, 15)
        
        lbl_bc = QLabel("CÓDIGO DE BARRAS / PLU:")
        lbl_bc.setStyleSheet("font-weight: bold; color: #475569; font-size: 11px; border: none;")
        self.txt_codigo = QLineEdit(datos.get('codigo', '') if datos else '')
        self.txt_codigo.setPlaceholderText("Escanea o escribe el código...")
        self.txt_codigo.setStyleSheet("""
            QLineEdit { 
                background: white; border: 2px solid #1E3A8A; border-radius: 8px; 
                padding: 12px; font-size: 22px; font-weight: 900; color: #000000; 
                font-family: 'Consolas', monospace;
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

        self.cmb_depto = QComboBox()
        self.cmb_depto.addItem("")
        try:
            deps = db_manager.execute_query("SELECT nombre FROM departamentos ORDER BY nombre") or []
            for d in deps: self.cmb_depto.addItem(d['nombre'])
        except: pass

        v_depto = QVBoxLayout()
        lbl_depto = QLabel("Departamento / Pasillo:")
        lbl_depto.setStyleSheet("font-weight: bold; color: #475569; font-size: 12px;")
        v_depto.addWidget(lbl_depto)
        v_depto.addWidget(self.cmb_depto)
        
        self.lbl_iva_info = QLabel("ℹ️ IVA Aplicado: 21.0% (tasa general)")
        self.lbl_iva_info.setStyleSheet("color: #059669; font-size: 11px; font-weight: bold; margin-top: 2px;")
        v_depto.addWidget(self.lbl_iva_info)
        grid.addLayout(v_depto, 1, 0)
        
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
        self.add_field(grid, "Unidad de Medida:", self.cmb_uni, 2, 0)

        self.chk_pes = QCheckBox("Es pesable / fraccionable (Balanza)")
        self.chk_pes.setChecked(bool(datos.get('es_pesable', 0)) if datos else False)
        self.chk_pes.setStyleSheet("font-weight: bold; color: #1E3A8A; margin-top: 10px;")
        grid.addWidget(self.chk_pes, 3, 0)

        # Columna 2: Precios y Stock
        price_card = QFrame()
        price_card.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px;")
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
        btn_cancel.setStyleSheet("background: #F1F5F9; color: #475569; padding: 15px; border-radius: 10px; font-weight: bold;")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 Guardar Producto")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton { background: #1E3A8A; color: white; font-weight: bold; padding: 15px; border-radius: 10px; }
            QPushButton:hover { background: #1E40AF; }
        """)
        btn_save.clicked.connect(self._ok)

        h_btns.addWidget(btn_cancel)
        h_btns.addStretch()
        h_btns.addWidget(btn_save)
        main_lay.addLayout(h_btns)

    def add_field(self, grid, label, widget, row, col):
        v = QVBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("font-weight: bold; color: #475569; font-size: 12px;")
        v.addWidget(lbl)
        v.addWidget(widget)
        grid.addLayout(v, row, col)

    def create_price_input(self, val, bold=False):
        inp = QLineEdit(val)
        weight = "bold" if bold else "normal"
        color = "#1E3A8A" if bold else "#1E293B"
        inp.setStyleSheet(f"background: white; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px; font-weight: {weight}; color: {color};")
        return inp

    def _ok(self):
        if not self.txt_nombre.text().strip():
            QMessageBox.warning(self, "Requerido", "El nombre es obligatorio."); return
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
            'categoria': 'GENERAL',
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
        lbl = QLabel("LISTADO DE DEPARTAMENTOS")
        lbl.setStyleSheet("font-weight: 900; color: #1e3a8a; font-size: 13px;")
        self.txt_buscar = QLineEdit(); self.txt_buscar.setPlaceholderText("🔍 Buscar departamento...")
        self.txt_buscar.textChanged.connect(lambda t: self._cargar(t))
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Departamento", "IVA (%)"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.itemClicked.connect(self._seleccionar)
        ll.addWidget(lbl); ll.addWidget(self.txt_buscar); ll.addWidget(self.tree)
        sp.addWidget(left)

        # Formulario derecho
        right = QWidget(); rl = QVBoxLayout(right); rl.setContentsMargins(20,20,20,20); rl.setSpacing(12)
        self.lbl_titulo_form = QLabel("NUEVO DEPARTAMENTO")
        self.lbl_titulo_form.setStyleSheet("font-weight: 900; color: #3b82f6; font-size: 15px;")
        lbl_n = QLabel("Nombre del Departamento:")
        lbl_n.setStyleSheet("font-weight: bold; color: #475569;")
        self.txt_nombre_dep = QLineEdit()
        self.txt_nombre_dep.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px; background: white; color: #0f172a; font-size: 14px; font-weight: bold;")
        
        lbl_iva = QLabel("Tasa de IVA (%):")
        lbl_iva.setStyleSheet("font-weight: bold; color: #475569;")
        self.txt_iva_dep = QLineEdit("21.0")
        self.txt_iva_dep.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px; background: white; color: #0f172a; font-size: 14px; font-weight: bold;")
        
        bx2 = QHBoxLayout()
        self.btn_guardar_dep  = QPushButton("✔ Guardar Departamento")
        self.btn_guardar_dep.setStyleSheet("background-color: #10b981; color: white; font-size: 12px;")
        self.btn_cancelar_dep = QPushButton("✖ Cancelar"); self.btn_cancelar_dep.setObjectName("gray")
        self.btn_guardar_dep.clicked.connect(self._guardar)
        self.btn_cancelar_dep.clicked.connect(self._iniciar_nuevo)
        bx2.addWidget(self.btn_guardar_dep); bx2.addWidget(self.btn_cancelar_dep)
        
        rl.addWidget(self.lbl_titulo_form)
        rl.addWidget(lbl_n)
        rl.addWidget(self.txt_nombre_dep)
        rl.addWidget(lbl_iva)
        rl.addWidget(self.txt_iva_dep)
        rl.addLayout(bx2)
        rl.addStretch()
        sp.addWidget(right)
        sp.setSizes([350, 650])
        root.addWidget(sp)

    def _cargar(self, filtro=''):
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
        self.lbl_titulo_form.setText("NUEVO DEPARTAMENTO")
        self.txt_nombre_dep.clear()
        self.txt_iva_dep.setText("21.0")
        self.txt_nombre_dep.setFocus()

    def _seleccionar(self, item, _):
        id_dep = item.data(0, Qt.UserRole)
        if id_dep and id_dep != -1:
            self._modo_edicion = id_dep
            self.lbl_titulo_form.setText("EDITAR DEPARTAMENTO")
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


# ── Catálogo de Productos ────────────────────────────────
class CatalogoProductos(QWidget):
    volver = pyqtSignal()

    HEADERS = ["", "Código", "Descripción del Producto", "Departamento", "IVA (%)",
               "Costo", "P. Venta", "P. Mayoreo", "Existencia",
               "Inv. Mínimo", "Inv. Máximo", "Tipo de Venta"]

    DEPTO_COLORS = [
        "#1e293b", "#0f172a", "#111827", "#1e1b4b",
        "#312e81", "#1e3a8a", "#1e40af", "#020617",
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
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Barra de filtros ─────────────────────────────
        fb = QFrame(); fb.setFixedHeight(60)
        fb.setStyleSheet("QFrame{background:#ffffff;border-bottom:1px solid #cbd5e1;}")
        fl = QHBoxLayout(fb); fl.setContentsMargins(15, 6, 15, 6); fl.setSpacing(12)
        
        ico_search = QLabel("🔍")
        ico_search.setStyleSheet("color: #475569; font-size: 16px; background: transparent;")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre, código o ID...")
        self.txt_buscar.setMinimumWidth(350)
        
        # Debounce timer para búsqueda rápida sin lag
        from PyQt5.QtCore import QTimer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.cargar_datos)
        self.txt_buscar.textChanged.connect(lambda: self.search_timer.start(300))

        lbl_dep = QLabel("FILTRAR POR DEPARTAMENTO:")
        lbl_dep.setStyleSheet("color:#1e3a8a;font-weight:800;font-size:10px;letter-spacing:1px; background: transparent;")
        self.cmb_depto = QComboBox()
        self.cmb_depto.setMinimumWidth(200)
        self.cmb_depto.currentIndexChanged.connect(self.cargar_datos)

        fl.addWidget(ico_search)
        fl.addWidget(self.txt_buscar)
        fl.addSpacing(15)
        fl.addWidget(lbl_dep); fl.addWidget(self.cmb_depto)
        fl.addStretch()
        root.addWidget(fb)

        # ── Tabla ────────────────────────────────────────
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(self.HEADERS))
        self.tabla.setHorizontalHeaderLabels(self.HEADERS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setShowGrid(True)
        self.tabla.setGridStyle(Qt.SolidLine)
        self.tabla.setStyleSheet(
            "QTableWidget{background:white;gridline-color:#f1f5f9;"
            "selection-background-color:#FDE047;selection-color:#0f172a;}"
            "QTableWidget::item{padding:8px; border-bottom: 1px solid #f1f5f9;}"
            "QHeaderView::section{background:white;color:#64748b;"
            "font-weight:900;padding:8px;border:none;border-bottom:2px solid #e2e8f0;font-size:10px;}"
        )
        col_widths = [28, 90, -1, 120, 70, 80, 80, 80, 80, 80, 80, 90]
        hh = self.tabla.horizontalHeader()
        for i, w in enumerate(col_widths):
            if w == -1:
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Fixed)
                self.tabla.setColumnWidth(i, w)

        self.tabla.verticalHeader().setDefaultSectionSize(26)
        self.tabla.doubleClicked.connect(self._modificar_seleccionado)
        root.addWidget(self.tabla)

        # ── Footer ───────────────────────────────────────
        ft = QFrame(); ft.setFixedHeight(34)
        ft.setStyleSheet("QFrame{background:#f1f5f9;border-top:1px solid #cbd5e1;}")
        fl2 = QHBoxLayout(ft); fl2.setContentsMargins(12, 0, 12, 0)
        self.lbl_total   = QLabel("0 productos")
        self.lbl_stock0  = QLabel("")
        self.lbl_sel     = QLabel("")
        for lbl in [self.lbl_total, self.lbl_stock0, self.lbl_sel]:
            lbl.setStyleSheet("color:#475569;font-size:11px; background: transparent;")
        fl2.addWidget(self.lbl_total)
        fl2.addSpacing(20); fl2.addWidget(self.lbl_stock0)
        fl2.addStretch();   fl2.addWidget(self.lbl_sel)
        root.addWidget(ft)

        self.tabla.itemSelectionChanged.connect(self._actualizar_sel)
        self.tabla.verticalScrollBar().valueChanged.connect(self._al_hacer_scroll)

    def _cargar_deptos(self):
        self.cmb_depto.blockSignals(True)
        self.cmb_depto.clear()
        self.cmb_depto.addItem("— Todos los departamentos —", None)
        rows = db_manager.execute_query(
            "SELECT DISTINCT departamento FROM productos "
            "WHERE departamento IS NOT NULL ORDER BY departamento"
        ) or []
        for i, r in enumerate(rows):
            dep = r['departamento']
            if dep:
                self.cmb_depto.addItem(dep, dep)
                if dep not in self._depto_color_map:
                    self._depto_color_map[dep] = self.DEPTO_COLORS[
                        len(self._depto_color_map) % len(self.DEPTO_COLORS)]
        self.cmb_depto.blockSignals(False)

    def cargar_datos(self):
        buscar = self.txt_buscar.text().strip()
        depto  = self.cmb_depto.currentData()

        q = "SELECT p.*, d.iva AS depto_iva FROM productos p LEFT JOIN departamentos d ON UPPER(p.departamento) = UPPER(d.nombre) WHERE 1=1"
        p = []
        if buscar:
            for palabra in buscar.split():
                q += " AND (p.nombre LIKE ? OR CAST(p.id AS TEXT) LIKE ? OR COALESCE(p.codigo,'') LIKE ?)"
                p += [f"%{palabra}%"] * 3
        if depto:
            q += " AND p.departamento=?"
            p.append(depto)
        q += " ORDER BY p.departamento, p.nombre"
        q += " LIMIT 5000"  # PERF: Límite de seguridad para tablas grandes

        self.all_rows = db_manager.execute_query(q, tuple(p)) or []
        self.loaded_count = 0
        self.tabla.setRowCount(0)
        
        # Cargar la primera página
        self._cargar_siguiente_pagina()

        # Calcular stock crítico de forma rápida de la memoria sin trabar la UI
        sin_stock = sum(1 for r in self.all_rows if (r['stock'] or 0.0) <= 0)

        n = len(self.all_rows)
        self.lbl_total.setText(f"📦 {n} PRODUCTOS EN INVENTARIO")
        self.lbl_total.setStyleSheet("color: #1e3a8a; font-weight: 800; background: transparent;")
        self.lbl_stock0.setText(
            f"⚠️ Stock Crítico: {sin_stock}" if sin_stock else "✅ Stock Saludable"
        )
        self.lbl_stock0.setStyleSheet(
            f"color:{'#ef4444' if sin_stock else '#10b981'}; font-size:11px; font-weight:bold; background: transparent;"
        )

    def _cargar_siguiente_pagina(self):
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
            tipo  = "GRANEL" if uni == 'KG' else "UNIDAD"
            
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

            row_bg = QColor("white")
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
                (f"${r['precio_mayoreo']:.2f}", Qt.AlignRight),
                (f"{stock:.2f}",     Qt.AlignRight),
                (f"{r['stock_minimo'] or 0:.2f}", Qt.AlignCenter),
                (f"{r['stock_maximo'] or 0:.2f}", Qt.AlignCenter),
                (tipo,               Qt.AlignCenter),
            ]

            for j, (v, align) in enumerate(vals, 1):
                it = QTableWidgetItem(v)
                it.setTextAlignment(Qt.AlignVCenter | align)
                it.setBackground(row_bg)
                it.setForeground(QColor("#1e293b"))

                if j == 8:
                    if stock <= 0:
                        it.setForeground(QColor("#ef4444"))
                        it.setBackground(QColor("#fef2f2"))
                    elif stock < 5:
                        it.setForeground(QColor("#f59e0b"))
                        it.setBackground(QColor("#fffbeb"))
                    else:
                        it.setForeground(QColor("#10b981"))

                if j == 11:
                    it.setForeground(QColor("#1e3a8a"))
                    it.setFont(QFont("Segoe UI", 9, QFont.Bold))

                self.tabla.setItem(i, j, it)
                
        self.loaded_count = fin
        self.tabla.blockSignals(False)

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
        if dlg.exec_():
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
                background: rgba(255, 255, 255, 0.2); color: white; font-weight: 800; border-radius: 10px; 
                padding: 10px 25px; border: 1px solid rgba(255, 255, 255, 0.4); font-size: 11px; letter-spacing: 1px;
            }
            QPushButton:hover { background: white; color: #1E3A8A; }
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)
        hl.addWidget(btn_back)
        
        hl.addSpacing(20)
        tit = QLabel("📦 GESTIÓN DE INVENTARIO <span style='color: rgba(255,255,255,0.7);'>2026</span>"); tit.setObjectName("titulo")
        tit.setStyleSheet("background: transparent;") # Protege contra solapamiento gris/blanco
        hl.addWidget(tit); hl.addStretch()
        root.addWidget(hdr)

        # Toolbar superior (Industrial White)
        self.toolbar = QFrame(); self.toolbar.setFixedHeight(70)
        self.toolbar.setStyleSheet("background-color: white; border-bottom: 2px solid #e2e8f0;")
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
        
        self.btn_deptos   = QPushButton("📁 DEPARTAMENTOS")
        self.btn_deptos.clicked.connect(self._mostrar_departamentos)
        
        for b in [self.btn_nuevo, self.btn_modif, self.btn_eliminar, self.btn_importar, self.btn_exportar, self.btn_deptos]:
            tl.addWidget(b)
        tl.addStretch()
        root.addWidget(self.toolbar)

        self.stack = QStackedWidget()

        self.catalogo = CatalogoProductos()

        self.panel_deptos = PanelDepartamentos()
        self.panel_deptos.volver.connect(self._volver_catalogo)
        self.panel_deptos.departamentos_cambiados.connect(self.catalogo._cargar_deptos)
        self.panel_deptos.departamentos_cambiados.connect(self.catalogo.cargar_datos)

        self.stack.addWidget(self.catalogo)      # 0 → catálogo
        self.stack.addWidget(self.panel_deptos)  # 1 → departamentos

        self.stack.setCurrentIndex(0)
        root.addWidget(self.stack)

    def _mostrar_departamentos(self, *args, **kwargs):
        self.toolbar.setVisible(False) # Elimina los botones duplicados de la vista principal
        self.stack.setCurrentIndex(1)

    def _volver_catalogo(self, *args, **kwargs):
        self.toolbar.setVisible(True)  # Restaura la botonera al regresar
        self.stack.setCurrentIndex(0)

    def cargar_datos(self):
        self.catalogo._cargar_deptos()
        self.catalogo.cargar_datos()

    def _nuevo(self, *args, **kwargs):
        dlg = DialogoProducto(parent=self)
        if dlg.exec_():
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
        rows_to_delete = []
        for i in range(self.catalogo.tabla.rowCount()):
            chk = self.catalogo.tabla.item(i, 0)
            if chk and chk.checkState() == Qt.Checked:
                rows_to_delete.append(i)
                
        if not rows_to_delete:
            selected_items = self.catalogo.tabla.selectedItems()
            rows_to_delete = list(set(item.row() for item in selected_items))
            
        if not rows_to_delete:
            QMessageBox.information(self, "Aviso", "Selecciona al menos un producto para eliminar.")
            return
            
        if len(rows_to_delete) == 1:
            row = rows_to_delete[0]
            item_id = self.catalogo.tabla.item(row, 1)
            item_nom = self.catalogo.tabla.item(row, 2)
            if not item_id or not item_nom: return
            id_p = item_id.text()
            nombre = item_nom.text()
            msg = f"¿Estás seguro de eliminar [{id_p}] {nombre}?"
        else:
            msg = f"¿Estás seguro de eliminar los {len(rows_to_delete)} productos seleccionados?"
            
        if QMessageBox.question(self, "Confirmar", msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            ids_to_delete = []
            for row in rows_to_delete:
                item_id = self.catalogo.tabla.item(row, 1)
                if item_id:
                    ids_to_delete.append(item_id.text())
                    
            if ids_to_delete:
                from src.database import db_manager
                placeholders = ",".join("?" * len(ids_to_delete))
                ok = db_manager.execute_non_query(f"DELETE FROM productos WHERE id IN ({placeholders})", tuple(ids_to_delete))
                if ok:
                    self.catalogo._cargar_deptos()
                    self.catalogo.cargar_datos()
                else:
                    QMessageBox.warning(self, "Error", "No se pudo eliminar los productos seleccionados.")
