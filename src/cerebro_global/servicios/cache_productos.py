"""
cache_productos.py - Servicio de caché en memoria de productos.

PROPÓSITO: Eliminar las queries repetidas a la base de datos durante el scroll
de la grilla de cartelería. En PCs viejas con HDD lento, cada query a MariaDB
puede tardar 20-80ms. Con 200+ productos y refresh cada 30s, esto genera
carga innecesaria que se nota como "trabada" del scroll.

USO:
    from src.cerebro_global.servicios.cache_productos import cache_productos

    productos = cache_productos.obtener_todos()
    producto = cache_productos.obtener_por_id(123)
    cache_productos.invalidar()  # fuerza recarga en el próximo acceso
"""

import threading
import time
import logging

logger = logging.getLogger(__name__)

_NOMBRES_CARTELERIA_EXCLUIDOS = ("articulo comun", "artículo común", "venta libre")


def _nombre_excluido_carteleria(nombre) -> bool:
    n = str(nombre or "").strip().lower()
    return any(x in n for x in _NOMBRES_CARTELERIA_EXCLUIDOS)


class CacheProductos:
    """
    Caché en memoria para el catálogo de productos.
    Thread-safe. TTL configurable (default: 30 segundos).
    """

    def __init__(self, ttl_segundos: int = 30):
        self._datos: list = []
        self._indice_id: dict = {}
        self._indice_nombre: dict = {}
        self._ultimo_refresh: float = 0.0
        self._ttl = ttl_segundos
        self._lock = threading.Lock()
        self._valido = False

    def _necesita_refresh(self) -> bool:
        return not self._valido or (time.time() - self._ultimo_refresh) > self._ttl

    def _cargar_desde_db(self):
        """Carga todos los productos de la BD en memoria."""
        try:
            from src.base_de_datos.database import db_manager
            rows = db_manager.execute_query(
                "SELECT id, nombre, precio, costo, stock, cant_oferta, precio_oferta, "
                "cant_mayoreo, precio_mayoreo, precio_oferta_relampago, precio_oferta_promedio, "
                "departamento, categoria, unidad, es_pesable, codigo, tipo_unidad_oferta "
                "FROM productos ORDER BY departamento, nombre"
            ) or []
            self._datos = rows
            self._indice_id = {str(r['id']): r for r in rows}
            self._indice_nombre = {}
            for r in rows:
                nom = str(r.get('nombre') or '').strip().lower()
                if nom:
                    self._indice_nombre.setdefault(nom, r)
            self._ultimo_refresh = time.time()
            self._valido = True
            logger.debug(f"[CacheProductos] Recargados {len(rows)} productos en memoria.")
        except Exception as e:
            logger.error(f"[CacheProductos] Error cargando desde DB: {e}")

    def obtener_todos(self) -> list:
        """Devuelve todos los productos. Recarga de DB si el caché expiró."""
        with self._lock:
            if self._necesita_refresh():
                self._cargar_desde_db()
            return self._datos

    def obtener_por_id(self, id_producto) -> dict | None:
        """Devuelve un producto por ID. O(1) gracias al índice."""
        with self._lock:
            if self._necesita_refresh():
                self._cargar_desde_db()
            return self._indice_id.get(str(id_producto))

    def obtener_por_departamento(self, departamento: str) -> list:
        """Devuelve todos los productos de un departamento específico."""
        return [p for p in self.obtener_todos()
                if str(p.get('departamento', '')).upper() == departamento.upper()]

    def obtener_en_oferta(self) -> list:
        """Devuelve productos con oferta activa (cant_oferta > 0 y precio_oferta > 0)."""
        return [p for p in self.obtener_todos()
                if float(p.get('cant_oferta') or 0) > 0 and float(p.get('precio_oferta') or 0) > 0]

    def obtener_con_mayoreo(self) -> list:
        """Devuelve productos con precio mayoreo configurado."""
        return [p for p in self.obtener_todos()
                if float(p.get('cant_mayoreo') or 0) > 0 and float(p.get('precio_mayoreo') or 0) > 0]

    def obtener_indice_nombre(self) -> dict:
        """Índice nombre.lower() → fila de producto (evita JOIN LOWER en MariaDB)."""
        with self._lock:
            if self._necesita_refresh():
                self._cargar_desde_db()
            return self._indice_nombre

    def obtener_filas_sync_precios(self) -> list:
        """Catálogo con precio>0 para sync cartelería (sin escanear productos en cada hilo)."""
        filas = []
        for p in self.obtener_todos():
            if float(p.get('precio') or 0) <= 0:
                continue
            if _nombre_excluido_carteleria(p.get('nombre')):
                continue
            filas.append(p)
        filas.sort(key=lambda r: str(r.get('categoria') or ''))
        return filas

    def obtener_ofertas_relampago(self, limit: int = 50) -> list:
        """Productos SOS ordenados por precio_oferta_relampago (sin query pesada concurrente)."""
        cand = []
        for p in self.obtener_todos():
            rel = float(p.get('precio_oferta_relampago') or 0)
            if rel <= 0:
                continue
            precio = float(p.get('precio') or 0)
            precio_of = float(p.get('precio_oferta') or 0)
            if precio <= 0 and precio_of <= 0:
                continue
            if _nombre_excluido_carteleria(p.get('nombre')):
                continue
            cand.append(p)
        cand.sort(key=lambda r: float(r.get('precio_oferta_relampago') or 0), reverse=True)
        return cand[:limit]

    def obtener_filas_fallback_top(self, limit: int = 50) -> list:
        """Fallback top ventas: precio>0 ordenado por nombre (muestreo en Python)."""
        cand = [
            p for p in self.obtener_todos()
            if float(p.get('precio') or 0) > 0 and not _nombre_excluido_carteleria(p.get('nombre'))
        ]
        cand.sort(key=lambda r: str(r.get('nombre') or '').lower())
        return cand[:limit]

    def invalidar(self):
        """Fuerza recarga en el próximo acceso (llamar después de editar un producto)."""
        with self._lock:
            self._valido = False
            self._indice_nombre = {}
        logger.debug("[CacheProductos] Caché invalidado.")

    def actualizar_producto(self, id_producto, nuevos_datos: dict):
        """Actualización parcial sin recargar todo el caché."""
        with self._lock:
            pid = str(id_producto)
            if pid in self._indice_id:
                self._indice_id[pid].update(nuevos_datos)
                # Sincronizar en la lista también
                for i, p in enumerate(self._datos):
                    if str(p['id']) == pid:
                        self._datos[i] = self._indice_id[pid]
                        break

    @property
    def esta_calido(self) -> bool:
        """True si el caché tiene datos y no ha expirado."""
        return self._valido and not self._necesita_refresh()

    @property
    def total_productos(self) -> int:
        return len(self._datos)


# Instancia global singleton para usar en todo el sistema
cache_productos = CacheProductos(ttl_segundos=30)
