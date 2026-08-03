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


class PanelDepartamentos(QWidget):
    departamentos_cambiados = pyqtSignal()
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
        form_card.setObjectName("formCard")
        form_card.setStyleSheet("QFrame#formCard { background: white; border: 1px solid #E2E8F0; border-radius: 12px; }")
        
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

        # ── Ícono de Rubro / Cartelería ────────────────────────────────────────
        lbl_ico = QLabel("Ícono visual (Cartelería y POS):")
        lbl_ico.setStyleSheet("font-weight: bold; border: none;")
        
        ico_lay = QHBoxLayout()
        ico_lay.setSpacing(10)

        self.lbl_preview_icono = QLabel("🖼️ Sin Ícono")
        self.lbl_preview_icono.setFixedSize(50, 50)
        self.lbl_preview_icono.setAlignment(Qt.AlignCenter)
        self.lbl_preview_icono.setStyleSheet("background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 10px; font-size: 20px;")

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
        rl.addWidget(lbl_ico)
        rl.addLayout(ico_lay)
        rl.addLayout(bx2)
        rl.addStretch()
        
        rl_main.addWidget(form_card)
        sp.addWidget(right)
        sp.setSizes([350, 650])
        root.addWidget(sp)

    def _abrir_galeria_iconos(self):
        from src.ui_global.inventario_ui.moleculas.dialogo_galeria_iconos import DialogoGaleriaIconos
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
                    self.lbl_preview_icono.setPixmap(pm.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    return
        self.lbl_preview_icono.setText("🖼️")
        self.lbl_preview_icono.setPixmap(QPixmap())

    def _cargar(self, filtro=''):
        from src.motor_inventario.motor_departamentos import MotorDepartamentos
        motor = MotorDepartamentos()
        self.tree.clear()
        sd = QTreeWidgetItem(self.tree, ["- Sin Departamento -", "—"])
        sd.setData(0, Qt.UserRole, -1)
        rows = motor.obtener_departamentos()
        for r in rows:
            if filtro and filtro.lower() not in r['nombre'].lower(): continue
            it = QTreeWidgetItem(self.tree, [r['nombre'], f"{r['iva']:.1f}%"])
            it.setData(0, Qt.UserRole, r['id'])

    def _iniciar_nuevo(self):
        self._modo_edicion = None
        self._icono_seleccionado = None
        self._actualizar_preview_icono(None)
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
            from src.motor_inventario.motor_departamentos import MotorDepartamentos
            rows = MotorDepartamentos().obtener_departamentos()
            val = "21.0"
            ico = None
            for r in rows:
                if r['id'] == id_dep:
                    val = f"{r['iva']:.1f}"
                    ico = r.get('icono')
                    break
            self.txt_iva_dep.setText(val)
            self._icono_seleccionado = ico
            self._actualizar_preview_icono(ico)
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

        from src.motor_inventario.motor_departamentos import MotorDepartamentos
        motor = MotorDepartamentos()
        ok, msg = motor.guardar_departamento(nombre, iva_val, self._modo_edicion, getattr(self, '_icono_seleccionado', None))
        if ok:
            self._cargar(); self.departamentos_cambiados.emit(); self._iniciar_nuevo()
        else:
            QMessageBox.warning(self,"Error", msg)

    def _eliminar(self):
        item = self.tree.currentItem()
        if not item: return
        id_dep = item.data(0, Qt.UserRole)
        if not id_dep or id_dep == -1: return
        nombre_depto = item.text(0)
        if QMessageBox.question(self,"Confirmar",f"¿Eliminar '{nombre_depto}'?",
                                QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            from src.motor_inventario.motor_departamentos import MotorDepartamentos
            motor = MotorDepartamentos()
            ok, msg = motor.eliminar_departamento(id_dep)
            if ok:
                self._cargar(); self.departamentos_cambiados.emit()
            else:
                QMessageBox.warning(self, "Error", msg)


# ── Panel Categorias (Departamentos de Mercadería) ──
