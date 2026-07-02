from src.utils.qt_compat import qt_exec
import hashlib
import os
from PIL import Image, ImageChops
from PyQt6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame, QGridLayout,
    QWidget, QApplication, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QKeyEvent
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

from src.cajero.paso6_cobro.componentes_paso6_cobro.teclado_numerico_lateral import TecladoNumericoLateral
from src.cajero.paso6_cobro.componentes_paso6_cobro.selector_metodo_pago import SelectorMetodoPago
from src.cajero.paso6_cobro.componentes_paso6_cobro.resumen_vuelto import ResumenVuelto
from src.cajero.paso6_cobro.componentes_paso6_cobro.logica.cobro_controller import CobroController

from src.cajero.paso6_cobro.componentes_paso6_cobro.generador_iconos import ensure_icons

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
        self._fondo_blur_pixmap = None   # fondo desenfocado capturado
        self.setup_ui()
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state("paso6")
        except:
            pass
        self.apply_glow()

    def showEvent(self, event):
        super().showEvent(event)
        # Capturar y desenfocar el fondo del padre al mostrarse
        QTimer.singleShot(0, self._capturar_fondo_blur)

    def _capturar_fondo_blur(self):
        """Captura la pantalla detrás del diálogo y aplica blur con PIL."""
        try:
            parent = self.parent()
            if parent is None:
                return

            # Capturar el widget padre como pixmap
            src = parent.grab()

            # Convertir QPixmap → PIL Image
            img_bytes = src.toImage()
            img_bytes = img_bytes.convertToFormat(
                img_bytes.Format.Format_RGBA8888
            )
            ptr = img_bytes.bits()
            ptr.setsize(img_bytes.sizeInBytes())
            from PIL import Image, ImageFilter
            import numpy as np
            arr = np.frombuffer(ptr, dtype=np.uint8).reshape(
                (img_bytes.height(), img_bytes.width(), 4)
            )
            pil_img = Image.fromarray(arr, 'RGBA')

            # Escalar al tamaño del diálogo, aplicar blur fuerte
            pil_img = pil_img.resize(
                (self.width(), self.height()), Image.LANCZOS
            )
            pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=22))

            # Oscurecer ligeramente (overlay semitransparente)
            from PIL import ImageDraw
            overlay = Image.new('RGBA', pil_img.size, (10, 15, 40, 140))
            pil_img = Image.alpha_composite(pil_img, overlay)

            # Convertir PIL → QPixmap
            from PyQt6.QtGui import QImage
            raw = pil_img.tobytes('raw', 'RGBA')
            qimg = QImage(
                raw, pil_img.width, pil_img.height,
                QImage.Format.Format_RGBA8888
            )
            self._fondo_blur_pixmap = QPixmap.fromImage(qimg)
            self.update()   # forzar repaint
        except Exception as e:
            import logging
            logging.debug(f"[Paso6] blur fondo: {e}")

    def paintEvent(self, event):
        """Dibuja el fondo desenfocado si está disponible."""
        if self._fondo_blur_pixmap:
            from PyQt6.QtGui import QPainter
            painter = QPainter(self)
            painter.drawPixmap(self.rect(), self._fondo_blur_pixmap)
            painter.end()
        else:
            super().paintEvent(event)


    def apply_glow(self):
        # Se elimina QGraphicsDropShadowEffect para rendimiento.
        pass

    def apply_theme(self):
        theme = config.get("theme", "light")
        self.main_frame.setObjectName("Paso6Main")
        self.main_frame.setProperty("theme", theme)
        self.main_frame.style().unpolish(self.main_frame)
        self.main_frame.style().polish(self.main_frame)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        # Envolvemos el layout principal en un QFrame base para heredar propiedades QSS
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("Paso6Main")
        layout.addWidget(self.main_frame)
        
        main_lay = QHBoxLayout(self.main_frame)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # --- SECCIÓN IZQUIERDA: PAGO (75%) ---
        left_panel = QWidget()
        left_panel.setObjectName("LeftPanelCobro")
        left_lay = QVBoxLayout(left_panel)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)

        # HEADER AZUL "COBRAR" (Estilo transparente premium)
        self.header = QLabel("COBRO")
        self.header.setObjectName("CobroHeader")
        self.header.setFixedHeight(64)
        left_lay.addWidget(self.header)

        # CONTENIDO IZQUIERDO
        content_lay = QVBoxLayout()
        content_lay.setContentsMargins(40, 20, 40, 20)
        content_lay.setSpacing(20)

        self.lbl_total = QLabel(f"$ {self.total_original:,.2f}") # Fijo en el monto original
        self.lbl_total.setObjectName("CobroTotal")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_lay.addWidget(self.lbl_total)

        # Cargar lista de clientes para fiado
        self.lista_clientes = db_manager.execute_query("SELECT id, nombre, limite_credito, deuda_actual FROM clientes ORDER BY nombre ASC")

        # Métodos de Pago
        self.selector_metodos = SelectorMetodoPago(self)
        self.selector_metodos.metodo_seleccionado.connect(self.procesar_click_metodo)
        self.btns = self.selector_metodos.get_botones()
        content_lay.addWidget(self.selector_metodos)
        content_lay.addSpacing(20)

        # Inputs de Pago
        grid_inputs = QGridLayout()
        grid_inputs.setSpacing(15)
        grid_inputs.setColumnStretch(0, 1)
        grid_inputs.setColumnStretch(1, 2)

        self.lbl_input1 = QLabel("Monto Recibido:")
        self.lbl_input1.setObjectName("InputLabel")
        grid_inputs.addWidget(self.lbl_input1, 0, 0)
        
        self.txt_pago = QLineEdit("")
        self.txt_pago.setObjectName("InputPago")
        self.txt_pago.setPlaceholderText("$ 0.00")
        self.txt_pago.textChanged.connect(self.calcular_vuelto)
        self.txt_pago.returnPressed.connect(self.intentar_finalizar)
        self.txt_pago.installEventFilter(self)
        grid_inputs.addWidget(self.txt_pago, 0, 1)
        
        self.lbl_input2 = QLabel("Otro Medio:")
        self.lbl_input2.setObjectName("InputLabel")
        grid_inputs.addWidget(self.lbl_input2, 1, 0)
        
        self.txt_otro = QLineEdit("0.00")
        self.txt_otro.setObjectName("InputPago")
        self.txt_otro.textChanged.connect(self.calcular_vuelto)
        self.txt_otro.returnPressed.connect(self.intentar_finalizar)
        self.txt_otro.installEventFilter(self)
        grid_inputs.addWidget(self.txt_otro, 1, 1)
        self.lbl_input2.hide(); self.txt_otro.hide()

        from PyQt6.QtWidgets import QComboBox
        self.lbl_cliente = QLabel("CLIENTE:")
        self.lbl_cliente.setObjectName("InputLabel")
        self.cmb_cliente = QComboBox()
        self.cmb_cliente.setObjectName("CmbClienteCobro")
        for c in self.lista_clientes:
            disp = float(c['limite_credito']) - float(c['deuda_actual'])
            self.cmb_cliente.addItem(f"{c['nombre']} (Disp: ${disp:,.2f})", c['id'])
            
        self.lbl_cliente.hide()
        self.cmb_cliente.hide()

        grid_inputs.addWidget(self.lbl_cliente, 2, 0)
        grid_inputs.addWidget(self.cmb_cliente, 2, 1)
        content_lay.addLayout(grid_inputs)
        
        # NUEVA LÍNEA HORIZONTAL DE MODIFICADORES COMPACTA
        grid_desc_rec = QGridLayout()
        
        self.lbl_desc = QLabel("Descuento ($):")
        self.lbl_desc.setObjectName("InputLabel")
        grid_desc_rec.addWidget(self.lbl_desc, 0, 0)
        
        self.txt_desc = QLineEdit("")
        self.txt_desc.setObjectName("InputDesc")
        self.txt_desc.setPlaceholderText("0.00")
        self.txt_desc.textChanged.connect(self.on_descuento_changed)
        self.txt_desc.installEventFilter(self)
        grid_desc_rec.addWidget(self.txt_desc, 0, 1)

        self.lbl_rec = QLabel("Recargo ($):")
        self.lbl_rec.setObjectName("InputLabel")
        grid_desc_rec.addWidget(self.lbl_rec, 0, 2)
        
        self.txt_rec = QLineEdit("")
        self.txt_rec.setObjectName("InputRec")
        self.txt_rec.setPlaceholderText("0.00")
        self.txt_rec.textChanged.connect(self.on_recargo_changed)
        self.txt_rec.installEventFilter(self)
        grid_desc_rec.addWidget(self.txt_rec, 0, 3)
        
        content_lay.addSpacing(10)
        content_lay.addLayout(grid_desc_rec)
        
        # NUEVO: Neto a cobrar destacado abajo
        self.lbl_neto = QLabel(f"NETO: $ {self.total_final:,.2f}")
        self.lbl_neto.setObjectName("NetoLabel")
        self.lbl_neto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_lay.addWidget(self.lbl_neto)

        # Vuelto (Extraído modularmente)
        self.resumen_vuelto = ResumenVuelto(self)
        content_lay.addWidget(self.resumen_vuelto)

        # Barra de Estado Mercado Pago
        self.lbl_mp_status = QLabel("")
        self.lbl_mp_status.setObjectName("LblMpStatus")
        self.lbl_mp_status.setProperty("estado", "info")
        self.lbl_mp_status.style().unpolish(self.lbl_mp_status)
        self.lbl_mp_status.style().polish(self.lbl_mp_status)
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
        right_panel.setObjectName("RightPanel")
        self.right_panel = right_panel
        right_panel.setMinimumWidth(400)
        right_lay = QVBoxLayout(right_panel)
        right_lay.setContentsMargins(12, 24, 12, 24)
        right_lay.setSpacing(6)
        
        def create_action_btn(fn_key, subtitle, callback, style="default"):
            btn = QPushButton(f"{fn_key}\n{subtitle}")
            btn.setFixedHeight(40)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setProperty("action_type", style)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(callback)
            return btn

        actions_grid = QGridLayout()
        actions_grid.setSpacing(6)
        actions_grid.setContentsMargins(0, 0, 0, 0)
        actions_grid.setColumnStretch(0, 1)
        actions_grid.setColumnStretch(1, 1)

        actions_grid.addWidget(create_action_btn("F1", "imprime", lambda: self.finalizar(True), style="primary"), 0, 0)
        self.btn_f2 = create_action_btn("F2", "s/imprime", lambda: self.finalizar(False), style="featured")
        actions_grid.addWidget(self.btn_f2, 0, 1)

        self.btn_descuento = create_action_btn("F3", "descuento", self.abrir_descuento, style="green")
        self.btn_recargo = create_action_btn("F4", "recargo", self.abrir_recargo, style="orange")
        actions_grid.addWidget(self.btn_descuento, 1, 0)
        actions_grid.addWidget(self.btn_recargo, 1, 1)

        self.btn_f11 = create_action_btn("F11", "Point MP", lambda: self.procesar_pago_mercadopago_point(), style="mp")
        self.btn_f12 = create_action_btn("F12", "Verif QR", lambda: self.verificar_transferencia_mp(), style="qr")
        actions_grid.addWidget(self.btn_f11, 2, 0)
        actions_grid.addWidget(self.btn_f12, 2, 1)

        right_lay.addLayout(actions_grid)

        btn_f10 = create_action_btn("F10", "AFIP", lambda: self.finalizar_fiscal_efectivo())
        btn_f10.hide()
        right_lay.addWidget(btn_f10)
        
        # Teclado numérico extraído modularmente
        self.teclado_lateral = TecladoNumericoLateral(self)
        self.teclado_lateral.key_clicked.connect(self.on_teclado_key_clicked)
        right_lay.addWidget(self.teclado_lateral)

        main_lay.addWidget(right_panel, 6)
        self.apply_theme()

        # Aplicar método inicial después de crear todos los widgets
        self.set_metodo("Efectivo")
        self.recargar_total_final()

        # Foco inicial en la casilla de pago para comenzar a escribir directamente
        self.txt_pago.setFocus()

    def procesar_click_metodo(self, key):
        if key == "Fiado":
            self._activar_fiado()
        else:
            self.set_metodo(key)

    def apply_theme(self):
        theme = config.get("theme", "light")
        self.main_frame.setProperty("theme", theme)
        self.main_frame.style().unpolish(self.main_frame)
        self.main_frame.style().polish(self.main_frame)
        
        # La actualización de color "Vuelto" estático ahora se maneja en estilos.qss mediante QFrame#Paso6Main[theme="..."] QLabel#LblVueltoTit
        self.resumen_vuelto.lbl_vuelto_tit.setObjectName("LblVueltoTit")

    def set_metodo(self, key):
        metodo_previo = self.current_metodo
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
            
            # Se elimina la lógica de sombra dinámica (QGraphicsDropShadowEffect) por rendimiento.
            
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
                lbl_text.setProperty("type", "metodo_lbl")
                lbl_text.setProperty("active", "true" if is_active else "false")
                lbl_text.style().unpolish(lbl_text)
                lbl_text.style().polish(lbl_text)
        
        if key == "Mixto":
            from src.cajero.paso6_cobro.widgets.pagos_mixtos import DialogoPagosMixtos
            tasa = config.get("tasa_usd", 1200.0)
            dlg = DialogoPagosMixtos(self.total_final, tasa, self)
            if qt_exec(dlg):
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
                    self.lbl_mp_status.setProperty("estado", "waiting")
                    self.lbl_mp_status.style().unpolish(self.lbl_mp_status)
                    self.lbl_mp_status.style().polish(self.lbl_mp_status)
                else:
                    self.lbl_mp_status.setProperty("estado", "waiting")
                    self.lbl_mp_status.style().unpolish(self.lbl_mp_status)
                    self.lbl_mp_status.style().polish(self.lbl_mp_status)
                self.lbl_mp_status.show()
                self.timer_mp.start(1000)
            else:
                self.lbl_mp_status.hide()
                self.timer_mp.stop()
        elif key == "Fiado":
            if metodo_previo != "Fiado":
                self._revertir_tras_fiado = metodo_previo
            self.lbl_input1.setText("MONTO A FIAR ($):")
            self.lbl_input2.hide()
            self.txt_otro.hide()
            self.lbl_cliente.hide()
            self.cmb_cliente.hide()
            self.txt_pago.setText(f"{self.total_final:.2f}")
            self.txt_pago.setReadOnly(True)
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
        self.txt_pago.setFocus()
        self.txt_pago.selectAll()

    def _activar_fiado(self):
        """Clic en tarjeta Fiado → resalta y abre Fiado Express."""
        rev = self.current_metodo if self.current_metodo != "Fiado" else "Efectivo"
        self.set_metodo("Fiado")
        self._abrir_fiado_express(rev)

    def _abrir_fiado_express(self, revertir_a="Efectivo"):
        """Fiado Express en 2 ventanas: paso1 sobre cobro → oculta paso6 → confirmación en mostrador."""
        from PyQt6.QtWidgets import QDialog
        from src.cajero.paso6_cobro.widgets.fiado_express import (
            DialogoFiadoExpressPaso1,
            DialogoFiadoExpressConfirmacion,
        )

        rev = revertir_a if revertir_a != "Fiado" else getattr(self, "_revertir_tras_fiado", "Efectivo")
        terminal = self.parent()
        self._fiado_flujo_activo = True

        cliente_ok = None
        dni_ref = ""

        while True:
            dlg1 = DialogoFiadoExpressPaso1(self.total_final, self)
            if qt_exec(dlg1) != QDialog.DialogCode.Accepted:
                self._fiado_flujo_activo = False
                self._fiado_cliente_id = None
                self.set_metodo(rev)
                return

            cliente_ok = dlg1.cliente
            dni_ref = dlg1.dni_ref

            dlg2 = DialogoFiadoExpressConfirmacion(
                self.total_final, cliente_ok, dni_ref, terminal
            )
            res2 = qt_exec(dlg2)

            if res2 == QDialog.DialogCode.Accepted:
                self.current_metodo = "Fiado"
                self._fiado_cliente_id = dlg2.cliente_id
                idx = self.cmb_cliente.findData(dlg2.cliente_id)
                if idx >= 0:
                    self.cmb_cliente.setCurrentIndex(idx)
                self.txt_pago.setText(f"{self.total_final:.2f}")
                self._fiado_flujo_activo = False
                QTimer.singleShot(80, lambda: self.finalizar(imprimir=False))
                return

            if getattr(dlg2, "reintentar_dni", False):
                continue

            self._fiado_flujo_activo = False
            self._fiado_cliente_id = None
            self.set_metodo(rev)
            return

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
            
            # Usamos el componente modular para actualizar el vuelto
            self.resumen_vuelto.actualizar_vuelto(vuelto)
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
                            self.lbl_mp_status.setProperty("estado", "success")
                            self.lbl_mp_status.style().unpolish(self.lbl_mp_status)
                            self.lbl_mp_status.style().polish(self.lbl_mp_status)
                        else:
                            self.lbl_mp_status.setProperty("estado", "success")
                            self.lbl_mp_status.style().unpolish(self.lbl_mp_status)
                            self.lbl_mp_status.style().polish(self.lbl_mp_status)
                        
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
            from src.repositories.cliente_repository import ClienteRepository

            cliente_id = getattr(self, "_fiado_cliente_id", None) or self.cmb_cliente.currentData()
            if not cliente_id:
                if not getattr(self, "_fiado_flujo_activo", False):
                    self._abrir_fiado_express(getattr(self, "_revertir_tras_fiado", "Efectivo"))
                else:
                    QMessageBox.warning(self, "Fiado", "No se seleccionó cliente.")
                return None
            c = ClienteRepository.obtener_por_id(cliente_id)
            if not c:
                QMessageBox.warning(self, "Fiado", "Cliente no encontrado.")
                return None
            disp = ClienteRepository.credito_disponible(c)
            p1_float = float(p1_t) if p1_t else 0
            if p1_float > disp + 0.01:
                QMessageBox.warning(self, "Fiado", f"Crédito insuficiente.\nDisp: ${disp:.2f}\nReq: ${p1_float:.2f}")
                return None

        p1, p2 = CobroController.validar_monto_suficiente(
            self.current_metodo, 
            self.total_final, 
            p1_t, 
            p2_t, 
            getattr(self, 'valores_mixtos', None)
        )
        
        if p1 is None and p2 is None:
            if self.current_metodo != "Mixto" and not p1_t.strip().replace('.', '', 1).isdigit():
                QMessageBox.critical(self, "ERROR", "Monto inválido ingresado.")
            else:
                # Si falta dinero y no es mixto, ofrecer pasarse a Mixto
                if self.current_metodo != "Mixto":
                    try:
                        p1_val = float(p1_t) if p1_t else 0.0
                    except ValueError:
                        p1_val = 0.0
                    self.set_metodo("Mixto")
                    faltante = self.total_final - p1_val
                    self.txt_otro.setText(f"{faltante:.2f}")
                    self.txt_otro.setFocus()
                    self.txt_otro.selectAll()
                else:
                    QMessageBox.critical(self, "MONTO INSUFICIENTE", "Falta dinero para cubrir el total.")
            return None
            
        return (p1, p2)

    def intentar_finalizar(self):
        if self.current_metodo == "Fiado":
            if getattr(self, "_fiado_flujo_activo", False):
                return
            if getattr(self, "_fiado_cliente_id", None):
                self.finalizar(imprimir=False)
            else:
                self._abrir_fiado_express(getattr(self, "_revertir_tras_fiado", "Efectivo"))
            return
        if self.current_metodo == "QR":
            from src.config import config
            config._load_config()
            token = config.get("mp_access_token", "")
            if not token:
                QMessageBox.warning(
                    self, "Configuración Faltante",
                    "Falta el Access Token de Mercado Pago.\n\n"
                    "Admin → Configuración → Terminales TPV → pegar token y Guardar."
                )
                return
            self._procesar_cobro_qr_pantalla(token, self.total_final)
            return
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
        _btn_compact = "border-radius: 8px; font-weight: 900; font-size: 14px; border: none; padding: 8px 12px;"
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
            from src.cajero.cajero_activo import CajeroActivo
            cajero_secundario = CajeroActivo.nombre if CajeroActivo.numero == 2 else ''
            
            id_v, self.resultado_venta = CobroController.procesar_y_guardar_venta(
                self.total_final,
                self.current_metodo,
                p1, p2,
                self.items_carrito,
                dict(config.current_user).get('username', 'cajero') if config.current_user else 'cajero',
                cajero_secundario,
                getattr(self, 'descuento_monto', 0.0),
                getattr(self, 'recargo_monto', 0.0),
                getattr(self, 'descuentaso_oferta', 0.0),
                getattr(self, 'nombre_pendiente', None)
            )
            if id_v:
                # Si fue fiado, actualizar la deuda y registrar en cuenta corriente
                if self.current_metodo == "Fiado":
                    from src.repositories.cliente_repository import ClienteRepository

                    cliente_id = getattr(self, "_fiado_cliente_id", None) or self.cmb_cliente.currentData()
                    if not cliente_id:
                        self._procesando_pago = False
                        QMessageBox.warning(self, "Fiado", "No se pudo identificar al cliente del fiado.")
                        return
                    c = ClienteRepository.obtener_por_id(cliente_id)
                    if not c:
                        self._procesando_pago = False
                        QMessageBox.warning(self, "Fiado", "Cliente no encontrado en la base de datos.")
                        return
                    nueva_deuda = float(dict(c).get("deuda_actual", 0)) + self.total_final
                    nombre_cli = dict(c).get("nombre", "")

                    db_manager.execute_non_query(
                        "UPDATE clientes SET deuda_actual = ? WHERE id = ?",
                        (nueva_deuda, cliente_id),
                    )
                    db_manager.execute_non_query(
                        "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion, venta_id) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (cliente_id, "CARGO", self.total_final, nueva_deuda, f"Venta a crédito Ticket #{id_v}", id_v),
                    )
                    self.resultado_venta["cliente_nombre"] = nombre_cli
            
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
            import traceback
            tb = traceback.format_exc()
            self._procesando_pago = False
            self.btn_cobrar.setEnabled(True)
            self.btn_cancelar.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Fallo al cobrar:\n{e}\n\n{tb}")

    def imprimir_ticket(self, id_v, abrir_manual=False, force_fiscal=False):
        try:
            from src.hardware.printer import printer_manager
            from src.cajero.cajero_activo import CajeroActivo
            
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
        from src.cajero.paso6_cobro.componentes_paso6_cobro.mercadopago_integracion import MercadoPagoIntegracion
        MercadoPagoIntegracion(self).procesar_pago_mercadopago_point()

    def _procesar_cobro_qr_pantalla(self, token, monto):
        from src.cajero.paso6_cobro.componentes_paso6_cobro.mercadopago_integracion import MercadoPagoIntegracion
        MercadoPagoIntegracion(self)._procesar_cobro_qr_pantalla(token, monto)

    def verificar_transferencia_mp(self):
        from src.cajero.paso6_cobro.componentes_paso6_cobro.mercadopago_integracion import MercadoPagoIntegracion
        MercadoPagoIntegracion(self).verificar_transferencia_mp()

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
            foco = self.focusWidget()
            if self.current_metodo == "Fiado":
                if getattr(self, "_fiado_flujo_activo", False):
                    return
                if getattr(self, "_fiado_cliente_id", None):
                    self.finalizar(imprimir=False)
                else:
                    self._abrir_fiado_express(getattr(self, "_revertir_tras_fiado", "Efectivo"))
                return
            if isinstance(foco, QPushButton) and foco in self.btns.values():
                # 1. ENTER ELIGE MÉTODO -> Salta al casillero de monto
                self.txt_pago.setFocus()
                self.txt_pago.selectAll()
            else:
                # 2 y 3. ENTER CONFIRMA Y CIERRA (Sin Ticket)
                self.intentar_finalizar()
        else:
            super().keyPressEvent(event)


 
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
        elif key in ("ESC", "Salir"):
            self.reject()
        else:
            teclado_key_map = {
                '0': Qt.Key_0, '1': Qt.Key_1, '2': Qt.Key_2, '3': Qt.Key_3, '4': Qt.Key_4,
                '5': Qt.Key_5, '6': Qt.Key_6, '7': Qt.Key_7, '8': Qt.Key_8, '9': Qt.Key_9,
                ',': Qt.Key_Comma
            }
            key_code = teclado_key_map.get(key, Qt.Key_unknown)
            event_press = QKeyEvent(QEvent.KeyPress, key_code, Qt.NoModifier, key)
            QApplication.sendEvent(focused, event_press)
            event_release = QKeyEvent(QEvent.KeyRelease, key_code, Qt.NoModifier, key)
            QApplication.sendEvent(focused, event_release)