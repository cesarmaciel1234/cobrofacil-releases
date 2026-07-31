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

# Removed database import


class PanelCategorias(QWidget):
    categorias_cambiadas = pyqtSignal()
    volver = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._modo_edicion = None
        self._setup_ui()
        self._cargar()

    def _setup_ui(self):
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', sans-serif; }
            QPushButton {
                background-color: #F1F5F9; color: #1E293B; border: 1px solid #CBD5E1;
                border-radius: 8px; padding: 10px 18px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #E2E8F0; border-color: #94A3B8; }
            QPushButton#blue, QPushButton[objectName="blue"] {
                background-color: #2563EB; color: #FFFFFF; border: none;
            }
            QPushButton#blue:hover, QPushButton[objectName="blue"]:hover {
                background-color: #1D4ED8;
            }
            QPushButton#danger, QPushButton[objectName="danger"] {
                background-color: #DC2626; color: #FFFFFF; border: none;
            }
            QPushButton#danger:hover, QPushButton[objectName="danger"]:hover {
                background-color: #B91C1C;
            }
            QPushButton#gray, QPushButton[objectName="gray"] {
                background-color: #64748B; color: #FFFFFF; border: none;
            }
            QPushButton#gray:hover, QPushButton[objectName="gray"]:hover {
                background-color: #475569;
            }
        """)
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
        form_frame.setObjectName("formFrame")
        form_frame.setStyleSheet("QFrame#formFrame { background: white; border-radius: 12px; border: 1px solid #E2E8F0; }")
        
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

        # ── Ícono de Rubro / Cartelería ────────────────────────────────────────
        lbl_ico = QLabel("Ícono visual (Cartelería y POS):")
        lbl_ico.setStyleSheet("border: none; font-weight: bold;")
        
        ico_lay = QHBoxLayout()
        ico_lay.setSpacing(10)

        self.lbl_preview_icono = QLabel("🖼️ Sin Ícono")
        self.lbl_preview_icono.setFixedSize(52, 52)
        self.lbl_preview_icono.setAlignment(Qt.AlignCenter)
        self.lbl_preview_icono.setStyleSheet("background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 10px; font-size: 22px;")

        self.btn_sel_icono = QPushButton("🎨 Seleccionar Ícono de Galería")
        self.btn_sel_icono.setCursor(Qt.PointingHandCursor)
        self.btn_sel_icono.setStyleSheet("""
            QPushButton {
                background: #F1F5F9; color: #1E293B; border: 1px solid #CBD5E1;
                border-radius: 8px; padding: 10px 16px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: #E2E8F0; border-color: #2563EB; }
        """)
        self.btn_sel_icono.clicked.connect(self._abrir_galeria_iconos)

        ico_lay.addWidget(self.lbl_preview_icono)
        ico_lay.addWidget(self.btn_sel_icono)
        ico_lay.addStretch()

        form_lay.addWidget(lbl_ico)
        form_lay.addLayout(ico_lay)

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

    def _abrir_galeria_iconos(self):
        from src.ui_global.inventario_ui.componentes.dialogo_galeria_iconos import DialogoGaleriaIconos
        dlg = DialogoGaleriaIconos(icono_actual=getattr(self, '_icono_seleccionado', None), parent=self)
        if qt_exec(dlg):
            sel = dlg.get_selected_icon()
            if sel:
                self._icono_seleccionado = sel
                self._actualizar_preview_icono(sel)

    def _actualizar_preview_icono(self, filename):
        if filename:
            import os
            from PyQt6.QtGui import QPixmap
            fpath = os.path.join(os.getcwd(), "Catalogos", "iconos_rubros", filename)
            if os.path.exists(fpath):
                pm = QPixmap(fpath)
                if not pm.isNull():
                    self.lbl_preview_icono.setPixmap(pm.scaled(42, 42, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    return
        self.lbl_preview_icono.setText("🖼️")
        self.lbl_preview_icono.setPixmap(QPixmap())

    def _cargar(self):
        from src.motor_inventario.motor_departamentos import MotorDepartamentos
        motor = MotorDepartamentos()
        self.tree.clear()
        
        # Calcular productos sin departamento asignado (General o nulo)
        sd_qty = motor.obtener_conteo_sin_categoria()
            
        sd = QTreeWidgetItem(self.tree, ["- Sin Departamento -", str(sd_qty)])
        sd.setForeground(0, QBrush(QColor("#64748b")))
        
        rows = motor.obtener_categorias_con_conteo()
        for r in rows:
            it = QTreeWidgetItem(self.tree, [r['nombre'], str(r['qty'])])
            it.setData(0, Qt.UserRole, r['id'])

    def _iniciar_nuevo(self):
        self._modo_edicion = None
        self._icono_seleccionado = None
        self._actualizar_preview_icono(None)
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

        from src.motor_inventario.motor_departamentos import MotorDepartamentos
        cats = MotorDepartamentos().obtener_categorias()
        ico = None
        for c in cats:
            if c['id'] == id_cat:
                ico = c.get('icono')
                break
        self._icono_seleccionado = ico
        self._actualizar_preview_icono(ico)

    def _guardar(self):
        nombre = self.txt_nombre_cat.text().strip()
        if not nombre: QMessageBox.warning(self,"Requerido","Ingresá un nombre."); return
        from src.motor_inventario.motor_departamentos import MotorDepartamentos
        motor = MotorDepartamentos()
        ok, msg = motor.guardar_categoria(nombre, self._modo_edicion, getattr(self, '_icono_seleccionado', None))
        if ok:
            self._cargar(); self.categorias_cambiadas.emit(); self._iniciar_nuevo()
        else:
            QMessageBox.warning(self, "Error", msg)

    def _eliminar(self):
        item = self.tree.currentItem()
        if not item: return
        id_cat = item.data(0, Qt.UserRole)
        if not id_cat or id_cat == -1: return
        nombre_cat = item.text(0)
        if QMessageBox.question(self,"Confirmar",f"¿Eliminar la categoría '{nombre_cat}'?",
                                QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            from src.motor_inventario.motor_departamentos import MotorDepartamentos
            motor = MotorDepartamentos()
            ok, msg = motor.eliminar_categoria(id_cat)
            if ok:
                self._cargar(); self.categorias_cambiadas.emit()
            else:
                QMessageBox.warning(self, "Error", msg)

# ── Catálogo de Productos ────────────────────────────────
