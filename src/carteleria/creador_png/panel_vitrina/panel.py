"""Asocia un PNG a cada producto para la cartelería de TV."""

from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFrame,
    QPushButton, QTreeWidget, QHeaderView, QGridLayout,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.carteleria.creador_png.panel_vitrina import guardar
from src.carteleria.creador_png.panel_vitrina import lista
from src.carteleria.creador_png.panel_vitrina import preview

try:
    import PyQt6.QtWebEngineWidgets
except ImportError:
    pass


class PanelPngProductos(QWidget):
    volver = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._producto_id = None
        self._icono_seleccionado = None
        from src.carteleria.assets_paths import png_productos_dir
        png_productos_dir()
        try:
            from src.motor_inventario.base.productos_db import asociar_png_por_nombre
            asociar_png_por_nombre()
        except Exception:
            pass
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
            QPushButton#blue { background-color: #2563EB; color: #FFFFFF; border: none; }
            QPushButton#blue:hover { background-color: #1D4ED8; }
            QPushButton#gray { background-color: #64748B; color: #FFFFFF; border: none; }
            QPushButton#gray:hover { background-color: #475569; }
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        tb = QFrame()
        tb.setFixedHeight(50)
        tb.setStyleSheet("QFrame{background: white; border-bottom: 1px solid #cbd5e1;}")
        tl = QHBoxLayout(tb)
        tl.setContentsMargins(15, 5, 15, 5)
        btn_volver = QPushButton("⬅ Volver al panel")
        btn_volver.setObjectName("gray")
        btn_volver.clicked.connect(self.volver.emit)
        tl.addWidget(btn_volver)
        tl.addStretch()
        root.addWidget(tb)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 20, 20, 20)
        cl.setSpacing(16)

        lbl = QLabel("PNG PRODUCTOS — VITRINA DE CARTELERÍA")
        lbl.setStyleSheet("font-size:18px; font-weight:800; color: #1E40AF;")
        cl.addWidget(lbl)

        from src.carteleria.assets_paths import png_productos_dir
        carpeta = png_productos_dir()
        hint = QLabel(
            "Elegí un producto, asociá un PNG y la TV lo muestra. "
            "Cargar desde la PC crea el archivo en esa carpeta (1024×1024, fondo transparente). "
            f"Ruta: {carpeta}"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #64748B; font-size: 13px;")
        cl.addWidget(hint)

        grid = QGridLayout()
        grid.setSpacing(20)

        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        form_frame.setStyleSheet(
            "QFrame#formFrame { background: #FFFFFF; border-radius: 6px; border: 1px solid #E2E8F0; }"
        )
        form_frame.setGraphicsEffect(None)

        form_lay = QVBoxLayout(form_frame)
        form_lay.setContentsMargins(20, 20, 20, 20)
        form_lay.setSpacing(15)

        self.lbl_titulo_form = QLabel("SELECCIONÁ UN PRODUCTO")
        self.lbl_titulo_form.setStyleSheet("font-weight: 800; font-size: 14px; color: #2563EB; border: none;")
        form_lay.addWidget(self.lbl_titulo_form)

        lbl_n = QLabel("Producto:")
        lbl_n.setStyleSheet("border: none; font-weight: bold; color: #2563EB;")
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setReadOnly(True)
        self.txt_nombre.setPlaceholderText("Hacé clic en un producto de la lista…")
        self.txt_nombre.setStyleSheet(
            "padding: 12px; border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC;"
        )
        form_lay.addWidget(lbl_n)
        form_lay.addWidget(self.txt_nombre)

        lbl_depto = QLabel("Departamento:")
        lbl_depto.setStyleSheet("border: none; font-weight: bold; color: #2563EB;")
        self.txt_depto = QLineEdit()
        self.txt_depto.setReadOnly(True)
        self.txt_depto.setStyleSheet(
            "padding: 12px; border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC;"
        )
        form_lay.addWidget(lbl_depto)
        form_lay.addWidget(self.txt_depto)

        lbl_ico = QLabel("PNG visual (Cartelería):")
        lbl_ico.setStyleSheet("border: none; font-weight: bold; color: #2563EB;")
        ico_lay = QHBoxLayout()
        ico_lay.setSpacing(10)
        self.lbl_preview_icono = QLabel("Sin PNG")
        self.lbl_preview_icono.setFixedSize(88, 88)
        self.lbl_preview_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview_icono.setStyleSheet(
            "background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 12px; font-size: 12px; color: #64748B;"
        )
        self.btn_sel_icono = QPushButton("🎨 Seleccionar PNG de Galería")
        self.btn_sel_icono.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sel_icono.clicked.connect(self._abrir_galeria)
        self.btn_cargar_pc = QPushButton("➕ Cargar PNG desde PC")
        self.btn_cargar_pc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cargar_pc.clicked.connect(self._cargar_desde_pc)
        self.btn_crear_png = QPushButton("✨ Creador PNG Pro")
        self.btn_crear_png.setObjectName("blue")
        self.btn_crear_png.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_crear_png.clicked.connect(self._crear_png_pro)
        ico_lay.addWidget(self.lbl_preview_icono)
        ico_lay.addWidget(self.btn_sel_icono)
        ico_lay.addWidget(self.btn_cargar_pc)
        ico_lay.addWidget(self.btn_crear_png)
        ico_lay.addStretch()
        form_lay.addWidget(lbl_ico)
        form_lay.addLayout(ico_lay)

        h_btn = QHBoxLayout()
        btn_quitar = QPushButton("Quitar PNG")
        btn_quitar.setObjectName("gray")
        btn_quitar.clicked.connect(self._quitar_png)
        btn_guardar = QPushButton("Guardar PNG del producto")
        btn_guardar.setObjectName("blue")
        btn_guardar.clicked.connect(self._guardar)
        h_btn.addWidget(btn_quitar)
        h_btn.addWidget(btn_guardar)
        form_lay.addLayout(h_btn)
        form_lay.addStretch()
        grid.addWidget(form_frame, 0, 0)

        right = QFrame()
        right.setStyleSheet("QFrame { background: white; border: 1px solid #E2E8F0; border-radius: 12px; }")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(12, 12, 12, 12)
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar producto o departamento…")
        self.txt_buscar.setStyleSheet(
            "padding: 10px 12px; border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC;"
        )
        self.txt_buscar.textChanged.connect(self._cargar)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Producto", "Departamento", "PNG"])
        self.tree.setColumnWidth(0, 220)
        self.tree.setColumnWidth(1, 140)
        self.tree.setStyleSheet(
            "QTreeWidget { background: white; border: none; font-size: 13px; }"
        )
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.itemClicked.connect(self._seleccionar)
        rl.addWidget(self.txt_buscar)
        rl.addWidget(self.tree)
        grid.addWidget(right, 0, 1)
        grid.setColumnStretch(0, 4)
        grid.setColumnStretch(1, 6)
        cl.addLayout(grid)
        root.addWidget(content)

    def _abrir_galeria(self):
        if not self._producto_id:
            QMessageBox.information(self, "PNG productos", "Primero elegí un producto de la lista.")
            return
        from src.carteleria.assets_paths import png_productos_dir
        from src.carteleria.creador_png.panel_vitrina.galeria.dialogo import abrir_galeria

        sel = abrir_galeria(
            self, png_productos_dir(),
            icono_actual=self._icono_seleccionado or "",
            producto=self.txt_nombre.text(),
        )
        if sel:
            self._icono_seleccionado = sel
            preview.pintar(self.lbl_preview_icono, sel)

    def _cargar_desde_pc(self):
        if not self._producto_id:
            QMessageBox.information(self, "PNG productos", "Primero elegí un producto de la lista.")
            return
        from src.carteleria.assets_paths import png_productos_dir
        from src.carteleria.creador_png.panel_vitrina.galeria.cargar import elegir_desde_pc

        nombre = elegir_desde_pc(
            self, png_productos_dir(),
            producto=self.txt_nombre.text(),
            icono_actual=self._icono_seleccionado or "",
        )
        if not nombre:
            return
        self._icono_seleccionado = nombre
        preview.pintar(self.lbl_preview_icono, nombre)

    def _crear_png_pro(self):
        if not self._producto_id:
            QMessageBox.information(self, "PNG productos", "Primero elegí un producto de la lista.")
            return
        import os
        from src.carteleria.creador_png.ventana_html import DialogoCreadorPNG
        from src.carteleria.creador_png.panel_vitrina.archivo import nombre_canonico

        sugerido = os.path.splitext(nombre_canonico(self.txt_nombre.text(), self._icono_seleccionado))[0]
        dlg = DialogoCreadorPNG(self, nombre_sugerido=sugerido)
        if qt_exec(dlg) and dlg.filename_guardado:
            self._icono_seleccionado = dlg.filename_guardado
            preview.pintar(self.lbl_preview_icono, self._icono_seleccionado)

    def _cargar(self, _texto=None):
        lista.cargar(self.tree, self.txt_buscar.text())

    def _seleccionar(self, item, _col):
        from PyQt6.QtCore import Qt
        self._producto_id = item.data(0, Qt.ItemDataRole.UserRole)
        self._icono_seleccionado = item.data(0, Qt.ItemDataRole.UserRole + 1) or None
        self.txt_nombre.setText(item.text(0))
        self.txt_depto.setText(item.data(0, Qt.ItemDataRole.UserRole + 2) or "")
        self.lbl_titulo_form.setText("PNG DEL PRODUCTO")
        preview.pintar(self.lbl_preview_icono, self._icono_seleccionado)

    def _quitar_png(self):
        self._icono_seleccionado = None
        preview.pintar(self.lbl_preview_icono, None)

    def _guardar(self):
        if not self._producto_id:
            QMessageBox.warning(self, "Requerido", "Seleccioná un producto.")
            return
        ok, msg = guardar.asociar(
            self._producto_id, self._icono_seleccionado, self.txt_nombre.text(),
        )
        if not ok:
            QMessageBox.warning(self, "Error", msg)
            return
        if msg:
            self._icono_seleccionado = msg
        nombre = self.txt_nombre.text()
        aviso = ""
        if self._icono_seleccionado:
            aviso = guardar.copiar_a_maestra(self._icono_seleccionado)
        self._cargar()
        lista.reseleccionar(self.tree, nombre, self._seleccionar)
        QMessageBox.information(self, "PNG productos", guardar.texto_listo(aviso))
