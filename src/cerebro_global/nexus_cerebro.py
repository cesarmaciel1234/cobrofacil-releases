from src.base_de_datos.database import db_manager
from datetime import datetime, timedelta
import re

class CerebroNexus:
    @staticmethod
    def obtener_metricas_live(caja_filter="todas"):
        from src.cerebro_global.cierre_caja_cerebro.motor_cierre import MotorCierre
        caja_num = None
        if caja_filter != "todas":
            import re
            num_match = re.search(r'\d+', str(caja_filter))
            caja_num = int(num_match.group()) if num_match else 1
            
        datos = MotorCierre.obtener_datos_cierre_diario(caja_id=caja_num)
        
        total_efectivo = datos.get("v_efectivo", 0)
        total_digital = datos.get("v_tarjeta", 0) + datos.get("v_trans", 0) + datos.get("v_vales", 0) + datos.get("v_cheque", 0)
        fondo_inicial = datos.get("fondo", 0)
        esperado_live = datos.get("v_caja_total", 0)

        return {
            "total_efectivo": total_efectivo,
            "total_digital": total_digital,
            "fondo_inicial": fondo_inicial,
            "esperado_live": esperado_live
        }

    @staticmethod
    def obtener_nuevas_ventas(last_id):
        hoy = datetime.now().strftime("%Y-%m-%d")
        query = (
            "SELECT id, caja_id, metodo_pago, total, usuario, fecha"
            " FROM ventas WHERE DATE(fecha) = ?"
        )
        params = [hoy]
        if last_id:
            query += " AND id > ?"
            params.append(last_id)
        query += " ORDER BY id ASC LIMIT 5"
        
        return db_manager.execute_query(query, tuple(params)) or []

    @staticmethod
    def registrar_evento_caja(origen_id, cat, msg, sale_date=None):
        origen = str(origen_id)
        c_id = 1
        match = re.search(r'\d+', origen.upper())
        if match:
            c_id = int(match.group())

        if cat == "VENTA":
            tipo_db = "[TICKET] Venta Remota"
            obs_db = f"[TICKET] {msg}"
        else:
            tipo_db = "ALERTA_SEGURIDAD" if cat == "ALERTA" else cat.upper()
            obs_db = f"[{cat}] {msg}"

        ts_now = datetime.now()
        ref_date = sale_date if sale_date is not None else ts_now
        ts = ref_date.strftime("%Y-%m-%d %H:%M:%S")

        try:
            if cat == "VENTA":
                ts_min = (ref_date - timedelta(seconds=60)).strftime("%Y-%m-%d %H:%M:%S")
                ts_max = (ref_date + timedelta(seconds=60)).strftime("%Y-%m-%d %H:%M:%S")
                existe = db_manager.execute_scalar(
                    "SELECT COUNT(id) FROM movimientos_caja WHERE observaciones = ? AND caja_id = ? AND fecha BETWEEN ? AND ?",
                    (obs_db, c_id, ts_min, ts_max)
                )
            else:
                ts_limite = (ts_now - timedelta(seconds=5)).strftime("%Y-%m-%d %H:%M:%S")
                existe = db_manager.execute_scalar(
                    "SELECT COUNT(id) FROM movimientos_caja WHERE observaciones = ? AND tipo = ? AND caja_id = ? AND fecha >= ?",
                    (obs_db, tipo_db, c_id, ts_limite)
                )

            if not existe or existe == 0:
                db_manager.execute_non_query(
                    "INSERT INTO movimientos_caja (fecha, tipo, observaciones, caja_id, usuario, monto) VALUES (?, ?, ?, ?, ?, ?)",
                    (ts, tipo_db, obs_db, c_id, "SISTEMA", 0.0)
                )
        except Exception as e:
            print(f"Error insertando evento de caja en DB: {e}")

    @staticmethod
    def obtener_bitacora(limit, offset, tipo_filtro, search_term, caja_filter):
        q = "SELECT * FROM movimientos_caja WHERE 1=1"
        p = []
        if tipo_filtro != 'Todos los Eventos':
            if tipo_filtro == 'Cierres Z':
                q += " AND tipo='CIERRE_Z'"
            elif 'Cierres Generales' in tipo_filtro:
                q += " AND tipo IN ('CIERRE_Z', 'CIERRE_TURNO', 'CIERRE_AUTO')"
            elif 'Alertas' in tipo_filtro:
                q += " AND tipo='ALERTA_SEGURIDAD'"
            elif 'Ventas Remotas' in tipo_filtro:
                q += " AND observaciones LIKE '%[TICKET]%'"
            elif 'Heartbeats' in tipo_filtro:
                q += " AND observaciones LIKE '%[SYNC]%'"

        if caja_filter != 'todas':
            import re
            num_match = re.search(r'\d+', str(caja_filter))
            if num_match:
                c_num = int(num_match.group())
                q += " AND caja_id = ?"
                p.append(c_num)

        if search_term:
            q += " AND (usuario LIKE ? OR observaciones LIKE ?)"
            p.append(f"%{search_term}%")
            p.append(f"%{search_term}%")
            
        from src.base_de_datos.database import db_manager
        q_count = "SELECT COUNT(id) FROM (" + q + ")"
        total = db_manager.execute_scalar(q_count, tuple(p)) or 0
        
        q_paginated = q + " ORDER BY id DESC LIMIT ? OFFSET ?"
        p.extend([limit, offset])
        logs = db_manager.execute_query(q_paginated, tuple(p)) or []
        
        all_logs = db_manager.execute_query(q + " ORDER BY id DESC", tuple(p[:-2])) or [] if not limit else []
        
        return total, logs, all_logs

    @staticmethod
    def obtener_historial_cierres(limit, offset, date_filter):
        q = """
            SELECT c.*, u.nombre as admin_nombre
            FROM movimientos_caja c
            LEFT JOIN usuarios u ON c.usuario = u.username
            WHERE c.tipo='CIERRE_Z'
        """
        p = []
        if date_filter and date_filter != 'Todas las Fechas':
            q += " AND DATE(c.fecha) = ?"
            p.append(date_filter)
            
        q += " ORDER BY c.id DESC LIMIT ? OFFSET ?"
        p.extend([limit, offset])
        from src.base_de_datos.database import db_manager
        return db_manager.execute_query(q, tuple(p)) or []

    @staticmethod
    def obtener_fechas_cierres():
        from src.base_de_datos.database import db_manager
        fechas = db_manager.execute_query("SELECT DISTINCT DATE(fecha) as d FROM movimientos_caja WHERE tipo='CIERRE_Z' ORDER BY d DESC")
        return [f['d'] for f in fechas] if fechas else []

    @staticmethod
    def ejecutar_query(q, p):
        from src.base_de_datos.database import db_manager
        return db_manager.execute_query(q, p)

    @staticmethod
    def ejecutar_escalar(q, p):
        from src.base_de_datos.database import db_manager
        return db_manager.execute_scalar(q, p)
