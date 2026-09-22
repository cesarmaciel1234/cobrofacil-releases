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
        return db_manager.execute_query("SELECT id, nombre, precio_combo, productos_json FROM combos") or []
