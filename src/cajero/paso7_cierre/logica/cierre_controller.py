import os
from datetime import datetime
from src.base_de_datos.database import db_manager

class CierreController:
    @staticmethod
    def obtener_datos_cierre(username, caja_id):
        today_str = datetime.now().strftime("%Y-%m-%d")

        # 1. Buscar apertura de la caja
        ap_rows = db_manager.execute_query(
            "SELECT fecha, monto FROM movimientos_caja WHERE caja_id=? AND tipo='APERTURA' ORDER BY id DESC LIMIT 1",
            (caja_id,),
        )
        if ap_rows:
            apertura_fecha = ap_rows[0]["fecha"]
            fondo = float(ap_rows[0]["monto"] or 0)
        else:
            apertura_fecha = f"{today_str} 00:00:00"
            fondo = float(
                db_manager.execute_scalar(
                    "SELECT monto FROM movimientos_caja WHERE tipo='APERTURA' AND LOWER(usuario) = LOWER(?) ORDER BY id DESC LIMIT 1",
                    (username,),
                )
                or db_manager.execute_scalar(
                    "SELECT monto FROM movimientos_caja WHERE tipo='APERTURA' ORDER BY id DESC LIMIT 1"
                )
                or 0
            )

        # 2. Ventas del turno
        res_v = db_manager.execute_query(
            """SELECT SUM(total) as t,
                      SUM(CASE WHEN metodo_pago != 'Fiado' THEN COALESCE(pago_otro, 0) ELSE 0 END) as ta,
                      SUM(CASE WHEN metodo_pago = 'Fiado' THEN total ELSE 0 END) as tf,
                      SUM(COALESCE(pago_efectivo, 0) - COALESCE(cambio, 0)) as te,
                      SUM(COALESCE(descuento, 0)) as tr
               FROM ventas
               WHERE caja_id=? AND fecha >= ? AND estado IN ('COMPLETADA', 'CERRADA')
                 AND LOWER(usuario) = LOWER(?)""",
            (caja_id, apertura_fecha, username),
        )
        v_total = float((res_v[0]["t"] if res_v else 0) or 0)
        v_tarj = float((res_v[0]["ta"] if res_v else 0) or 0)
        v_fiado = float((res_v[0]["tf"] if res_v else 0) or 0)
        v_efec_ventas = float((res_v[0]["te"] if res_v else 0) or 0)
        v_redondeo = float((res_v[0]["tr"] if res_v else 0) or 0)

        # 3. Alertas
        alertas = db_manager.execute_scalar(
            "SELECT COUNT(*) FROM movimientos_caja WHERE tipo='ALERTA_SEGURIDAD' AND LOWER(usuario) = LOWER(?) AND date(fecha) = ?",
            (username, today_str),
        ) or 0

        # 4. Datos Diarios (Para corte diario admin)
        res_d = db_manager.execute_query(
            "SELECT SUM(total) as t, SUM(CASE WHEN metodo_pago != 'Fiado' THEN pago_otro ELSE 0 END) as ta, SUM(CASE WHEN metodo_pago = 'Fiado' THEN total ELSE 0 END) as tf FROM ventas WHERE date(fecha) = ? AND estado IN ('COMPLETADA','CERRADA')",
            (today_str,),
        )
        d_total = float((res_d[0]["t"] if res_d else 0) or 0)
        d_tarj = float((res_d[0]["ta"] if res_d else 0) or 0)
        d_fiado = float((res_d[0]["tf"] if res_d else 0) or 0)

        # 5. Deuda histórica
        f_hist = abs(
            float(
                db_manager.execute_scalar(
                    "SELECT SUM(monto) FROM movimientos_caja WHERE tipo='CIERRE_Z' AND LOWER(usuario) = LOWER(?) AND monto < 0",
                    (username,),
                )
                or 0
            )
        )

        esperado = db_manager.get_efectivo_en_caja(caja_id)

        return {
            "fondo": fondo,
            "t_efec": v_efec_ventas,
            "t_tarj": v_tarj,
            "t_fiado": v_fiado,
            "t_total": v_total,
            "d_total": d_total,
            "d_tarj": d_tarj,
            "d_fiado": d_fiado,
            "f_hist": f_hist,
            "alertas": alertas,
            "esperado": esperado,
            "caja_id": caja_id,
            "apertura_fecha": apertura_fecha,
            "t_redondeo": v_redondeo
        }

    @staticmethod
    def finalizar_cierre(username, caja_id, fisico, dif, esperado, apertura_fecha, t_total, modo="turno"):
        """
        Registra el cierre Z en base de datos, envía ticket e email.
        """
        # 1. Insertar movimiento de cierre
        db_manager.execute_non_query(
            "INSERT INTO movimientos_caja (tipo, monto, usuario, observaciones, caja_id) VALUES ('CIERRE_Z', ?, ?, ?, ?)", 
            (dif, username, f"Modo:{modo} | Fis:${fisico:.2f} | Esp:${esperado:.2f}", caja_id)
        )
        
        # 2. Actualizar estado de ventas
        if apertura_fecha:
            db_manager.execute_non_query(
                "UPDATE ventas SET estado='CERRADA' WHERE estado='COMPLETADA' AND caja_id=? AND fecha >= ?",
                (caja_id, apertura_fecha),
            )
        else:
            db_manager.execute_non_query(
                "UPDATE ventas SET estado='CERRADA' WHERE estado='COMPLETADA' AND usuario=? AND caja_id=?",
                (username, caja_id),
            )
        
        # 3. Imprimir ticket
        try:
            from src.hardware.printer import printer_manager
            # Mock de self.datos
            datos_impresion = {
                "t_total": t_total,
                "esperado": esperado,
                "segunda_tiketera": True, 
                "modo": modo
            }
            printer_manager.imprimir_ticket_z(username, fisico, dif, datos_impresion)
        except Exception as e:
            print(f"Error imprimiendo ticket Z: {e}")
            
        # 4. Enviar Email
        try:
            from src.services.email_service import enviar_reporte_cierre_z
            datos_cierre = {
                'caja_id': caja_id,
                'usuario': username,
                'tipo_cierre': 'CIERRE DE TURNO',
                'efectivo_esperado': esperado,
                'efectivo_fisico': fisico,
                'diferencia': dif,
                'total_ventas': t_total
            }
            enviar_reporte_cierre_z(datos_cierre)
        except Exception as email_err:
            print(f"Error enviando email: {email_err}")
            
        return True
