from src.base_de_datos.database import db_manager
from datetime import datetime, timedelta
import re

class CerebroNexus:
    @staticmethod
    def obtener_metricas_live(caja_filter="todas"):
        hoy = datetime.now().strftime("%Y-%m-%d")
        params_totales = [hoy]
        filtro_caja_sql = ""
        
        caja_num = 1
        if caja_filter != "todas":
            num_match = re.search(r'\d+', str(caja_filter))
            caja_num = int(num_match.group()) if num_match else 1
            filtro_caja_sql = " AND caja_id = ?"
            params_totales.append(caja_num)

        total_efectivo = db_manager.execute_scalar(
            f'''SELECT SUM(
                CASE
                    WHEN metodo_pago IN ('Efectivo', 'Mixto')
                         OR UPPER(COALESCE(metodo_pago, '')) LIKE '%EFECTIVO%'
                    THEN COALESCE(pago_efectivo, 0)
                         - CASE WHEN COALESCE(cambio, 0) > 0 THEN COALESCE(cambio, 0) ELSE 0 END
                    ELSE 0
                END
            ) FROM ventas
            WHERE DATE(fecha) = ? AND estado IN ('COMPLETADA', 'COMPLETADO', 'CERRADA', 'CERRADO')
            {filtro_caja_sql}''',
            tuple(params_totales)
        ) or 0.0

        total_digital = db_manager.execute_scalar(
            f"SELECT SUM(total) FROM ventas"
            f" WHERE DATE(fecha) = ? AND metodo_pago NOT IN ('Efectivo', 'Mixto')"
            f" AND estado IN ('COMPLETADA', 'COMPLETADO', 'CERRADA', 'CERRADO')"
            f"{filtro_caja_sql}",
            tuple(params_totales)
        ) or 0.0
        
        fondo_inicial = 0.0
        esperado_live = float(total_efectivo or 0)
        
        if caja_filter != "todas":
            fondo_inicial = float(db_manager.execute_scalar(
                "SELECT monto FROM movimientos_caja WHERE tipo='APERTURA' AND caja_id = ? ORDER BY id DESC LIMIT 1",
                (caja_num,)
            ) or 0.0)
            esperado = db_manager.get_efectivo_en_caja(caja_num)
            esperado_live = float(esperado) if esperado else 0.0
        else:
            fondo_inicial = float(db_manager.execute_scalar(
                "SELECT SUM(monto) FROM movimientos_caja WHERE tipo='APERTURA' AND DATE(fecha) = ?",
                (hoy,)
            ) or 0.0)
            esperado_live = float(fondo_inicial or 0) + float(total_efectivo or 0)

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
