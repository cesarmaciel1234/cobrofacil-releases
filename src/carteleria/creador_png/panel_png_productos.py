"""Asocia un PNG a cada producto para la cartelería de TV."""

import os

from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFrame,
    QPushButton, QTreeWidget, QTreeWidgetItem, QHeaderView, QGridLayout,
    QMessageBox, QGraphicsDropShadowEffect, QFileDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap

# PREVENCIÓN DE CRASH: Cargar WebEngine al inicio para evitar segfault por carga perezosa
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
            QPushButton#danger { background-color: #DC2626; color: #FFFFFF; border: none; }
            QPushButton#danger:hover { background-color: #B91C1C; }
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
            "QFrame#formFrame { background: white; border-radius: 12px; border: 1px solid #E2E8F0; }"
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        form_frame.setGraphicsEffect(shadow)

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
        from src.ui_global.inventario_ui.moleculas.dialogo_galeria_iconos import DialogoGaleriaIconos
        from src.carteleria.assets_paths import carpetas_galeria_png, png_productos_dir
        carpetas = carpetas_galeria_png()
        dlg = DialogoGaleriaIconos(
            icono_actual=self._icono_seleccionado,
            parent=self,
            titulo="PNG del producto (foto de vitrina)",
            target_dir=png_productos_dir(),
            extra_dirs=carpetas[1:],
            nombre_sugerido=self.txt_nombre.text(),
        )
        if qt_exec(dlg):
            sel = dlg.get_selected_icon()
            if sel:
                self._icono_seleccionado = sel
                self._actualizar_preview(sel)

    def _cargar_desde_pc(self):
        if not self._producto_id:
            QMessageBox.information(self, "PNG productos", "Primero elegí un producto de la lista.")
            return
        from src.ui_global.inventario_ui.moleculas.dialogo_galeria_iconos import DialogoCargarPng
        from src.carteleria.assets_paths import png_productos_dir
        origen, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar PNG", "",
            "Imágenes (*.png *.jpg *.jpeg *.webp)",
        )
        if not origen:
            return
        carpeta = png_productos_dir()
        dlg = DialogoCargarPng(
            origen=origen,
            destino_dir=carpeta,
            nombre_sugerido=self.txt_nombre.text(),
            parent=self,
        )
        if not qt_exec(dlg):
            return
        nombre = dlg.filename_guardado
        if not nombre:
            return
        self._icono_seleccionado = nombre
        self._actualizar_preview(nombre)

    def _crear_png_pro(self):
        if not self._producto_id:
            QMessageBox.information(self, "PNG productos", "Primero elegí un producto de la lista.")
            return

        from src.carteleria.creador_png.ventana_html import DialogoCreadorPNG

        sugerido = self.txt_nombre.text().lower().replace(" ", "_")
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            sugerido = sugerido.replace(char, "")
        if not sugerido:
            sugerido = "producto"

        dlg = DialogoCreadorPNG(self, nombre_sugerido=sugerido)
        if qt_exec(dlg) and dlg.filename_guardado:
            self._icono_seleccionado = dlg.filename_guardado
            self._actualizar_preview(self._icono_seleccionado)
            ok_sync, sync_msg = self._sincronizar_a_maestra(dlg.filename_guardado)
            if not ok_sync and sync_msg:
                QMessageBox.warning(self, "Envío a maestra", sync_msg)

    def _sincronizar_a_maestra(self, filename: str):
        """Envía el PNG a la maestra (API :8000, luego Creador PNG :5000)."""
        from src.config import config
        if config.get("is_master", True) and not config.get("carteleria_is_slave"):
            return True, ""

        db_host = str(
            config.get("preferred_master_ip")
            or config.get("carteleria_master_ip")
            or config.get("db_host")
            or ""
        ).strip()
        if not db_host or db_host.lower() in ("127.0.0.1", "localhost"):
            return True, ""

        from src.carteleria.assets_paths import ruta_archivo_icono
        fpath = ruta_archivo_icono(filename)
        if not fpath or not os.path.exists(fpath):
            return False, "No se encontró el PNG local para enviar."

        import requests

        urls = [
            f"http://{db_host}:8000/api/carteleria/upload_png",
            f"http://{db_host}:5000/upload_carteleria_png",
            f"http://{db_host}:5055/upload_carteleria_png",
        ]
        last_err = ""
        for url in urls:
            try:
                with open(fpath, "rb") as f:
                    res = requests.post(
                        url,
                        files={"file": (filename, f, "image/png")},
                        timeout=8,
                    )
                if res.status_code == 200:
                    print(f"[Cartelería] PNG {filename} enviado a maestra {url}")
                    return True, f"PNG copiado a la maestra ({db_host})."
                last_err = f"HTTP {res.status_code} en {url}"
            except Exception as e:
                last_err = str(e)
                continue
        return (
            False,
            f"No se pudo enviar el PNG a la maestra {db_host}.\n"
            "Encendé esa PC y el Servidor de Tienda (puerto 8000).\n"
            f"{last_err}",
        )

    def _actualizar_preview(self, filename):
        self.lbl_preview_icono.setPixmap(QPixmap())
        if filename:
            from src.carteleria.assets_paths import ruta_archivo_icono
            fpath = ruta_archivo_icono(filename)
            if fpath:
                pm = QPixmap(fpath)
                if not pm.isNull():
                    self.lbl_preview_icono.setPixmap(
                        pm.scaled(
                            80, 80,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
                    self.lbl_preview_icono.setText("")
                    return
        self.lbl_preview_icono.setText("Sin PNG")

    def _cargar(self, _texto=None):
        from src.motor_inventario.base.productos_db import listar_productos_png
        self.tree.clear()
        rows = listar_productos_png(self.txt_buscar.text())
        for r in rows:
            png = str(r.get("icono") or "").strip()
            it = QTreeWidgetItem(self.tree, [
                str(r.get("nombre") or ""),
                str(r.get("departamento") or r.get("categoria") or "—"),
                png or "—",
            ])
            it.setData(0, Qt.ItemDataRole.UserRole, r.get("id"))
            it.setData(0, Qt.ItemDataRole.UserRole + 1, png)
            it.setData(0, Qt.ItemDataRole.UserRole + 2, str(r.get("departamento") or r.get("categoria") or ""))

    def _seleccionar(self, item, _col):
        self._producto_id = item.data(0, Qt.ItemDataRole.UserRole)
        self._icono_seleccionado = item.data(0, Qt.ItemDataRole.UserRole + 1) or None
        self.txt_nombre.setText(item.text(0))
        self.txt_depto.setText(item.data(0, Qt.ItemDataRole.UserRole + 2) or "")
        self.lbl_titulo_form.setText("PNG DEL PRODUCTO")
        self._actualizar_preview(self._icono_seleccionado)

    def _quitar_png(self):
        self._icono_seleccionado = None
        self._actualizar_preview(None)

    def _guardar(self):
        if not self._producto_id:
            QMessageBox.warning(self, "Requerido", "Seleccioná un producto.")
            return
        from src.motor_inventario.base.productos_db import guardar_icono_producto
        ok, msg = guardar_icono_producto(self._producto_id, self._icono_seleccionado)
        if ok:
            nombre = self.txt_nombre.text()
            extra = ""
            if self._icono_seleccionado:
                ok_sync, sync_msg = self._sincronizar_a_maestra(self._icono_seleccionado)
                if sync_msg:
                    extra = "\n\n" + sync_msg
                if not ok_sync:
                    QMessageBox.warning(self, "Envío a maestra", sync_msg or "No se pudo enviar.")
            self._cargar()
            self._reseleccionar(nombre)
            QMessageBox.information(
                self,
                "PNG productos",
                "Listo. La cartelería va a mostrar ese PNG en las tarjetas de ese producto."
                + extra,
            )
        else:
            QMessageBox.warning(self, "Error", msg)

    def _reseleccionar(self, nombre):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.text(0) == nombre:
                self.tree.setCurrentItem(item)
                self._seleccionar(item, 0)
                break
