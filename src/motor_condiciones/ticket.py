class MotorCondicionesTicket:
    @staticmethod
    def evaluar(metodo_pago, abono_cuenta, total_final, items_carrito):
        mensajes = []
        
        # Condición: Si hubo un abono a cuenta (pago en Centro de Cobranzas)
        # y la venta se cierra por Fiado/Cuenta Corriente, inyectamos el mensaje.
        if abono_cuenta > 0.009:
            mensajes.append("*** Pago de deuda procesado ***")
            mensajes.append(f"Abono registrado: ")

        # Retornamos los mensajes combinados separados por salto de linea
        return "\n".join(mensajes) if mensajes else None