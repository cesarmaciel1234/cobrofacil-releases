"""El cajero cobra un abono por acá. Si algo falla, devuelve aviso y no tira."""


def pedir(parent, monto):
    try:
        from src.clientes_fiado.interfaz.cobro.medio import pedir_medio

        return pedir_medio(parent, monto)
    except Exception:
        return None


def asentar(cliente_id, monto, deuda, perfil, quien, resultado):
    try:
        if resultado is None or not getattr(resultado, "ok", False):
            return {"ok": False, "aviso": "No se pudo cobrar la cuenta. La venta sigue."}
        from src.clientes_fiado.cerebro.cerebro import cerebro

        exito, saldo, nombre = cerebro.abonar_caja(
            cliente_id, monto, deuda,
            medio=resultado.medio, perfil=perfil, quien=quien,
            nota=getattr(resultado, "detalle", "") or "",
        )
        if not exito:
            return {"ok": False, "aviso": "No se pudo registrar el pago del cliente."}
        return {
            "ok": True,
            "entra_caja": bool(resultado.entra_caja),
            "monto_caja": float(resultado.monto_caja or 0),
            "motivo": f"Pago de clientes: {nombre} ({resultado.medio})",
            "nombre": nombre,
            "saldo": float(saldo or 0),
            "aviso": "",
        }
    except Exception:
        return {"ok": False, "aviso": "No se pudo cobrar la cuenta. La venta sigue."}
