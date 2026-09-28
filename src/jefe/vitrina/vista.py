"""Cara izquierda del panel jefe. Pinta. No decide qué es oferta."""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.jefe.reportes.financiero.dinero import fmt_plata
from src.jefe.reportes.letra import etiqueta, fuente_limpia
from src.jefe.vitrina.consulta import listar
from src.jefe.vitrina.tarjeta import TarjetaOferta

# (texto del botón, nombre que entiende periodo.resolver)
PERIODOS = (
    ("Hoy", "Hoy"),
    ("Semana", "Semana Actual"),
    ("Mes", "Mes Actual"),
    ("Año", "Año actual"),
    ("Período", "Periodo..."),
)

_BTN_IDLE = (
    "QPushButton { background: #FFFFFF; color: #475569; border: 1px solid #E2E8F0; "
    "border-radius: 13px; padding: 3px 12px; font-weight: 400; letter-spacing: 0px; }"
    "QPushButton:hover { background: #EEF2FF; color: #4338CA; }"
)
_BTN_ACTIVO = (
    "QPushButton { background: #0F172A; color: #FFFFFF; border: 1px solid #0F172A; "
    "border-radius: 13px; padding: 3px 12px; font-weight: 400; letter-spacing: 0px; }"
)


def _dia_corto(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}" if len(iso) >= 10 else iso


