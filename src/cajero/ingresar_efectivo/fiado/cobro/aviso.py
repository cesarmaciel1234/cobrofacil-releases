"""Cartel del abono. El mismo toast del cobro, centrado en F6."""
from src.cajero.paso6_cobro.aviso_en_cobro.toast import AvisoCobro


class AvisoAbono(AvisoCobro):
    def ubicar(self):
        hoja = self.parentWidget()
        if hoja is None:
            return
        ancho = max(320, min(520, hoja.width() - 40))
        self.setFixedWidth(ancho)
        self.adjustSize()
        alto = max(88, self.sizeHint().height())
        x = max(8, (hoja.width() - ancho) // 2)
        y = max(8, (hoja.height() - alto) // 3)
        self.setGeometry(x, y, ancho, alto)
        self.raise_()
