"""Cruza consultas. Si una fuente falla, las otras siguen."""


def _medio(texto):
    m = (texto or "").upper().replace("É", "E")
    if "TRANSFER" in m:
        return "Transferencia"
    if any(x in m for x in ("TARJETA", "DEBITO", "POINT")):
        return "Tarjeta"
    if "CREDITO" in m and "MASCREDITO" not in m:
        return "Tarjeta"
    if any(x in m for x in ("QR", "MERCADOPAGO")) or m == "MP":
        return "QR"
    return (texto or "QR").split(":")[0].strip() or "QR"


def _fila(**kwargs):
    from src.motor_auditoria_digital.consultas.ids import id_pago, ticket_cobro, ticket_venta

    tv = ticket_venta(kwargs.get("ticket_venta"))
    tc = ticket_cobro(kwargs.get("ticket_cobro")) if kwargs.get("ticket_cobro") else ""
    return {
        "fecha": kwargs.get("fecha") or "",
        "id": id_pago(kwargs.get("pago_id"), bool(kwargs.get("f9"))),
        "nombre": kwargs.get("nombre") or "—",
        "monto": float(kwargs.get("monto") or 0),
        "monto_mp": float(kwargs.get("monto_mp") or 0),
        "neto": float(kwargs.get("neto") or 0),
        "monto_ticket": float(kwargs.get("monto_ticket") or 0),
        "estado": kwargs.get("estado") or "",
        "ticket_venta": tv,
        "ticket_cobro": tc,
        "ticket": tv or tc or "—",
        "op_type": kwargs.get("op_type") or "",
        "email": kwargs.get("email") or "",
    }


def armar(desde, hasta):
    filas = []
    try:
        from src.motor_auditoria_digital.consultas.rango import en_rango
        from src.motor_auditoria_digital.consultas.vinculos import mapas
        from src.motor_auditoria_digital.consultas.pagos_mp import listar as pagos_mp
        from src.motor_auditoria_digital.consultas.tickets import listar as tickets
        from src.motor_auditoria_digital.libro_f9.libro import lista as lista_f9
        from src.motor_auditoria_digital.consultas.cobranzas import listar as cobranzas

        por_pago, _firmados = mapas()
        lista_pagos = []
        try:
            lista_pagos = list(pagos_mp() or [])
        except Exception:
            lista_pagos = []
        try:
            from src.motor_cobros_digitales.libro.tabla import tickets_por_pago

            extra = tickets_por_pago([str(p.get("id") or "") for p in lista_pagos]) or {}
            for pid, nro in extra.items():
                if pid and nro and pid not in por_pago:
                    por_pago[pid] = nro
        except Exception:
            pass
        f9 = lista_f9()
        abonos = []
        try:
            abonos = cobranzas(desde, hasta)
        except Exception:
            abonos = []
        por_cobro_pago = {
            str(a.get("pago_id") or ""): a for a in abonos if a.get("pago_id")
        }
        cobros_vistos = set()
        ventas = []
        try:
            ventas = tickets(desde, hasta, clases=("digital",))
        except Exception:
            ventas = []
        por_ticket = {str(v.get("ticket") or ""): v for v in ventas if v.get("ticket")}
        vistos = set()

        for p in lista_pagos:
            try:
                if str(p.get("estado") or "").upper() == "OMITIDO":
                    continue
                if p.get("op_type") == "account_fund":
                    continue
                fecha = p.get("fecha") or ""
                if not en_rango(fecha, desde, hasta):
                    continue
                pid = str(p.get("id") or "")
                nro = por_pago.get(pid, "")
                estado = str(p.get("estado") or "").upper()
                monto_mp = float(p.get("monto") or 0)
                neto = float(p.get("neto") or monto_mp)
                cobro = por_cobro_pago.get(pid)
                venta = por_ticket.get(nro) or {}
                if cobro:
                    cobros_vistos.add(str(cobro.get("id") or ""))
                    medio = _medio(cobro.get("metodo") or "QR")
                    quien = cobro.get("nombre") or "Cliente"
                    if estado == "APPROVED":
                        estado = "COBRANZA"
                    filas.append(_fila(
                        fecha=fecha,
                        pago_id=pid,
                        nombre=f"Cobranza {medio} · {quien}",
                        monto=float(cobro.get("monto") or monto_mp),
                        monto_mp=monto_mp,
                        neto=neto,
                        monto_ticket=float(cobro.get("monto") or 0),
                        estado=estado,
                        ticket_cobro=cobro.get("ticket_cobro") or cobro.get("id"),
                        op_type="cobranza",
                        email=p.get("email") or "",
                    ))
                elif nro:
                    vistos.add(nro)
                    if estado == "APPROVED":
                        estado = "FIRMADO"
                    medio = _medio(venta.get("metodo") or p.get("nombre") or "QR")
                    filas.append(_fila(
                        fecha=fecha,
                        pago_id=pid,
                        nombre=f"Venta {medio}",
                        monto=float(venta.get("monto") or monto_mp),
                        monto_mp=monto_mp,
                        neto=neto,
                        monto_ticket=float(venta.get("monto") or 0),
                        estado=estado,
                        ticket_venta=nro,
                        op_type=p.get("op_type") or "",
                        email=p.get("email") or "",
                    ))
                else:
                    if estado == "APPROVED":
                        estado = "SIN TICKET"
                    quien = p.get("nombre") or "—"
                    if str(quien).strip().lower() in ("cliente", "—", "-", ""):
                        quien = "Cobro MP sin ticket"
                    else:
                        quien = f"MP · {quien}"
                    filas.append(_fila(
                        fecha=fecha,
                        pago_id=pid,
                        nombre=quien,
                        monto=monto_mp,
                        monto_mp=monto_mp,
                        neto=neto,
                        estado=estado,
                        op_type=p.get("op_type") or "",
                        email=p.get("email") or "",
                    ))
            except Exception:
                continue

        firmados_db = set()
        try:
            from src.motor_cobros_digitales.veredicto.conciliar import tickets_firmados

            firmados_db = tickets_firmados(desde, hasta)
        except Exception:
            pass

        for venta in ventas:
            try:
                if venta.get("clase") != "digital":
                    continue
                nro = str(venta.get("ticket") or "")
                if not nro or nro in vistos:
                    continue
                vistos.add(nro)
                medio = _medio(venta.get("metodo") or "QR")
                manual = nro in f9
                firmado = nro in firmados_db
                estado = "F9 MANUAL" if manual else ("FIRMADO" if firmado else "SIN FIRMAR")
                filas.append(_fila(
                    fecha=venta.get("fecha") or "",
                    f9=manual,
                    nombre=f"Venta {medio}" + (" · F9" if manual else ""),
                    monto=float(venta.get("monto") or 0),
                    monto_ticket=float(venta.get("monto") or 0),
                    estado=estado,
                    ticket_venta=nro,
                    op_type="ticket",
                ))
            except Exception:
                continue

        for nro, dato in f9.items():
            if nro in vistos:
                continue
            try:
                if not en_rango(dato.get("cuando") or "", desde, hasta):
                    continue
                tipo = "digital"
                try:
                    from src.motor_cobros_digitales.veredicto.medios import clase

                    tipo = clase(dato.get("metodo") or "")
                except Exception:
                    pass
                if tipo != "digital":
                    continue
                medio = _medio(dato.get("metodo") or "QR")
                filas.append(_fila(
                    fecha=dato.get("cuando") or "",
                    f9=True,
                    nombre=f"Venta {medio} · F9",
                    monto=float(dato.get("monto") or 0),
                    monto_ticket=float(dato.get("monto") or 0),
                    estado="F9 MANUAL",
                    ticket_venta=nro,
                    op_type="f9",
                ))
            except Exception:
                continue

        for cobro in abonos:
            try:
                clave = str(cobro.get("id") or "")
                if not clave or clave in cobros_vistos:
                    continue
                cobros_vistos.add(clave)
                medio = _medio(cobro.get("metodo") or "QR")
                quien = cobro.get("nombre") or "Cliente"
                pago = str(cobro.get("pago_id") or "").strip()
                f9 = (not pago) or pago.upper() == "F9 MANUAL"
                filas.append(_fila(
                    fecha=cobro.get("fecha") or "",
                    pago_id=pago if not f9 else "",
                    f9=f9,
                    nombre=f"Cobranza {medio} · {quien}",
                    monto=float(cobro.get("monto") or 0),
                    monto_ticket=float(cobro.get("monto") or 0),
                    estado="COBRANZA",
                    ticket_cobro=cobro.get("ticket_cobro") or clave,
                    op_type="cobranza",
                ))
            except Exception:
                continue
        filas = _cerrar_parejas_unicas(filas)
        filas.sort(key=lambda r: r.get("fecha") or "", reverse=True)
    except Exception:
        return filas
    return filas


