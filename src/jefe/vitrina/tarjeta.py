"""Una plaza de la vitrina. La vista no calcula precios."""

from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout

from src.jefe.reportes.financiero.dinero import fmt_plata
from src.jefe.reportes.letra import fuente_limpia


class TarjetaOferta(QFrame):
    def __init__(self, plaza: int):
        super().__init__()
        self.setObjectName("TarjetaOferta")
        self.setStyleSheet(
            "QFrame#TarjetaOferta { background: #111827; border: 1px solid #1F2937; "
            "border-radius: 14px; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(6)

        self.lbl_tag = QLabel(f"PLAZA {plaza:02d}")
        self.lbl_tag.setFont(fuente_limpia(10))
        self.lbl_tag.setStyleSheet(
            "color: #94A3B8; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        self.lbl_nombre = QLabel("Sin oferta")
        self.lbl_nombre.setWordWrap(True)
        self.lbl_nombre.setFont(fuente_limpia(16))
        self.lbl_nombre.setStyleSheet(
            "color: #F8FAFC; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        self.lbl_antes = QLabel("")
        self.lbl_antes.setFont(fuente_limpia(12))
        self.lbl_antes.setStyleSheet(
            "color: #FFFFFF; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        self.linea = QFrame()
        self.linea.setFixedHeight(2)
        self.linea.setStyleSheet("background: #FF4D00; border: none; max-width: 88px;")
        self.linea.hide()
        self.lbl_precio = QLabel("")
        self.lbl_precio.setFont(fuente_limpia(20))
        self.lbl_precio.setStyleSheet(
            "color: #F8FAFC; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        lay.addWidget(self.lbl_tag)
        lay.addWidget(self.lbl_nombre, 1)
        lay.addWidget(self.lbl_antes)
        lay.addWidget(self.linea)
        lay.addWidget(self.lbl_precio)
        self._plaza = plaza

    def vaciar(self):
        self.lbl_tag.setText(f"PLAZA {self._plaza:02d}  ·  LIBRE")
        self.lbl_nombre.setText("Sin oferta")
        self.lbl_antes.setText("")
        self.lbl_precio.setText("")
        self.linea.hide()

    def cargar(self, oferta: dict):
        self.lbl_tag.setText(f"PLAZA {self._plaza:02d}  ·  {oferta['pct']}%")
        self.lbl_nombre.setText(oferta["nombre"] or "Producto")
        self.lbl_antes.setText(fmt_plata(oferta["lista"]))
        self.lbl_precio.setText(fmt_plata(oferta["oferta"]))
        self.linea.show()
