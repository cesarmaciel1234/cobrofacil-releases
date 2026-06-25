import hashlib
import os
from PIL import Image, ImageChops
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame, QGridLayout,
    QWidget, QGraphicsDropShadowEffect, QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor, QKeyEvent
from src.base_de_datos.database import db_manager
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
        self.setFixedSize(1200, 780)
        
        self.current_metodo = "Efectivo"
        self.setup_ui()
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state("paso6")
        except:
            pass
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

        # HEADER AZUL "COBRAR" (Estilo transparente premium)
        self.header = QLabel("  COBRAR")
        self.header.setFixedHeight(64)
        left_lay.addWidget(self.header)

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
        btn_lay.setSpacing(25)
        self.btns = {}
        metodos = [
            ("💰", "Efectivo", "Efectivo"), 
            ("💳", "Crédito", "Tarjeta"), 
            ("🏦", "Transf.", "Transferencia"),
            ("📱", "QR", "QR"),
            ("👥", "Fiado", "Fiado"),
            ("🔀", "Mixto", "Mixto")
        ]
        
        # Cargar lista de clientes para fiado
        self.lista_clientes = db_manager.execute_query("SELECT id, nombre, limite_credito, deuda_actual FROM clientes ORDER BY nombre ASC")

        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(base_dir, "assets")

        btn_lay.addStretch()
        theme = config.get("theme", "light")
        for icon, text, key in metodos:
            container = QFrame()
            container.setFixedSize(120, 105)
            if theme == "dark":
                container.setStyleSheet("""
                    QFrame {
                        background: #1E293B;
                        border: 1.5px solid #334155;
                        border-radius: 24px;
                    }
                    QFrame[active="true"] {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 rgba(59, 130, 246, 0.15), 
                            stop:1 rgba(59, 130, 246, 0.05)
                        );
                        border: 2.5px solid #3B82F6;
                    }
                    QFrame:hover {
                        background: #334155;
                        border-color: rgba(59, 130, 246, 0.60);
                    }
                """)
            else:
                container.setStyleSheet("""
                    QFrame {
                        background: #FFFFFF;
                        border: 1.5px solid #EEF2F8;
                        border-radius: 24px;
                    }
                    QFrame[active="true"] {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 rgba(59, 130, 246, 0.08), 
                            stop:1 rgba(59, 130, 246, 0.03)
                        );
                        border: 2.5px solid #3B82F6;
                    }
                    QFrame:hover {
                        background: #F8FAFC;
                        border-color: rgba(59, 130, 246, 0.40);
                    }
                """)
            container.setProperty("active", False)
            
            # Sombra inicial suave
            shadow = QGraphicsDropShadowEffect(container)
            shadow.setBlurRadius(16)
            shadow.setColor(QColor(59, 130, 246, 20))
            shadow.setOffset(0, 5)
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
        self.txt_pago.setStyleSheet("""
            QLineEdit {
                background: #F8FAFC;
                border: 1.5px solid #E2E8F0;
                border-radius: 16px;
                padding: 10px 16px;
                font-size: 28px;
                font-weight: 900;
                color: #1E3A8A;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #3B82F6;
                background: rgba(59, 130, 246, 0.04);
                color: #0F172A;
            }
        """)
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

        from PyQt5.QtWidgets import QComboBox
        self.lbl_cliente = QLabel("CLIENTE:")
        self.lbl_cliente.setStyleSheet(self.lbl_input1.styleSheet())
        self.lbl_cliente.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.cmb_cliente = QComboBox()
        self.cmb_cliente.setStyleSheet("""
            QComboBox {
                background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 10px 16px; font-size: 20px; font-weight: bold; color: #1E3A8A;
            }
        """)
        for c in self.lista_clientes:
            disp = float(c['limite_credito']) - float(c['deuda_actual'])
            self.cmb_cliente.addItem(f"{c['nombre']} (Disp: ${disp:,.2f})", c['id'])
            
        self.lbl_cliente.hide()
        self.cmb_cliente.hide()

        input_grid.addWidget(self.lbl_input1, 0, 0)
        input_grid.addWidget(self.txt_pago, 0, 1)
        input_grid.addWidget(self.lbl_input2, 1, 0)
        input_grid.addWidget(self.txt_otro, 1, 1)
        input_grid.addWidget(self.lbl_cliente, 2, 0)
        input_grid.addWidget(self.cmb_cliente, 2, 1)
        content_lay.addLayout(input_grid)
        
        # NUEVA LÍNEA HORIZONTAL DE MODIFICADORES COMPACTA (Abajo del monto)
        mod_lay = QHBoxLayout()
        mod_lay.setSpacing(10)
        
        self.lbl_desc = QLabel("DESCUENTO ($ o %):")
        self.lbl_desc.setStyleSheet("font-weight: 900; color: #10B981; font-size: 16px;")
        self.lbl_desc.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_desc = QLineEdit("")
        self.txt_desc.setPlaceholderText("0.00")
        self.txt_desc.setFixedWidth(140)
        self.txt_desc.setStyleSheet("""
            QLineEdit {
                background: #F8FAFC;
                border: 1.5px solid #E2E8F0;
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 18px;
                font-weight: 900;
                color: #10B981;
                text-align: center;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #10B981;
                background: rgba(16, 185, 129, 0.04);
            }
        """)
        self.txt_desc.textChanged.connect(self.on_descuento_changed)
        self.txt_desc.installEventFilter(self)

        self.lbl_rec = QLabel("RECARGO ($ o %):")
        self.lbl_rec.setStyleSheet("font-weight: 900; color: #F59E0B; font-size: 16px;")
        self.lbl_rec.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_rec = QLineEdit("")
        self.txt_rec.setPlaceholderText("0.00")
        self.txt_rec.setFixedWidth(140)
        self.txt_rec.setStyleSheet("""
            QLineEdit {
                background: #F8FAFC;
                border: 1.5px solid #E2E8F0;
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 18px;
                font-weight: 900;
                color: #F59E0B;
                text-align: center;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #F59E0B;
                background: rgba(245, 158, 11, 0.04);
            }
        """)
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
        self.lbl_mp_status.setStyleSheet("font-weight: 800; font-size: 12px; color: #0284c7; background: #e0f2fe; padding: 8px 16px; border: none; border-radius: 10px; font-family: 'Segoe UI';")
        self.lbl_mp_status.hide()
        content_lay.addWidget(self.lbl_mp_status)
        
        self.timer_mp = QTimer(self)
        self.timer_mp.timeout.connect(self.verificar_pago_mp_automatico)
        
        content_lay.addStretch()
        left_lay.addLayout(content_lay)
        main_lay.addWidget(left_panel, 11)
        
        # --- SECCIÓN DERECHA: ACCIONES (~35%) ---
        theme = config.get("theme", "light")
        right_panel = QFrame()
        self.right_panel = right_panel
        right_panel.setMinimumWidth(400)
        right_lay = QVBoxLayout(right_panel)
        right_lay.setContentsMargins(12, 24, 12, 24)
        right_lay.setSpacing(6)
        
        def create_action_btn(fn_key, subtitle, callback, style="default"):
            btn = QPushButton(f"{fn_key}\n{subtitle}")
            btn.setFixedHeight(40)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            base = "border-radius: 16px; font-family: 'Segoe UI', sans-serif; font-size: 10px; font-weight: 900; padding: 2px 8px;"
            if style == "primary":
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #2563EB);
                        color: white; border: none; {base}
                    }}
                    QPushButton:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #1D4ED8);
                    }}
                """)
            elif style == "green":
                btn.setStyleSheet(f"QPushButton {{ background: #10B981; color: white; border: none; {base} }} QPushButton:hover {{ background: #059669; }}")
            elif style == "orange":
                btn.setStyleSheet(f"QPushButton {{ background: #F59E0B; color: white; border: none; {base} }} QPushButton:hover {{ background: #D97706; }}")
            elif theme == "dark":
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #334155; color: #F8FAFC;
                        border: 1.5px solid #475569; {base}
                    }}
                    QPushButton:hover {{ background-color: #475569; border-color: #64748B; }}
                    QPushButton:pressed {{ background-color: #1E293B; }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #FFFFFF; color: #1E293B;
                        border: 1.5px solid #E2E8F0; {base}
                    }}
                    QPushButton:hover {{ background-color: #F1F5F9; border-color: #CBD5E1; }}
                    QPushButton:pressed {{ background-color: #E2E8F0; }}
                """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(callback)
            return btn

        actions_grid = QGridLayout()
        actions_grid.setSpacing(6)
        actions_grid.setContentsMargins(0, 0, 0, 0)
        actions_grid.setColumnStretch(0, 1)
        actions_grid.setColumnStretch(1, 1)

        actions_grid.addWidget(create_action_btn("F1", "imprime", lambda: self.finalizar(True), style="primary"), 0, 0)
        actions_grid.addWidget(create_action_btn("F2", "s/imprime", lambda: self.finalizar(False)), 0, 1)

        self.btn_descuento = create_action_btn("F3", "descuento", self.abrir_descuento, style="green")
        self.btn_recargo = create_action_btn("F4", "recargo", self.abrir_recargo, style="orange")
        actions_grid.addWidget(self.btn_descuento, 1, 0)
        actions_grid.addWidget(self.btn_recargo, 1, 1)

        self.btn_f11 = create_action_btn("F11", "Point MP", lambda: self.procesar_pago_mercadopago_point())
        self.btn_f12 = create_action_btn("F12", "Verif QR", lambda: self.verificar_transferencia_mp())
        actions_grid.addWidget(self.btn_f11, 2, 0)
        actions_grid.addWidget(self.btn_f12, 2, 1)

        right_lay.addLayout(actions_grid)

        btn_f10 = create_action_btn("F10", "AFIP", lambda: self.finalizar_fiscal_efectivo())
        btn_f10.hide()
        right_lay.addWidget(btn_f10)
        
        # Teclado numérico físico propio (incrustado directamente)
        self.build_teclado_propio(right_lay)

        main_lay.addWidget(right_panel, 6)
        self.apply_theme()

        # Aplicar método inicial después de crear todos los widgets
        self.set_metodo("Efectivo")
        self.recargar_total_final()

        # Foco inicial en la casilla de pago para comenzar a escribir directamente
        self.txt_pago.setFocus()

    def apply_theme(self):
        theme = config.get("theme", "light")
        if theme == "dark":
            self.main_frame.setStyleSheet("QFrame#MainFrame { background-color: #0F172A; border-radius: 28px; border: none; }")
            self.header.setStyleSheet("background-color: transparent; color: #F8FAFC; font-size: 16px; font-weight: 900; border: none; padding-left: 24px; letter-spacing: 3px;")
            self.lbl_total.setStyleSheet("color: #38BDF8; font-size: 85px; font-weight: 900; font-family: 'Segoe UI Black'; border: none;")
            
            self.lbl_input1.setStyleSheet("font-weight: 900; color: #F8FAFC; font-size: 18px;")
            self.lbl_input2.setStyleSheet("font-weight: 900; color: #F8FAFC; font-size: 18px;")
            
            pago_style = """
                QLineEdit {
                    background: #1E293B;
                    border: 1.5px solid #334155;
                    border-radius: 16px;
                    padding: 10px 16px;
                    font-size: 28px;
                    font-weight: 900;
                    color: #38BDF8;
                    font-family: 'Segoe UI', sans-serif;
                }
                QLineEdit:focus {
                    border: 2px solid #3B82F6;
                    background: #0F172A;
                    color: #F8FAFC;
                }
            """
            self.txt_pago.setStyleSheet(pago_style)
            self.txt_otro.setStyleSheet(pago_style)
            
            self.txt_desc.setStyleSheet("""
                QLineEdit {
                    background: #1E293B;
                    border: 1.5px solid #334155;
                    border-radius: 12px;
                    padding: 6px 12px;
                    font-size: 18px;
                    font-weight: 900;
                    color: #10B981;
                    text-align: center;
                    font-family: 'Segoe UI', sans-serif;
                }
                QLineEdit:focus {
                    border: 2px solid #10B981;
                    background: #0F172A;
                }
            """)
            self.txt_rec.setStyleSheet("""
                QLineEdit {
                    background: #1E293B;
                    border: 1.5px solid #334155;
                    border-radius: 12px;
                    padding: 6px 12px;
                    font-size: 18px;
                    font-weight: 900;
                    color: #F59E0B;
                    text-align: center;
                    font-family: 'Segoe UI', sans-serif;
                }
                QLineEdit:focus {
                    border: 2px solid #F59E0B;
                    background: #0F172A;
                }
            """)
            
            self.lbl_neto.setStyleSheet("font-weight: 900; color: #38BDF8; font-size: 26px; letter-spacing: 1px; margin-top: 5px;")
            self.lbl_vuelto_tit.setStyleSheet("font-weight: 900; color: #94A3B8; font-size: 20px;")
            
            if hasattr(self, 'right_panel'):
                self.right_panel.setStyleSheet("QFrame { background-color: #1E293B; border: none; border-top-right-radius: 28px; border-bottom-right-radius: 28px; }")
            
            if hasattr(self, 'kb_frame'):
                self.kb_frame.setStyleSheet("""
                    QFrame {
                        background-color: #1E293B;
                        border-radius: 20px;
                        border: 1px solid #334155;
                    }
                """)
        else:
            self.main_frame.setStyleSheet("QFrame#MainFrame { background-color: #FFFFFF; border-radius: 28px; border: none; }")
            self.header.setStyleSheet("background-color: transparent; color: #1E3A8A; font-size: 16px; font-weight: 900; border: none; padding-left: 24px; letter-spacing: 3px;")
            self.lbl_total.setStyleSheet("color: #1E3A8A; font-size: 85px; font-weight: 900; font-family: 'Segoe UI Black'; border: none;")
            
            self.lbl_input1.setStyleSheet("font-weight: 900; color: #1E3A8A; font-size: 18px;")
            self.lbl_input2.setStyleSheet("font-weight: 900; color: #1E3A8A; font-size: 18px;")
            
            pago_style = """
                QLineEdit {
                    background: #F8FAFC;
                    border: 1.5px solid #E2E8F0;
                    border-radius: 16px;
                    padding: 10px 16px;
                    font-size: 28px;
                    font-weight: 900;
                    color: #1E3A8A;
                    font-family: 'Segoe UI', sans-serif;
                }
                QLineEdit:focus {
                    border: 2px solid #3B82F6;
                    background: rgba(59, 130, 246, 0.04);
                    color: #0F172A;
                }
            """
            self.txt_pago.setStyleSheet(pago_style)
            self.txt_otro.setStyleSheet(pago_style)
            
            self.txt_desc.setStyleSheet("""
                QLineEdit {
                    background: #F8FAFC;
                    border: 1.5px solid #E2E8F0;
                    border-radius: 12px;
                    padding: 6px 12px;
                    font-size: 18px;
                    font-weight: 900;
                    color: #10B981;
                    text-align: center;
                    font-family: 'Segoe UI', sans-serif;
                }
                QLineEdit:focus {
                    border: 2px solid #10B981;
                    background: rgba(16, 185, 129, 0.04);
                }
            """)
            self.txt_rec.setStyleSheet("""
                QLineEdit {
                    background: #F8FAFC;
                    border: 1.5px solid #E2E8F0;
                    border-radius: 12px;
                    padding: 6px 12px;
                    font-size: 18px;
                    font-weight: 900;
                    color: #F59E0B;
                    text-align: center;
                    font-family: 'Segoe UI', sans-serif;
                }
                QLineEdit:focus {
                    border: 2px solid #F59E0B;
                    background: rgba(245, 158, 11, 0.04);
                }
            """)
            
            self.lbl_neto.setStyleSheet("font-weight: 900; color: #1E3A8A; font-size: 26px; letter-spacing: 1px; margin-top: 5px;")
            self.lbl_vuelto_tit.setStyleSheet("font-weight: 900; color: #64748B; font-size: 20px;")
            
            if hasattr(self, 'right_panel'):
                self.right_panel.setStyleSheet("QFrame { background-color: #F8FAFC; border: none; border-top-right-radius: 28px; border-bottom-right-radius: 28px; }")
            
            if hasattr(self, 'kb_frame'):
                self.kb_frame.setStyleSheet("""
                    QFrame {
                        background-color: #F1F5F9;
                        border-radius: 20px;
                        border: 1px solid #E2E8F0;
                    }
                """)

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
                    shadow.setBlurRadius(28)
                    shadow.setColor(QColor(59, 130, 246, 60)) # Brillo azul iOS flotante
                    shadow.setOffset(0, 10) # Sombra más lejana para elevar el widget
                else:
                    shadow.setBlurRadius(16)
                    shadow.setColor(QColor(59, 130, 246, 20)) # Sombra suave base
                    shadow.setOffset(0, 5)
            
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
                theme = config.get("theme", "light")
                if is_active:
                    color = "#38BDF8" if theme == "dark" else "#1E3A8A"
                else:
                    color = "#94A3B8" if theme == "dark" else "#475569"
                lbl_text.setStyleSheet(f"font-size: 13px; font-weight: 900; color: {color}; background: transparent; border: none;")
        
        if key == "Mixto":
            from src.cajero.widgets.pagos_mixtos import DialogoPagosMixtos
            tasa = config.get("tasa_usd", 1200.0)
            dlg = DialogoPagosMixtos(self.total_final, tasa, self)
            if dlg.exec_():
                self.valores_mixtos = dlg.get_valores()
                self.current_metodo = "Mixto"
                self.lbl_input1.setText("MÚLTIPLES PAGOS ($):")
                self.lbl_input2.hide(); self.txt_otro.hide()
                self.lbl_cliente.hide(); self.cmb_cliente.hide()
                self.txt_pago.setText(f"{self.total_final:.2f}")
                self.txt_pago.setReadOnly(True)
                self.lbl_mp_status.hide()
                self.timer_mp.stop()
                
                # Si hay monto de tarjeta, mandarlo al Point antes de finalizar
                monto_tarjeta = self.valores_mixtos.get("tarjeta", 0.0)
                if monto_tarjeta > 0:
                    QTimer.singleShot(200, lambda: self.procesar_pago_mercadopago_point())
                else:
                    # Sin tarjeta, finalizar directo
                    QTimer.singleShot(200, lambda: self.finalizar(True))
            else:
                self.set_metodo("Efectivo")
            return
        elif key in ["Tarjeta", "Transferencia", "QR"]:
            self.lbl_input1.setText("PAGA CON ($):")
            self.lbl_input2.hide(); self.txt_otro.hide()
            self.lbl_cliente.hide(); self.cmb_cliente.hide()
            # Autocompletar monto para medios electrónicos (evita errores y agiliza)
            self.txt_pago.setText(f"{self.total_final:.2f}")
            
            if key == "Transferencia":
                self.lbl_mp_status.setText(f"📡 ESCUCHANDO MERCADO PAGO EN TIEMPO REAL... (${self.total_final:.2f})")
                theme = config.get("theme", "light")
                if theme == "dark":
                    self.lbl_mp_status.setStyleSheet("font-weight: bold; font-size: 13px; color: #38BDF8; background: #1E293B; padding: 10px; border-radius: 8px; border: 1px dashed #38BDF8;")
                else:
                    self.lbl_mp_status.setStyleSheet("font-weight: bold; font-size: 13px; color: #0284c7; background: #e0f2fe; padding: 10px; border-radius: 8px; border: 1px dashed #0284c7;")
                self.lbl_mp_status.show()
                self.timer_mp.start(1000)
            else:
                self.lbl_mp_status.hide()
                self.timer_mp.stop()
        elif key == "Fiado":
            self.lbl_input1.setText("MONTO A FIAR ($):")
            self.lbl_input2.hide(); self.txt_otro.hide()
            self.lbl_cliente.show(); self.cmb_cliente.show()
            self.txt_pago.setText(f"{self.total_final:.2f}")
            self.txt_pago.setReadOnly(True) # No puede fiar una parte y pagar el resto aquí, para mixto usar mixto
            self.lbl_mp_status.hide()
            self.timer_mp.stop()
        else:
            self.lbl_input1.setText("PAGA CON ($):")
            self.lbl_input2.hide(); self.txt_otro.hide()
            self.lbl_cliente.hide(); self.cmb_cliente.hide()
            self.txt_pago.setReadOnly(False)
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
            
            if self.current_metodo == "Mixto" and hasattr(self, 'valores_mixtos'):
                p1 = self.valores_mixtos.get("efectivo", 0) + (self.valores_mixtos.get("usd", 0) * config.get("tasa_usd", 1200.0))
                p2 = self.valores_mixtos.get("tarjeta", 0) + self.valores_mixtos.get("mercadopago", 0)
            else:
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
                        theme = config.get("theme", "light")
                        if theme == "dark":
                            self.lbl_mp_status.setStyleSheet("font-weight: 900; font-size: 13px; color: #4ADE80; background: #14532D; padding: 10px; border-radius: 8px; border: 1px solid #22C55E;")
                        else:
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

        if self.current_metodo == "Fiado":
            if self.cmb_cliente.count() == 0:
                QMessageBox.warning(self, "Error", "No hay clientes registrados para fiar.")
                return None
            cliente_id = self.cmb_cliente.currentData()
            c_index = self.cmb_cliente.currentIndex()
            # Fetch client to check limit
            c = self.lista_clientes[c_index]
            disp = float(c['limite_credito']) - float(c['deuda_actual'])
            p1_float = float(p1_t) if p1_t else 0
            if p1_float > disp:
                QMessageBox.critical(self, "Límite Excedido", f"El monto a fiar (${p1_float:,.2f}) excede el límite disponible del cliente (${disp:,.2f}).")
                return None

        try:
            if self.current_metodo == "Mixto" and hasattr(self, 'valores_mixtos'):
                p1 = self.valores_mixtos.get("efectivo", 0) + (self.valores_mixtos.get("usd", 0) * config.get("tasa_usd", 1200.0))
                p2 = self.valores_mixtos.get("tarjeta", 0) + self.valores_mixtos.get("mercadopago", 0)
            else:
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
        monto_desc = getattr(self, 'descuento_monto', 0.0)
        monto_rec = getattr(self, 'recargo_monto', 0.0)
        
        self.total_final = max(0.0, self.total_original - monto_desc + monto_rec)
        
        # El total de arriba sigue mostrando el original fijo
        self.lbl_total.setText(f"${self.total_original:,.2f}")
        
        # El neto destacado de abajo se actualiza en caliente
        self.lbl_neto.setText(f"NETO A PAGAR: ${self.total_final:,.2f}")
        
        # Actualizar visualización del botón de Descuento (Premium UX!)
        _btn_compact = "border-radius: 16px; font-weight: 900; font-size: 10px; border: none; padding: 2px 8px;"
        if getattr(self, 'descuento_monto', 0.0) > 0:
            self.btn_descuento.setText(f"F3\n-${self.descuento_monto:,.0f}")
            self.btn_descuento.setStyleSheet(f"background: #047857; color: white; {_btn_compact}")
        else:
            self.btn_descuento.setText("F3\ndescuento")
            self.btn_descuento.setStyleSheet(f"background: #10B981; color: white; {_btn_compact}")
            
        if getattr(self, 'recargo_monto', 0.0) > 0:
            self.btn_recargo.setText(f"F4\n+${self.recargo_monto:,.0f}")
            self.btn_recargo.setStyleSheet(f"background: #B45309; color: white; {_btn_compact}")
        else:
            self.btn_recargo.setText("F4\nrecargo")
            self.btn_recargo.setStyleSheet(f"background: #F59E0B; color: white; {_btn_compact}")
            
        # Si el método es electrónico, actualizar el autocompletado del pago de inmediato
        if self.current_metodo in ["Tarjeta", "Transferencia"]:
            self.txt_pago.setText(f"{self.total_final:.2f}")
            
        self.calcular_vuelto()

    def on_descuento_changed(self, text):
        try:
            txt = text.strip()
            if not txt:
                self.descuento_monto = 0.0
            elif txt.endswith('%'):
                val = float(txt[:-1])
                self.descuento_monto = self.total_original * (max(0, min(100, val)) / 100.0)
            else:
                val = float(txt.replace('$', '').strip())
                self.descuento_monto = max(0.0, val)
            self.recargar_total_final()
        except ValueError:
            pass

    def on_recargo_changed(self, text):
        try:
            txt = text.strip()
            if not txt:
                self.recargo_monto = 0.0
            elif txt.endswith('%'):
                val = float(txt[:-1])
                self.recargo_monto = self.total_original * (max(0, val) / 100.0)
            else:
                val = float(txt.replace('$', '').strip())
                self.recargo_monto = max(0.0, val)
            self.recargar_total_final()
        except ValueError:
            pass

    def abrir_descuento(self):
        self.txt_desc.setFocus()
        self.txt_desc.selectAll()

    def abrir_recargo(self):
        self.txt_rec.setFocus()
        self.txt_rec.selectAll()

    def finalizar_fiscal_efectivo(self):
        self.set_metodo("Efectivo")
        self.finalizar(True, force_fiscal=True)

    def finalizar(self, imprimir=True, force_fiscal=False):
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
            
            monto_desc = getattr(self, 'descuento_monto', 0.0)
            monto_rec = getattr(self, 'recargo_monto', 0.0)
            
            descuentaso_oferta = getattr(self, 'descuentaso_oferta', 0.0)
            descuento_total = monto_desc + descuentaso_oferta
            
            estado_venta = 'COMPLETADA'
            nombre_cliente_guardar = ''
            if getattr(self, 'nombre_pendiente', None):
                estado_venta = 'TRANSF_PENDIENTE'
                nombre_cliente_guardar = self.nombre_pendiente

            self.resultado_venta = {
                'total': self.total_final,
                'pago_con': p1 + p2,
                'cambio': (p1 + p2) - self.total_final,
                'pago_efectivo': pago_efectivo,
                'pago_otro': pago_otro,
                'usuario': config.current_user.get('username', 'cajero'),
                'usuario_secundario': CajeroActivo.nombre if CajeroActivo.numero == 2 else '',
                'metodo_pago': self.current_metodo,
                'estado': estado_venta,
                'cliente_nombre': nombre_cliente_guardar,
                'descuento': descuento_total,
                'recargo': monto_rec
            }
            
            id_v = db_manager.guardar_venta_completa(self.resultado_venta, self.items_carrito)
            if id_v:
                # Si fue fiado, actualizar la deuda y registrar en cuenta corriente
                if self.current_metodo == "Fiado" and self.cmb_cliente.count() > 0:
                    cliente_id = self.cmb_cliente.currentData()
                    c_index = self.cmb_cliente.currentIndex()
                    c = self.lista_clientes[c_index]
                    nueva_deuda = float(c['deuda_actual']) + self.total_final
                    
                    db_manager.execute_non_query(
                        "UPDATE clientes SET deuda_actual = ? WHERE id = ?",
                        (nueva_deuda, cliente_id)
                    )
                    db_manager.execute_non_query(
                        "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion, venta_id) VALUES (?, ?, ?, ?, ?, ?)",
                        (cliente_id, 'CARGO', self.total_final, nueva_deuda, f'Venta a crédito Ticket #{id_v}', id_v)
                    )
            
                from src.hardware.printer import printer_manager
                # Determinar si el cajón debe abrirse según el método y configuración
                debe_abrir = False
                if self.current_metodo == "Efectivo": debe_abrir = config.get("drawer_open_cash", True)
                elif self.current_metodo == "Mixto": debe_abrir = config.get("drawer_open_mixed", True)
                elif self.current_metodo == "Tarjeta": debe_abrir = config.get("drawer_open_card", False)
                elif self.current_metodo == "Transferencia": debe_abrir = config.get("drawer_open_transfer", False)
                elif self.current_metodo == "Fiado": debe_abrir = config.get("drawer_open_fiado", False)

                if debe_abrir:
                    drawer_manager.set_authorized(True)

                if imprimir:
                    # Imprimir ticket (internamente puede abrir el cajón si se le pide)
                    self.imprimir_ticket(id_v, abrir_manual=debe_abrir, force_fiscal=force_fiscal)
                elif debe_abrir:
                    # No imprimimos, pero abrimos el cajón para el efectivo
                    drawer_manager.abrir(autorizada=True)

                self.accept()
        except Exception as e:
            self._procesando_pago = False
            QMessageBox.critical(self, "Error", f"Fallo al cobrar: {e}")

    def imprimir_ticket(self, id_v, abrir_manual=False, force_fiscal=False):
        try:
            from src.hardware.printer import printer_manager
            from src.cajero.paso5_terminal import CajeroActivo
            
            monto_desc = getattr(self, 'descuento_monto', 0.0)
            monto_rec = getattr(self, 'recargo_monto', 0.0)
            
            descuentaso_oferta = getattr(self, 'descuentaso_oferta', 0.0)
            descuento_total = monto_desc + descuentaso_oferta
            
            # El ticket imprimirá y abrirá si abrir_manual es True
            printer_manager.imprimir_ticket_venta(
                id_v, self.items_carrito, self.total_final, 
                self.resultado_venta['pago_con'], self.resultado_venta['cambio'],
                abrir_cajon=abrir_manual, discount_amount=descuento_total, surcharge_amount=monto_rec,
                cajero=CajeroActivo.nombre, metodo_pago=self.resultado_venta.get('metodo_pago', 'Efectivo'),
                force_fiscal=force_fiscal
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
            elif event.type() == QEvent.FocusOut:
                # Si pierde el foco hacia algo que no sea un botón interno, no ocultar
                pass
                return False
            
            # Asegurarnos de que las teclas de función (F1-F12) se procesen siempre, aunque el cursor esté en el casillero
            if k == Qt.Key_F11:
                self.procesar_pago_mercadopago_point()
                return True
            elif k == Qt.Key_F12:
                self.verificar_transferencia_mp()
                return True
            elif k == Qt.Key_F1:
                self.finalizar(True)
                return True
        
        return super().eventFilter(watched, event)



    def procesar_pago_mercadopago_point(self):
        import requests
        from src.config import config
        from PyQt5.QtWidgets import QProgressDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton
        from PyQt5.QtCore import QTimer, Qt
        
        # Forzar recarga por si se editó el archivo externamente
        config._load_config()
        
        token = config.get("mp_access_token", "")
        device_id = config.get("mp_device_id", "")
        
        if not token or not device_id:
            QMessageBox.warning(self, "Configuración Faltante", "Falta el Access Token o el Device ID de Mercado Pago Point en la configuración.")
            return

        if self.current_metodo not in ["Tarjeta", "Mixto", "QR"]:
            self.set_metodo("Tarjeta")
            
        if self.current_metodo == "Mixto":
            if hasattr(self, 'widget_mixto'):
                self.valores_mixtos = self.widget_mixto.get_valores()
                monto = self.valores_mixtos.get("tarjeta", 0.0)
            else:
                monto = 0.0
        else:
            monto_str = self.txt_pago.text().replace("$", "").replace(" ", "").strip()
            try:
                from src.utils.parser import parse_float_regional
                monto = parse_float_regional(monto_str)
            except:
                monto = self.total_final

        if monto <= 0:
            msg = "El monto de Tarjeta (Point) en pago Mixto es cero." if self.current_metodo == "Mixto" else "Ingrese un monto a cobrar válido."
            QMessageBox.warning(self, "Monto inválido", msg)
            return

        # QR usa un flujo completamente distinto (orden QR en pantalla, no terminal)
        if self.current_metodo == "QR":
            self._procesar_cobro_qr_pantalla(token, monto)
            return

        url = f"https://api.mercadopago.com/point/integration-api/devices/{device_id}/payment-intents"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        import uuid
        intent_id = str(uuid.uuid4())
        
        # Mercado Pago requiere el monto en centavos para Argentina/Brasil
        monto_centavos = int(round(monto * 100))
        
        # Si el método es QR, forzamos que la terminal muestre su QR
        if self.current_metodo == "QR":
            payload = {
                "amount": monto_centavos,
                "payment_mode": "qr",
                "additional_info": {
                    "external_reference": intent_id,
                    "print_on_terminal": True
                }
            }
            msg_progreso = "Enviando monto a la Terminal Point (modo QR)..."
        else:
            payload = {
                "amount": monto_centavos,
                "additional_info": {
                    "external_reference": intent_id,
                    "print_on_terminal": True
                }
            }
            msg_progreso = "Enviando monto a la Terminal Point..."
        
        progreso = QProgressDialog(msg_progreso, "Cancelar", 0, 0, self)
        progreso.setWindowTitle("Mercado Pago Point")
        progreso.setWindowModality(Qt.WindowModal)
        progreso.show()
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            progreso.close()
            
            if response.status_code in [200, 201]:
                # Iniciar el Polling Dialog
                data = response.json()
                mp_intent_id = data.get("id")
                
                class MPPollingDialog(QDialog):
                    def __init__(self, parent, token, device_id, intent_id, monto_original, modo="Tarjeta"):
                        super().__init__(parent)
                        self.token = token
                        self.device_id = device_id
                        self.intent_id = intent_id
                        self.monto_original = monto_original
                        self.aprobado = False
                        
                        self.setWindowTitle("Esperando Pago...")
                        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint) # Sin botón de cerrar
                        self.setFixedSize(350, 150)
                        
                        layout = QVBoxLayout(self)
                        if modo == "QR":
                            msg_label = f"📱 Mostre el QR de la terminal al cliente.\nEsperando pago QR por:\n${monto_original:,.2f}"
                        else:
                            msg_label = f"💳 Por favor, pida al cliente que pase la tarjeta por:\n${monto_original:,.2f}"
                        self.lbl_status = QLabel(msg_label)
                        self.lbl_status.setAlignment(Qt.AlignCenter)
                        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold;")
                        layout.addWidget(self.lbl_status)
                        
                        self.btn_cancel = QPushButton("Cancelar Cobro en la Terminal")
                        self.btn_cancel.setStyleSheet("background-color: #EF4444; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
                        self.btn_cancel.clicked.connect(self.cancelar_cobro)
                        layout.addWidget(self.btn_cancel)
                        
                        self.timer = QTimer(self)
                        self.timer.timeout.connect(self.check_status)
                        self.timer.start(2500) # Cada 2.5 segundos
                        
                    def check_status(self):
                        poll_url = f"https://api.mercadopago.com/point/integration-api/payment-intents/{self.intent_id}"
                        head = {"Authorization": f"Bearer {self.token}"}
                        try:
                            res = requests.get(poll_url, headers=head, timeout=5)
                            if res.status_code == 200:
                                state = res.json().get("state")
                                if state == "FINISHED":
                                    self.timer.stop()
                                    self.aprobado = True
                                    self.accept()
                                elif state in ["CANCELED", "ERROR"]:
                                    self.timer.stop()
                                    QMessageBox.warning(self, "Cobro Cancelado", f"El cobro fue cancelado o rechazado en la terminal (Estado: {state}).")
                                    self.reject()
                        except:
                            pass # Ignorar errores de red temporales
                            
                    def cancelar_cobro(self):
                        self.btn_cancel.setEnabled(False)
                        self.btn_cancel.setText("Cancelando...")
                        self.timer.stop()
                        
                        # Send DELETE to cancel intent on device
                        cancel_url = f"https://api.mercadopago.com/point/integration-api/devices/{self.device_id}/payment-intents/{self.intent_id}"
                        head = {"Authorization": f"Bearer {self.token}"}
                        try:
                            requests.delete(cancel_url, headers=head, timeout=5)
                        except:
                            pass
                        
                        self.reject()
                        
                # Mostrar el diálogo
                dialog = MPPollingDialog(self, token, device_id, mp_intent_id, monto, modo=self.current_metodo)
                if dialog.exec_() == QDialog.Accepted:
                    # El pago fue exitoso y FINALIZADO
                    self.txt_pago.setText(str(monto))
                    self.finalizar(True)
            else:
                try:
                    err_data = response.json()
                    msg = err_data.get("message", "Error desconocido")
                except:
                    msg = response.text
                QMessageBox.critical(self, "Error MP", f"No se pudo enviar el monto a la terminal:\n{msg}")
        except Exception as e:
            progreso.close()
            QMessageBox.critical(self, "Error de Conexión", f"Error de conexión con Mercado Pago:\n{e}")

    def _procesar_cobro_qr_pantalla(self, token, monto):
        """Genera un QR dinámico en pantalla para que el cliente escanee con su celular."""
        import requests
        import uuid
        import qrcode
        import io
        from src.config import config
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
        from PyQt5.QtGui import QPixmap, QImage
        from PyQt5.QtCore import QTimer, Qt

        # Datos de la cuenta MP
        user_id = 171085024
        external_pos_id = config.get("mp_qr_pos_external_id", "default")
        
        headers_mp = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        ref = str(uuid.uuid4())
        payload = {
            "external_reference": ref,
            "title": "Venta en caja",
            "description": "Cobro QR",
            "total_amount": monto,
            "items": [
                {
                    "sku_number": "001",
                    "category": "others",
                    "title": "Venta",
                    "description": "Cobro en caja",
                    "unit_price": monto,
                    "quantity": 1,
                    "unit_measure": "unit",
                    "total_amount": monto
                }
            ],
            "cash_out": {"amount": 0}
        }

        url = f"https://api.mercadopago.com/instore/orders/qr/seller/collectors/{user_id}/pos/{external_pos_id}/qrs"

        try:
            resp = requests.put(url, json=payload, headers=headers_mp, timeout=10)
        except Exception as e:
            QMessageBox.critical(self, "Error de Conexion", f"No se pudo crear la orden QR:\n{e}")
            return

        if resp.status_code not in [200, 201]:
            # Interpretar el error de MP para dar un mensaje claro al usuario
            try:
                err_data = resp.json()
                err_code = err_data.get("code", "")
                err_msg  = err_data.get("message", "")
            except Exception:
                err_code = ""
                err_msg  = resp.text

            if resp.status_code == 403 or "UNAUTHORIZED" in err_code:
                msg_usuario = (
                    "\u26a0\ufe0f  Tu token NO tiene permiso para crear \u00f3rdenes QR (Error 403).\n\n"
                    "Caus as m\u00e1s comunes:\n"
                    "  1\u25e6 El token es de PRUEBA (TEST-...) pero la cuenta es Productiva.\n"
                    "  2\u25e6 El cajero QR no fue creado en el panel de Mercado Pago.\n"
                    "  3\u25e6 El 'external_pos_id' no coincide con el POS registrado.\n\n"
                    "\u2705  Soluci\u00f3n paso a paso:\n"
                    "  1. Ing res\u00e1 a mercadopago.com/developers\n"
                    "  2. Cre\u00e1 una aplicaci\u00f3n con permiso 'QR Code'\n"
                    "  3. En 'Credenciales de Producci\u00f3n' copi\u00e1 el Access Token\n"
                    "  4. En 'Puntos de venta' cre\u00e1 un cajero y cop i\u00e1 el 'external_id'\n"
                    "  5. Peg\u00e1 ambos datos en Admin \u2192 Configuraci\u00f3n \u2192 Mercado Pago"
                )
            elif resp.status_code == 401:
                msg_usuario = (
                    "\u274c  Token inv\u00e1lido o expirado (Error 401).\n\n"
                    "Actualiz\u00e1 el Access Token en Admin \u2192 Configuraci\u00f3n \u2192 Mercado Pago."
                )
            elif resp.status_code == 404:
                msg_usuario = (
                    "\u274c  El POS no fue encontrado (Error 404).\n\n"
                    "El 'external_pos_id' configurado no existe en tu cuenta de MP.\n"
                    "Verific\u00e1 el ID en mercadopago.com \u2192 Tu negocio \u2192 Puntos de venta."
                )
            else:
                msg_usuario = (
                    f"Error al crear la orden QR (HTTP {resp.status_code}).\n\n"
                    f"C\u00f3digo: {err_code}\n"
                    f"Detalle: {err_msg}"
                )

            QMessageBox.critical(self, "\u26a0\ufe0f  Error Mercado Pago QR", msg_usuario)
            return

        data = resp.json()
        qr_data = data.get("qr_data", "")

        if not qr_data:
            QMessageBox.critical(self, "Error MP", "Mercado Pago no devolvio datos de QR.")
            return

        # Generar imagen QR en memoria
        qr_img = qrcode.make(qr_data)
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG")
        buf.seek(0)
        qimage = QImage()
        qimage.loadFromData(buf.read())
        pixmap = QPixmap.fromImage(qimage)

        # Dialogo con QR grande
        parent_ref = self

        class QRDialog(QDialog):
            def __init__(self, parent):
                super().__init__(parent)
                self.pagado = False
                self.setWindowTitle("Cobro QR - Mercado Pago")
                self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
                self.setFixedSize(420, 520)
                self.setStyleSheet("background-color: #0F172A; border-radius: 16px;")

                lay = QVBoxLayout(self)
                lay.setSpacing(10)

                lbl_titulo = QLabel("Que el cliente escanee con\nla app de Mercado Pago")
                lbl_titulo.setAlignment(Qt.AlignCenter)
                lbl_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #38BDF8; padding: 8px; border: none;")
                lay.addWidget(lbl_titulo)

                lbl_qr = QLabel()
                lbl_qr.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                lbl_qr.setAlignment(Qt.AlignCenter)
                lbl_qr.setStyleSheet("background: white; border-radius: 12px; padding: 10px;")
                lay.addWidget(lbl_qr)

                lbl_monto = QLabel(f"${monto:,.2f}")
                lbl_monto.setAlignment(Qt.AlignCenter)
                lbl_monto.setStyleSheet("font-size: 32px; font-weight: 900; color: #10B981; border: none;")
                lay.addWidget(lbl_monto)

                self.lbl_estado = QLabel("Esperando pago...")
                self.lbl_estado.setAlignment(Qt.AlignCenter)
                self.lbl_estado.setStyleSheet("font-size: 12px; color: #94A3B8; border: none;")
                lay.addWidget(self.lbl_estado)

                btn_cancelar = QPushButton("Cancelar")
                btn_cancelar.setStyleSheet("background-color: #EF4444; color: white; padding: 10px; font-weight: bold; border-radius: 8px; font-size: 13px; border: none;")
                btn_cancelar.clicked.connect(self.cancelar)
                lay.addWidget(btn_cancelar)

                # Polling cada 3 segundos buscando el pago
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.buscar_pago)
                self.timer.start(3000)

            def buscar_pago(self):
                import datetime
                try:
                    now = datetime.datetime.utcnow()
                    begin = (now - datetime.timedelta(minutes=5)).isoformat() + "Z"
                    end = now.isoformat() + "Z"
                    search_url = f"https://api.mercadopago.com/v1/payments/search?sort=date_created&criteria=desc&limit=10&status=approved&external_reference={ref}&range=date_created&begin_date={begin}&end_date={end}"
                    head = {"Authorization": f"Bearer {token}"}
                    r = requests.get(search_url, headers=head, timeout=5)
                    if r.status_code == 200:
                        results = r.json().get("results", [])
                        if results:
                            self.timer.stop()
                            self.pagado = True
                            self.lbl_estado.setText("PAGO APROBADO!")
                            self.lbl_estado.setStyleSheet("font-size: 14px; color: #10B981; font-weight: bold; border: none;")
                            QTimer.singleShot(1000, self.accept)
                except:
                    pass

            def cancelar(self):
                self.timer.stop()
                # Borrar la orden QR
                try:
                    del_url = f"https://api.mercadopago.com/instore/orders/qr/seller/collectors/{user_id}/pos/{external_pos_id}/qrs"
                    requests.delete(del_url, headers=headers_mp, timeout=5)
                except:
                    pass
                self.reject()

        dlg = QRDialog(self)
        if dlg.exec_() == QDialog.Accepted and dlg.pagado:
            self.txt_pago.setText(str(monto))
            self.finalizar(True)

    def verificar_transferencia_mp(self):
        import requests
        from src.config import config
        from PyQt5.QtWidgets import QProgressDialog, QMessageBox
        import datetime
        from src.database.db_manager import db_manager

        token = config.get("mp_access_token", "")
        if not token:
            QMessageBox.warning(self, "Configuración Faltante", "Falta el Access Token de Mercado Pago en la configuración.")
            return
            
        monto_str = self.txt_pago.text().replace("$", "").replace(" ", "").strip()
        try:
            from src.utils.parser import parse_float_regional
            monto = parse_float_regional(monto_str)
        except:
            monto = self.total_final
            
        if self.current_metodo == "Mixto" and hasattr(self, 'widget_mixto'):
            # En mixto, usamos el valor del campo Transferencia (cuyo key original era mercadopago)
            monto = self.widget_mixto.get_valores().get("mercadopago", 0.0)
            
        if monto <= 0:
            msg = "El monto a verificar es cero. Asegúrese de haber ingresado un monto válido en Transf./QR."
            QMessageBox.warning(self, "Monto inválido", msg)
            return

        progreso = QProgressDialog("Buscando transferencias y QR recientes en Mercado Pago...", "Cancelar", 0, 0, self)
        progreso.setWindowTitle("Verificando Pagos MP")
        progreso.setWindowModality(Qt.WindowModal)
        progreso.show()

        try:
            # Buscar pagos de las últimas 2 horas
            now = datetime.datetime.utcnow()
            begin_date = (now - datetime.timedelta(hours=2)).isoformat() + "Z"
            end_date = now.isoformat() + "Z"
            
            url = f"https://api.mercadopago.com/v1/payments/search?sort=date_created&criteria=desc&limit=50&status=approved&range=date_created&begin_date={begin_date}&end_date={end_date}"
            headers = {"Authorization": f"Bearer {token}"}
            
            resp = requests.get(url, headers=headers, timeout=15)
            progreso.close()
            
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                
                transferencia_encontrada = None
                
                for p in results:
                    p_amount = p.get("transaction_amount")
                    p_id = str(p.get("id"))
                    
                    # Verificamos si el monto coincide
                    if p_amount == monto:
                        # Verificamos que no haya sido usada antes
                        existe = db_manager.execute_query("SELECT id FROM mp_transferencias_usadas WHERE payment_id = ?", (p_id,))
                        if not existe:
                            transferencia_encontrada = p
                            break
                            
                if transferencia_encontrada:
                    p_id = str(transferencia_encontrada.get("id"))
                    payer = transferencia_encontrada.get("payer", {})
                    payer_info = payer.get("first_name", "") + " " + payer.get("last_name", "")
                    if not payer_info.strip():
                        payer_info = payer.get("email", "Desconocido")
                        
                    reply = QMessageBox.question(
                        self, "Pago Encontrado", 
                        f"Se encontró un pago/transferencia reciente por ${monto:,.2f}.\n\n"
                        f"Origen: {payer_info.strip()}\n"
                        f"ID: {p_id}\n\n"
                        f"¿Confirmar y asociar este pago a la venta actual?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        # Guardar el ID para que no se re-utilice
                        try:
                            db_manager.execute_non_query("INSERT INTO mp_transferencias_usadas (payment_id) VALUES (?)", (p_id,))
                        except:
                            pass # Si ya estaba, fallará silenciosamente
                            
                        # Finalizar venta
                        QMessageBox.information(self, "Cobro Aprobado", "Pago validado correctamente. Emitiendo ticket...")
                        self.txt_pago.setText(str(monto))
                        self.finalizar(True)
                else:
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("No Encontrada")
                    msg_box.setText(f"No se encontró ninguna transferencia o código QR reciente, nueva y no utilizada por el monto exacto de ${monto:,.2f}.")
                    msg_box.setInformativeText("Si confías en este cliente y quieres dejar el cobro en espera de que llegue la transferencia, presiona 'Forzar Pendiente'.")
                    msg_box.setIcon(QMessageBox.Warning)
                    
                    btn_ok = msg_box.addButton("Aceptar", QMessageBox.AcceptRole)
                    btn_forzar = msg_box.addButton("Forzar Pendiente", QMessageBox.ActionRole)
                    
                    msg_box.exec_()
                    
                    if msg_box.clickedButton() == btn_forzar:
                        from PyQt5.QtWidgets import QInputDialog
                        nombre, ok = QInputDialog.getText(self, "Cobro Pendiente", "Ingrese el nombre del cliente para buscarlo luego:")
                        if ok and nombre.strip():
                            self.nombre_pendiente = nombre.strip()
                            self.txt_pago.setText(str(monto))
                            self.finalizar(True)
            else:
                QMessageBox.critical(self, "Error MP", f"No se pudieron buscar las transferencias:\n{resp.text}")
        except Exception as e:
            progreso.close()
            QMessageBox.critical(self, "Error de Conexión", f"Error de conexión con Mercado Pago:\n{e}")

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
        elif k == Qt.Key_F10: self.finalizar_fiscal_efectivo()
        elif k == Qt.Key_F11: self.procesar_pago_mercadopago_point()
        elif k == Qt.Key_F12: self.verificar_transferencia_mp()
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

    def build_teclado_propio(self, right_lay):
        theme = config.get("theme", "light")
        self.kb_frame = QFrame()
        self.kb_frame.setObjectName("KeyboardFrame")
        if theme == "dark":
            self.kb_frame.setStyleSheet("""
                QFrame#KeyboardFrame {
                    background-color: #1E293B;
                    border: 1px solid #334155;
                    border-radius: 24px;
                }
            """)
        else:
            self.kb_frame.setStyleSheet("""
                QFrame#KeyboardFrame {
                    background-color: #F1F5F9;
                    border: none;
                    border-radius: 24px;
                }
            """)
        self.kb_frame.setMinimumHeight(330)
        self.kb_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        kb_layout = QVBoxLayout(self.kb_frame)
        kb_layout.setContentsMargins(10, 10, 10, 10)
        kb_layout.setSpacing(5)
        
        rows = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            [",", "0", "⌫"],
            ["ESC", "ENTER"]
        ]
        
        # Mapeo de teclas de caracteres comunes
        self.teclado_key_map = {
            '0': Qt.Key_0, '1': Qt.Key_1, '2': Qt.Key_2, '3': Qt.Key_3, '4': Qt.Key_4,
            '5': Qt.Key_5, '6': Qt.Key_6, '7': Qt.Key_7, '8': Qt.Key_8, '9': Qt.Key_9,
            ',': Qt.Key_Comma
        }
        
        if theme == "dark":
            btn_style = """
                QPushButton {
                    background-color: #334155;
                    color: #F8FAFC;
                    font-size: 16px;
                    font-weight: 800;
                    font-family: 'Segoe UI', sans-serif;
                    border: none;
                    border-radius: 14px;
                    min-width: 48px;
                    min-height: 48px;
                }
                QPushButton:hover {
                    background-color: #475569;
                }
            """
            bg_backspace = "#7F1D1D"
            color_backspace = "#FCA5A5"
            bg_esc = "#334155"
            color_esc = "#94A3B8"
        else:
            btn_style = """
                QPushButton {
                    background-color: #FFFFFF;
                    color: #1E293B;
                    font-size: 16px;
                    font-weight: 800;
                    font-family: 'Segoe UI', sans-serif;
                    border: none;
                    border-radius: 14px;
                    min-width: 48px;
                    min-height: 48px;
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                }
            """
            bg_backspace = "#FEE2E2"
            color_backspace = "#EF4444"
            bg_esc = "#F3F4F6"
            color_esc = "#475569"
        
        for row in rows:
            row_lay = QHBoxLayout()
            row_lay.setSpacing(5)
            row_lay.setContentsMargins(0, 0, 0, 0)
            
            for key in row:
                btn = QPushButton(key)
                btn.setStyleSheet(btn_style)
                btn.setFocusPolicy(Qt.NoFocus)
                btn.setCursor(Qt.PointingHandCursor)
                
                # Estilos específicos para teclas especiales
                if key == "⌫":
                    btn.setStyleSheet(btn_style + f"QPushButton {{ background-color: {bg_backspace}; color: {color_backspace}; }}")
                elif key == "ESC":
                    btn.setStyleSheet(btn_style + f"QPushButton {{ background-color: {bg_esc}; color: {color_esc}; }}")
                elif key == "ENTER":
                    btn.setStyleSheet(btn_style + "QPushButton { background-color: #3B82F6; color: white; }")
                
                btn.clicked.connect(lambda checked, k=key: self.on_teclado_key_clicked(k))
                row_lay.addWidget(btn, 1)
                
            kb_layout.addLayout(row_lay)
            
        right_lay.addWidget(self.kb_frame)
 
    def on_teclado_key_clicked(self, key):
        focused = self.focusWidget()
        if not focused or not isinstance(focused, QLineEdit):
            focused = self.txt_pago
            
        if key == "⌫":
            event_press = QKeyEvent(QEvent.KeyPress, Qt.Key_Backspace, Qt.NoModifier, "")
            QApplication.sendEvent(focused, event_press)
            event_release = QKeyEvent(QEvent.KeyRelease, Qt.Key_Backspace, Qt.NoModifier, "")
            QApplication.sendEvent(focused, event_release)
        elif key == "ENTER":
            event_press = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier, "\n")
            QApplication.sendEvent(focused, event_press)
            event_release = QKeyEvent(QEvent.KeyRelease, Qt.Key_Return, Qt.NoModifier, "\n")
            QApplication.sendEvent(focused, event_release)
        elif key == "ESC":
            self.reject()
        else:
            key_code = self.teclado_key_map.get(key, Qt.Key_unknown)
            event_press = QKeyEvent(QEvent.KeyPress, key_code, Qt.NoModifier, key)
            QApplication.sendEvent(focused, event_press)
            event_release = QKeyEvent(QEvent.KeyRelease, key_code, Qt.NoModifier, key)
            QApplication.sendEvent(focused, event_release)
