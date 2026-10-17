"""Abrir y cerrar Chrome kiosk. Esc no apaga. F11 sí."""

import logging

from PyQt6.QtCore import QTimer

logger = logging.getLogger("LanzadorDirectoTV")


class ArranqueMixin:
    def lanzar(self, screen_index=None):
        try:
            self.last_error = ""
            self._vivo = True
            self._retry_count = 0
            if screen_index is None:
                from src.carteleria.lanzador_tv.navegador_kiosk import indice_monitor_tv
                from src.config import config

                guardado = config.get("carteleria_tv_screen")
                screen_index = indice_monitor_tv() if guardado is None else int(guardado)
            self.screen_index = screen_index
            if self._cuello and self._cuello.httpd:
                self._cuello.screen_index = screen_index
                try:
                    self._cuello.asegurar_navegador()
                except Exception as e:
                    logger.warning("Reabrir Chrome: %s", e)
                try:
                    self._iniciar_motores()
                except Exception as e:
                    logger.warning("Motores al reusar TV: %s", e)
                self._recordar_tv(encendida=True)
                logger.info("TV ya estaba en %s — no se cerró el navegador", self._cuello.url_tv())
                return True
            from src.config import config
            from src.carteleria.lanzador_tv.cerebro_lanzador_tv import ServidorCuello

            puerto = int(config.get("carteleria_tv_port") or 8765)
            self._cuello = ServidorCuello(self, port=puerto)
            self._cargar_datos_iniciales()
            if not self._cuello.iniciar(screen_index=screen_index):
                self.last_error = getattr(self._cuello, "last_error", "") or (
                    "No se pudo iniciar el servidor de la TV."
                )
                logger.warning("Primer arranque HTTP falló; reintento una vez")
                if not self._cuello.iniciar(screen_index=screen_index):
                    self.detener()
                    return False
            QTimer.singleShot(50, self._iniciar_motores)
            self._recordar_tv(encendida=True)
            logger.info(
                "Cartelería TV en %s  (F10 monitor · F11 salir)",
                self._cuello.url_tv(),
            )
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error("Error lanzando cartelería directa: %s", e)
            return False

    def _recordar_tv(self, encendida: bool):
        try:
            from src.config import config

            config.data["carteleria_tv_encendida"] = bool(encendida)
            if self._cuello and self._cuello.port:
                config.data["carteleria_tv_port"] = int(self._cuello.port)
            if self.screen_index is not None:
                config.data["carteleria_tv_screen"] = int(self.screen_index)
            config.save()
        except Exception:
            pass

    def detener(self):
        try:
            self._vivo = False
            for timer in (
                self._sync_timer,
                self._sello_timer,
                self._watch_timer,
                self._clima_timer,
                self._retry_timer,
            ):
                if timer:
                    timer.stop()
            if self._sync_worker and self._sync_worker.isRunning():
                self._sync_worker.requestInterruption()
            if self._clima_worker and self._clima_worker.isRunning():
                self._clima_worker.requestInterruption()
            if self._cuello:
                self._cuello.detener()
                self._cuello = None
            logger.info("Cartelería TV directa detenida")
        except Exception as e:
            logger.error("Error deteniendo cartelería: %s", e)

    def on_tv_control(self, action):
        action = str(action or "").strip().lower()
        QTimer.singleShot(0, lambda a=action: self._on_tv_control_main(a))

    def _on_tv_control_main(self, action):
        if action in ("stop", "f11"):
            self._recordar_tv(encendida=False)
            self.detener()
        elif action in ("esc",):
            return
        elif action in ("monitor", "f10"):
            self._handle_f10()

    def _handle_f10(self):
        logger.info("F10 presionado - cambiando monitor")
        try:
            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance()
            n = len(app.screens()) if app else 1
        except Exception:
            n = 1
        self.screen_index = ((self.screen_index or 0) + 1) % max(n, 1)
        if self._cuello:
            try:
                self._cuello.reubicar(self.screen_index)
                self._recordar_tv(encendida=True)
            except Exception as e:
                logger.warning("F10 reubicar: %s", e)
