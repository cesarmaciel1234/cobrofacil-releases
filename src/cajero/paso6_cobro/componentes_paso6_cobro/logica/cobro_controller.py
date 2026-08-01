from src.config import config
from src.base_de_datos.database import db_manager

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
                p1 = valores_mixtos.get("efectivo", 0) + (valores_mixtos.get("usd", 0) * config.get("tasa_usd", 1200.0))
                p2 = valores_mixtos.get("tarjeta", 0) + valores_mixtos.get("mercadopago", 0)
            else:
                p1 = float(p1_t) if p1_t else 0.0
                p2 = float(p2_t) if p2_t and metodo == "Mixto" else 0.0
            
            if (p1 + p2) < total_final:
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
        nombre_pendiente=None
    ):
        """
        Prepara el diccionario de venta y lo guarda en la base de datos.
        Retorna el id_venta generado, o None si falló.
        """
        estado_venta = 'COMPLETADA'
        nombre_cliente_guardar = ''
        if nombre_pendiente:
            estado_venta = 'TRANSF_PENDIENTE'
            nombre_cliente_guardar = nombre_pendiente

        pago_efectivo = p1 if metodo_pago in ["Efectivo", "Mixto"] else 0
        pago_otro = p2 if metodo_pago == "Mixto" else (p1 if metodo_pago != "Efectivo" else 0)

        descuento_total = monto_descuento + descuentaso_oferta

        resultado_venta = {
            'total': total_final,
            'pago_con': p1 + p2,
            'cambio': (p1 + p2) - total_final,
            'pago_efectivo': pago_efectivo,
            'pago_otro': pago_otro,
            'usuario': cajero_actual,
            'usuario_secundario': cajero_secundario,
            'metodo_pago': metodo_pago,
            'estado': estado_venta,
            'cliente_nombre': nombre_cliente_guardar,
            'descuento': descuento_total,
            'recargo': monto_recargo
        }

        # Guardar en base de datos
        id_v = db_manager.guardar_venta_completa(resultado_venta, items_carrito)
        return id_v, resultado_venta

    @staticmethod
    def procesar_fiado(cliente_id, total_final, id_v):
        """
        Registra la deuda del cliente por una venta Fiada.
        """
        from src.repositories.cliente_repository import ClienteRepository
        
        if not cliente_id:
            return False, "No se pudo identificar al cliente del fiado."
            
        c = ClienteRepository.obtener_por_id(cliente_id)
        if not c:
            return False, "Cliente no encontrado en la base de datos."
            
        nueva_deuda = float(dict(c).get("deuda_actual", 0)) + total_final
        nombre_cli = dict(c).get("nombre", "")

        db_manager.execute_non_query(
            "UPDATE clientes SET deuda_actual = ? WHERE id = ?",
            (nueva_deuda, cliente_id),
        )
        db_manager.execute_non_query(
            "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion, venta_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (cliente_id, "CARGO", total_final, nueva_deuda, f"Venta a crédito Ticket #{id_v}", id_v),
        )
        return True, nombre_cli

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
        elif debe_abrir:
            drawer_manager.abrir(autorizada=True)

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
        force_fiscal
    ):
        """
        Orquesta el guardado de la venta, el fiado, la apertura del cajón y la impresión.
        Retorna (True, None) si tiene éxito, o (False, "mensaje de error").
        """
        try:
            id_v, resultado_venta = CobroController.procesar_y_guardar_venta(
                total_final,
                metodo,
                p1, p2,
                items_carrito,
                cajero,
                cajero_sec,
                descuento,
                recargo,
                oferta,
                nombre_pendiente
            )
            
            if not id_v:
                return False, "Error al guardar la venta en la base de datos."
                
            # Si fue fiado o clientes, actualizar la deuda
            if metodo in ("Fiado", "Clientes"):
                exito, cli_res = CobroController.procesar_fiado(cliente_id, total_final, id_v)
                if not exito:
                    return False, cli_res
                resultado_venta["cliente_nombre"] = cli_res

            descuento_total = descuento + oferta
            CobroController.procesar_cajon_impresion(
                metodo, 
                imprimir, 
                id_v, 
                items_carrito, 
                total_final, 
                resultado_venta, 
                cajero, 
                descuento_total, 
                recargo, 
                force_fiscal
            )
            
            return True, None
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return False, f"Fallo al cobrar:\n{e}\n\n{tb}"