def _cerrar_parejas_unicas(filas):
    """Pago MP y ticket del mismo monto, únicos y a pocos minutos: una sola fila FIRMADO. No escribe la base."""
    try:
        from src.motor_cobros_digitales.enlace.automatico import _dt, parejas
    except Exception:
        return filas
    sueltos = []
    ventas = []
    idx_pago = {}
    idx_venta = {}
    for i, f in enumerate(filas or []):
        est = str(f.get("estado") or "").upper()
        if est == "SIN TICKET":
            pid = str(f.get("id") or "").strip()
            cuando = _dt(f.get("fecha"))
            if pid and pid not in ("—", "-") and cuando:
                sueltos.append((pid, cuando, float(f.get("monto_mp") or f.get("monto") or 0)))
                idx_pago[pid] = i
        elif est == "SIN FIRMAR":
            nro = str(f.get("ticket_venta") or "").strip()
            cuando = _dt(f.get("fecha"))
            if nro and nro not in ("—", "-") and cuando:
                ventas.append((nro, cuando, float(f.get("monto_ticket") or f.get("monto") or 0)))
                idx_venta[nro] = i
    if not sueltos or not ventas:
        return filas
    quitar = set()
    try:
        pares = parejas(ventas, sueltos)
    except Exception:
        return filas
    for pid, nro in pares:
        i_p = idx_pago.get(pid)
        i_v = idx_venta.get(nro)
        if i_p is None or i_v is None:
            continue
        pago = filas[i_p]
        venta = filas[i_v]
        pago["estado"] = "FIRMADO"
        pago["ticket_venta"] = nro
        pago["ticket"] = nro
        pago["monto_ticket"] = float(venta.get("monto_ticket") or venta.get("monto") or 0)
        pago["monto"] = pago["monto_ticket"] or float(pago.get("monto") or 0)
        pago["nombre"] = venta.get("nombre") or pago.get("nombre")
        quitar.add(i_v)
    if not quitar:
        return filas
    return [f for i, f in enumerate(filas) if i not in quitar]
