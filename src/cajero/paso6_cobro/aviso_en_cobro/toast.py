from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class AvisoCobro(QFrame):
    """Cartel grande sobre la hoja. No es una ventana y no hay que cerrarlo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AvisoCobro")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setStyleSheet(
            "QFrame#AvisoCobro {"
            " background: #FEF3C7; border: 3px solid #F59E0B; border-radius: 18px;"
            "}"
            "QLabel { background: transparent; border: none; color: #92400E;"
            " font-size: 28px; font-weight: 900; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 22)
        self.texto = QLabel("")
        self.texto.setWordWrap(True)
        self.texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.texto)
        self._reloj = QTimer(self)
        self._reloj.setSingleShot(True)
        self._reloj.timeout.connect(self.hide)
        self.hide()

    def mostrar(self, mensaje):
        self.texto.setText(mensaje)
        self.show()
        self.raise_()
        self._reloj.start(4500)
        QTimer.singleShot(0, self.ubicar)

    def ubicar(self):
        hoja = self.parentWidget()
        if hoja is None:
            return
        cobro = hoja
        while cobro is not None and not hasattr(cobro, "txt_desc"):
            cobro = cobro.parentWidget()
        if cobro is None:
            return
        ancla = cobro.txt_desc
        rotulo = cobro.lbl_desc
        recargo = cobro.txt_rec
        x = rotulo.mapTo(hoja, rotulo.rect().topLeft()).x()
        borde = recargo.mapTo(hoja, recargo.rect().bottomRight())
        base = ancla.mapTo(hoja, ancla.rect().bottomLeft()).y()
        ancho = max(360, min(borde.x() - x, hoja.width() - x - 8))
        self.setFixedWidth(ancho)
        self.adjustSize()
        alto = max(88, self.sizeHint().height())
        y = max(8, base - alto)
        self.setGeometry(max(8, x), y, ancho, alto)
        self.raise_()
