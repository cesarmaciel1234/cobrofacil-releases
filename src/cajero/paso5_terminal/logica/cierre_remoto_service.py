from src.base_de_datos.database import db_manager

class CierreRemotoService:
    def verificar_solicitud_cierre_remoto(self, c_id):
        res_ap = db_manager.execute_query(
            "SELECT fecha FROM movimientos_caja WHERE tipo = 'APERTURA' AND caja_id = ? ORDER BY id DESC LIMIT 1",
            (c_id,)
        )
        ult_apertura = "1970-01-01 00:00:00"
        if res_ap:
            ult_apertura = res_ap[0]['fecha']
            
        res = db_manager.execute_query(
            "SELECT id, observaciones FROM movimientos_caja WHERE tipo = 'SOLICITUD_CIERRE' AND caja_id = ? AND observaciones NOT LIKE '%PROCESADO%' AND fecha >= ? ORDER BY id DESC LIMIT 1",
            (c_id, ult_apertura)
        )
        if res:
            db_manager.execute_non_query(
                "UPDATE movimientos_caja SET observaciones = 'PROCESADO' WHERE tipo = 'SOLICITUD_CIERRE' AND caja_id = ? AND fecha >= ?",
                (c_id, ult_apertura)
            )
            return True
        return False
