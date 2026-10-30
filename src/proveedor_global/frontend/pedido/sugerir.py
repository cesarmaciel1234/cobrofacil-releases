"""Cuánto pedir de un suelto, con el reparto del proveedor y el stock medido.

No usa el pico de una compra vieja. Si no hay días, no inventa la cantidad.
"""

from datetime import date

from src.proveedor_global.frontend.pedido.reparto import dias as dias_de
from src.proveedor_global.frontend.pedido.stock_memoria import anotar, puntos
from src.proveedor_global.frontend.predictiva.motor.calcular import definir, proyectar


def preparar(pedidos) -> None:
    """Anota el stock de hoy y, si ya se puede, cambia la cantidad del suelto."""
    hoy = date.today()
    pares = []
    for info in (pedidos or {}).values():
        for item in info.get("items") or []:
            if item.get("es_formula") or item.get("id") is None:
                continue
            pares.append((item.get("id"), item.get("stock_actual")))
    if pares:
        anotar(hoy.isoformat(), pares)
    for nombre, info in (pedidos or {}).items():
        aplicar_grupo(nombre, info, hoy)


def aplicar_grupo(nombre, info, hoy=None) -> None:
    if not isinstance(info, dict):
        return
    hoy = hoy or date.today()
    reparto = dias_de(nombre)
    costo = 0.0
    presupuesto = 0.0
    for item in info.get("items") or []:
        if not item.get("es_formula"):
            decision = decidir(
                item.get("stock_actual"),
                reparto,
                puntos(item.get("id")),
                hoy,
            )
            if decision.get("aplica"):
                pedido = float(decision.get("pedir") or 0)
                item["cantidad_a_pedir"] = pedido
                item["motivo"] = "stock"
                base = float(item.get("valor_unitario") or item.get("costo_unitario") or 0)
                item["presupuesto_linea"] = round(pedido * base, 2)
                item["costo_estimado_total"] = round(
                    pedido * float(item.get("costo_unitario") or 0), 2
                )
            if decision.get("porque"):
                item["porque"] = decision["porque"]
        costo += float(item.get("costo_estimado_total") or 0)
        presupuesto += float(item.get("presupuesto_linea") or item.get("costo_estimado_total") or 0)
    info["costo_total_estimado"] = round(costo, 2)
    info["presupuesto_estimado"] = round(presupuesto, 2)


def decidir(stock, reparto, serie, hoy) -> dict:
    """aplica False deja la alarma como está. El texto igual puede decir que faltan días."""
    try:
        actual = float(stock or 0)
    except (TypeError, ValueError):
        actual = 0.0
    ritmo, corto, medido, tasas = _medir(serie)
    banda = definir(tasas)
    if banda["listo"] and ritmo > float(banda["maximo"] or 0):
        ritmo = float(banda["maximo"])
    if actual <= 0:
        corto = True
    if not reparto:
        if corto:
            return {
                "aplica": False,
                "porque": "Stock en cero: nos quedamos cortos. Faltan los días de reparto del proveedor.",
            }
        return {"aplica": False, "porque": ""}
    if not medido and corto:
        return {
            "aplica": True,
            "pedir": 0,
            "porque": (
                "Stock en cero: nos quedamos cortos. "
                "Todavía no hay un mes de stock para saber cuánto. No se repite la compra vieja."
            ),
        }
    if medido and ritmo <= 0 and not corto:
        return {
            "aplica": True,
            "pedir": 0,
            "porque": "Sin movimiento antes del reparto. No se pide de más.",
        }
    if not medido:
        return {"aplica": False, "porque": ""}
    proy = proyectar(hoy, reparto, ritmo, max(actual, 0.0), "unidades")
    if corto:
        proy["porque"] += " El stock llegó a cero: nos quedamos cortos."
    if banda["listo"]:
        proy["porque"] += (
            f" Pico viejo {_num(banda['pico'])} por día, no se compra."
            f" Mínimo histórico {_num(banda['minimo'])}."
            f" Máximo histórico {_num(banda['maximo'])}."
        )
    proy["aplica"] = True
    return proy


def _medir(serie) -> tuple:
    """Venta por día hasta el primer cero. Los días ya en cero no bajan el ritmo."""
    limpios = []
    for fila in serie or []:
        if not isinstance(fila, dict) or not fila.get("fecha"):
            continue
        try:
            cuando = date.fromisoformat(str(fila["fecha"])[:10])
            stock = float(fila.get("stock") or 0)
        except (TypeError, ValueError):
            continue
        limpios.append((cuando, stock))
    limpios.sort(key=lambda par: par[0])
    if len(limpios) < 2:
        return 0.0, False, False, []
    vendido = 0.0
    corto = False
    tasas = []
    fin = limpios[-1][0]
    for indice in range(1, len(limpios)):
        previo = limpios[indice - 1][1]
        actual = limpios[indice][1]
        if actual <= previo:
            tramo = max(1, (limpios[indice][0] - limpios[indice - 1][0]).days)
            tasas.append((previo - actual) / tramo)
        if previo > actual:
            vendido += previo - actual
        if actual <= 0:
            corto = True
            if previo > 0:
                fin = limpios[indice][0]
                break
    dias = max(1, (fin - limpios[0][0]).days)
    return vendido / dias, corto, True, tasas


def _num(valor) -> str:
    return f"{float(valor):.2f}".rstrip("0").rstrip(".")
