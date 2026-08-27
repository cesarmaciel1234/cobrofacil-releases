"""Asocia un PNG a cada producto para la cartelería de TV."""

from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFrame,
    QPushButton, QTreeWidget, QTreeWidgetItem, QHeaderView, QGridLayout,
    QMessageBox, QGraphicsDropShadowEffect, QSlider, QComboBox, QSpinBox,
    QDialog, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QPixmap


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
        from PyQt6.QtWidgets import QFileDialog
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
            
        import os
        import subprocess
        from src.carteleria.assets_paths import png_productos_dir
        
        origen, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Foto para Convertir", "",
            "Imágenes (*.png *.jpg *.jpeg *.webp)",
        )
        if not origen:
            return
            
        carpeta = png_productos_dir()
        sugerido = self.txt_nombre.text().lower().replace(" ", "_")
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            sugerido = sugerido.replace(char, '')
        if not sugerido:
            sugerido = "producto"
            
        destino_base = os.path.join(carpeta, sugerido)
        destino = destino_base + ".png"
        counter = 1
        while os.path.exists(destino):
            destino = f"{destino_base}_{counter}.png"
            counter += 1

        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "creator png", "convertir_imagen.py"))
        
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        python_exe = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
        if not os.path.exists(python_exe):
            python_exe = "python"
        
        class DialogCreadorPNGPro(QDialog):
            def __init__(self, parent_widget=None, origen_img=None, destino_path=None, script=None, python="python"):
                super().__init__(parent_widget)
                self.origen_img = origen_img
                self.destino_path = destino_path
                self.script_path = script
                self.python_exe = python
                self.setWindowTitle("✨ Creador PNG Pro - Cartelería")
                self.setFixedSize(1100, 750)
                self.setStyleSheet("""
                    QDialog { background-color: #F8FAFC; font-family: 'Segoe UI', sans-serif; }
                    QLabel#title { font-size: 20px; font-weight: 800; color: #1E293B; margin-bottom: 15px; }
                    QLabel#subtitle { font-size: 13px; color: #64748B; margin-bottom: 20px; }
                    QLabel#section { font-size: 14px; font-weight: 700; color: #1E40AF; margin-top: 15px; }
                    QLabel#img_label { background-color: #E2E8F0; border: 2px dashed #CBD5E1; border-radius: 8px; font-weight: bold; color: #64748B; }
                    QLabel#value { font-size: 12px; color: #64748B; font-weight: 600; }
                    QPushButton { padding: 10px 20px; font-weight: bold; border-radius: 6px; font-size: 13px; }
                    QPushButton#accept { background-color: #2563EB; color: white; border: none; }
                    QPushButton#accept:hover { background-color: #1D4ED8; }
                    QPushButton#reject { background-color: #EF4444; color: white; border: none; }
                    QPushButton#reject:hover { background-color: #DC2626; }
                    QPushButton#apply { background-color: #10B981; color: white; border: none; }
                    QPushButton#apply:hover { background-color: #059669; }
                    QPushButton#preset { background-color: #8B5CF6; color: white; border: none; }
                    QPushButton#preset:hover { background-color: #7C3AED; }
                    QComboBox { padding: 8px; border: 1px solid #CBD5E1; border-radius: 6px; background: white; }
                """)
                
                self.setup_ui()
                self.load_original()
                
            def setup_ui(self):
                layout = QVBoxLayout(self)
                layout.setSpacing(15)
                
                # Header
                title = QLabel("✨ Creador PNG Pro - Cartelería", self)
                title.setObjectName("title")
                title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(title)
                
                subtitle = QLabel("Requisitos: 1024x1024px (mín 512px) • 150 DPI • Fondo transparente", self)
                subtitle.setObjectName("subtitle")
                subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(subtitle)
                
                # Images comparison
                images_layout = QHBoxLayout()
                images_layout.setSpacing(20)
                
                # Original
                orig_container = QVBoxLayout()
                lbl_orig_title = QLabel("Imagen Original", self)
                lbl_orig_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_orig_title.setStyleSheet("font-weight: 700; color: #64748B;")
                self.lbl_orig = QLabel(self)
                self.lbl_orig.setObjectName("img_label")
                self.lbl_orig.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.lbl_orig.setFixedSize(450, 450)
                orig_container.addWidget(lbl_orig_title)
                orig_container.addWidget(self.lbl_orig)
                images_layout.addLayout(orig_container)
                
                # Result
                res_container = QVBoxLayout()
                lbl_res_title = QLabel("Resultado Procesado", self)
                lbl_res_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_res_title.setStyleSheet("font-weight: 700; color: #64748B;")
                self.lbl_res = QLabel("Clic en 'Aplicar' para procesar", self)
                self.lbl_res.setObjectName("img_label")
                self.lbl_res.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.lbl_res.setFixedSize(450, 450)
                res_container.addWidget(lbl_res_title)
                res_container.addWidget(self.lbl_res)
                images_layout.addLayout(res_container)
                
                layout.addLayout(images_layout)
                
                # Controls section
                controls_frame = QFrame()
                controls_frame.setStyleSheet("background: white; border-radius: 8px; border: 1px solid #E2E8F0; padding: 15px;")
                controls_layout = QVBoxLayout(controls_frame)
                
                # Preset selector (always visible)
                preset_layout = QHBoxLayout()
                preset_layout.addWidget(QLabel("Preset:", self))
                self.combo_preset = QComboBox()
                self.combo_preset.addItems(["Custom", "📺 Cartelería (1024x1024)", "🌐 Web Optimized", "🖨️ Print Quality"])
                self.combo_preset.currentIndexChanged.connect(self.apply_preset)
                preset_layout.addWidget(self.combo_preset)
                preset_layout.addStretch()
                controls_layout.addLayout(preset_layout)
                
                # Advanced settings toggle button
                self.btn_toggle_advanced = QPushButton("⚙️ Configuración Avanzada", self)
                self.btn_toggle_advanced.setStyleSheet("background-color: #64748B; color: white; border: none; border-radius: 6px; padding: 8px;")
                self.btn_toggle_advanced.clicked.connect(self.toggle_advanced)
                controls_layout.addWidget(self.btn_toggle_advanced)
                
                # Advanced parameters container (collapsible)
                self.advanced_container = QWidget()
                self.advanced_container.setVisible(False)
                advanced_layout = QVBoxLayout(self.advanced_container)
                advanced_layout.setContentsMargins(0, 10, 0, 0)
                
                # Parameters grid
                params_layout = QGridLayout()
                params_layout.setSpacing(10)
                
                # Black threshold
                params_layout.addWidget(QLabel("Umbral Negro:", self), 0, 0)
                self.slider_black = QSlider(Qt.Orientation.Horizontal)
                self.slider_black.setRange(0, 100)
                self.slider_black.setValue(35)
                self.slider_black.valueChanged.connect(self.update_values)
                params_layout.addWidget(self.slider_black, 0, 1)
                self.lbl_black_val = QLabel("35", self)
                self.lbl_black_val.setObjectName("value")
                params_layout.addWidget(self.lbl_black_val, 0, 2)
                
                # White threshold
                params_layout.addWidget(QLabel("Umbral Blanco:", self), 1, 0)
                self.slider_white = QSlider(Qt.Orientation.Horizontal)
                self.slider_white.setRange(200, 255)
                self.slider_white.setValue(245)
                self.slider_white.valueChanged.connect(self.update_values)
                params_layout.addWidget(self.slider_white, 1, 1)
                self.lbl_white_val = QLabel("245", self)
                self.lbl_white_val.setObjectName("value")
                params_layout.addWidget(self.lbl_white_val, 1, 2)
                
                # Sharpness
                params_layout.addWidget(QLabel("Nitidez:", self), 2, 0)
                self.slider_sharpness = QSlider(Qt.Orientation.Horizontal)
                self.slider_sharpness.setRange(5, 20)
                self.slider_sharpness.setValue(14)
                self.slider_sharpness.valueChanged.connect(self.update_values)
                params_layout.addWidget(self.slider_sharpness, 2, 1)
                self.lbl_sharpness_val = QLabel("1.4", self)
                self.lbl_sharpness_val.setObjectName("value")
                params_layout.addWidget(self.lbl_sharpness_val, 2, 2)
                
                # Contrast
                params_layout.addWidget(QLabel("Contraste:", self), 3, 0)
                self.slider_contrast = QSlider(Qt.Orientation.Horizontal)
                self.slider_contrast.setRange(5, 20)
                self.slider_contrast.setValue(11)
                self.slider_contrast.valueChanged.connect(self.update_values)
                params_layout.addWidget(self.slider_contrast, 3, 1)
                self.lbl_contrast_val = QLabel("1.1", self)
                self.lbl_contrast_val.setObjectName("value")
                params_layout.addWidget(self.lbl_contrast_val, 3, 2)
                
                advanced_layout.addLayout(params_layout)
                controls_layout.addWidget(self.advanced_container)
                layout.addWidget(controls_frame)
                
                # Buttons
                btn_layout = QHBoxLayout()
                btn_layout.setSpacing(15)
                
                self.btn_reject = QPushButton("❌ Cancelar", self)
                self.btn_reject.setObjectName("reject")
                self.btn_reject.clicked.connect(self.reject)
                
                self.btn_apply = QPushButton("🔄 Aplicar Cambios", self)
                self.btn_apply.setObjectName("apply")
                self.btn_apply.clicked.connect(self.apply_processing)
                
                self.btn_ai = QPushButton("✨ Mejorar con IA", self)
                self.btn_ai.setStyleSheet("background-color: #8B5CF6; color: white; border: none;")
                self.btn_ai.clicked.connect(self.apply_ai)
                self.btn_ai.setEnabled(False)
                
                self.btn_accept = QPushButton("✅ Usar esta Imagen", self)
                self.btn_accept.setObjectName("accept")
                self.btn_accept.clicked.connect(self.accept)
                self.btn_accept.setEnabled(False)
                
                btn_layout.addStretch()
                btn_layout.addWidget(self.btn_reject)
                btn_layout.addWidget(self.btn_apply)
                btn_layout.addWidget(self.btn_ai)
                btn_layout.addWidget(self.btn_accept)
                btn_layout.addStretch()
                
                layout.addLayout(btn_layout)
                
            def load_original(self):
                pix_orig = QPixmap(self.origen_img).scaled(450, 450, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.lbl_orig.setPixmap(pix_orig)
                
            def update_values(self):
                self.lbl_black_val.setText(str(self.slider_black.value()))
                self.lbl_white_val.setText(str(self.slider_white.value()))
                self.lbl_sharpness_val.setText(f"{self.slider_sharpness.value() / 10:.1f}")
                self.lbl_contrast_val.setText(f"{self.slider_contrast.value() / 10:.1f}")
                self.combo_preset.setCurrentIndex(0)  # Set to custom when manually adjusted
                
            def toggle_advanced(self):
                is_visible = self.advanced_container.isVisible()
                self.advanced_container.setVisible(not is_visible)
                if not is_visible:
                    self.btn_toggle_advanced.setText("⚙️ Ocultar Configuración Avanzada")
                else:
                    self.btn_toggle_advanced.setText("⚙️ Configuración Avanzada")
                
            def apply_preset(self, index):
                if index == 1:  # Cartelería
                    self.slider_black.setValue(35)
                    self.slider_white.setValue(245)
                    self.slider_sharpness.setValue(14)
                    self.slider_contrast.setValue(11)
                elif index == 2:  # Web
                    self.slider_black.setValue(40)
                    self.slider_white.setValue(240)
                    self.slider_sharpness.setValue(12)
                    self.slider_contrast.setValue(11)
                elif index == 3:  # Print
                    self.slider_black.setValue(30)
                    self.slider_white.setValue(250)
                    self.slider_sharpness.setValue(15)
                    self.slider_contrast.setValue(12)
                
            def apply_processing(self):
                self.btn_apply.setEnabled(False)
                self.btn_reject.setEnabled(False)
                self.btn_accept.setEnabled(False)
                self.lbl_res.setStyleSheet("border: 2px dashed #CBD5E1; background-color: #E2E8F0;")
                self.lbl_res.setText("Procesando imagen (sin IA)...")
                QApplication.processEvents()
                
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                try:
                    command = [
                        self.python_exe, self.script_path, self.origen_img, self.destino_path,
                        '--black_threshold', str(self.slider_black.value()),
                        '--white_threshold', str(self.slider_white.value()),
                        '--sharpness_factor', str(self.slider_sharpness.value() / 10),
                        '--contrast_factor', str(self.slider_contrast.value() / 10),
                        '--output_size', '1024'
                    ]
                    
                    result = subprocess.run(command, capture_output=True, text=True)
                    print(f"DEBUG: Procesamiento sin IA - stdout: {result.stdout}")
                    print(f"DEBUG: Procesamiento sin IA - stderr: {result.stderr}")
                    
                    if result.returncode == 0 and os.path.exists(self.destino_path):
                        pix_res = QPixmap(self.destino_path)
                        self.lbl_res.setStyleSheet("background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAMUlEQVQ4T2NkYGAQYcAP3neF8BngjE8H48FADg1M7I4hA/DBTDQeGowYRoMhgYF3wQcAbSgKz+cK/L0AAAAASUVORK5CYII='); background-repeat: repeat; border: 2px solid #10B981;")
                        self.lbl_res.setPixmap(pix_res.scaled(450, 450, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                        self.lbl_res.setText("")
                        self.btn_accept.setEnabled(True)
                        self.btn_ai.setEnabled(True)
                    else:
                        self.lbl_res.setText(f"Error: {result.stderr[-150:] if result.stderr else 'Procesamiento fallido'}")
                except Exception as e:
                    self.lbl_res.setText(f"Error: {str(e)}")
                    print(f"DEBUG: Exception en apply_processing: {e}")
                finally:
                    QApplication.restoreOverrideCursor()
                    self.btn_apply.setEnabled(True)
                    self.btn_reject.setEnabled(True)
                    
            def apply_ai(self):
                self.btn_ai.setEnabled(False)
                self.btn_apply.setEnabled(False)
                self.btn_reject.setEnabled(False)
                self.btn_accept.setEnabled(False)
                self.lbl_res.setStyleSheet("border: 2px dashed #CBD5E1; background-color: #E2E8F0;")
                self.lbl_res.setText("Mejorando con IA...\n(Puede tardar unos 15s la primera vez)")
                QApplication.processEvents()
                
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                try:
                    command = [
                        self.python_exe, self.script_path, self.origen_img, self.destino_path,
                        '--black_threshold', str(self.slider_black.value()),
                        '--white_threshold', str(self.slider_white.value()),
                        '--sharpness_factor', str(self.slider_sharpness.value() / 10),
                        '--contrast_factor', str(self.slider_contrast.value() / 10),
                        '--output_size', '1024',
                        '--use_ai'
                    ]
                    
                    result = subprocess.run(command, capture_output=True, text=True)
                    if result.returncode == 0 and os.path.exists(self.destino_path):
                        pix_res = QPixmap(self.destino_path)
                        self.lbl_res.setStyleSheet("background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAMUlEQVQ4T2NkYGAQYcAP3neF8BngjE8H48FADg1M7I4hA/DBTDQeGowYRoMhgYF3wQcAbSgKz+cK/L0AAAAASUVORK5CYII='); background-repeat: repeat; border: 2px solid #8B5CF6;")
                        self.lbl_res.setPixmap(pix_res.scaled(450, 450, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                        self.lbl_res.setText("")
                        self.btn_accept.setEnabled(True)
                        self.btn_ai.setText("✨ IA Aplicada ✓")
                    else:
                        self.lbl_res.setText(f"Error IA: {result.stderr[-100:] if result.stderr else 'Procesamiento IA fallido'}")
                        self.btn_ai.setEnabled(True)
                except Exception as e:
                    self.lbl_res.setText(f"Error IA: {str(e)}")
                    self.btn_ai.setEnabled(True)
                finally:
                    QApplication.restoreOverrideCursor()
                    self.btn_apply.setEnabled(True)
                    self.btn_reject.setEnabled(True)

        dlg = DialogCreadorPNGPro(self, origen, destino, script_path, python_exe)
        
        # Apply carteleria preset by default
        dlg.combo_preset.setCurrentIndex(1)
        
        if qt_exec(dlg):
            nombre_archivo = os.path.basename(destino)
            self._icono_seleccionado = nombre_archivo
            self._actualizar_preview(nombre_archivo)
        else:
            if os.path.exists(destino):
                try:
                    os.remove(destino)
                except:
                    pass

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
            self._cargar()
            self._reseleccionar(nombre)
            QMessageBox.information(
                self,
                "PNG productos",
                "Listo. La cartelería va a mostrar ese PNG en las tarjetas de ese producto.",
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
