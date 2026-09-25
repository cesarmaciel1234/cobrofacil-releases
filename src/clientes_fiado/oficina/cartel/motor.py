from src.clientes_fiado.oficina.cartel.nombre import SubmotorNombre
from src.clientes_fiado.oficina.cartel.saldos import SubmotorSaldos
from src.clientes_fiado.oficina.cuenta.motor import MotorCuenta


def _ficha(fila):
    if isinstance(fila, dict):
        return dict(fila)
    if hasattr(fila, "keys"):
        try:
            return {clave: fila[clave] for clave in fila.keys()}
        except Exception:
            return {}
    return {}


class MotorCartel:
    """Llena el cartel de confirmación. Un submotor que falla no corta a los otros."""

    def __init__(self):
        self.nombre = SubmotorNombre()
        self.saldos = SubmotorSaldos()
        self.cuenta = MotorCuenta()

    def armar(self, cliente):
        ficha = _ficha(cliente)
        try:
            fresco = self.cuenta.obtener(ficha.get("id"))
            if fresco:
                ficha = _ficha(fresco)
        except Exception:
            pass
        saludo = "Sin datos"
        try:
            saludo = self.nombre.leer(ficha) or "Sin datos"
        except Exception:
            saludo = "Sin datos"
        saldo, disponible = None, None
        try:
            saldo, disponible = self.saldos.leer(ficha)
        except Exception:
            saldo, disponible = None, None
        return {"saludo": saludo, "saldo": saldo, "disponible": disponible}
