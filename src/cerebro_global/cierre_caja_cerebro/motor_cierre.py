from datetime import datetime

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

class MotorCierre:
    """
    Cerebro Global para el Cierre de Caja.
    Centraliza las consultas de la base de datos y la lógica de cálculo
    para que cualquier módulo (Admin, Jefe, Cajero) reciba los mismos datos
    y tenga las mismas reglas (ej: ganancia estimada).
    """

    @staticmethod
    def obtener_datos_cierre_diario(fecha_str=None, cajero=None, caja_id=None):
        try:
            target_date = fecha_str if fecha_str else datetime.now().strftime("%Y-%m-%d")
            
            cajero_cond_ventas = ""
            params_ventas = [target_date]
            
            cajero_cond_fondo = ""
            params_fondo = [target_date]
            
            if cajero:
                cajero_cond_ventas += " AND usuario = ?"
                params_ventas.append(cajero)
                cajero_cond_fondo += " AND usuario = ?"
                params_fondo.append(cajero)
                
            if caja_id:
                cajero_cond_ventas += " AND caja_id = ?"
                params_ventas.append(caja_id)
                cajero_cond_fondo += " AND caja_id = ?"
                params_fondo.append(caja_id)
            
            # Fondo del cajero o del día
            fondo = float(db_manager.execute_scalar(
                f"SELECT monto FROM movimientos_caja WHERE tipo='APERTURA' AND date(fecha) = ? {cajero_cond_fondo} ORDER BY id DESC LIMIT 1",
                tuple(params_fondo)
            ) or 0)
            
            # Ventas Efectivo
            v_efectivo = float(db_manager.execute_scalar(
                f"SELECT SUM(total) FROM ventas WHERE estado='COMPLETADA' AND metodo_pago='Efectivo' AND date(fecha) = ? {cajero_cond_ventas}",
                tuple(params_ventas)
            ) or 0)

            # Ventas Tarjeta
            v_tarjeta = float(db_manager.execute_scalar(
                f"SELECT SUM(total) FROM ventas WHERE estado='COMPLETADA' AND metodo_pago LIKE '%Tarjeta%' AND date(fecha) = ? {cajero_cond_ventas}",
                tuple(params_ventas)
            ) or 0)

            # Transferencia / Fiado
            v_trans = float(db_manager.execute_scalar(
                f"SELECT SUM(total) FROM ventas WHERE estado='COMPLETADA' AND (metodo_pago='Transferencia' OR metodo_pago='Fiado') AND date(fecha) = ? {cajero_cond_ventas}",
                tuple(params_ventas)
            ) or 0)

            v_totales = v_efectivo + v_tarjeta + v_trans
            v_caja_total = fondo + v_efectivo
            ganancia_estimada = v_totales * 0.30 # Placeholder demo 30%

            return {
                "fondo": fondo,
                "v_efectivo": v_efectivo,
                "v_tarjeta": v_tarjeta,
                "v_trans": v_trans,
                "v_totales": v_totales,
                "v_caja_total": v_caja_total,
                "ganancia_estimada": ganancia_estimada
            }
        except Exception as e:
            print(f"Error en MotorCierre: {e}")
            return {
                "fondo": 0.0, "v_efectivo": 0.0, "v_tarjeta": 0.0, "v_trans": 0.0,
                "v_totales": 0.0, "v_caja_total": 0.0, "ganancia_estimada": 0.0
            }
