"""
Caché de catálogo para TV y motores.

Reglas: nunca lanza hacia afuera; si la BD falla, sigue sirviendo lo último;
un solo refresh a la vez.
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)


def _fila_dict(row) -> dict:
    if isinstance(row, dict):
        return dict(row)
    try:
        return dict(row)
    except Exception:
        return {}


def _num(v, default=0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


class CacheProductos:
    def __init__(self, ttl_segundos: int = 60, backoff_segundos: float = 8.0):
        self._datos: list = []
        self._indice_id: dict = {}
        self._ultimo_refresh: float = 0.0
        self._ttl = max(5, int(ttl_segundos))
        self._backoff = max(2.0, float(backoff_segundos))
        self._lock = threading.Lock()
        self._valido = False
        self._refreshing = False
        self._fallos = 0

    def _necesita_refresh(self) -> bool:
        if self._refreshing:
            return False
        if not self._valido:
            if self._fallos:
                espera = min(self._backoff * (2 ** (self._fallos - 1)), 120)
                return (time.time() - self._ultimo_refresh) >= espera
            return True
        return (time.time() - self._ultimo_refresh) >= self._ttl

    def _fetch_rows(self) -> list:
        from src.base_de_datos.database import db_manager

        rows = db_manager.execute_query(
            "SELECT id, nombre, precio, costo, stock, cant_oferta, precio_oferta, "
            "cant_mayoreo, precio_mayoreo, precio_oferta_relampago, precio_oferta_promedio, "
            "departamento, categoria, unidad, es_pesable, codigo "
            "FROM productos ORDER BY departamento, nombre"
        ) or []
        out = []
        for r in rows:
            d = _fila_dict(r)
            if d.get("id") is not None:
                out.append(d)
        return out

    def _aplicar(self, rows: list) -> None:
        self._datos = rows
        self._indice_id = {str(r.get("id")): r for r in rows}
        self._ultimo_refresh = time.time()
        self._valido = True
        self._fallos = 0

    def _refrescar_si_hace_falta(self) -> None:
        with self._lock:
            if not self._necesita_refresh():
                return
            self._refreshing = True
        try:
            rows = self._fetch_rows()
            with self._lock:
                self._aplicar(rows)
        except Exception as e:
            logger.warning("[CacheProductos] BD no disponible, se mantiene caché: %s", e)
            with self._lock:
                self._fallos = min(self._fallos + 1, 8)
                self._ultimo_refresh = time.time()
                if self._datos:
                    self._valido = True
        finally:
            with self._lock:
                self._refreshing = False

    def obtener_todos(self) -> list:
        try:
            self._refrescar_si_hace_falta()
            with self._lock:
                return [dict(p) for p in self._datos]
        except Exception:
            logger.exception("[CacheProductos] obtener_todos")
            return []

    def obtener_por_id(self, id_producto) -> dict | None:
        try:
            if id_producto is None:
                return None
            self._refrescar_si_hace_falta()
            with self._lock:
                hit = self._indice_id.get(str(id_producto))
                return dict(hit) if hit else None
        except Exception:
            logger.exception("[CacheProductos] obtener_por_id")
            return None

    def obtener_por_departamento(self, departamento: str) -> list:
        clave = str(departamento or "").upper()
        return [
            p for p in self.obtener_todos()
            if str(p.get("departamento") or "").upper() == clave
        ]

    def obtener_en_oferta(self) -> list:
        return [
            p for p in self.obtener_todos()
            if _num(p.get("cant_oferta")) > 0 and _num(p.get("precio_oferta")) > 0
        ]

    def obtener_con_mayoreo(self) -> list:
        return [
            p for p in self.obtener_todos()
            if _num(p.get("cant_mayoreo")) > 0 and _num(p.get("precio_mayoreo")) > 0
        ]

    def invalidar(self):
        try:
            with self._lock:
                self._valido = False
                self._fallos = 0
        except Exception:
            pass

    def actualizar_producto(self, id_producto, nuevos_datos: dict):
        try:
            if not nuevos_datos:
                return
            with self._lock:
                pid = str(id_producto)
                if pid not in self._indice_id:
                    self._valido = False
                    return
                self._indice_id[pid].update(nuevos_datos)
                for i, p in enumerate(self._datos):
                    if str(p.get("id")) == pid:
                        self._datos[i] = self._indice_id[pid]
                        break
        except Exception:
            logger.exception("[CacheProductos] actualizar_producto")
            self.invalidar()

    @property
    def esta_calido(self) -> bool:
        with self._lock:
            return bool(self._valido and self._datos and not self._necesita_refresh())

    @property
    def total_productos(self) -> int:
        with self._lock:
            return len(self._datos)


cache_productos = CacheProductos(ttl_segundos=60)
