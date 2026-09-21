"""Cara izquierda del panel jefe. Pinta. No decide qué es oferta."""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.jefe.reportes.financiero.dinero import fmt_plata
from src.jefe.reportes.letra import etiqueta, fuente_limpia
from src.jefe.vitrina.consulta import listar
from src.jefe.vitrina.tarjeta import TarjetaOferta


class PanelPublicidad(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelPublicidad")
        self.setFont(fuente_limpia(13))
        self._idx = 0
        self._ofertas = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        self.lbl_saludo = etiqueta("Buenos dias", 22)
        self.lbl_saludo.setStyleSheet(
            "color: #0F172A; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        self.lbl_sub = etiqueta("Vitrina de tienda", 12)
        self.lbl_sub.setStyleSheet(
            "color: #64748B; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        root.addWidget(self.lbl_saludo)
        root.addWidget(self.lbl_sub)

        kpis = QHBoxLayout()
        kpis.setSpacing(10)
        self.lbl_gan = self._chip("Ganancia de hoy", "—")
        self.lbl_inv = self._chip("Inventario al costo", "—")
        kpis.addWidget(self.lbl_gan, 1)
        kpis.addWidget(self.lbl_inv, 1)
        root.addLayout(kpis)

        self.btn_export = QPushButton("Exportar ganancias")
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setFixedHeight(36)
        self.btn_export.setFont(fuente_limpia(11))
        self.btn_export.setStyleSheet(
            "QPushButton { background: #0F172A; color: #FFFFFF; border: none; "
            "border-radius: 10px; font-weight: 400; letter-spacing: 0px; }"
            "QPushButton:hover { background: #1E293B; }"
        )
        root.addWidget(self.btn_export)

        escena = QFrame()
        escena.setObjectName("VitrinaEscena")
        escena.setMinimumHeight(360)
        escena.setStyleSheet(
            "QFrame#VitrinaEscena { background: #0B1220; border-radius: 18px; "
            "border: 1px solid #1E293B; }"
        )
        sc = QVBoxLayout(escena)
        sc.setContentsMargins(16, 14, 16, 14)
        sc.setSpacing(12)

        cabeza = QHBoxLayout()
        chip = QLabel("EN PANTALLA")
        chip.setFont(fuente_limpia(10))
        chip.setStyleSheet(
            "color: #94A3B8; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        self.lbl_marca = QLabel("4 plazas")
        self.lbl_marca.setFont(fuente_limpia(12))
        self.lbl_marca.setStyleSheet(
            "color: #CBD5E1; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        cabeza.addWidget(chip)
        cabeza.addStretch()
        cabeza.addWidget(self.lbl_marca)
        sc.addLayout(cabeza)

        grilla = QGridLayout()
        grilla.setSpacing(10)
        grilla.setRowStretch(0, 1)
        grilla.setRowStretch(1, 1)
        grilla.setColumnStretch(0, 1)
        grilla.setColumnStretch(1, 1)
        self._tarjetas = [TarjetaOferta(i + 1) for i in range(4)]
        for i, t in enumerate(self._tarjetas):
            grilla.addWidget(t, i // 2, i % 2)
        sc.addLayout(grilla, 1)

        self.lbl_estado = QLabel("Cuatro plazas. Solo descuentos reales.")
        self.lbl_estado.setWordWrap(True)
        self.lbl_estado.setFont(fuente_limpia(11))
        self.lbl_estado.setStyleSheet(
            "color: #64748B; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        sc.addWidget(self.lbl_estado)
        root.addWidget(escena, 1)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotar)
        self._timer.start(6000)
        QTimer.singleShot(200, self.refrescar_vitrina)

    def _chip(self, titulo: str, valor: str) -> QFrame:
        f = QFrame()
        f.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }"
        )
        lay = QVBoxLayout(f)
        lay.setContentsMargins(14, 12, 14, 12)
        t = etiqueta(titulo, 11)
        t.setStyleSheet(
            "color: #64748B; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        v = etiqueta(valor, 16)
        v.setStyleSheet(
            "color: #0F172A; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        lay.addWidget(t)
        lay.addWidget(v)
        f._valor = v
        return f

    def set_metricas(self, ganancia: float, inventario: float):
        self.lbl_gan._valor.setText(fmt_plata(ganancia))
        self.lbl_inv._valor.setText(fmt_plata(inventario))

    def set_saludo(self, texto: str):
        self.lbl_saludo.setText(texto)

    def refrescar_vitrina(self):
        self._ofertas = listar()
        self._idx = 0
        self._pintar()

    def _rotar(self):
        if len(self._ofertas) > 4:
            self._idx = (self._idx + 4) % len(self._ofertas)
            self._pintar()

    def _pintar(self):
        n = len(self._ofertas)
        if n == 0:
            for t in self._tarjetas:
                t.vaciar()
            self.lbl_marca.setText("0 ofertas reales")
            self.lbl_estado.setText("Sin ofertas activas. No se inventan avisos.")
            return
        for i, t in enumerate(self._tarjetas):
            if n > 4:
                t.cargar(self._ofertas[(self._idx + i) % n])
            elif i < n:
                t.cargar(self._ofertas[i])
            else:
                t.vaciar()
        self.lbl_marca.setText(f"{min(n, 4)} de {n} ofertas")
        self.lbl_estado.setText("Lista en blanco. Tachado naranja. Precio menor vigente.")
