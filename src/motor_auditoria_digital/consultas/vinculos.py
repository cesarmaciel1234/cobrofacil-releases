"""Pregunta al libro de firmas de caja. Solo lectura."""


def mapas():
    por_pago = {}
    por_ticket = set()
    try:
        from src.cajero.paso6_cobro.vinculo_mp.libro import _leer

        for mes in _leer().values():
            if not isinstance(mes, dict):
                continue
            for pid, dato in mes.items():
                if not isinstance(dato, dict):
                    continue
                nro = str(dato.get("ticket") or "").strip()
                if not nro:
                    continue
                por_pago[str(pid)] = nro
                por_ticket.add(nro)
    except Exception:
        pass
    return por_pago, por_ticket