class PanelPublicidad(QWidget):
    # desde, hasta ('YYYY-MM-DD'), etiqueta
    periodo_cambiado = pyqtSignal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelPublicidad")
        self.setFont(fuente_limpia(13))
        self._idx = 0
        self._ofertas = []
        self._es_hoy = True
        self._periodo_btn = "Hoy"

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
        fila_sub = QHBoxLayout()
        fila_sub.setSpacing(6)
        fila_sub.addWidget(self.lbl_sub)
        fila_sub.addStretch()
        self._botones_periodo = {}
        for texto, _clave in PERIODOS:
            b = QPushButton(texto)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFont(fuente_limpia(11))
            b.setFixedHeight(28)
            b.setStyleSheet(_BTN_ACTIVO if texto == "Hoy" else _BTN_IDLE)
            b.clicked.connect(lambda _c=False, t=texto: self._elegir_periodo(t))
            fila_sub.addWidget(b)
            self._botones_periodo[texto] = b
        root.addLayout(fila_sub)

        self.lbl_origen = etiqueta("", 11)
        self.lbl_origen.setStyleSheet(
            "color: #92400E; background: #FEF3C7; border: 1px solid #FDE68A; "
            "border-radius: 8px; padding: 4px 10px; font-weight: 400; letter-spacing: 0px;"
        )
        self.lbl_origen.setVisible(False)
        root.addWidget(self.lbl_origen)

        kpis = QHBoxLayout()
        kpis.setSpacing(10)
        self.lbl_gan = self._chip("Ganancia de hoy", "—")
        self.lbl_inv = self._chip("Inventario al costo", "—")
        kpis.addWidget(self.lbl_gan, 1)
        kpis.addWidget(self.lbl_inv, 1)
        root.addLayout(kpis)

        cuentas = QHBoxLayout()
        cuentas.setSpacing(10)
        self.lbl_pagos = self._chip("Pagos clientes", "—")
        self.lbl_deuda = self._chip("Deuda clientes", "—")
        cuentas.addWidget(self.lbl_pagos, 1)
        cuentas.addWidget(self.lbl_deuda, 1)
        root.addLayout(cuentas)

        extras = QHBoxLayout()
        extras.setSpacing(10)
        self.lbl_redondeo = self._chip("Redondeo del día", "—")
        self.lbl_digitales = self._chip("Digitales sin firmar / total", "—")
        extras.addWidget(self.lbl_redondeo, 1)
        extras.addWidget(self.lbl_digitales, 1)
        root.addLayout(extras)

        caja = QHBoxLayout()
        caja.setSpacing(10)
        self.lbl_tickets = self._chip("Tickets del día", "—")
        self.lbl_cancel = self._chip("Cancelaciones del día", "—")
        caja.addWidget(self.lbl_tickets, 1)
        caja.addWidget(self.lbl_cancel, 1)
        root.addLayout(caja)

        # (chip, título en Hoy, título con período). Inventario y deuda son foto del momento.
        self._periodales = (
            (self.lbl_gan, "Ganancia de hoy", "Ganancia"),
            (self.lbl_pagos, "Pagos clientes", "Pagos clientes"),
            (self.lbl_redondeo, "Redondeo del día", "Redondeo"),
            (self.lbl_digitales, "Digitales sin firmar / total", "Digitales sin firmar / total"),
            (self.lbl_tickets, "Tickets del día", "Tickets"),
            (self.lbl_cancel, "Cancelaciones del día", "Cancelaciones"),
        )

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
        d = etiqueta("", 10)
        d.setStyleSheet(
            "color: #94A3B8; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        d.hide()
        lay.addWidget(t)
        lay.addWidget(v)
        lay.addWidget(d)
        f._titulo = t
        f._valor = v
        f._detalle = d
        return f

    def _elegir_periodo(self, texto: str):
        from src.jefe.reportes.periodo import resolver_rango_periodo

        clave = dict(PERIODOS)[texto]
        rango = resolver_rango_periodo(clave, self)
        if rango is None:
            return
        desde, hasta = rango[0][:10], rango[1][:10]
        self._periodo_btn = texto
        for t, b in self._botones_periodo.items():
            b.setStyleSheet(_BTN_ACTIVO if t == texto else _BTN_IDLE)
        if texto == "Período":
            etiqueta_p = f"{_dia_corto(desde)} – {_dia_corto(hasta)}" if desde != hasta else _dia_corto(desde)
        else:
            etiqueta_p = texto
        self._es_hoy = texto == "Hoy"
        self.lbl_sub.setText("Vitrina de tienda" if self._es_hoy else f"Vitrina de tienda · {etiqueta_p}")
        for chip, t_hoy, t_base in self._periodales:
            chip._titulo.setText(t_hoy if self._es_hoy else f"{t_base} · {etiqueta_p}")
        self.periodo_cambiado.emit(desde, hasta, etiqueta_p)

    @staticmethod
    def _poner_detalle(chip: QFrame, texto: str):
        chip._detalle.setText(texto)
        chip._detalle.setVisible(bool(texto))

    def set_metricas(self, ganancia: float, inventario: float):
        self.set_ganancia(ganancia)
        self.set_inventario(inventario)

    def set_ganancia(self, ganancia):
        if ganancia is None:
            self.lbl_gan._valor.setText("Sin costo cargado")
            self._poner_detalle(self.lbl_gan, "Cargá precio de costo para firmarla")
            return
        self.lbl_gan._valor.setText(fmt_plata(ganancia))
        self._poner_detalle(self.lbl_gan, "")

    def set_inventario(self, inventario: float):
        self.lbl_inv._valor.setText(fmt_plata(inventario))

    def set_cuentas(self, pagos: float, deuda: float):
        self.lbl_pagos._valor.setText(fmt_plata(pagos))
        self.lbl_deuda._valor.setText(fmt_plata(deuda))

    def set_cobros_dia(self, redondeo: float, digitales_sin_firmar: int, digitales_total: int = 0):
        self.lbl_redondeo._valor.setText(fmt_plata(redondeo))
        sin = int(digitales_sin_firmar or 0)
        tot = int(digitales_total or 0)
        self.lbl_digitales._valor.setText(f"{sin} / {tot}" if tot else str(sin))

    def set_tickets_dia(self, cantidad: int, total: float):
        cantidad = int(cantidad or 0)
        self.lbl_tickets._valor.setText(f"{cantidad} · {fmt_plata(total)}")
        promedio = float(total or 0) / cantidad if cantidad else 0.0
        self._poner_detalle(self.lbl_tickets, f"Promedio {fmt_plata(promedio)}" if cantidad else "")

    def set_cancelaciones_dia(self, datos: dict):
        cant = int((datos or {}).get("cant") or 0)
        if not cant:
            self.lbl_cancel._valor.setText("0")
            self._poner_detalle(self.lbl_cancel, "")
            return
        self.lbl_cancel._valor.setText(f"{cant} · {fmt_plata(datos.get('monto') or 0)}")
        cuando = str(datos.get("cuando") or "")
        if self._es_hoy:
            cuando = cuando[11:16]
        elif len(cuando) >= 16:
            cuando = f"{_dia_corto(cuando)} {cuando[11:16]}"
        partes = [p for p in (cuando, datos.get("usuario")) if p]
        self._poner_detalle(self.lbl_cancel, "Última " + " · ".join(partes) if partes else "")

    def set_saludo(self, texto: str):
        self.lbl_saludo.setText(texto)

    def set_origen(self, texto: str):
        """Franja ámbar: sin maestra, de cuándo es la copia que se está viendo. Vacío = en vivo."""
        self.lbl_origen.setText(texto)
        self.lbl_origen.setVisible(bool(texto))

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
