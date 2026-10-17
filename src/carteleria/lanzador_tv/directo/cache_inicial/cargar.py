"""Primera pintura: solo carteleria_cache.json. MariaDB va en el pulso."""

import logging

logger = logging.getLogger("LanzadorDirectoTV")


class CacheInicialMixin:
    def _cargar_datos_iniciales(self):
        try:
            from src.carteleria.vitrina.red.cache import leer_cache

            data = leer_cache() or {}
            productos = data.get("precios") or []
            self._sync_status = "offline"
            if not productos:
                logger.info("Sin caché; Chrome abre y el pulso llena en hilo")
                self._publicar_estado()
                return
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
            logger.info("TV desde caché: %s productos", len(self.rows_precios))
        except Exception as e:
            logger.error("Caché inicial: %s", e, exc_info=True)
            try:
                self._publicar_estado()
            except Exception:
                pass
