"""Cálculo simple de interés por ticket a partir del libro de cuenta."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


TASA_MENSUAL = Decimal("0.03")
TASA_APALANCAMIENTO = Decimal("0.05")
DIAS_MES = Decimal("30")
PLAZO_DIAS_CORTE = 30


def politicas_activas() -> tuple[Decimal, Decimal, int]:
    try:
        from src.clientes_fiado.oficina.barrial.mantenimiento import (
            porcentaje_base,
            porcentaje_apalancamiento,
            plazo_dias_defecto,
        )
        base = Decimal(str(porcentaje_base())) / Decimal("100")
        apal = Decimal(str(porcentaje_apalancamiento())) / Decimal("100")
        plazo = int(plazo_dias_defecto())
        return base, apal, plazo
    except Exception:
        return TASA_MENSUAL, TASA_APALANCAMIENTO, PLAZO_DIAS_CORTE
INICIO_ACTIVACION = "interes_ticket_activado_en"
MARCA_INTERES = "INTERÉS MENSUAL · 3%"
MARCA_DETALLE = "\n[TPV_INTERES_TICKET_V1]"
MARCA_REVERSO = "\n[TPV_INTERES_REVERSO_V1]"
CENTAVO = Decimal("0.01")


def _ficha(fila) -> dict:
    if isinstance(fila, dict):
        return fila
    if hasattr(fila, "keys"):
        return {clave: fila[clave] for clave in fila.keys()}
    return {}


def _decimal(valor) -> Decimal:
    try:
        numero = Decimal(str(valor or 0))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(f"Monto inválido en cuenta corriente: {valor!r}") from error
    if not numero.is_finite():
        raise ValueError("Monto no finito en cuenta corriente")
    return numero


def _fecha(valor) -> datetime:
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=None)
    if isinstance(valor, date):
        return datetime.combine(valor, time.min)
    texto = str(valor or "").strip()
    if not texto:
        raise ValueError("Movimiento de cuenta sin fecha")
    texto = texto.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(texto).replace(tzinfo=None)
    except ValueError as error:
        raise ValueError(f"Fecha inválida en cuenta corriente: {texto!r}") from error


def _a_centavos(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def clave_ticket(fila) -> str:
    dato = _ficha(fila)
    venta_id = dato.get("venta_id")
    if venta_id not in (None, "", 0, "0"):
        return f"V:{str(venta_id).strip()}"
    tipo = str(dato.get("tipo") or "").upper()
    desc = str(dato.get("descripcion") or "")
    if desc.startswith(MARCA_INTERES) or "MANTENIMIENTO" in desc:
        return ""
    mov_id = dato.get("id")
    if tipo == "CARGO" and mov_id not in (None, "", 0, "0"):
        return f"M:{str(mov_id).strip()}"
    if tipo == "ANULACION":
        hallado = re.search(r"cargo\s+#(\d+)", desc, re.IGNORECASE)
        if hallado:
            return f"M:{hallado.group(1)}"
    return ""


def _monto_ticket(dato) -> Decimal:
    return _decimal(dato.get("monto"))


def _leer_detalle(descripcion: str):
    inicio = descripcion.find(MARCA_DETALLE)
    if inicio < 0:
        return None
    bruto = descripcion[inicio + len(MARCA_DETALLE):]
    try:
        detalle = json.loads(bruto)
    except json.JSONDecodeError as error:
        raise ValueError("Detalle de interés por ticket dañado") from error
    if not isinstance(detalle, dict) or not detalle:
        raise ValueError("Detalle de interés por ticket vacío o inválido")
    salida = {}
    for clave, monto in detalle.items():
        clave = str(clave)
        if not (clave.startswith("V:") or clave.startswith("M:")):
            raise ValueError("Clave de ticket inválida en el interés")
        valor = _decimal(monto)
        if valor <= 0:
            raise ValueError("Monto de interés inválido en el detalle")
        salida[clave] = valor
    return salida


def _leer_reverso(descripcion: str):
    inicio = descripcion.find(MARCA_REVERSO)
    if inicio < 0:
        return None
    bruto = descripcion[inicio + len(MARCA_REVERSO):]
    try:
        detalle = json.loads(bruto)
    except json.JSONDecodeError as error:
        raise ValueError("Reverso de interés por ticket dañado") from error
    if not isinstance(detalle, dict):
        raise ValueError("Reverso de interés por ticket inválido")
    clave = str(detalle.get("ticket") or "")
    monto = _decimal(detalle.get("monto"))
    if not (clave.startswith("V:") or clave.startswith("M:")) or monto < 0:
        raise ValueError("Reverso de interés por ticket inválido")
    return clave, monto


def descripcion_interes(detalle: dict[str, Decimal]) -> str:
    datos = {
        clave: format(_a_centavos(monto), ".2f")
        for clave, monto in detalle.items()
        if _a_centavos(monto) > 0
    }
    if not datos:
        raise ValueError("No hay interés para registrar")
    return MARCA_INTERES + MARCA_DETALLE + json.dumps(
        datos, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    )


def descripcion_reverso(ticket: str, monto: Decimal) -> str:
    prefijo = "cargo manual #" if str(ticket).startswith("M:") else "ticket #"
    ref_txt = str(ticket)[2:]
    return (
        f"Reversión de interés · {prefijo}{ref_txt}"
        + MARCA_REVERSO
        + json.dumps(
            {"ticket": ticket, "monto": format(_a_centavos(monto), ".2f")},
            ensure_ascii=True,
            separators=(",", ":"),
        )
    )


def proyectar_interes(
    movimientos,
    fecha_activacion,
    ahora=None,
    tasa_base=None,
    tasa_apal=None,
    dias_plazo=None,
) -> dict:
    """Reconstruye capital e interés desde el libro, sin capitalizar intereses."""
    activacion = _fecha(fecha_activacion)
    hasta = _fecha(ahora or datetime.now())
    cfg_base, cfg_apal, cfg_plazo = politicas_activas()
    t_base = _decimal(tasa_base if tasa_base is not None else cfg_base)
    t_apal = _decimal(tasa_apal if tasa_apal is not None else cfg_apal)
    plazo_activo = int(dias_plazo if dias_plazo is not None else cfg_plazo)

    filas = [_ficha(fila) for fila in (movimientos or [])]
    eventos = []
    anulaciones_ticket = set()
    for indice, dato in enumerate(filas):
        tipo = str(dato.get("tipo") or "").upper()
        if tipo == "ANULACION" and clave_ticket(dato):
            anulaciones_ticket.add(clave_ticket(dato))
        fecha = _fecha(dato.get("fecha"))
        try:
            orden = int(dato.get("id") or indice)
        except (TypeError, ValueError):
            orden = indice
        eventos.append((fecha, orden, indice, dato))
    eventos.sort(key=lambda evento: (evento[0], evento[1], evento[2]))

    tickets = {}
    orden_tickets = []
    otros = []

    def acumular_hasta(destino: datetime):
        t_destino = destino.date()
        for ticket in orden_tickets:
            estado = tickets[ticket]
            if not estado["activo"] or estado["capital"] <= 0:
                estado["ultima_fecha"] = max(estado["ultima_fecha"], destino)
                continue
            desde = max(estado["ultima_fecha"], estado["inicio"])
            t_desde = desde.date()
            if t_destino <= t_desde:
                estado["ultima_fecha"] = max(estado["ultima_fecha"], destino)
                continue

            t_inicio = estado["inicio"].date()
            fecha_corte = t_inicio + timedelta(days=plazo_activo)

            fin_normal = min(t_destino, max(t_desde, fecha_corte))
            dias_normal = max(0, (fin_normal - t_desde).days)

            ini_apal = max(t_desde, fecha_corte)
            dias_apal = max(0, (t_destino - ini_apal).days)

            if dias_normal or dias_apal:
                tasa_normal = t_base / DIAS_MES
                tasa_morosa = (t_base + t_apal) / DIAS_MES
                interes_tramo = estado["capital"] * (
                    tasa_normal * Decimal(dias_normal) + tasa_morosa * Decimal(dias_apal)
                )
                estado["no_facturado"] += interes_tramo

            estado["ultima_fecha"] = max(estado["ultima_fecha"], destino)

    def pagar_cargos(monto: Decimal, cargos):
        restante = monto
        for cargo in cargos:
            if restante <= 0:
                break
            saldo = cargo["saldo"]
            aplicado = min(saldo, restante)
            cargo["saldo"] -= aplicado
            restante -= aplicado
            if cargo["ticket"]:
                estado = tickets[cargo["ticket"]]
                estado["capital"] = max(Decimal("0"), estado["capital"] - aplicado)
        return restante

    for fecha, _orden, _indice, dato in eventos:
        if fecha > hasta:
            continue
        acumular_hasta(fecha)
        tipo = str(dato.get("tipo") or "").upper()
        descripcion = str(dato.get("descripcion") or "")
        clave = clave_ticket(dato)

        if tipo == "CARGO":
            detalle = _leer_detalle(descripcion)
            if detalle is not None:
                total_detalle = sum(detalle.values(), Decimal("0"))
                if _a_centavos(total_detalle) != _a_centavos(_monto_ticket(dato)):
                    raise ValueError("El detalle de interés no coincide con su movimiento")
                for ticket, interes in detalle.items():
                    estado = tickets.get(ticket)
                    if estado is None or not estado["activo"]:
                        raise ValueError("Interés asociado a un ticket inexistente o cancelado")
                    estado["interes_en_saldo"] += interes
                    estado["interes_generado"] += interes
                    estado["no_facturado"] = Decimal("0")
                continue

            if clave:
                if clave in tickets:
                    raise ValueError(f"Ticket duplicado en cuenta corriente: {clave}")
                fecha_inicio = max(fecha, activacion)
                estado = {
                    "id": dato.get("id"),
                    "ticket": clave,
                    "venta_id": dato.get("venta_id"),
                    "inicio": fecha_inicio,
                    "ultima_fecha": fecha_inicio,
                    "capital": max(Decimal("0"), _monto_ticket(dato)),
                    "interes_en_saldo": Decimal("0"),
                    "interes_generado": Decimal("0"),
                    "interes_pagado": Decimal("0"),
                    "no_facturado": Decimal("0"),
                    "activo": True,
                }
                tickets[clave] = estado
                orden_tickets.append(clave)
                otros.append({"id": dato.get("id"), "ticket": clave, "saldo": estado["capital"]})
                if (
                    str(descripcion).startswith(("BORRADO · ", "CANCELADO · "))
                    and clave not in anulaciones_ticket
                ):
                    estado["capital"] = Decimal("0")
                    estado["activo"] = False
                    otros[-1]["saldo"] = Decimal("0")
            else:
                otros.append({
                    "id": dato.get("id"),
                    "ticket": "",
                    "saldo": max(Decimal("0"), _monto_ticket(dato)),
                })
            continue

        if tipo == "ABONO":
            restante = max(Decimal("0"), _monto_ticket(dato))
            if fecha < activacion:
                restante = pagar_cargos(restante, otros)
            else:
                for ticket in orden_tickets:
                    if restante <= 0:
                        break
                    estado = tickets[ticket]
                    if not estado["activo"]:
                        continue
                    aplicado = min(estado["interes_en_saldo"], restante)
                    estado["interes_en_saldo"] -= aplicado
                    estado["interes_pagado"] += aplicado
                    restante -= aplicado
                for ticket in orden_tickets:
                    if restante <= 0:
                        break
                    estado = tickets[ticket]
                    if not estado["activo"]:
                        continue
                    aplicado = min(estado["capital"], restante)
                    estado["capital"] -= aplicado
                    restante -= aplicado
                    for cargo in otros:
                        if cargo["ticket"] == ticket:
                            cargo["saldo"] = max(Decimal("0"), cargo["saldo"] - aplicado)
                            break
                restante = pagar_cargos(
                    restante, [cargo for cargo in otros if not cargo["ticket"]]
                )
                # Al pagar, el saldo remanente arranca su conteo diario desde la fecha del abono
                for ticket in orden_tickets:
                    estado = tickets[ticket]
                    if estado["capital"] > Decimal("0.009"):
                        estado["no_facturado"] = Decimal("0")
                        estado["ultima_fecha"] = max(estado["ultima_fecha"], fecha)
                        estado["inicio"] = max(estado["inicio"], fecha)
            continue

        if tipo == "ANULACION":
            reverso = _leer_reverso(descripcion)
            if clave and clave in tickets:
                estado = tickets[clave]
                estado["capital"] = Decimal("0")
                estado["activo"] = False
                estado["no_facturado"] = Decimal("0")
                estado["interes_en_saldo"] = Decimal("0")
                for cargo in otros:
                    if cargo["ticket"] == clave:
                        cargo["saldo"] = Decimal("0")
                        break
                if reverso is not None:
                    ticket_reversado, monto_reversado = reverso
                    if ticket_reversado != clave:
                        raise ValueError("El reverso no coincide con el ticket anulado")
                    estado["interes_generado"] = max(
                        Decimal("0"), estado["interes_generado"] - monto_reversado
                    )
                continue
            if reverso is not None:
                raise ValueError("Reversión de interés sin ticket en el historial")
            hallado = re.search(r"cargo\s+#(\d+)", descripcion, re.IGNORECASE)
            if hallado:
                cargo_id = hallado.group(1)
                for cargo in otros:
                    if str(cargo["id"]) == cargo_id:
                        cargo["saldo"] = Decimal("0")
                        break

    acumular_hasta(hasta)
    salida = {}
    for clave in orden_tickets:
        estado = tickets[clave]
        dias = max(0, (hasta.date() - estado["inicio"].date()).days)
        if not estado["activo"]:
            continue
        if estado["capital"] <= Decimal("0.009"):
            interes_acum = Decimal("0")
            interes_crudo = Decimal("0")
            dias_vis = 0
        else:
            interes_acum = _a_centavos(estado["no_facturado"])
            interes_crudo = estado["no_facturado"]
            dias_vis = dias

        salida[clave] = {
            "id": estado["id"],
            "ticket": clave,
            "venta_id": estado["venta_id"],
            "capital_pendiente": float(estado["capital"]),
            "interes_en_saldo": float(estado["interes_en_saldo"]),
            "interes_generado": float(estado["interes_generado"]),
            "interes_pagado": float(estado["interes_pagado"]),
            "interes_acumulado": float(interes_acum),
            "interes_crudo": float(interes_crudo),
            "dias": dias_vis,
            "dias_plazo": plazo_activo,
            "en_apalancamiento": dias_vis > plazo_activo,
        }
    total_nuevo = sum(
        (_decimal(dato["interes_acumulado"]) for dato in salida.values()),
        Decimal("0"),
    )
    return {
        "tickets": salida,
        "interes_acumulado": float(total_nuevo),
        "fecha_calculo": hasta,
    }
