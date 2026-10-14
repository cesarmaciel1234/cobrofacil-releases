"""Cara izquierda del panel jefe. Pinta KPIs. No muestra ofertas."""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from src.jefe.reportes.financiero.dinero import fmt_plata
from src.jefe.reportes.letra import etiqueta, fuente_limpia

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
    periodo_cambiado = pyqtSignal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelPublicidad")
        self.setFont(fuente_limpia(13))
        self._es_hoy = False
        self._periodo_btn = "Mes"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        self.lbl_saludo = etiqueta("Buenos dias", 22)
        self.lbl_saludo.setStyleSheet(
            "color: #0F172A; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        self.lbl_sub = etiqueta("Vitrina de tienda · Mes", 12)
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
            b.setStyleSheet(_BTN_ACTIVO if texto == "Mes" else _BTN_IDLE)
            b.clicked.connect(lambda _c=False, t=texto: self._elegir_periodo(t))
            fila_sub.addWidget(b)
            self._botones_periodo[texto] = b
        root.addLayout(fila_sub)

        self.lbl_origen = etiqueta("", 11)
        self.lbl_origen.setStyleSheet(
            "color: #9A3412; background: #FFF7ED; border: 1px solid #FFEDD5; "
            "border-left: 5px solid #F97316; border-radius: 6px; "
            "padding: 8px 14px; font-weight: 500; letter-spacing: 0px;"
        )
        self.lbl_origen.setVisible(False)
        root.addWidget(self.lbl_origen)

        kpis = QHBoxLayout()
        kpis.setSpacing(10)
        self.lbl_gan = self._chip("Ganancia · Mes", "—")
        self.lbl_inv = self._chip("Inventario al costo", "—")
        kpis.addWidget(self.lbl_gan, 1)
        kpis.addWidget(self.lbl_inv, 1)
        root.addLayout(kpis)

        cuentas = QHBoxLayout()
        cuentas.setSpacing(10)
        self.lbl_pagos = self._chip("Pagos clientes · Mes", "—")
        self.lbl_deuda = self._chip("Deuda clientes", "—")
        cuentas.addWidget(self.lbl_pagos, 1)
        cuentas.addWidget(self.lbl_deuda, 1)
        root.addLayout(cuentas)

        digitales = QHBoxLayout()
        digitales.setSpacing(10)
        self.lbl_tickets_dig = self._chip("Tickets digitales · Mes", "—")
        self.lbl_cliente = self._chip("Cliente · Mes", "—")
        digitales.addWidget(self.lbl_tickets_dig, 1)
        digitales.addWidget(self.lbl_cliente, 1)
        root.addLayout(digitales)

        extras = QHBoxLayout()
        extras.setSpacing(10)
        self.lbl_sin_firmar = self._chip("Sin firmar / F9 · Mes", "—")
        self.lbl_redondeo = self._chip("Redondeo · Mes", "—")
        extras.addWidget(self.lbl_sin_firmar, 1)
        extras.addWidget(self.lbl_redondeo, 1)
        root.addLayout(extras)

        caja = QHBoxLayout()
        caja.setSpacing(10)
        self.lbl_tickets = self._chip("Tickets · Mes", "—")
        self.lbl_cancel = self._chip("Cancelaciones · Mes", "—")
        caja.addWidget(self.lbl_tickets, 1)
        caja.addWidget(self.lbl_cancel, 1)
        root.addLayout(caja)

        self._periodales = (
            (self.lbl_gan, "Ganancia parcial", "Ganancia"),
            (self.lbl_pagos, "Pagos clientes", "Pagos clientes"),
            (self.lbl_tickets_dig, "Tickets digitales", "Tickets digitales"),
            (self.lbl_cliente, "Cliente", "Cliente"),
            (self.lbl_sin_firmar, "Sin firmar / F9", "Sin firmar / F9"),
            (self.lbl_redondeo, "Redondeo del día", "Redondeo"),
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

        huecos = QGridLayout()
        huecos.setSpacing(10)
        huecos.setRowStretch(0, 1)
        huecos.setRowStretch(1, 1)
        huecos.setColumnStretch(0, 1)
        huecos.setColumnStretch(1, 1)
        for i in range(4):
            huecos.addWidget(self._hueco(), i // 2, i % 2)
        root.addLayout(huecos, 1)

        QTimer.singleShot(0, lambda: self._elegir_periodo("Mes"))

    def _hueco(self) -> QFrame:
        f = QFrame()
        f.setMinimumHeight(88)
        f.setStyleSheet(
            "QFrame { background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 12px; }"
        )
        lay = QVBoxLayout(f)
        lay.setContentsMargins(14, 12, 14, 12)
        t = etiqueta("Reservado", 11)
        t.setStyleSheet(
            "color: #94A3B8; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        v = etiqueta("—", 16)
        v.setStyleSheet(
            "color: #CBD5E1; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        d = etiqueta("Espacio para una tarjeta", 10)
        d.setStyleSheet(
            "color: #CBD5E1; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        lay.addWidget(t)
        lay.addWidget(v)
        lay.addWidget(d)
        lay.addStretch()
        return f

    def _chip(self, titulo: str, valor: str) -> QFrame:
        f = QFrame()
        f.setMinimumHeight(96)
        f.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        f.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }"
        )
        lay = QVBoxLayout(f)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(4)
        t = etiqueta(titulo, 11)
        t.setStyleSheet(
            "color: #64748B; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        v = etiqueta(valor, 16)
        v.setWordWrap(False)
        v.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        v.setStyleSheet(
            "color: #0F172A; background: transparent; border: none; "
            "font-weight: 500; letter-spacing: 0px;"
        )
        d = etiqueta("", 10)
        d.setStyleSheet(
            "color: #94A3B8; background: transparent; border: none; "
            "font-weight: 400; letter-spacing: 0px;"
        )
        d.hide()
        fila = QHBoxLayout()
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(12)
        fila.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        fila.addWidget(v, 1)
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(22)
        sep.setStyleSheet("background: #E2E8F0; border: none;")
        sep.hide()
        fila.addWidget(sep, 0, Qt.AlignmentFlag.AlignVCenter)
        r = etiqueta("", 18)
        r.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        r.setStyleSheet(
            "color: #B45309; background: transparent; border: none; "
            "font-weight: 600; letter-spacing: 0px;"
        )
        r.hide()
        fila.addWidget(r, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(t)
        lay.addLayout(fila, 1)
        lay.addWidget(d)
        f._titulo = t
        f._valor = v
        f._sep = sep
        f._ratio = r
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

    def set_cobros_dia(
        self,
        redondeo: float,
        digitales_sin_firmar: int,
        digitales_total: int = 0,
        cuenta_dni: int = 0,
        mp_sin_ticket: int = 0,
        tickets_digitales: float = 0,
        cliente: float = 0,
        sin_firmar_monto: float = 0,
        firmados: float = 0,
    ):
        self.lbl_redondeo._valor.setText(fmt_plata(redondeo))
        self.lbl_tickets_dig._valor.setText(fmt_plata(tickets_digitales))
        self._poner_detalle(
            self.lbl_tickets_dig,
            f"Firmados {fmt_plata(firmados)}" if firmados else "",
        )
        self.lbl_cliente._valor.setText(fmt_plata(cliente))
        self._poner_detalle(self.lbl_cliente, "Cobranza QR / tarjeta / transferencia")
        self.lbl_sin_firmar._valor.setText(fmt_plata(sin_firmar_monto))
        sin_n = int(digitales_sin_firmar or 0)
        tot_n = int(digitales_total or 0)
        self.lbl_sin_firmar._ratio.setText(f"{sin_n} / {tot_n}")
        self.lbl_sin_firmar._ratio.show()
        self.lbl_sin_firmar._sep.show()
        if tot_n:
            self._poner_detalle(
                self.lbl_sin_firmar,
                f"{sin_n} tickets no firmados de {tot_n}",
            )
        else:
            self._poner_detalle(self.lbl_sin_firmar, "")

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
        self.lbl_origen.setText(texto)
        self.lbl_origen.setVisible(bool(texto))

    def refrescar_vitrina(self):
        return
