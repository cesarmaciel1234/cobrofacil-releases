"""Timers de sync, sello, clima y watchdog. Un pulso vacío no borra la TV."""

import logging

from PyQt6.QtCore import QTimer

from src.carteleria.motor_carteleria.db_sync_worker import DbSyncWorker
from src.carteleria.motor_carteleria.clima_worker import ClimaWorker

logger = logging.getLogger("LanzadorDirectoTV")

SYNC_MS = 15_000
SELLO_MS = 1_000
CLIMA_MS = 15 * 60 * 1000


class MotoresMixin:
    def _iniciar_motores(self):
        try:
            if self._sync_worker is None:
                self._sync_worker = DbSyncWorker(self)
                self._sync_worker.sync_finished.connect(self._on_sync_finished)
            if self._clima_worker is None:
                self._clima_worker = ClimaWorker(self)
                self._clima_worker.clima_actualizado.connect(self._on_clima_actualizado)
            if self._sync_timer is None:
                self._sync_timer = QTimer(self)
                self._sync_timer.timeout.connect(self._sincronizar)
            if self._clima_timer is None:
                self._clima_timer = QTimer(self)
                self._clima_timer.timeout.connect(self._sincronizar_clima)
            if self._sello_timer is None:
                self._sello_timer = QTimer(self)
                self._sello_timer.timeout.connect(self._mirar_sello)
            if self._watch_timer is None:
                self._watch_timer = QTimer(self)
                self._watch_timer.timeout.connect(self._vigilar_navegador)
            self._sync_timer.start(SYNC_MS)
            self._sello_timer.start(SELLO_MS)
            self._watch_timer.start(3000)
            self._clima_timer.start(CLIMA_MS)
            self._sincronizar()
            self._sincronizar_clima()
        except Exception as e:
            logger.warning("Error iniciando motores: %s", e)
            QTimer.singleShot(3000, self._iniciar_motores)

    def _sincronizar(self):
        try:
            if self._sync_worker and not self._sync_worker.isRunning():
                self._sync_worker.start()
        except Exception as e:
            logger.warning("Sync no arrancó: %s", e)

    def _mirar_sello(self):
        try:
            from src.central_red_global.sync_tienda.aviso_tv import leer_sello
            import time

            marca = leer_sello()
        except Exception:
            return
        if not marca or marca == self._sello_visto:
            return
        ahora = time.monotonic()
        if ahora - self._ultimo_sync_mono < 2.0:
            return
        self._sello_visto = marca
        self._ultimo_sync_mono = ahora
        self._sincronizar()

    def _vigilar_navegador(self):
        if not self._vivo or not self._cuello:
            return
        try:
            if self._cuello.navegador_vivo():
                return
            logger.info("TV: el kiosk no está; abro una sola ventana en %s", self._cuello.url_tv())
            self._cuello.asegurar_navegador()
        except Exception as e:
            logger.warning("Watchdog TV: %s", e)

    def _sincronizar_clima(self):
        try:
            if self._clima_worker and not self._clima_worker.isRunning():
                self._clima_worker.start()
        except Exception:
            pass

    def _on_sync_finished(self, data, status):
        if not self._vivo:
            return
        try:
            data = data or {}
            productos = data.get("precios") or []
            if not productos:
                if status and not self.rows_precios:
                    self._sync_status = status
                    self._publicar_estado()
                logger.warning("Sync '%s' sin productos — se conserva el catálogo", status)
                if self.rows_precios:
                    return
                self._retry_count += 1
                delay = min(3000 * (2 ** min(self._retry_count, 4)), 30000)
                QTimer.singleShot(int(delay), self._sincronizar)
                return
            self._retry_count = 0
            self._sync_status = status or "online"
            try:
                from src.central_red_global.sync_tienda.ranking.desde_payload import asegurar_ranking
                from src.central_red_global.sync_tienda.rol import es_esclava, host_maestra

                if es_esclava():
                    data = asegurar_ranking(data, host_maestra())
            except Exception:
                pass
            self.sos_data = data.get("sos") or []
            self.top10_data = data.get("top10") or {}
            self._ranking_remoto = data.get("ranking") or {}
            try:
                from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad

                pub = data.get("publicidad")
                if pub is not None:
                    motor_publicidad.aplicar_remoto(pub)
            except Exception:
                pass
            self._aplicar_catalogo(productos)
            logger.info(
                "Sync %s: %s productos (rotacion=%s)",
                self._sync_status,
                len(self.rows_precios),
                len(self._paneles.get("rotacion") or []),
            )
        except Exception as e:
            logger.warning("Error procesando sync: %s", e, exc_info=True)
            self._publicar_estado()

    def _on_clima_actualizado(self, icon_name, text):
        if not self._vivo:
            return
        self._clima_icon = icon_name or "sol"
        self._clima = text
        if self.rows_precios:
            self._refrescar_paneles(force=True)
