from src.base_de_datos.database import db_manager
from src.config import config

class HistorialController:
    """Controlador para la lógica de base de datos del Historial de Caja."""

    def __init__(self):
        pass

    def get_ventas(self, txt_search="", metodo_filt="TODOS", q_date_iso=None, q_date_l1=None, q_date_l2=None, t_desde=None, t_hasta=None, is_default_time=True):
        """Mismo día que el historial del jefe. q_date_l1 y q_date_l2 quedan por compatibilidad."""
        del q_date_l1, q_date_l2
        from src.historial_ventas.listar import listar_tickets

        hora_desde = None
        hora_hasta = None
        if not is_default_time and t_desde is not None and t_hasta is not None:
            hora_desde = t_desde.toString("HH:mm")
            hora_hasta = t_hasta.toString("HH:mm")
        return listar_tickets(
            texto=txt_search or "",
            metodo=metodo_filt or "TODOS",
            fecha_iso=q_date_iso,
            ver_todo=not bool(q_date_iso),
            hora_desde=hora_desde,
            hora_hasta=hora_hasta,
        )

    def get_detalle_venta(self, id_venta: int):
        """Devuelve (venta_dict, lista_items) para un ticket específico."""
        venta = db_manager.execute_query("SELECT * FROM ventas WHERE id = ?", (id_venta,))
        if not venta:
            return None, []
        v = venta[0]
        items = db_manager.execute_query("SELECT cantidad, nombre_producto, precio_unitario, subtotal FROM detalles_ventas WHERE id_venta = ?", (id_venta,))
        return v, items

    def is_admin(self):
        role = (config.current_user or {}).get("role", "cajero")
        return role == 'admin'

    def get_username(self):
        return (config.current_user or {}).get("username", "cajero")

    def cancelar_venta(self, id_venta: int, username: str) -> bool:
        """Cancela la venta e impacta el inventario."""
        return db_manager.cancelar_venta_transaccional(id_venta, username)

    def plan_devolucion(self, id_venta: int) -> dict:
        try:
            return db_manager.plan_devolucion(id_venta) or {}
        except Exception:
            return {}

    @staticmethod
    def texto_monto(monto: float) -> str:
        from src.cajero.paso8_historial.logica.formato import fmt_moneda

        return fmt_moneda(float(monto or 0))

    @staticmethod
    def texto_devolucion(plan: dict) -> str:
        """El aviso de plata para el cajero: devolver en efectivo y se descuenta del cierre."""
        from src.cajero.paso8_historial.logica.formato import fmt_moneda

        if not plan:
            return "Deberá devolver el importe en efectivo. Se descontará del cierre al finalizar el turno."
        monto = float(plan.get("a_devolver") or 0)
        if monto <= 0:
            return f"Venta {plan.get('metodo') or 'a cuenta'}: no se devuelve efectivo, se anula la deuda del cliente."
        return (
            f"DEBERÁ DEVOLVER {fmt_moneda(monto)} EN EFECTIVO al cliente.\n"
            "Se descontará del cierre al finalizar el turno."
        )

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
