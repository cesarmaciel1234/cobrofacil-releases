from src.config import config
from src.utils.dinero import redondear_dinero

class CobroController:
    """
    Controlador para manejar la lógica matemática y de base de datos del Paso 6 (Cobro).
    Desacopla los cálculos y validaciones de la interfaz visual.
    """

    @staticmethod
    def validar_monto_suficiente(metodo, total_final, p1_t, p2_t=None, valores_mixtos=None):
        """
        Valida que el dinero ingresado cubra el total.
        Retorna (monto_principal, monto_secundario) si es válido, o (None, None) si falta dinero/error.
        """
        try:
            if metodo == "Mixto" and valores_mixtos:
                p1 = valores_mixtos.get("efectivo", 0)
                p2 = (
                    valores_mixtos.get("tarjeta", 0)
                    + valores_mixtos.get("mercadopago", 0)
                    + valores_mixtos.get("qr", 0)
                    + valores_mixtos.get("cliente", 0)
                )
            else:
                p1 = float(p1_t) if p1_t else 0.0
                p2 = float(p2_t) if p2_t and metodo == "Mixto" else 0.0

            p1 = redondear_dinero(p1)
            p2 = redondear_dinero(p2)
            if redondear_dinero(p1 + p2) + 0.001 < redondear_dinero(total_final):
                return None, None

            return p1, p2
        except ValueError:
            return None, None

    @staticmethod
    def calcular_vuelto_y_totales(total_original, monto_descuento, monto_recargo):
        """
        Calcula el total final considerando recargos y descuentos.
        Retorna total_final.
        """
        return max(0.0, total_original - monto_descuento + monto_recargo)

    @staticmethod
    def procesar_y_guardar_venta(
        total_final,
        metodo_pago,
        p1,
        p2,
        items_carrito,
        cajero_actual,
        cajero_secundario,
        monto_descuento=0.0,
        monto_recargo=0.0,
        descuentaso_oferta=0.0,
        nombre_pendiente=None,
        request_id=None
    ):
        """
        Prepara el diccionario de venta y lo guarda en la base de datos.
        Retorna el id_venta generado, o None si falló.
        """
        from src.cajero.paso6_cobro.motor_pagos.comandos.persistir_cobro import persistir_cobro

        datos = {
            "metodo": metodo_pago,
            "total_final": total_final,
            "p1": p1,
            "p2": p2,
            "items_carrito": items_carrito,
            "cajero": cajero_actual,
            "cajero_sec": cajero_secundario,
            "descuento": monto_descuento,
            "recargo": monto_recargo,
            "oferta": descuentaso_oferta,
            "nombre_pendiente": nombre_pendiente,
            "cliente_id": None,
            "request_id": request_id,
        }
        return persistir_cobro(datos)

    @staticmethod
    def procesar_cajon_impresion(metodo_pago, imprimir, id_v, items_carrito, total_final, resultado_venta, cajero_nombre, descuento_total, monto_recargo, force_fiscal=False):
        """
        Decide si debe abrir el cajón y llama al gestor de impresión.
        """
        from src.hardware.printer import printer_manager
        from src.hardware.cash_drawer import drawer_manager

        debe_abrir = False
        if metodo_pago == "Efectivo": debe_abrir = config.get("drawer_open_cash", True)
        elif metodo_pago == "Mixto": debe_abrir = config.get("drawer_open_mixed", True)
        elif metodo_pago == "Tarjeta": debe_abrir = config.get("drawer_open_card", False)
        elif metodo_pago == "Transferencia": debe_abrir = config.get("drawer_open_transfer", False)
        elif metodo_pago == "Fiado": debe_abrir = config.get("drawer_open_fiado", False)

        if debe_abrir:
            drawer_manager.set_authorized(True)

        if imprimir:
            try:
                printer_manager.imprimir_ticket_venta(
                    id_v, items_carrito, total_final,
                    resultado_venta['pago_con'], resultado_venta['cambio'],
                    abrir_cajon=debe_abrir, discount_amount=descuento_total, surcharge_amount=monto_recargo,
                    cajero=cajero_nombre, metodo_pago=metodo_pago,
                    force_fiscal=force_fiscal
                )
            except Exception as e:
                import logging
                logging.error(f"Error al imprimir ticket: {e}")
        else:
            if debe_abrir:
                drawer_manager.abrir(autorizada=True)
            if config.get("opt_corte_papel_sin_ticket", False):
                try:
                    printer_manager.cortar_papel()
                except Exception as e:
                    import logging
                    logging.error(f"Error al ejecutar corte de papel sin ticket: {e}")

    @staticmethod
    def completar_transaccion(
        total_final,
        metodo,
        p1,
        p2,
        items_carrito,
        cajero,
        cajero_sec,
        descuento,
        recargo,
        oferta,
        nombre_pendiente,
        cliente_id,
        imprimir,
        force_fiscal,
        request_id=None
    ):
        """
        Orquesta el guardado de la venta, el fiado, la apertura del cajón y la impresión.
        Retorna (True, None) si tiene éxito, o (False, "mensaje de error").
        """
        try:
            from src.cajero.paso6_cobro.motor_pagos.motor_principal import MotorPrincipalCobros

            return MotorPrincipalCobros.iniciar_transaccion(
                metodo,
                {
                    "total_final": total_final,
                    "p1": p1,
                    "p2": p2,
                    "items_carrito": items_carrito,
                    "cajero": cajero,
                    "cajero_sec": cajero_sec,
                    "descuento": descuento,
                    "recargo": recargo,
                    "oferta": oferta,
                    "nombre_pendiente": nombre_pendiente,
                    "cliente_id": cliente_id,
                    "imprimir": imprimir,
                    "force_fiscal": force_fiscal,
                    "request_id": request_id,
                },
            )
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return False, f"Fallo al cobrar:\n{e}\n\n{tb}"
