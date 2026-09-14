"""Cerebro Jefe: insiste en inventario y costo. No usa s/d (eso es sin departamento)."""

from src.jefe.reportes.financiero.dinero import fmt_plata, pct_vs


def texto_insights(kpis: dict, chart_data: dict, pago_sum: dict, donut_data: dict) -> str:
    ventas = float(kpis.get("ventas") or 0)
    tickets = int(kpis.get("tickets") or 0)
    ticket_medio = float(kpis.get("ticket_medio") or 0)
    costo = float(kpis.get("costo") or 0)
    ganancia = float(kpis.get("ganancia") or 0)
    margen = float(kpis.get("margen") or 0)
    ventas_prev = kpis.get("ventas_prev")
    pico_label = kpis.get("pico_label") or ""
    pico_val = float(kpis.get("pico_val") or 0)

    if ventas <= 0:
        return (
            "No hay tickets en este periodo. "
            "Mientras tanto: cargá inventario y precio de costo en cada producto. "
            "Sin eso no hay ganancia que firmar."
        )

    if chart_data and not pico_label:
        mejor = max(chart_data.items(), key=lambda x: float(x[1].get("ventas") or 0))
        pico_label, pico_val = mejor[0], float(mejor[1].get("ventas") or 0)

    depto = "sin departamento"
    if donut_data:
        depto = max(donut_data.items(), key=lambda x: x[1])[0]
        if str(depto).strip().lower() in ("", "s/d", "sd", "general", "sin departamento"):
            depto = "sin departamento"
    pago = "sin dato de pago"
    if pago_sum:
        pago = max(pago_sum.items(), key=lambda x: x[1])[0]

    vs = ""
    if ventas_prev is not None:
        vs = f" Vs periodo anterior: {pct_vs(ventas, float(ventas_prev))}."

    if costo <= 0.009:
        gan_txt = (
            "<b>Falta precio de costo.</b> Cargá inventario y costo en productos. "
            "Hasta que no esté, la ganancia neta no se publica "
            f"(si se copiara la venta sería {fmt_plata(ventas)}: eso no se firma)."
        )
    else:
        gan_txt = f"Ganancia neta {fmt_plata(ganancia)} · margen {margen:.0f}%."

    return (
        f"<ul>"
        f"<li style='margin-bottom:8px;'><b>Caja:</b> {fmt_plata(ventas)} en {tickets} tickets "
        f"(ticket medio {fmt_plata(ticket_medio)}).{vs}</li>"
        f"<li style='margin-bottom:8px;'><b>Pico:</b> {pico_label} con {fmt_plata(pico_val)}. "
        f"Departamento: {depto}. Pago: {pago}.</li>"
        f"<li style='margin-bottom:8px;'><b>Costo e inventario:</b> {gan_txt}</li>"
        f"</ul>"
    )
