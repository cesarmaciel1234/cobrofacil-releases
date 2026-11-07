"""Estado de cuenta barrial: activo | suspendido."""

from src.clientes_fiado.oficina.barrial.reglas import ESTADO_ACTIVO, ESTADO_SUSPENDIDO


def normalizar(valor) -> str:
    texto = str(valor or "").strip().lower()
    if texto == ESTADO_SUSPENDIDO:
        return ESTADO_SUSPENDIDO
    return ESTADO_ACTIVO


def esta_suspendido(cliente) -> bool:
    if not cliente:
        return False
    ficha = dict(cliente) if not isinstance(cliente, dict) else cliente
    return normalizar(ficha.get("estado_cuenta")) == ESTADO_SUSPENDIDO


def suspender(cliente_id) -> bool:
    """Marca suspendido. Auditoría SUSPENDIDO. No toca la deuda."""
    from src.clientes_fiado.oficina.huella.eventos import editar

    return bool(editar(cliente_id, {"estado_cuenta": ESTADO_SUSPENDIDO}, accion="SUSPENDIDO"))


def reactivar(cliente_id) -> bool:
    """Vuelve a activo. Auditoría REACTIVADO."""
    from src.clientes_fiado.oficina.huella.eventos import editar

    return bool(editar(cliente_id, {"estado_cuenta": ESTADO_ACTIVO}, accion="REACTIVADO"))
