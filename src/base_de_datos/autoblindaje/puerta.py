"""La clase junta las cuatro piezas. Las constantes son de todas."""

from src.base_de_datos.autoblindaje.grabar.diario import Grabar
from src.base_de_datos.autoblindaje.quien.maestra import Quien
from src.base_de_datos.autoblindaje.rutas.carpetas import Rutas
from src.base_de_datos.autoblindaje.sanar.integridad import Sanar


class AutoBlindajeDB(Rutas, Quien, Grabar, Sanar):
    """Respaldo del negocio: tres carpetas, la maestra de ahora, y la cura si la base se rompe."""

    PERIODIC_INTERVAL_HOURS = 0.5
    MAX_DAILY_STYLE = 30
    MAX_PRE_RESTORE = 20
    TABLAS_INCREMENTAL_VENTA = (
        "ventas",
        "detalles_ventas",
        "detalle_ventas",
        "movimientos_caja",
    )
