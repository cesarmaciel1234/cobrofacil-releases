import os
import sys
import json
import unicodedata
import re
import math

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QMainWindow, QShortcut, QFrame, QScrollArea, 
                             QLineEdit, QPushButton, QProgressBar, QSizePolicy, 
                             QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QPoint, pyqtProperty, pyqtSignal, QSize, QEasingCurve
from PyQt5.QtGui import QKeySequence, QFont, QPainter, QColor, QPen, QBrush, QPainterPath

# ─── Rutas ──────────────────────────────────────────────────────────────────
_DIR       = os.path.dirname(os.path.abspath(__file__))
MANUAL_JSON = os.path.join(_DIR, "manual_cajero.json")

# ─── Pasos del Tutor ────────────────────────────────────────────────────────
PASOS_TUTOR = [
    {"msg": "👋 ¡Hola! Soy tu asistente de CobroFacil POS. Estoy aquí para ayudarte.", "espera": 3},
    {"msg": "🛒 TERMINAL DE VENTAS: Simplemente pasa el código de barras del producto con el lector láser.", "espera": 4},
    {"msg": "✏️ Multiplicador: escribe CANTIDAD * CÓDIGO  (Ej: 6*779001234) y presiona ENTER.", "espera": 4},
    {"msg": "➕ Artículo sin código: escribe +PRECIO  (Ej: +500) y presiona ENTER.", "espera": 4},
    {"msg": "⚖️ BALANZA: escanea el código de la balanza (Systel/Kretz). El sistema calcula el precio automáticamente.", "espera": 4},
    {"msg": "💳 COBRAR: presiona F12 (o ENTER con el buscador vacío) para ir a la pantalla de cobro.", "espera": 4},
    {"msg": "💰 Selecciona el método de pago con las flechas ←→: Efectivo, Tarjeta o Mixto. Luego ENTER.", "espera": 4},
    {"msg": "🖨️ FINALIZAR: F1 = cobra e imprime ticket · F2 = cobra sin ticket · ENTER = igual que F2.", "espera": 4},
    {"msg": "✅ ¡Tutorial completo! Ahora podés consultarme cualquier duda escribiendo en el chat. 💬", "espera": 3},
]

# ─── Motor de Consultas ──────────────────────────────────────────────────────
def _normalizar(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^\w\s]", "", sin_tildes).strip()

class ChatManual:
    def __init__(self):
        self.entradas = []
        try:
            if not os.path.exists(MANUAL_JSON):
                with open(MANUAL_JSON, "w", encoding="utf-8") as f:
                    json.dump({"entradas": [{"id":"demo", "preguntas":["cobrar", "f12"], "respuesta":"Presiona F12 para cobrar."}]}, f)
            with open(MANUAL_JSON, "r", encoding="utf-8") as f:
                self.entradas = json.load(f).get("entradas", [])
        except Exception as e:
            self.entradas = [{"id": "error", "preguntas": [], "respuesta": f"⚠️ Error cargando manual: {e}"}]

    def consultar(self, texto: str) -> str:
        q = _normalizar(texto.strip())
        if not q: return ""
        mejor_score, mejor_resp = 0, None
        for entrada in self.entradas:
            if not entrada.get("preguntas"): continue
            score = sum(len(kw) for kw in entrada["preguntas"] if _normalizar(kw) in q)
            if score > mejor_score:
                mejor_score, mejor_resp = score, entrada["respuesta"]
        if mejor_resp: return mejor_resp
        for entrada in self.entradas:
            if entrada.get("id") == "no_encontrado": return entrada["respuesta"]
        return "🤔 No encontré información. Consultá con tu supervisor."


# ─── COMPONENTES NATIVOS PYQT5 ──────────────────────────────────────────────

