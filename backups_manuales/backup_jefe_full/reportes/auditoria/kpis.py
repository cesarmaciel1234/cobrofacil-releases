"""Textos de KPI y pie. La vista no calcula."""

from src.jefe.reportes.financiero.dinero import fmt_plata


def tarjeta_comparativa(diff: float) -> tuple[str, str]:
    if diff > 0:
        return f"+{diff:,.1f}%", "green"
    if diff < 0:
        return f"{diff:,.1f}%", "red"
    return "0.0%", "gray"


def pie(tot: dict) -> dict:
    t1, v1 = tot["top1"]
    t2, v2 = tot["top2"]
    return {
        "regs": f"Tickets: {tot['tickets']}  ·  Líneas: {tot['lineas']}",
        "unidades": f"Unidades: {tot['unidades']:,.0f} un",
        "kilos": f"Peso: {tot['kilos']:,.3f} kg",
        "depto1": f"{str(t1)[:16]}: {fmt_plata(v1)}",
        "depto2": f"{str(t2)[:16]}: {fmt_plata(v2)}",
        "otros": f"Otros: {fmt_plata(tot['otros'])}",
        "monto": f"Facturado: {fmt_plata(tot['monto'])}",
    }
