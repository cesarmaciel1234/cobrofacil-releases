from src.base_de_datos.database import db_manager
from src.config import config
from datetime import datetime

class HistorialController:
    """Controlador para la lógica de base de datos del Historial de Caja."""

    def __init__(self):
        pass

    def get_ventas(self, txt_search="", metodo_filt="TODOS", q_date_iso=None, q_date_l1=None, q_date_l2=None, t_desde=None, t_hasta=None, is_default_time=True):
        """
        Obtiene y filtra las ventas de la base de datos basándose en los criterios indicados.
        Retorna (filtered_res, total_exitoso)
        """
        role = (config.current_user or {}).get("role", "cajero")
        # El admin ve todo, el cajero en teoría también en esta versión
        query = """
            SELECT v.id, v.fecha, v.total, v.usuario, v.estado, v.metodo_pago,
                   IFNULL(SUM(dv.cantidad), 0) as cant_arts,
                   GROUP_CONCAT(dv.nombre_producto, ' ') as prod_names
            FROM ventas v
            LEFT JOIN detalles_ventas dv ON dv.id_venta = v.id
            GROUP BY v.id
            ORDER BY v.id DESC LIMIT 500
        """
        raw_res = db_manager.execute_query(query)
        if not raw_res:
            return [], 0.0

        filtered_res = []
        total_exitoso = 0.0

        for r in raw_res:
            f_raw = r['fecha']
            f_str = ""
            if f_raw is not None:
                f_str = f_raw.strftime("%Y-%m-%d %H:%M:%S") if hasattr(f_raw, "strftime") else str(f_raw)
            
            match_date = (q_date_iso in f_str or q_date_l1 in f_str or q_date_l2 in f_str)
            
            match_time = True
            if not is_default_time and t_desde is not None and t_hasta is not None:
                try:
                    dt = None
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d"):
                        try:
                            dt = datetime.strptime(f_str, fmt)
                            break
                        except:
                            continue
                    if dt:
                        from PyQt6.QtCore import QTime
                        v_time = QTime(dt.hour, dt.minute, dt.second)
                        match_time = (t_desde <= v_time <= t_hasta)
                    else:
                        match_time = False
                except:
                    match_time = False
            
            match_method = (metodo_filt == "TODOS" or metodo_filt in str(r['metodo_pago'] or "").upper())
            
            match_text = True
            if txt_search:
                search_pool = f"{r['id']} {r['usuario']} {r['fecha']} {r['metodo_pago']} {r['total']}".lower()
                if txt_search not in search_pool:
                    prod_str = str(r['prod_names'] or "").lower()
                    match_text = (txt_search in prod_str)

            if match_date and match_time and match_method and match_text:
                filtered_res.append(r)
                estado_str = str(r['estado']).upper()
                if not estado_str.startswith("CANCELAD"):
                    total_exitoso += r['total']

        return filtered_res, total_exitoso

    def get_detalle_venta(self, id_venta: int):
        """Devuelve (venta_dict, lista_items) para un ticket específico."""
        venta = db_manager.execute_query("SELECT * FROM ventas WHERE id = ?", (id_venta,))
        if not venta:
            return None, []
        v = venta[0]
        items = db_manager.execute_query("SELECT cantidad, nombre_producto, subtotal FROM detalles_ventas WHERE id_venta = ?", (id_venta,))
        return v, items

    def is_admin(self):
        role = (config.current_user or {}).get("role", "cajero")
        return role == 'admin'
        
    def get_username(self):
        return (config.current_user or {}).get("username", "cajero")

    def cancelar_venta(self, id_venta: int, username: str) -> bool:
        """Cancela la venta e impacta el inventario."""
        return db_manager.cancelar_venta_transaccional(id_venta, username)
        
    def reimprimir_ticket(self, id_venta: int):
        v = db_manager.execute_query("SELECT * FROM ventas WHERE id = ?", (id_venta,))
        if not v:
            raise Exception("Venta no encontrada")
        v = v[0]
        db_items = db_manager.execute_query("SELECT id_producto as id, nombre_producto as nombre, cantidad as cant, precio_unitario as precio, subtotal FROM detalles_ventas WHERE id_venta = ?", (id_venta,))
        db_items_dict = [dict(item) for item in db_items]
        
        desc_val = float(v['descuento']) if ('descuento' in v.keys() and v['descuento'] is not None) else 0.0
        rec_val = float(v['recargo']) if ('recargo' in v.keys() and v['recargo'] is not None) else 0.0
        
        from src.hardware.printer import printer_manager
        v_dict = dict(v)
        printer_manager.imprimir_ticket_venta(
            v['id'], db_items_dict, v['total'], v['pago_con'], v['cambio'],
            abrir_cajon=False, estado=v['estado'] if 'estado' in v.keys() else 'COMPLETADA',
            discount_amount=desc_val, surcharge_amount=rec_val,
            metodo_pago=v_dict.get('metodo_pago', 'Efectivo')
        )
