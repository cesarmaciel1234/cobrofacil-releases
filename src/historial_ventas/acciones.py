from src.historial_ventas.caja import controller


def detalle(id_venta: int):
    return controller().get_detalle_venta(int(id_venta))


def cancelar(id_venta: int, username: str) -> bool:
    return controller().cancelar_venta(int(id_venta), username)


def reimprimir(id_venta: int) -> None:
    controller().reimprimir_ticket(int(id_venta))
