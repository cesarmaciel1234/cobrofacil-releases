"""Abona una deuda previa desde Fiado sin alterar el total de la venta actual."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoAbonoPrevio:
    ok: bool
    cancelado: bool = False
    cliente_id: int = 0
    monto: float = 0.0
    nombre: str = ""
    saldo: float = 0.0
    deuda_anterior: float = 0.0
    aviso: str = ""


def cobrar_deuda_previa(parent, cliente) -> ResultadoAbonoPrevio:
    """Abre F6 para el cliente actual y registra el abono como movimiento separado."""
    from src.cajero.ingresar_efectivo import DialogoIngresoEfectivo
    from src.clientes_fiado.interfaz.cobro.medios.cerrar import asentar
    from src.config import config
    from src.utils.qt_compat import qt_exec

    dlg = DialogoIngresoEfectivo(parent=parent)
    dlg.abrir_para_cliente(cliente)
    if not qt_exec(dlg):
        return ResultadoAbonoPrevio(ok=False, cancelado=True)
    try:
        cliente_id = int(dlg.cliente_id)
        ficha_id = int(cliente.get("id"))
    except (TypeError, ValueError):
        cliente_id = ficha_id = 0
    if (
        dlg.tipo_ingreso != "FIADO"
        or not cliente_id
        or cliente_id != ficha_id
        or dlg.monto_ingresado <= 0
        or dlg.resultado is None
        or not getattr(dlg.resultado, "ok", False)
    ):
        return ResultadoAbonoPrevio(
            ok=False,
            aviso="No se pudo confirmar el abono. La venta sigue pendiente.",
        )

    from src.cajero.cajero_activo import CajeroActivo

    hecho = asentar(
        cliente_id,
        dlg.monto_ingresado,
        dlg.deuda_actual,
        "Cajero",
        CajeroActivo.nombre,
        dlg.resultado,
        imprimir_saldo=False,
    )
    if not hecho.get("ok"):
        return ResultadoAbonoPrevio(
            ok=False,
            aviso=hecho.get("aviso") or "No se pudo registrar el abono. La venta sigue pendiente.",
        )

    aviso = ""
    if hecho.get("entra_caja"):
        from src.cajero.paso5_terminal.logica.movimientos_caja_service import MovimientosCajaService

        registrado = MovimientosCajaService().registrar_ingreso_efectivo(
            hecho["monto_caja"],
            CajeroActivo.nombre,
            hecho["motivo"],
            config.get("caja_id", 1),
            abrir_cajon=False,
            imprimir=False,
        )
        if not registrado:
            aviso = "El abono quedó registrado, pero no se pudo anotar el efectivo en la caja."

    return ResultadoAbonoPrevio(
        ok=True,
        cliente_id=cliente_id,
        monto=float(dlg.monto_ingresado),
        nombre=str(hecho.get("nombre") or cliente.get("nombre") or "Cliente"),
        saldo=float(hecho.get("saldo") or 0.0),
        deuda_anterior=float(dlg.deuda_actual or 0.0),
        aviso=aviso,
    )
