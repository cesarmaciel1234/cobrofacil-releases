import hashlib
import os
from PIL import Image, ImageChops
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame, QGridLayout,
    QWidget, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor
from src.database import db_manager
from src.config import config
from src.hardware.cash_drawer import drawer_manager

try:
    from src.ui_components.virtual_keyboard import VirtualKeyboard
    HAS_KEYBOARD = True
except Exception as e:
    import logging
    logging.warning(f"Módulo de teclado virtual no disponible en Paso6Cobro: {e}")
    HAS_KEYBOARD = False

def ensure_icons():
    """Autogenera los iconos recortándolos y haciéndolos transparentes si no existen."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(base_dir, "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
            
        required = ["tarjeta.png", "mixto.png", "transferencia.png", "efectivo.png"]
        missing = [r for r in required if not os.path.exists(os.path.join(assets_dir, r))]
        if not missing:
            return

        # Intentar cargar PIL sólo si faltan iconos
        try:
            from PIL import Image, ImageChops
        except ImportError:
            from src.logger import logger
            logger.warning("PIL (Pillow) no está instalado. No se pueden autogenerar iconos faltantes.")
            return

        p1 = os.path.join(assets_dir, "media__1779193497248.png")
        p2 = os.path.join(assets_dir, "media__1779193546849.png")

        def process_and_save(img, save_path):
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            bg = Image.new(img.mode, img.size, (255, 255, 255, 255))
            diff = ImageChops.difference(img, bg)
            diff_rgb = diff.convert('RGB')
            bbox = diff_rgb.getbbox()
            if bbox:
                img = img.crop(bbox)
            
            datas = img.getdata()
            newData = []
            for item in datas:
                if item[0] > 235 and item[1] > 235 and item[2] > 235:
                    newData.append((255, 255, 255, 0))
                else:
                    newData.append(item)
            img.putdata(newData)
            img.save(save_path, "PNG")

        if os.path.exists(p1):
            im1 = Image.open(p1)
            w, h = im1.size
            tarjeta_img = im1.crop((0, 0, int(w * 0.35), h))
            process_and_save(tarjeta_img, os.path.join(assets_dir, "tarjeta.png"))
            mixto_img = im1.crop((int(w * 0.35), 0, int(w * 0.65), h))
            process_and_save(mixto_img, os.path.join(assets_dir, "mixto.png"))
            transf_img = im1.crop((int(w * 0.65), 0, w, h))
            process_and_save(transf_img, os.path.join(assets_dir, "transferencia.png"))

        if os.path.exists(p2):
            im2 = Image.open(p2)
            process_and_save(im2, os.path.join(assets_dir, "efectivo.png"))
    except Exception as e:
        from src.logger import logger
        logger.warning(f"Error autogenerando iconos: {e}")

# Ejecutar proceso autogenerador
ensure_icons()

class Paso6Cobro(QDialog):
    """
    PASO 6: VENTANA DE COBRO ELITE 2026
    Diseño premium, sombras cinemáticas y lógica infalible.
    """
    def __init__(self, total, items_carrito, parent=None):
        super().__init__(parent)
        self.total_original = total
        self.total_final = total
        self.items_carrito = items_carrito
        self.descuento_porcentaje = 0.0
        self.recargo_porcentaje = 0.0
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(910, 760)
        
        self.current_metodo = "Efectivo"
        self.setup_ui()
        self.apply_glow()

    def apply_glow(self):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor(67, 126, 232, 150)) # Brillo azul Elite
        glow.setOffset(0, 0)
        self.main_frame.setGraphicsEffect(glow)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)
        
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("QFrame#MainFrame { background-color: white; border-radius: 20px; border: 1px solid #CBD5E1; }")
        self.main_frame.setObjectName("MainFrame")
        layout.addWidget(self.main_frame)
        
        main_lay = QHBoxLayout(self.main_frame)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # --- SECCIÓN IZQUIERDA: PAGO (75%) ---
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: transparent;")
        left_lay = QVBoxLayout(left_panel)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)

        # HEADER AZUL "COBRAR"
        header = QLabel("  COBRAR")
        header.setFixedHeight(45)
        header.setStyleSheet("background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E3A8A, stop:1 #3B82F6); color: white; font-size: 18px; font-weight: 900; border-top-left-radius: 19px; padding-left: 20px; letter-spacing: 2px;")
        left_lay.addWidget(header)

        # CONTENIDO IZQUIERDO
        content_lay = QVBoxLayout()
        content_lay.setContentsMargins(40, 20, 40, 20)
        content_lay.setSpacing(20)

        self.lbl_total = QLabel(f"${self.total_original:,.2f}") # Fijo en el monto original
        self.lbl_total.setStyleSheet("color: #1E3A8A; font-size: 85px; font-weight: 900; font-family: 'Segoe UI Black'; border: none;")
        self.lbl_total.setAlignment(Qt.AlignCenter)
        content_lay.addWidget(self.lbl_total)

        # Métodos de Pago
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(20)
        self.btns = {}
        metodos = [
            ("💰", "Efectivo", "Efectivo"), 
            ("💳", "Crédito", "Tarjeta"), 
            ("🔀", "Mixto", "Mixto"), 
            ("🏦", "Transf.", "Transferencia")
        ]
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(base_dir, "assets")

        btn_lay.addStretch()
        for icon, text, key in metodos:
            container = QFrame()
            container.setFixedSize(120, 105)
            container.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 rgba(255, 255, 255, 0.75), 
                        stop:0.46 rgba(255, 255, 255, 0.6), 
                        stop:0.47 rgba(255, 255, 255, 0.25), 
                        stop:1 rgba(255, 255, 255, 0.45)
                    );
                    border: 1px solid rgba(255, 255, 255, 0.65); 
                    border-radius: 22px;
                }
                QFrame[active="true"] {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 rgba(243, 248, 255, 0.95), 
                        stop:0.46 rgba(224, 237, 255, 0.85), 
                        stop:0.47 rgba(191, 219, 254, 0.55), 
                        stop:1 rgba(219, 234, 254, 0.75)
                    );
                    border: 2.5px solid #3B82F6;
                }
                QFrame:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 rgba(255, 255, 255, 0.85), 
                        stop:0.46 rgba(255, 255, 255, 0.7), 
                        stop:0.47 rgba(255, 255, 255, 0.35), 
                        stop:1 rgba(255, 255, 255, 0.55)
                    );
                    border-color: rgba(59, 130, 246, 0.6);
                }
            """)
            container.setProperty("active", False)
            
            # Sombra inicial para efecto de flotación (iOS Style)
            shadow = QGraphicsDropShadowEffect(container)
            shadow.setBlurRadius(12)
            shadow.setColor(QColor(0, 0, 0, 25))
            shadow.setOffset(0, 4)
            container.setGraphicsEffect(shadow)
            
            c_lay = QVBoxLayout(container)
            c_lay.setContentsMargins(5, 5, 5, 5)
            c_lay.setSpacing(0)
            
            lbl_icon = QLabel()
            lbl_icon.setAlignment(Qt.AlignCenter)
            
            # Cargar imagen de icono o fallback a emoji si no existe
            icon_path = os.path.join(assets_dir, f"{key.lower()}.png")
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                lbl_icon.setPixmap(pixmap.scaled(96, 82, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                lbl_icon.setStyleSheet("background: transparent; border: none;")
            else:
                lbl_icon.setText(icon)
                lbl_icon.setStyleSheet("font-size: 38px; background: transparent; border: none;")
            
            c_lay.addWidget(lbl_icon)
            
            # Boton invisible superpuesto para capturar clicks
            btn_overlay = QPushButton(container)
            btn_overlay.setFixedSize(120, 105)
            btn_overlay.setStyleSheet("background: transparent; border: none;")
            btn_overlay.setCursor(Qt.PointingHandCursor)
            btn_overlay.setFocusPolicy(Qt.NoFocus)
            
            def make_callback(k=key):
                return lambda: self.set_metodo(k)
                
            btn_overlay.clicked.connect(make_callback())
            
            # Guardamos referencias en el diccionario btns
            self.btns[key] = {
                "frame": container,
                "lbl_text": None,
                "overlay": btn_overlay
            }
            
            btn_lay.addWidget(container)
            
        btn_lay.addStretch()
        
        content_lay.addLayout(btn_lay)
        content_lay.addSpacing(20)

        # Inputs de Pago
        input_grid = QGridLayout()
        input_grid.setSpacing(15)
        input_grid.setColumnStretch(0, 1)
        input_grid.setColumnStretch(1, 2)

        self.lbl_input1 = QLabel("PAGA CON ($):")
        self.lbl_input1.setStyleSheet("font-weight: 900; color: #1E3A8A; font-size: 18px;")
        self.lbl_input1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.txt_pago = QLineEdit("")
        self.txt_pago.setPlaceholderText("0.00")
        self.txt_pago.setStyleSheet("background: #F8FAFC; border: 2px solid #CBD5E1; border-radius: 12px; padding: 8px 15px; font-size: 32px; font-weight: 900; color: #1E3A8A;")
        self.txt_pago.textChanged.connect(self.calcular_vuelto)
        self.txt_pago.returnPressed.connect(self.intentar_finalizar)
        self.txt_pago.installEventFilter(self)
        
        self.lbl_input2 = QLabel("TARJETA/OTRO ($):")
        self.lbl_input2.setStyleSheet(self.lbl_input1.styleSheet())
        self.lbl_input2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.txt_otro = QLineEdit("0.00")
        self.txt_otro.setStyleSheet(self.txt_pago.styleSheet())
        self.txt_otro.textChanged.connect(self.calcular_vuelto)
        self.txt_otro.returnPressed.connect(self.intentar_finalizar)
        self.txt_otro.installEventFilter(self)
        self.lbl_input2.hide(); self.txt_otro.hide()

        input_grid.addWidget(self.lbl_input1, 0, 0)
        input_grid.addWidget(self.txt_pago, 0, 1)
        input_grid.addWidget(self.lbl_input2, 1, 0)
        input_grid.addWidget(self.txt_otro, 1, 1)
        content_lay.addLayout(input_grid)
        
        # NUEVA LÍNEA HORIZONTAL DE MODIFICADORES COMPACTA (Abajo del monto)
        mod_lay = QHBoxLayout()
        mod_lay.setSpacing(10)
        
        self.lbl_desc = QLabel("DESCUENTO (%):")
        self.lbl_desc.setStyleSheet("font-weight: 900; color: #10B981; font-size: 16px;")
        self.lbl_desc.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_desc = QLineEdit("0.00")
        self.txt_desc.setFixedWidth(120)
        self.txt_desc.setStyleSheet("background: #F8FAFC; border: 2px solid #CBD5E1; border-radius: 10px; padding: 6px 12px; font-size: 20px; font-weight: 900; color: #10B981; text-align: center;")
        self.txt_desc.textChanged.connect(self.on_descuento_changed)
        self.txt_desc.installEventFilter(self)
        
        self.lbl_rec = QLabel("RECARGO (%):")
        self.lbl_rec.setStyleSheet("font-weight: 900; color: #F59E0B; font-size: 16px;")
        self.lbl_rec.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_rec = QLineEdit("0.00")
        self.txt_rec.setFixedWidth(120)
        self.txt_rec.setStyleSheet("background: #F8FAFC; border: 2px solid #CBD5E1; border-radius: 10px; padding: 6px 12px; font-size: 20px; font-weight: 900; color: #F59E0B; text-align: center;")
        self.txt_rec.textChanged.connect(self.on_recargo_changed)
        self.txt_rec.installEventFilter(self)
        
        mod_lay.addStretch()
        mod_lay.addWidget(self.lbl_desc)
        mod_lay.addWidget(self.txt_desc)
        mod_lay.addSpacing(30)
        mod_lay.addWidget(self.lbl_rec)
        mod_lay.addWidget(self.txt_rec)
        mod_lay.addStretch()
        
        content_lay.addSpacing(10)
        content_lay.addLayout(mod_lay)
        
        # NUEVO: Neto a cobrar destacado abajo
        self.lbl_neto = QLabel(f"NETO A PAGAR: ${self.total_final:,.2f}")
        self.lbl_neto.setStyleSheet("font-weight: 900; color: #1E3A8A; font-size: 26px; letter-spacing: 1px; margin-top: 5px;")
        self.lbl_neto.setAlignment(Qt.AlignCenter)
        content_lay.addWidget(self.lbl_neto)

        # Vuelto
        vuelto_lay = QHBoxLayout()
        vuelto_lay.setSpacing(15)
        self.lbl_vuelto_tit = QLabel("SU CAMBIO:")
        self.lbl_vuelto_tit.setStyleSheet("font-weight: 900; color: #64748B; font-size: 20px;")
        self.lbl_vuelto_tit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_vuelto_val = QLabel("$0.00")
        self.lbl_vuelto_val.setStyleSheet("color: #10B981; font-size: 36px; font-weight: 900;")
        
        vuelto_lay.addStretch()
        vuelto_lay.addWidget(self.lbl_vuelto_tit)
        vuelto_lay.addWidget(self.lbl_vuelto_val)
        vuelto_lay.addStretch()
        content_lay.addLayout(vuelto_lay)

        # Barra de Estado Mercado Pago
        self.lbl_mp_status = QLabel("")
        self.lbl_mp_status.setAlignment(Qt.AlignCenter)
        self.lbl_mp_status.setStyleSheet("font-weight: bold; font-size: 13px; color: #0284c7; background: #e0f2fe; padding: 10px; border: 1px dashed #0284c7;")
        self.lbl_mp_status.hide()
        content_lay.addWidget(self.lbl_mp_status)

        self.timer_mp = QTimer(self)
        self.timer_mp.timeout.connect(self.verificar_pago_mp_automatico)
        
        content_lay.addStretch()
        left_lay.addLayout(content_lay)
        main_lay.addWidget(left_panel, 7)

        # --- SECCIÓN DERECHA: ACCIONES (25%) ---
        right_panel = QFrame()
        right_panel.setStyleSheet("QFrame { background-color: #F8FAFC; border-left: 1px solid #E2E8F0; border-top-right-radius: 19px; border-bottom-right-radius: 19px; }")
        right_lay = QVBoxLayout(right_panel)
        right_lay.setContentsMargins(15, 30, 15, 30)
        right_lay.setSpacing(12)

        def create_action_btn(text, callback, is_primary=False):
            btn = QPushButton(text)
            if is_primary:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3B82F6; color: white; padding: 15px; 
                        border: none; border-radius: 12px; font-size: 13px; font-weight: 900;
                    }
                    QPushButton:hover { background-color: #2563EB; }
                    QPushButton:pressed { background-color: #1D4ED8; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: white; color: #1E293B; padding: 15px; 
                        border: 2px solid #E2E8F0; border-radius: 12px; font-size: 13px; font-weight: 900;
                    }
                    QPushButton:hover { background-color: #F1F5F9; border-color: #CBD5E1; }
                    QPushButton:pressed { background-color: #E2E8F0; }
                """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(callback)
            return btn

        right_lay.addWidget(create_action_btn("🖨️ F1 - Cobrar e Imprimir", lambda: self.finalizar(True), is_primary=True))
        right_lay.addWidget(create_action_btn("🤝 F2 - Cobrar sin imprimir", lambda: self.finalizar(False)))
        right_lay.addWidget(create_action_btn("⌨️ ESC - Cancelar", self.reject))
        right_lay.addSpacing(20)
        
        self.btn_descuento = create_action_btn("🏷️ F3 - Descuento", self.abrir_descuento)
        self.btn_recargo = create_action_btn("📈 F4 - Recargo", self.abrir_recargo)
        right_lay.addWidget(self.btn_descuento)
        right_lay.addWidget(self.btn_recargo)
        
        if HAS_KEYBOARD:
            self.teclado_virtual = VirtualKeyboard(self, embedded=True)
            self.teclado_virtual.set_layout_mode("123")
            right_lay.addWidget(self.teclado_virtual)
        else:
            right_lay.addStretch()
            
            lbl_info_tit = QLabel("TOTAL DE ARTÍCULOS")
            lbl_info_tit.setStyleSheet("color: #64748B; font-weight: 900; font-size: 13px; border: none;")
            lbl_info_tit.setAlignment(Qt.AlignCenter)
            right_lay.addWidget(lbl_info_tit)
            
            lbl_info_val = QLabel(f"{sum(i['cant'] for i in self.items_carrito):g}")
            lbl_info_val.setStyleSheet("color: #1E3A8A; font-size: 28px; font-weight: 900; border: none;")
            lbl_info_val.setAlignment(Qt.AlignCenter)
            right_lay.addWidget(lbl_info_val)

        main_lay.addWidget(right_panel, 3)

        # Aplicar método inicial después de crear todos los widgets
        self.set_metodo("Efectivo")

        # Foco inicial en la casilla de pago para comenzar a escribir directamente
        self.txt_pago.setFocus()

    def set_metodo(self, key):
        self.current_metodo = key
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(base_dir, "assets")
        
        for k, b_dict in self.btns.items():
            is_active = (k == key)
            
            frame = b_dict["frame"]
            lbl_text = b_dict.get("lbl_text")
            
            frame.setProperty("active", is_active)
            # Forzar actualización de estilo
            frame.style().unpolish(frame)
            frame.style().polish(frame)
            frame.update()
            
            # Modificar la sombra dinámicamente para simular que el botón "flota" más alto al estar seleccionado
            shadow = frame.graphicsEffect()
            if isinstance(shadow, QGraphicsDropShadowEffect):
                if is_active:
                    shadow.setBlurRadius(25)
                    shadow.setColor(QColor(59, 130, 246, 85)) # Brillo azul iOS flotante
                    shadow.setOffset(0, 8) # Sombra más lejana para elevar el widget
                else:
                    shadow.setBlurRadius(12)
                    shadow.setColor(QColor(0, 0, 0, 25)) # Sombra suave base
                    shadow.setOffset(0, 4)
            
            # Zoom dinámico de los iconos:
            # Encontrar el QLabel de la imagen dentro del frame
            lbl_icon = frame.findChild(QLabel)
            if lbl_icon:
                icon_path = os.path.join(assets_dir, f"{k.lower()}.png")
                if os.path.exists(icon_path):
                    pixmap = QPixmap(icon_path)
                    # Tamaño según actividad (zoom de 110x95 en activo, 96x82 en inactivo)
                    w_icon, h_icon = (110, 95) if is_active else (96, 82)
                    lbl_icon.setPixmap(pixmap.scaled(w_icon, h_icon, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            if lbl_text:
                if is_active:
                    lbl_text.setStyleSheet("font-size: 13px; font-weight: 900; color: #1E3A8A; background: transparent; border: none;")
                else:
                    lbl_text.setStyleSheet("font-size: 13px; font-weight: 900; color: #475569; background: transparent; border: none;")
        
        if key == "Mixto":
            self.lbl_input1.setText("EFECTIVO ($):")
            self.lbl_input2.show(); self.txt_otro.show()
            self.txt_pago.clear()
            self.lbl_mp_status.hide()
            self.timer_mp.stop()
        elif key in ["Tarjeta", "Transferencia"]:
            self.lbl_input1.setText("PAGA CON ($):")
            self.lbl_input2.hide(); self.txt_otro.hide()
            # Autocompletar monto para medios electrónicos (evita errores y agiliza)
            self.txt_pago.setText(f"{self.total_final:.2f}")
            
            if key == "Transferencia":
                self.lbl_mp_status.setText(f"📡 ESCUCHANDO MERCADO PAGO EN TIEMPO REAL... (${self.total_final:.2f})")
                self.lbl_mp_status.setStyleSheet("font-weight: bold; font-size: 13px; color: #0284c7; background: #e0f2fe; padding: 10px; border-radius: 8px; border: 1px dashed #0284c7;")
                self.lbl_mp_status.show()
                self.timer_mp.start(1000)
            else:
                self.lbl_mp_status.hide()
                self.timer_mp.stop()
        else:
            self.lbl_input1.setText("PAGA CON ($):")
            self.lbl_input2.hide(); self.txt_otro.hide()
            # Limpiar para forzar ingreso manual y cálculo de vuelto real
            self.txt_pago.clear()
            self.lbl_mp_status.hide()
            self.timer_mp.stop()
        self.calcular_vuelto()
        
        # El cursor siempre vive en el casillero de monto y se selecciona todo al cambiar de método
        self.txt_pago.setFocus()
        self.txt_pago.selectAll()

    def calcular_vuelto(self):
        try:
            p1_t = self.txt_pago.text().replace('$', '').replace(',', '').strip()
            p2_t = self.txt_otro.text().replace('$', '').replace(',', '').strip()
            p1 = float(p1_t) if p1_t else 0
            p2 = float(p2_t) if p2_t and self.current_metodo == "Mixto" else 0
            total_pagado = p1 + p2
            vuelto = total_pagado - self.total_final
            
            if vuelto < 0:
                self.lbl_vuelto_tit.setText("FALTA:")
                self.lbl_vuelto_val.setText(f"${abs(vuelto):,.2f}")
                self.lbl_vuelto_val.setStyleSheet("color: #EF4444; font-size: 40px; font-weight: 900;")
            else:
                self.lbl_vuelto_tit.setText("SU CAMBIO:")
                self.lbl_vuelto_val.setText(f"${vuelto:,.2f}")
                self.lbl_vuelto_val.setStyleSheet("color: #10B981; font-size: 40px; font-weight: 900;")
        except: pass

    def verificar_pago_mp_automatico(self):
        try:
            import time
            from src.admin.admin10_mp import Admin10MP
            if hasattr(Admin10MP, 'ultimo_pago_detectado') and Admin10MP.ultimo_pago_detectado is not None:
                pago = Admin10MP.ultimo_pago_detectado
                ahora = time.time()
                
                # Validar que el pago haya ocurrido hace menos de 90 segundos
                if ahora - pago['timestamp'] <= 90:
                    # Validar que el monto coincida exactamente con self.total_final (permitiendo un margen de 0.05)
                    monto_pago = pago['monto']
                    if abs(monto_pago - self.total_final) <= 0.05:
                        # Consumir el pago para evitar duplicados
                        Admin10MP.ultimo_pago_detectado = None
                        
                        # Detener el timer para evitar ejecuciones paralelas
                        self.timer_mp.stop()
                        
                        self.txt_pago.setText(f"{monto_pago:.2f}")
                        self.lbl_mp_status.setText(f"✅ ¡PAGO DE {pago['nombre'].upper()} DETECTADO Y APROBADO!")
                        self.lbl_mp_status.setStyleSheet("font-weight: 900; font-size: 13px; color: #15803d; background: #dcfce7; padding: 10px; border-radius: 8px; border: 1px solid #16a34a;")
                        
                        # Esperar 1.5 segundos para la animación y finalizar con ticket
                        QTimer.singleShot(1500, lambda: self.finalizar(imprimir=True))
        except Exception as e:
            print(f"Error verificando auto-pago MP: {e}")

    def _validar_pago(self):
        """ Centraliza la validación para evitar redundancias y errores de arqueo. """
        p1_t = self.txt_pago.text().replace('$', '').replace(',', '').strip()
        p2_t = self.txt_otro.text().replace('$', '').replace(',', '').strip()
        
        if not p1_t:
            QMessageBox.warning(self, "¡DATO REQUERIDO!", "INGRESE EL MONTO RECIBIDO\n\nEl sistema debe registrar con cuánto pagó el cliente para el arqueo.")
            self.txt_pago.setFocus()
            return None

        try:
            p1 = float(p1_t)
            p2 = float(p2_t) if p2_t and self.current_metodo == "Mixto" else 0
            
            if (p1 + p2) < self.total_final:
                # Si falta dinero y no es mixto, ofrecer pasarse a Mixto
                if self.current_metodo != "Mixto":
                    self.set_metodo("Mixto")
                    faltante = self.total_final - p1
                    self.txt_otro.setText(f"{faltante:.2f}")
                    self.txt_otro.setFocus()
                    self.txt_otro.selectAll()
                    return None
                else:
                    QMessageBox.critical(self, "MONTO INSUFICIENTE", f"Faltan ${(self.total_final - (p1+p2)):.2f} para cubrir el total.")
                    return None
            
            return (p1, p2)
        except ValueError:
            QMessageBox.critical(self, "ERROR", "Monto inválido ingresado.")
            return None

    def intentar_finalizar(self):
        vals = self._validar_pago()
        if vals:
            # Enter se comporta como F2 (Solo registrar, sin imprimir) para máxima velocidad
            self.finalizar(imprimir=False)

    def recargar_total_final(self):
        monto_desc = self.total_original * (self.descuento_porcentaje / 100.0)
        monto_rec = self.total_original * (self.recargo_porcentaje / 100.0)
        
        self.total_final = max(0.0, self.total_original - monto_desc + monto_rec)
        
        # El total de arriba sigue mostrando el original fijo
        self.lbl_total.setText(f"${self.total_original:,.2f}")
        
        # El neto destacado de abajo se actualiza en caliente
        self.lbl_neto.setText(f"NETO A PAGAR: ${self.total_final:,.2f}")
        
        # Actualizar visualización del botón de Descuento (Premium UX!)
        if self.descuento_porcentaje > 0:
            self.btn_descuento.setText(f"🏷️ DESC: {self.descuento_porcentaje:g}% (F3)")
            self.btn_descuento.setStyleSheet("background: #047857; color: white; padding: 15px; border-radius: 10px; font-weight: 900; font-size: 12px; border: 2px solid #34D399;")
        else:
            self.btn_descuento.setText("🏷️ DESCUENTO (F3)")
            self.btn_descuento.setStyleSheet("background: #10B981; color: white; padding: 15px; border-radius: 10px; font-weight: 900; font-size: 12px; border: none;")
            
        # Actualizar visualización del botón de Recargo (Premium UX!)
        if self.recargo_porcentaje > 0:
            self.btn_recargo.setText(f"📈 REC: {self.recargo_porcentaje:g}% (F4)")
            self.btn_recargo.setStyleSheet("background: #B45309; color: white; padding: 15px; border-radius: 10px; font-weight: 900; font-size: 12px; border: 2px solid #FBBF24;")
        else:
            self.btn_recargo.setText("📈 RECARGO (F4)")
            self.btn_recargo.setStyleSheet("background: #F59E0B; color: white; padding: 15px; border-radius: 10px; font-weight: 900; font-size: 12px; border: none;")
            
        # Si el método es electrónico, actualizar el autocompletado del pago de inmediato
        if self.current_metodo in ["Tarjeta", "Transferencia"]:
            self.txt_pago.setText(f"{self.total_final:.2f}")
            
        self.calcular_vuelto()

    def on_descuento_changed(self, text):
        try:
            val = float(text.strip()) if text.strip() else 0.0
            if val < 0: val = 0.0
            if val > 100: val = 100.0
            self.descuento_porcentaje = val
            self.recargar_total_final()
        except ValueError:
            pass

    def on_recargo_changed(self, text):
        try:
            val = float(text.strip()) if text.strip() else 0.0
            if val < 0: val = 0.0
            if val > 500: val = 500.0
            self.recargo_porcentaje = val
            self.recargar_total_final()
        except ValueError:
            pass

    def abrir_descuento(self):
        self.txt_desc.setFocus()
        self.txt_desc.selectAll()

    def abrir_recargo(self):
        self.txt_rec.setFocus()
        self.txt_rec.selectAll()

    def finalizar(self, imprimir=True):
        if getattr(self, '_procesando_pago', False):
            return
        
        vals = self._validar_pago()
        if not vals: return
        
        self._procesando_pago = True
        p1, p2 = vals
        
        try:
            pago_efectivo = p1 if self.current_metodo in ["Efectivo", "Mixto"] else 0
            pago_otro = p2 if self.current_metodo == "Mixto" else (p1 if self.current_metodo != "Efectivo" else 0)
            
            from src.cajero.paso5_terminal import CajeroActivo
            
            monto_desc = self.total_original * (self.descuento_porcentaje / 100.0)
            monto_rec = self.total_original * (self.recargo_porcentaje / 100.0)
            
            self.resultado_venta = {
                'total': self.total_final,
                'pago_con': p1 + p2,
                'cambio': (p1 + p2) - self.total_final,
                'pago_efectivo': pago_efectivo,
                'pago_otro': pago_otro,
                'usuario': config.current_user.get('username', 'cajero'),
                'usuario_secundario': CajeroActivo.nombre if CajeroActivo.numero == 2 else '',
                'metodo_pago': self.current_metodo,
                'estado': 'COMPLETADA',
                'descuento': monto_desc,
                'recargo': monto_rec
            }
            
            id_v = db_manager.guardar_venta_completa(self.resultado_venta, self.items_carrito)
            if id_v:
                from src.hardware.printer import printer_manager
                # Determinar si el cajón debe abrirse según el método y configuración
                debe_abrir = False
                if self.current_metodo == "Efectivo": debe_abrir = config.get("drawer_open_cash", True)
                elif self.current_metodo == "Mixto": debe_abrir = config.get("drawer_open_mixed", True)
                elif self.current_metodo == "Tarjeta": debe_abrir = config.get("drawer_open_card", False)
                elif self.current_metodo == "Transferencia": debe_abrir = config.get("drawer_open_transfer", False)

                if debe_abrir:
                    drawer_manager.set_authorized(True)

                if imprimir:
                    # Imprimir ticket (internamente puede abrir el cajón si se le pide)
                    self.imprimir_ticket(id_v, abrir_manual=debe_abrir)
                elif debe_abrir:
                    # No imprimimos, pero abrimos el cajón para el efectivo
                    drawer_manager.abrir(autorizada=True)

                self.accept()
        except Exception as e:
            self._procesando_pago = False
            QMessageBox.critical(self, "Error", f"Fallo al cobrar: {e}")

    def imprimir_ticket(self, id_v, abrir_manual=False):
        try:
            from src.hardware.printer import printer_manager
            from src.cajero.paso5_terminal import CajeroActivo
            
            monto_desc = self.total_original * (self.descuento_porcentaje / 100.0)
            monto_rec = self.total_original * (self.recargo_porcentaje / 100.0)
            
            # El ticket imprimirá y abrirá si abrir_manual es True
            printer_manager.imprimir_ticket_venta(
                id_v, self.items_carrito, self.total_final, 
                self.resultado_venta['pago_con'], self.resultado_venta['cambio'],
                abrir_cajon=abrir_manual, discount_amount=monto_desc, surcharge_amount=monto_rec,
                cajero=CajeroActivo.nombre, metodo_pago=self.resultado_venta.get('metodo_pago', 'Efectivo')
            )
        except: pass

    def reject(self):
        try:
            self.timer_mp.stop()
        except: pass
        super().reject()

    def eventFilter(self, watched, event):
        # Evitar fallos de inicialización si los widgets aún no se han creado en setup_ui
        if not hasattr(self, 'txt_pago') or not hasattr(self, 'txt_otro') or not hasattr(self, 'txt_desc') or not hasattr(self, 'txt_rec'):
            return super().eventFilter(watched, event)
            
        if watched in [self.txt_pago, self.txt_otro, self.txt_desc, self.txt_rec] and event.type() == QEvent.KeyPress:
            k = event.key()
            if k in (Qt.Key_Left, Qt.Key_Right):
                # Desviar flechas a la navegación de métodos de pago
                methods = list(self.btns.keys())
                curr_idx = methods.index(self.current_metodo)
                if k == Qt.Key_Left: next_idx = (curr_idx - 1) % len(methods)
                else: next_idx = (curr_idx + 1) % len(methods)
                self.set_metodo(methods[next_idx])
                return True # Consumir evento
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event):
        k = event.key()
        # Navegación de métodos con flechas (Solo si no estamos en un QLineEdit con texto)
        if k in (Qt.Key_Left, Qt.Key_Right):
            methods = list(self.btns.keys())
            curr_idx = methods.index(self.current_metodo)
            if k == Qt.Key_Left: next_idx = (curr_idx - 1) % len(methods)
            else: next_idx = (curr_idx + 1) % len(methods)
            self.set_metodo(methods[next_idx])
            return

        if k == Qt.Key_F1: self.finalizar(True)
        elif k == Qt.Key_F2: self.finalizar(False)
        elif k == Qt.Key_F3: self.abrir_descuento()
        elif k == Qt.Key_F4: self.abrir_recargo()
        elif k == Qt.Key_Escape: self.reject()
        elif k in (Qt.Key_Return, Qt.Key_Enter):
            # Lógica de Enter Inteligente: 3 Pasos
            foco = self.focusWidget()
            if isinstance(foco, QPushButton) and foco in self.btns.values():
                # 1. ENTER ELIGE MÉTODO -> Salta al casillero de monto
                self.txt_pago.setFocus()
                self.txt_pago.selectAll()
            else:
                # 2 y 3. ENTER CONFIRMA Y CIERRA (Sin Ticket)
                self.intentar_finalizar()
        else:
            super().keyPressEvent(event)
