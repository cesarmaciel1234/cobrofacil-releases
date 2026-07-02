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

from src.admin.inventario.theme import STYLE

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
        self.tree.setHeaderLabels(["Nombre del Departamento", "N° Productos"])
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
            db_manager.execute_non_query("CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL)")
            db_manager.execute_non_query("INSERT OR IGNORE INTO categorias (nombre) SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL AND categoria != ''")
        except: pass

        self.tree.clear()
        
        # Calcular productos sin departamento asignado (General o nulo)
        try:
            sd_res = db_manager.execute_query("SELECT COUNT(id) as c FROM productos WHERE categoria IS NULL OR categoria = '' OR categoria = 'GENERAL'")
            sd_qty = sd_res[0]['c'] if sd_res else 0
        except:
            sd_qty = 0
            
        sd = QTreeWidgetItem(self.tree, ["- Sin Departamento -", str(sd_qty)])
        sd.setForeground(0, QBrush(QColor("#64748b")))
        
        query = """
            SELECT c.id, c.nombre, COUNT(p.id) as qty 
            FROM categorias c 
            LEFT JOIN productos p ON UPPER(p.categoria) = UPPER(c.nombre) 
            GROUP BY c.id, c.nombre 
            ORDER BY c.nombre
        """
        rows = db_manager.execute_query(query) or []
        for r in rows:
            it = QTreeWidgetItem(self.tree, [r['nombre'], str(r['qty'])])
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
