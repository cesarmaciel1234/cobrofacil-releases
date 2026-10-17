"""Arma columnas en hilo. Si el motor falla, lista simple. Nunca emite vacío si hay precios."""

import logging

from PyQt6.QtCore import QThread, QTimer, pyqtSignal

logger = logging.getLogger("LanzadorDirectoTV")


def paneles_vacios():
    return {
        "hero": None,
        "destacados": [],
        "rotacion": [],
        "combos": [],
        "columna3": [],
        "ia": [],
    }


def paneles_fallback(productos):
    vivos = [p for p in (productos or []) if p.get("nombre") and (p.get("precio") or 0) > 0]
    base = paneles_vacios()
    if not vivos:
        return base
    base["destacados"] = vivos[:8]
    base["rotacion"] = [
        {"id": "inventario", "titulo": "Tu lista", "subtitulo": "Inventario", "items": vivos[:10]}
    ]
    return base


class PanelesWorker(QThread):
    listo = pyqtSignal(dict)

    def __init__(self, productos, clima_icon, clima, ranking=None, parent=None):
        super().__init__(parent)
        self._productos = productos
        self._clima_icon = clima_icon
        self._clima = clima
        self._ranking = ranking or {}

    def run(self):
        try:
            from src.carteleria.motor_carteleria.estado_tv import armar_paneles

            paneles = armar_paneles(
                self._productos, self._clima_icon, self._clima, ranking_remoto=self._ranking
            )
            if not paneles or not (paneles.get("rotacion") or paneles.get("destacados")):
                paneles = paneles_fallback(self._productos)
            self.listo.emit({"paneles": paneles or paneles_fallback(self._productos), "precios": self._productos})
        except Exception:
            logger.exception("Error armando paneles — fallback")
            self.listo.emit({"paneles": paneles_fallback(self._productos), "precios": self._productos})


class PanelesMixin:
    def _paneles_vacios(self):
        self._paneles = paneles_vacios()

    def _refrescar_paneles(self, force=False):
        if not self.rows_precios:
            self._paneles_vacios()
            self._publicar_estado()
            return
        huella = self._huella_catalogo()
        if not force and huella == self._huella and self._paneles.get("rotacion"):
            self._publicar_estado()
            return
        if self._paneles_worker and self._paneles_worker.isRunning():
            self._publicar_estado()
            return
        self._huella = huella
        copia = [dict(p) for p in self.rows_precios]
        if self._paneles_worker is not None:
            try:
                self._paneles_worker.listo.disconnect(self._on_paneles_listos)
            except Exception:
                pass
        self._paneles_worker = PanelesWorker(
            copia, self._clima_icon, self._clima, self._ranking_remoto, self
        )
        self._paneles_worker.listo.connect(self._on_paneles_listos)
        self._paneles_worker.start()
        self._publicar_estado()

    def _on_paneles_listos(self, payload):
        if not self._vivo:
            return
        paneles = (payload or {}).get("paneles") if isinstance(payload, dict) else payload
        precios = (payload or {}).get("precios") if isinstance(payload, dict) else None
        if paneles:
            self._paneles = paneles
        else:
            logger.warning("Paneles vacíos — reintento en 2s, se conserva lo anterior")
            QTimer.singleShot(2000, lambda: self._refrescar_paneles(force=True))
        if precios:
            self.rows_precios = precios
        self._publicar_estado()
