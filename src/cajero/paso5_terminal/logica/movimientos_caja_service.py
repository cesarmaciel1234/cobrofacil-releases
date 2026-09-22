from src.base_de_datos.database import db_manager

class MovimientosCajaService:
    def obtener_efectivo_caja(self, c_id):
        return db_manager.get_efectivo_en_caja(c_id)

    def registrar_retiro_efectivo(self, monto, usuario, motivo, c_id):
        query = "INSERT INTO movimientos_caja (tipo, monto, usuario, observaciones, caja_id) VALUES ('RETIRO', ?, ?, ?, ?)"
        if db_manager.execute_non_query(query, (monto, usuario, motivo, c_id)):
            try:
                from src.hardware.printer import printer_manager
                printer_manager.abrir_cajon()
                printer_manager.imprimir_movimiento_caja('RETIRO DE EFECTIVO', monto, motivo, usuario, c_id)
                return True
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error imprimiendo retiro: {e}")
                return True # Success regardless of printing
        return False

    def registrar_ingreso_efectivo(self, monto, usuario, motivo, c_id):
        query = "INSERT INTO movimientos_caja (tipo, monto, usuario, observaciones, caja_id) VALUES ('INGRESO', ?, ?, ?, ?)"
        if db_manager.execute_non_query(query, (monto, usuario, motivo, c_id)):
            try:
                from src.hardware.printer import printer_manager
                printer_manager.abrir_cajon()
                printer_manager.imprimir_movimiento_caja('INGRESO DE EFECTIVO', monto, motivo, usuario, c_id)
                return True
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error imprimiendo ingreso: {e}")
                return True
        return False
