"""Bruto/neto MP vs tickets digitales vs cobranza digital de clientes."""


def de_filas(filas):
    bruto = 0.0
    neto = 0.0
    tickets = 0.0
    firmados = 0.0
    sin_firmar = 0.0
    cliente = 0.0
    n_sin_firmar = 0
    n_tickets = 0
    for p in filas or []:
        try:
            estado = str(p.get("estado") or "").upper()
            if p.get("op_type") == "account_fund" or estado in ("CARGA DE FONDOS", "OMITIDO", "CUENTA / DNI"):
                continue
            monto_mp = float(p.get("monto_mp") if p.get("monto_mp") is not None else (p.get("monto") or 0))
            neto_fila = float(p.get("neto") or 0)
            monto_ticket = float(p.get("monto_ticket") if p.get("monto_ticket") is not None else 0)
            if estado in ("CLIENTE", "COBRANZA"):
                plata = monto_ticket or float(p.get("monto") or 0)
                cliente += plata
                if monto_mp:
                    bruto += monto_mp
                    neto += neto_fila
                continue
            if estado == "SIN TICKET":
                bruto += monto_mp
                neto += neto_fila
                continue
            if estado in ("F9 MANUAL", "SIN FIRMAR"):
                plata = monto_ticket or float(p.get("monto") or 0)
                tickets += plata
                sin_firmar += plata
                n_sin_firmar += 1
                n_tickets += 1
                continue
            if estado in ("FIRMADO", "APPROVED"):
                bruto += monto_mp
                neto += neto_fila
                plata = monto_ticket or float(p.get("monto") or 0)
                if str(p.get("ticket") or "—") not in ("", "—"):
                    tickets += plata
                    firmados += plata
                    n_tickets += 1
        except Exception:
            continue
    return {
        "bruto": bruto,
        "neto": neto,
        "tickets": tickets,
        "firmados": firmados,
        "sin_firmar": sin_firmar,
        "cliente": cliente,
        "n_sin_firmar": n_sin_firmar,
        "n_tickets": n_tickets,
    }