class RobotAvatar(QWidget):
    """Widget de Robot dibujado con QPainter y animado con QPropertyAnimation"""
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)
        self.setCursor(Qt.PointingHandCursor)
        
        self.blinking = False
        self.talking = False
        
        # Animación de parpadeo aleatorio
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._do_blink)
        self.blink_timer.start(3500)
        
        # Animación de habla
        self.talk_timer = QTimer(self)
        self.talk_timer.timeout.connect(self._talk_frame)
        self.mouth_open = False
        
        # Animación de flotar (Hover)
        self._anim_offset = 0.0
        self.hover_timer = QTimer(self)
        self.hover_timer.timeout.connect(self._update_hover)
        self.hover_timer.start(30)
        
        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

    def _do_blink(self):
        self.blinking = True
        self.update()
        QTimer.singleShot(150, self._end_blink)
        self.blink_timer.setInterval(3000 + (self.width() % 2000)) # Aleatorio simple
        
    def _end_blink(self):
        self.blinking = False
        self.update()

    def set_talking(self, talking: bool):
        self.talking = talking
        if talking:
            self.talk_timer.start(160)
        else:
            self.talk_timer.stop()
            self.mouth_open = False
            self.update()
            
    def _talk_frame(self):
        self.mouth_open = not self.mouth_open
        self.update()
        
    def _update_hover(self):
        self._anim_offset += 0.05
        self.update()

    def paintEvent(self, event):
        from PyQt5.QtGui import QLinearGradient, QPainterPath
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calcular offset de flotación (seno)
        y_offset = math.sin(self._anim_offset) * 4
        painter.translate(0, y_offset)
        
        # 1. ANTENA REACTIVA
        painter.setPen(QPen(QColor("#475569"), 3, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(40, 5, 40, 15)
        
        if self.talking:
            # Rojo parpadeante si está respondiendo
            ant_color = QColor("#EF4444") if self.mouth_open else QColor("#991B1B")
            glow_color = QColor(239, 68, 68, 80) if self.mouth_open else QColor(0,0,0,0)
        else:
            # Cyan estático si espera
            ant_color = QColor("#06B6D4")
            glow_color = QColor(6, 182, 212, 80)
            
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(glow_color))
        painter.drawEllipse(35, 0, 10, 10)
        painter.setBrush(QBrush(ant_color))
        painter.drawEllipse(37, 2, 6, 6)

        # 2. CUERPO DEL ROBOT (Volumen 3D Silencioso)
        body_grad = QLinearGradient(10, 15, 70, 65)
        body_grad.setColorAt(0.0, QColor("#334155")) # Luz
        body_grad.setColorAt(1.0, QColor("#0F172A")) # Sombra profunda
        
        path = QPainterPath()
        path.addRoundedRect(10, 15, 60, 50, 25, 25) # Forma de cápsula
        
        painter.setBrush(QBrush(body_grad))
        painter.setPen(QPen(QColor("#1E293B"), 2))
        painter.drawPath(path)
        
        # 3. VISOR (Efecto de Cristal)
        visor_path = QPainterPath()
        visor_path.addRoundedRect(16, 30, 48, 22, 10, 10)
        
        visor_grad = QLinearGradient(16, 30, 16, 52)
        visor_grad.setColorAt(0.0, QColor("#000000"))
        visor_grad.setColorAt(0.5, QColor("#09090b"))
        visor_grad.setColorAt(1.0, QColor("#18181b"))
        
        painter.setBrush(QBrush(visor_grad))
        painter.setPen(QPen(QColor("#000000"), 1))
        painter.drawPath(visor_path)
        
        # Brillo reflejado en el borde superior del cristal
        painter.setBrush(QBrush(QColor(255, 255, 255, 20)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(18, 32, 44, 6, 3, 3)
        
        # 4. OJOS NEON CON REFLEXIÓN
        painter.setPen(Qt.NoPen)
        if self.blinking:
            # Línea plana al parpadear
            painter.setBrush(QBrush(QColor("#06B6D4")))
            painter.drawRoundedRect(24, 40, 12, 2, 1, 1)
            painter.drawRoundedRect(44, 40, 12, 2, 1, 1)
        else:
            # Ojo luminoso
            painter.setBrush(QBrush(QColor("#22D3EE")))
            
            # Dinamismo sutil al hablar
            eye_h = 10 if not self.talking else (8 if self.mouth_open else 10)
            eye_y = 36 if not self.talking else (37 if self.mouth_open else 36)
            
            painter.drawRoundedRect(24, int(eye_y), 12, int(eye_h), 5, 5)
            painter.drawRoundedRect(44, int(eye_y), 12, int(eye_h), 5, 5)
            
            # Reflexión interna blanca
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(27, int(eye_y) + 2, 3, 3)
            painter.drawEllipse(47, int(eye_y) + 2, 3, 3)
            
        # 5. BOCA AMIGABLE (Sonrisa LED)
        if self.talking and self.mouth_open:
            # Boca hablando (óvalo iluminado cyan)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#06B6D4")))
            painter.drawEllipse(35, 44, 10, 6)
        else:
            # Sonrisa LED
            painter.setPen(QPen(QColor("#06B6D4"), 2, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            # Arco: x=32, y=40, w=16, h=10. start=0, span=-180 (forma de U)
            painter.drawArc(32, 40, 16, 10, 0 * 16, -180 * 16)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos()
            self._is_dragging = False

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            diff = event.globalPos() - self._drag_pos
            if diff.manhattanLength() > 3:
                self._is_dragging = True
            self._drag_pos = event.globalPos()
            parent = self.parentWidget()
            if parent:
                parent.move(parent.pos() + diff)
                if hasattr(parent, 'guardar_offset_relativo'):
                    parent.guardar_offset_relativo()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not getattr(self, '_is_dragging', False):
                self.clicked.emit()
            self._is_dragging = False


class FlowLayout(QHBoxLayout):
    """Layout simple horizontal que envuelve (wrap) si no entra"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(6)


class ChatBubble(QFrame):
    """Contenedor principal del chat, estilo limpio QSS"""
    close_requested = pyqtSignal()
    query_requested = pyqtSignal(str)
    tutor_start_requested = pyqtSignal()
    tutor_skip_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 500)
        self.setStyleSheet("""
            QFrame#MainBubble {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 16px;
            }
            QLabel#Title {
                color: #0f172a;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#BtnClose {
                color: #64748b;
                font-size: 18px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
            QPushButton#BtnClose:hover { color: #ef4444; }
            
            QScrollArea {
                border: none;
                background: transparent;
            }
            QWidget#ScrollContent {
                background: transparent;
            }
            
            QLineEdit#ChatInput {
                background: #ffffff;
                border: 2px solid #0f172a;
                border-radius: 8px;
                padding: 8px;
                color: #0f172a;
                font-size: 13px;
                font-weight: 600;
            }
            QLineEdit#ChatInput:focus { border-color: #4f46e5; }
            
            QPushButton#BtnSend {
                background-color: #4f46e5;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #0f172a;
                border-radius: 8px;
                padding: 6px 12px;
            }
            QPushButton#BtnSend:hover { background-color: #6366f1; }
            
            QPushButton.SugBtn {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
                color: #334155;
            }
            QPushButton.SugBtn:hover { background-color: #f1f5f9; border-color: #94a3b8; }
            
            /* Mensajes */
            QLabel.MsgBot {
                background-color: #eff6ff;
                border: 1px solid #bfdbfe;
                border-radius: 10px;
                border-top-left-radius: 2px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 600;
                color: #1e3a5f;
            }
            QLabel.MsgUser {
                background-color: #0f172a;
                border-radius: 10px;
                border-top-right-radius: 2px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 600;
                color: white;
            }
            
            /* Tutor */
            QFrame#TutorBar {
                background-color: #f1f5f9;
                border-radius: 6px;
            }
            QProgressBar {
                border: none;
                background-color: #e2e8f0;
                border-radius: 3px;
                height: 6px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background-color: #4f46e5;
                border-radius: 3px;
            }
            QLabel#TutorLbl { font-size: 11px; font-weight: bold; color: #64748b; }
            QPushButton#BtnSkip {
                background: transparent; border: 1px solid #cbd5e1;
                border-radius: 4px; color: #64748b; font-size: 10px; font-weight: bold; padding: 2px 6px;
            }
            QPushButton#BtnSkip:hover { color: #ef4444; border-color: #ef4444; }
        """)
        self.setObjectName("MainBubble")
        
        # Sombra
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(16, 16, 16, 16)
        main_lay.setSpacing(10)

        # Header
        header_lay = QHBoxLayout()
        header_lay.setContentsMargins(0,0,0,0)
        lbl_title = QLabel("📖 Manual del Cajero")
        lbl_title.setObjectName("Title")
        btn_close = QPushButton("✕")
        btn_close.setObjectName("BtnClose")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.close_requested.emit)
        header_lay.addWidget(lbl_title)
        header_lay.addStretch()
        header_lay.addWidget(btn_close)
        main_lay.addLayout(header_lay)

        # Tutor Bar
        self.tutor_frame = QFrame()
        self.tutor_frame.setObjectName("TutorBar")
        tutor_lay = QHBoxLayout(self.tutor_frame)
        tutor_lay.setContentsMargins(6,6,6,6)
        
        self.lbl_tutor = QLabel("Paso 1")
        self.lbl_tutor.setObjectName("TutorLbl")
        self.prog_tutor = QProgressBar()
        self.prog_tutor.setValue(0)
        self.prog_tutor.setTextVisible(False)
        self.prog_tutor.setFixedHeight(6)
        
        btn_skip = QPushButton("Omitir")
        btn_skip.setObjectName("BtnSkip")
        btn_skip.setCursor(Qt.PointingHandCursor)
        btn_skip.clicked.connect(self.tutor_skip_requested.emit)
        
        tutor_lay.addWidget(self.lbl_tutor)
        tutor_lay.addWidget(self.prog_tutor, 1)
        tutor_lay.addWidget(btn_skip)
        
        self.tutor_frame.hide() # Oculto por defecto
        main_lay.addWidget(self.tutor_frame)

        # Scroll Area (Mensajes)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("ScrollContent")
        self.msg_layout = QVBoxLayout(self.scroll_content)
        self.msg_layout.setContentsMargins(0, 0, 5, 0)
        self.msg_layout.setSpacing(10)
        self.msg_layout.addStretch() # Empuja los mensajes arriba
        
        self.scroll.setWidget(self.scroll_content)
        main_lay.addWidget(self.scroll, 1)

        # Sugerencias
        sug_lay = FlowLayout()
        sugerencias = [
            ("⌨️ Atajos", "atajos de teclado"),
            ("💳 Cobrar", "como cobro"),
            ("⚖️ Balanza", "balanza"),
            ("🏁 Cierre", "cerrar turno")
        ]
        for text, query in sugerencias:
            btn = QPushButton(text)
            btn.setProperty("class", "SugBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, q=query: self._send_query(q))
            sug_lay.addWidget(btn)
            
        btn_tut = QPushButton("🎓 Tutorial")
        btn_tut.setProperty("class", "SugBtn")
        btn_tut.setCursor(Qt.PointingHandCursor)
        btn_tut.clicked.connect(self.tutor_start_requested.emit)
        sug_lay.addWidget(btn_tut)
        sug_lay.addStretch()
        
        sug_wrapper = QWidget()
        sug_wrapper.setLayout(sug_lay)
        main_lay.addWidget(sug_wrapper)

        # Input Row
        inp_lay = QHBoxLayout()
        inp_lay.setContentsMargins(0,0,0,0)
        self.input_field = QLineEdit()
        self.input_field.setObjectName("ChatInput")
        self.input_field.setPlaceholderText("Escribí tu consulta...")
        self.input_field.returnPressed.connect(self._on_send)
        
        btn_send = QPushButton("➤")
        btn_send.setObjectName("BtnSend")
        btn_send.setCursor(Qt.PointingHandCursor)
        btn_send.clicked.connect(self._on_send)
        
        inp_lay.addWidget(self.input_field, 1)
        inp_lay.addWidget(btn_send)
        main_lay.addLayout(inp_lay)

    def add_message(self, text: str, is_bot: bool = True):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        if is_bot:
            lbl.setProperty("class", "MsgBot")
            lbl.setText(f"🤖 {text}")
            align = Qt.AlignLeft
        else:
            lbl.setProperty("class", "MsgUser")
            align = Qt.AlignRight
            
        # Re-aplicar estilo por si acaso
        lbl.setStyleSheet(self.styleSheet())
        
        # Añadir al layout antes del stretch final
        count = self.msg_layout.count()
        self.msg_layout.insertWidget(count - 1, lbl, 0, align)
        
        # Scroll al final
        QTimer.singleShot(50, self._scroll_to_bottom)
        
    def _scroll_to_bottom(self):
        vsb = self.scroll.verticalScrollBar()
        vsb.setValue(vsb.maximum())

    def _on_send(self):
        txt = self.input_field.text().strip()
        if txt:
            self.input_field.clear()
            self._send_query(txt)
            
    def _send_query(self, query: str):
        self.add_message(query, is_bot=False)
        self.query_requested.emit(query)

    def set_tutor_mode(self, active: bool, idx: int=0, total: int=1):
        if active:
            self.tutor_frame.show()
            self.lbl_tutor.setText(f"Paso {idx}/{total}")
            pct = int((idx / total) * 100)
            self.prog_tutor.setValue(pct)
        else:
            self.tutor_frame.hide()

    def set_focus_input(self):
        self.input_field.setFocus()

    # ── Lógica para Arrastrar la Burbuja ──
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            diff = event.globalPos() - self._drag_pos
            self._drag_pos = event.globalPos()
            parent = self.parentWidget()
            if parent:
                parent.move(parent.pos() + diff)
                if hasattr(parent, 'guardar_offset_relativo'):
                    parent.guardar_offset_relativo()
        super().mouseMoveEvent(event)


# ─── WIDGET PRINCIPAL (OVERLAY TRANSPARENTE) ────────────────────────────────

class ChatManualWidget(QWidget):
    """Contenedor invisible que maneja al Robot y la Burbuja y sigue a la ventana padre."""
    def __init__(self, parent_window=None):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Tamaño suficientemente grande para alojar la burbuja y el robot
        self.resize(380, 600)
        
        # Offset relativo para permitir arrastre
        self._offset_x = None
        self._offset_y = None
        
        self.motor = ChatManual()
        self._tutor_idx = 0
        self._tutor_activo = False
        self._tutor_timer = QTimer(self)
        self._tutor_timer.setSingleShot(True)
        self._tutor_timer.timeout.connect(self._tutor_avanzar)
        
        self._setup_ui()
        
        if self.parent_window:
            self.parent_window.installEventFilter(self)
            
        # Atajo Esc para cerrar el chat si tiene el foco
        self.shortcut_esc = QShortcut(QKeySequence("Esc"), self)
        self.shortcut_esc.activated.connect(self.cerrar_chat)

    def _setup_ui(self):
        # Usamos posiciones absolutas en este contenedor para posicionar libremente Robot y Bubble
        self.bubble = ChatBubble(self)
        self.bubble.move(10, 10)
        self.bubble.hide()
        
        # Conectar señales de la burbuja
        self.bubble.close_requested.connect(self.cerrar_chat)
        self.bubble.query_requested.connect(self._handle_query)
        self.bubble.tutor_start_requested.connect(self.iniciar_tutor)
        self.bubble.tutor_skip_requested.connect(self.omitir_tutor)
        
        self.robot = RobotAvatar(self)
        self.robot.move(self.width() - 90, self.height() - 90)
        self.robot.clicked.connect(self.toggle_chat)
        
        # Efecto de Opacidad para apertura/cierre
        self.opacity_effect = QGraphicsOpacityEffect(self.bubble)
        self.bubble.setGraphicsEffect(self.opacity_effect)
        self.anim_opacity = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_opacity.setDuration(200)
        
        # Efecto de escalar
        self.anim_pos = QPropertyAnimation(self.bubble, b"pos")
        self.anim_pos.setDuration(250)
        self.anim_pos.setEasingCurve(QEasingCurve.OutBack)
        
        # Mensaje de bienvenida inicial
        QTimer.singleShot(300, lambda: self.bubble.add_message("👋 ¡Hola! Soy tu asistente de CobroFacil POS. Hacé clic en 🎓 Tutorial para empezar.", True))

    def _handle_query(self, text: str):
        self.robot.set_talking(True)
        
        # Simular pequeño delay de pensamiento
        def _responder():
            respuesta = self.motor.consultar(text)
            self.bubble.add_message(respuesta, True)
            self.robot.set_talking(False)
            
        QTimer.singleShot(600, _responder)

    def toggle_chat(self):
        if self.bubble.isVisible():
            self.cerrar_chat()
        else:
            self.abrir_y_desplegar()

    def abrir_y_desplegar(self):
        if not self.isVisible():
            self.show()
            self.raise_()
            
        if not self.bubble.isVisible():
            self.bubble.show()
            self.anim_opacity.setStartValue(0.0)
            self.anim_opacity.setEndValue(1.0)
            self.anim_pos.setStartValue(QPoint(10, 100))
            self.anim_pos.setEndValue(QPoint(10, 10))
            self.anim_opacity.start()
            self.anim_pos.start()
            
        self.activateWindow()
        self.bubble.set_focus_input()

    def cerrar_chat(self):
        if self.bubble.isVisible():
            self.anim_opacity.setStartValue(1.0)
            self.anim_opacity.setEndValue(0.0)
            self.anim_pos.setStartValue(QPoint(10, 10))
            self.anim_pos.setEndValue(QPoint(10, 50))
            self.anim_opacity.start()
            self.anim_pos.start()
            # Ocultar luego de terminar animación
            QTimer.singleShot(250, self.bubble.hide)

    def guardar_offset_relativo(self):
        if self.parent_window:
            self._offset_x = self.x() - self.parent_window.x()
            self._offset_y = self.y() - self.parent_window.y()

    def actualizar_posicion(self):
        if self.parent_window:
            if self._offset_x is None:
                # Por defecto abajo a la derecha, por encima de la barra inferior
                x_pos = self.parent_window.x() + self.parent_window.width() - self.width() - 20
                y_pos = self.parent_window.y() + self.parent_window.height() - self.height() - 80
            else:
                # Mantener la posición arrastrada relativa al padre
                x_pos = self.parent_window.x() + self._offset_x
                y_pos = self.parent_window.y() + self._offset_y
            self.move(max(0, x_pos), max(0, y_pos))

    def eventFilter(self, obj, event):
        if obj == self.parent_window and event.type() in (event.Move, event.Resize):
            if self.isVisible():
                self.actualizar_posicion()
        return super().eventFilter(obj, event)

    # ── Lógica Tutor ──
    def iniciar_tutor(self):
        self._tutor_idx = 0
        self._tutor_activo = True
        self.abrir_y_desplegar()
        self._tutor_ejecutar_paso()

    def _tutor_ejecutar_paso(self):
        if not self._tutor_activo: return
        if self._tutor_idx >= len(PASOS_TUTOR):
            self.bubble.add_message("✅ ¡Tutorial completado! Estoy listo para tus consultas.", True)
            self.bubble.set_tutor_mode(False)
            self._tutor_activo = False
            return
            
        paso  = PASOS_TUTOR[self._tutor_idx]
        total = len(PASOS_TUTOR)
        idx   = self._tutor_idx + 1
        
        self.robot.set_talking(True)
        self.bubble.add_message(paso["msg"], True)
        self.bubble.set_tutor_mode(True, idx, total)
        
        QTimer.singleShot(1000, lambda: self.robot.set_talking(False))
        
        self._tutor_idx += 1
        if self._tutor_idx <= total:
            self._tutor_timer.start(paso.get("espera", 3) * 1000)
        else:
            self._tutor_timer.start(1000)

    def _tutor_avanzar(self):
        self._tutor_ejecutar_paso()
        
    def omitir_tutor(self):
        self._tutor_activo = False
        self._tutor_timer.stop()
        self.bubble.set_tutor_mode(False)
        self.bubble.add_message("⏭️ Tutorial omitido.", True)



