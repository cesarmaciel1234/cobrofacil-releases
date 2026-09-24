from src.base_de_datos.database import db_manager

class StockOfertasService:
    def stock_disponible(self, p, p_id):
        """Calcula el stock real en base de datos para un producto, o infinito si es servicio/artículo común."""
        if p_id == "000": return float('inf')

        # En el futuro, aquí se consultaría la BD en tiempo real para evitar condiciones de carrera,
        # pero por rendimiento en cajas, se usa el stock del diccionario provisto si está actualizado.
        try:
            return float(p['stock'] or 0.0)
        except:
            return 0.0

    def obtener_stock_db(self, p_id):
        res = db_manager.execute_query("SELECT stock FROM productos WHERE id=?", (p_id,))
        return float(res[0]["stock"] or 0) if res else 0.0

    def get_stock_critico_count(self):
        query = "SELECT COUNT(*) FROM productos WHERE stock <= stock_minimo AND stock_minimo > 0"
        return db_manager.execute_scalar(query) or 0

    def obtener_producto_para_refresh(self, p_id):
        res = db_manager.execute_query("SELECT nombre, precio, cant_oferta, precio_oferta, cant_mayoreo, precio_mayoreo FROM productos WHERE id=?", (p_id,))
        return res[0] if res else None

    def obtener_ofertas_producto(self, p_id):
        res = db_manager.execute_query("SELECT precio, cant_oferta, precio_oferta, cant_mayoreo, precio_mayoreo FROM productos WHERE id=?", (p_id,))
        return res[0] if res else None

    def obtener_combos(self):
        """Lista cruda de combos. Se recuerda 15 s para no pegarle a la base en cada escaneo."""
        self._combos_recordados()
        return self._combos_cache[1]

    def combos_para_ticket(self):
        """Combos ya leídos del JSON. El ticket no vuelve a parsear en cada producto."""
        self._combos_recordados()
        return self._combos_cache[2]

    def _combos_recordados(self):
        import json
        import time
        ahora = time.monotonic()
        cache = getattr(self, "_combos_cache", None)
        if cache and (ahora - cache[0]) < 15:
            return
        filas = db_manager.execute_query(
            "SELECT id, nombre, precio_combo, productos_json FROM combos"
        ) or []
        listos = []
        for r in filas:
            try:
                crudo = r.get("productos_json", r[3] if isinstance(r, tuple) else "[]")
                reqs = json.loads(crudo or "[]")
                listos.append({
                    "id": r.get("id", r[0] if isinstance(r, tuple) else ""),
                    "nombre": r.get("nombre", r[1] if isinstance(r, tuple) else ""),
                    "precio_combo": float(r.get("precio_combo", r[2] if isinstance(r, tuple) else 0)),
                    "reqs": reqs,
                })
            except Exception:
                continue
        self._combos_cache = (ahora, filas, listos)
