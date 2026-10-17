"""Kiosk TV: mixins. No espera MariaDB. Un pulso vacío no borra la cara."""

from PyQt6.QtCore import QObject

from src.carteleria.lanzador_tv.directo.arranque.lanzar import ArranqueMixin
from src.carteleria.lanzador_tv.directo.cache_inicial.cargar import CacheInicialMixin
from src.carteleria.lanzador_tv.directo.catalogo.aplicar import CatalogoMixin
from src.carteleria.lanzador_tv.directo.estado.publicar import EstadoMixin
from src.carteleria.lanzador_tv.directo.motores.pulso import MotoresMixin
from src.carteleria.lanzador_tv.directo.paneles.hilo import PanelesMixin


class LanzadorDirectoTV(
    ArranqueMixin,
    CacheInicialMixin,
    MotoresMixin,
    CatalogoMixin,
    PanelesMixin,
    EstadoMixin,
    QObject,
):
    def __init__(self):
        super().__init__()
        self.screen_index = None
        self._cuello = None
        self._sync_worker = None
        self._clima_worker = None
        self._sync_timer = None
        self._sello_timer = None
        self._sello_visto = ""
        self._clima_timer = None
        self._sync_status = "offline"
        self._clima_icon = "sol"
        self._clima = ""
        self.rows_precios = []
        self.sos_data = []
        self.top10_data = {}
        self._ranking_remoto = {}
        self._paneles = {
            "hero": None,
            "destacados": [],
            "rotacion": [],
            "combos": [],
            "columna3": [],
            "ia": [],
        }
        self._state_cache = {"config": {"data_status": "offline"}, "precios": []}
        self._huella = ""
        self._vivo = False
        self._paneles_worker = None
        self.last_error = ""
        self._retry_count = 0
        self._max_retries = 10
        self._watch_timer = None
        self._ultimo_sync_mono = 0.0
        self._retry_timer = None


__all__ = ["LanzadorDirectoTV"]
