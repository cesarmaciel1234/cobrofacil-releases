"""Tablas del nodo. La cola se mira; no se reenvía desde acá."""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.central_red_global.servidor.ventana.consola import _Puente, _Senal
from src.central_red_global.servidor.ventana.grilla import Grilla
from src.central_red_global.servidor.ventana.presencia import arrancar as arrancar_presencia
from src.central_red_global.servidor.ventana.presencia import foto as foto_presencia
from src.central_red_global.servidor.ventana.vigia import (
    acortar,
    canal,
    catalogo,
    filas_auditoria,
    filas_cambios,
    filas_tickets,
)

_ENGANCHADO = False


class _Listo(QObject):
    paquete = pyqtSignal(object)


def _titulo(texto: str) -> QLabel:
    etiqueta = QLabel(texto)
    etiqueta.setStyleSheet("font-size: 11px; font-weight: 700; color: #94A3B8;")
    return etiqueta


class Tablero(QWidget):
    """Catálogo de la base, cola de tickets, cola de cambios y bitácora."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TableroNodo")
        self.setAutoFillBackground(True)
        self._senal = _Senal(self)
        self._senal.lista.connect(self._desde_log)
        self._antes_tickets: int | None = None
        self._antes_cambios: int | None = None
        self._firma_tickets: tuple | None = None
        self._firma_cambios: tuple | None = None
        self._firma_local: tuple | None = None
        self._firma_replica: tuple | None = None
        self._firma_auditoria: tuple | None = None
        self._visto_red: dict[str, float] = {}
        self._ocupado = False
        self._listo = _Listo(self)
        self._listo.paquete.connect(self._aplicar)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        self.chip_tickets = self._chip("tickets …")
        self.chip_cambios = self._chip("cambios …")
        self.chip_local = self._chip("punpro.db …")
        self.chip_replica = self._chip("réplica …")
        self.chip_auditoria = self._chip("auditoría …")
        for chip in (
            self.chip_tickets,
            self.chip_cambios,
            self.chip_local,
            self.chip_replica,
            self.chip_auditoria,
        ):
            chips.addWidget(chip)
        chips.addStretch()
        lay.addLayout(chips)

        red = QHBoxLayout()
        red.setSpacing(8)
        self.lbl_linea = QLabel("maestra …")
        self.lbl_linea.setStyleSheet(self._estilo_linea(False))
        self.lbl_pcs = QLabel("conexiones …")
        self.lbl_pcs.setWordWrap(True)
        self.lbl_pcs.setStyleSheet("font-size: 12px; font-weight: 600; color: #E2E8F0;")
        red.addWidget(self.lbl_linea)
        red.addWidget(self.lbl_pcs, 1)
        lay.addLayout(red)

        grilla = QGridLayout()
        grilla.setHorizontalSpacing(14)
        grilla.setVerticalSpacing(14)

        self.lbl_local = _titulo("punpro.db  ·  base local")
        self.local = Grilla(["tabla", "filas"])
        caja_local = self._caja(self.lbl_local, self.local, "#38BDF8")

        self.lbl_replica = _titulo("espejo_tienda.db  ·  réplica")
        self.replica = Grilla(["tabla", "filas"])
        caja_replica = self._caja(self.lbl_replica, self.replica, "#34D399")

        self.lbl_tickets = _titulo("cola_tickets")
        self.tickets = Grilla(["hora", "total", "pago", "detalle", "estado"])
        caja_tickets = self._caja(self.lbl_tickets, self.tickets, "#FBBF24")

        self.lbl_cambios = _titulo("cola_cambios")
        self.cambios = Grilla(["hora", "tipo", "nombre", "valor", "estado"])
        caja_cambios = self._caja(self.lbl_cambios, self.cambios, "#C4B5FD")

        self.lbl_bitacora = _titulo("bitácora")
        self.bitacora = Grilla(["hora", "canal", "evento"])
        caja_bitacora = self._caja(self.lbl_bitacora, self.bitacora, "#94A3B8")

        self.lbl_auditoria = _titulo("auditoría de stock")
        self.auditoria = Grilla(["hora", "producto", "conteo", "quien", "origen"])
        caja_auditoria = self._caja(self.lbl_auditoria, self.auditoria, "#FB7185")

        grilla.addWidget(caja_local, 0, 0)
        grilla.addWidget(caja_replica, 0, 1)
        grilla.addWidget(caja_tickets, 1, 0)
        grilla.addWidget(caja_cambios, 1, 1)
        grilla.addWidget(caja_bitacora, 2, 0)
        grilla.addWidget(caja_auditoria, 2, 1)
        grilla.setColumnStretch(0, 1)
        grilla.setColumnStretch(1, 1)
        grilla.setRowStretch(0, 2)
        grilla.setRowStretch(1, 3)
        grilla.setRowStretch(2, 2)
        lay.addLayout(grilla, 1)

        self._reloj = QTimer(self)
        self._reloj.setInterval(3000)
        self._reloj.timeout.connect(self.mirar)
        self._reloj.start()
        arrancar_presencia()
        QTimer.singleShot(200, self.mirar)

    @staticmethod
    def _estilo_linea(en_linea: bool) -> str:
        if en_linea:
            return (
                "font-size: 12px; font-weight: 700; color: #86EFAC; "
                "background: #052E16; border: 1px solid #166534; "
                "border-radius: 8px; padding: 4px 10px;"
            )
        return (
            "font-size: 12px; font-weight: 700; color: #FCA5A5; "
            "background: #450A0A; border: 1px solid #991B1B; "
            "border-radius: 8px; padding: 4px 10px;"
        )

    def _pintar_red(self, red: dict) -> None:
        en_linea = bool(red.get("en_linea"))
        destino = str(red.get("destino") or "").strip()
        estado = "en línea" if en_linea else "desconectada"
        donde = f"  ·  {destino}" if destino and not red.get("es_maestra") else ""
        self.lbl_linea.setText(f"Maestra {estado}{donde}")
        self.lbl_linea.setStyleSheet(self._estilo_linea(en_linea))
        pcs = [nombre for nombre, _rol in (red.get("pcs") or []) if nombre]
        if pcs:
            self.lbl_pcs.setText("Conexiones entrantes  ·  " + "  ·  ".join(pcs))
        else:
            self.lbl_pcs.setText("Conexiones entrantes  ·  ninguna")

    def _chip(self, texto: str) -> QLabel:
        etiqueta = QLabel(texto)
        etiqueta.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #E2E8F0; "
            "background: #1E293B; border: 1px solid #334155; "
            "border-radius: 8px; padding: 4px 8px;"
        )
        return etiqueta

    def _caja(self, titulo: QLabel, tabla: Grilla, acento: str) -> QFrame:
        caja = QFrame()
        caja.setObjectName("CajaNodo")
        caja.setStyleSheet(
            "QFrame#CajaNodo {"
            "background: #0F172A;"
            "border: 2px solid #64748B;"
            "border-radius: 10px;"
            "}"
        )
        lay = QVBoxLayout(caja)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setSpacing(6)
        marca = QFrame()
        marca.setFixedHeight(3)
        marca.setStyleSheet(f"background: {acento}; border: none; border-radius: 2px;")
        lay.addWidget(marca)
        lay.addWidget(titulo)
        lay.addWidget(tabla, 1)
        return caja

    def pausar(self) -> None:
        """Al cerrar u ocultar: no sigue contando filas en la base."""
        self._reloj.stop()

    def reanudar(self) -> None:
        if not self._reloj.isActive():
            self._reloj.start()
        self.mirar()

    def escribir(self, texto: str, nivel: int = logging.INFO) -> None:
        self._anotar("red", texto, nivel)

    def enganchar(self) -> None:
        global _ENGANCHADO
        if _ENGANCHADO:
            return
        _ENGANCHADO = True
        puente = _Puente(self._senal)
        raiz = logging.getLogger()
        if raiz.level == logging.NOTSET or raiz.level > logging.INFO:
            raiz.setLevel(logging.INFO)
        raiz.addHandler(puente)

    def _anotar(self, nombre: str, texto: str, nivel: int) -> None:
        hora = datetime.now().strftime("%H:%M:%S")
        marca = "WARN" if nivel >= logging.WARNING else "INFO"
        if nivel >= logging.ERROR:
            marca = "ERROR"
        self.bitacora.agregar((hora, f"{nombre} {marca}", texto))

    def _desde_log(self, nivel: int, texto: str) -> None:
        corto = acortar(texto)
        if not corto:
            return
        destino = canal(corto)
        if destino == "red":
            ahora = time.time()
            if ahora - self._visto_red.get(corto, 0) < 30:
                return
            self._visto_red[corto] = ahora
        self._anotar(destino, corto, nivel)

    def mirar(self) -> None:
        if self._ocupado or not self._reloj.isActive():
            return
        self._ocupado = True

        def _leer():
            try:
                paquete = (
                    filas_tickets(),
                    filas_cambios(),
                    catalogo(),
                    filas_auditoria(),
                    foto_presencia(),
                )
            except Exception:
                paquete = None
            try:
                self._listo.paquete.emit(paquete)
            except RuntimeError:
                return

        threading.Thread(target=_leer, name="ventana-base", daemon=True).start()

    def _aplicar(self, paquete) -> None:
        self._ocupado = False
        if not paquete or not self.isVisible():
            return
        (n_tickets, filas_t), (n_cambios, filas_c), (local, n_local, replica, n_replica), (
            n_auditoria,
            filas_a,
        ), red = paquete
        firma_t = (n_tickets, tuple(filas_t))
        if firma_t != self._firma_tickets:
            self.tickets.poner(filas_t)
            if self._antes_tickets is not None and n_tickets < self._antes_tickets:
                self._anotar(
                    "tickets",
                    f"la maestra recibió {self._antes_tickets - n_tickets}",
                    logging.INFO,
                )
            self._firma_tickets = firma_t
            self._antes_tickets = n_tickets
            self.lbl_tickets.setText(f"cola_tickets  ·  {n_tickets} filas")
        firma_c = (n_cambios, tuple(filas_c))
        if firma_c != self._firma_cambios:
            self.cambios.poner(filas_c)
            if self._antes_cambios is not None and n_cambios < self._antes_cambios:
                self._anotar(
                    "cambios",
                    f"la maestra recibió {self._antes_cambios - n_cambios} cambios",
                    logging.INFO,
                )
            self._firma_cambios = firma_c
            self._antes_cambios = n_cambios
            self.lbl_cambios.setText(f"cola_cambios  ·  {n_cambios} filas")
        firma_a = (n_auditoria, tuple(filas_a))
        if firma_a != self._firma_auditoria:
            if self._firma_auditoria is not None:
                previas = set(self._firma_auditoria[1])
                for fila in filas_a:
                    if fila not in previas:
                        self._anotar("auditoría", f"{fila[1]}  {fila[2]}  {fila[4]}", logging.INFO)
            self.auditoria.poner(filas_a or [("sin conteos", "—", "—", "—", "—")])
            self._firma_auditoria = firma_a
            self.lbl_auditoria.setText(f"auditoría de stock  ·  {n_auditoria}")
        firma_l = tuple(local)
        if firma_l != self._firma_local:
            self.local.poner(local or [("sin archivo", "—")])
            self._firma_local = firma_l
            self.lbl_local.setText(
                f"punpro.db  ·  {len(local)} de {n_local} tablas, las más grandes"
            )
        firma_r = tuple(replica)
        if firma_r != self._firma_replica:
            self.replica.poner(replica or [("sin réplica", "—")])
            self._firma_replica = firma_r
            self.lbl_replica.setText(
                f"espejo_tienda.db  ·  {len(replica)} de {n_replica} tablas, las más grandes"
                if n_replica
                else "espejo_tienda.db  ·  sin réplica"
            )
        self.chip_tickets.setText(f"{n_tickets} tickets")
        self.chip_cambios.setText(f"{n_cambios} cambios")
        self.chip_local.setText(f"punpro.db  {n_local} tablas")
        self.chip_replica.setText(
            f"réplica  {n_replica} tablas" if n_replica else "réplica ausente"
        )
        self.chip_auditoria.setText(f"{n_auditoria} auditorías")
        self._pintar_red(red if isinstance(red, dict) else {})
