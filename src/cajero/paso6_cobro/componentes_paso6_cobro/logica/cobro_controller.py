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
