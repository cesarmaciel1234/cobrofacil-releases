from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class DialogoCandado(QDialog):
    """
    Pantalla de bloqueo clásica. Muestra dos botones/paneles grandes simétricos:
    [1] CAJERO (azul) y [2] AUXILIAR (verde).
    Ambos requieren validación de PIN para acceder y reconfiguran su hardware respectivo.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        if parent:
            self.setFixedSize(parent.size())
        else:
            self.setFixedSize(1280, 800)
        self._build()

    def _build(self):
        from src.config import config
        # Fondo desenfocado leve (el blur real lo hace el padre)
        fondo = QFrame(self)
        fondo.setGeometry(0, 0, self.width(), self.height())
        fondo.setObjectName("DialogoCandadoFondo")

        # Contenedor central más alto (500px como pidió el usuario) y con bordes suaves
        w, h = 600, 500
        container = QFrame(self)
        container.setFixedSize(w, h)
        container.move((self.width() - w) // 2, (self.height() - h) // 2)
        container.setObjectName("DialogoCandadoContenedor")
        
        # Se elimina el efecto de sombra (QGraphicsDropShadowEffect) para mejorar rendimiento en equipos de bajos recursos.

        main_lay = QVBoxLayout(container)
        main_lay.setContentsMargins(40, 40, 40, 40)
        main_lay.setSpacing(25)

        # Título superior
        lbl_icon = QLabel("🔒  TERMINAL BLOQUEADA")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setObjectName("DialogoCandadoTitulo")
        main_lay.addWidget(lbl_icon)

        lbl_sub = QLabel("Selecciona tu perfil de caja para continuar:")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setObjectName("DialogoCandadoSubtitulo")
        main_lay.addWidget(lbl_sub)

        # Layout horizontal para las dos tarjetas simétricas
        cards_lay = QHBoxLayout()
        cards_lay.setSpacing(20)

        name_c1 = config.get("nombre_cajero_1", "CAJERO")
        name_c2 = config.get("nombre_cajero_2", "AUXILIAR")

        # --- TARJETA [1] CAJERO (AZUL) ---
        self.btn_cajero = QPushButton()
        self.btn_cajero.setFixedSize(240, 160)
        self.btn_cajero.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cajero.setObjectName("DialogoCandadoBtnCajero")
        lay_c1 = QVBoxLayout(self.btn_cajero)
        lay_c1.setContentsMargins(15, 20, 15, 20)
        
        lbl_t1 = QLabel(f"🔵  [1]  {name_c1.upper()}")
        lbl_t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_t1.setObjectName("DialogoCandadoCajeroT1")
        lbl_p1 = QLabel("Perfil Principal\n(Cajón e impresora 1)")
        lbl_p1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_p1.setObjectName("DialogoCandadoCajeroP1")
        lay_c1.addWidget(lbl_t1)
        lay_c1.addWidget(lbl_p1)
        self.btn_cajero.clicked.connect(lambda: self._pedir_pin(1))

        # --- TARJETA [2] AUXILIAR (VERDE) ---
        self.btn_auxiliar = QPushButton()
        self.btn_auxiliar.setFixedSize(240, 160)
        self.btn_auxiliar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_auxiliar.setObjectName("DialogoCandadoBtnAuxiliar")
        lay_c2 = QVBoxLayout(self.btn_auxiliar)
        lay_c2.setContentsMargins(15, 20, 15, 20)
        
        lbl_t2 = QLabel(f"🟢  [2]  {name_c2.upper()}")
        lbl_t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_t2.setObjectName("DialogoCandadoAuxiliarT2")
        lbl_p2 = QLabel("Perfil Secundario\n(Cajón e impresora 2)")
        lbl_p2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_p2.setObjectName("DialogoCandadoAuxiliarP2")
        lay_c2.addWidget(lbl_t2)
        lay_c2.addWidget(lbl_p2)
        self.btn_auxiliar.clicked.connect(lambda: self._pedir_pin(2))

        cards_lay.addWidget(self.btn_cajero)
        cards_lay.addWidget(self.btn_auxiliar)
        main_lay.addLayout(cards_lay)
        
        main_lay.addStretch()

        # Mensaje IA / Aprendizaje
        ai_tip = QLabel("🤖 Misma sesión de turno: el auxiliar cobra con su PIN y activa su cajón físico. Usa F10 para bloquear al salir.")
        ai_tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ai_tip.setWordWrap(True)
        ai_tip.setObjectName("DialogoCandadoIA")
        main_lay.addWidget(ai_tip)

    def _pedir_pin(self, numero_cajero):
        from src.config import config
        from src.cajero.cajero_activo import CajeroActivo
        from src.cajero.paso5_terminal.dialogos.dialogo_pin import DialogoPIN
        from src.utils.qt_compat import qt_exec
        nombre = config.get(f"nombre_cajero_{numero_cajero}", f"Cajero {numero_cajero}").upper()
        dlg = DialogoPIN(nombre, parent=self)
        if qt_exec(dlg) and dlg.ok:
            CajeroActivo.set(numero_cajero)
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            return  # No se puede escapar sin acción
        if event.key() == Qt.Key.Key_1:
            self._pedir_pin(1)
            return
        if event.key() == Qt.Key.Key_2:
            self._pedir_pin(2)
            return
