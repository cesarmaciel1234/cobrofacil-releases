"""Un solo camino para restaurar, venga la copia del admin o del jefe."""

from __future__ import annotations

import datetime as _dt
import os

from src.logger import logger

from .destino import Destino, destino_actual
from .sumar import sumar


def modo(fuente, destino: Destino) -> str:
    """reemplazo: el respaldo pisa sus tablas y se recargan las ventas de hoy. suma: solo agrega lo que falta."""
    if fuente.tipo == "copia":
        return "suma"
    if fuente.tipo == "sqlite":
        return "reemplazo" if destino.motor == "sqlite" else "suma"
    return "reemplazo"


def _mysql_exe() -> str:
    from src.utils.paths import get_base_path

    return os.path.join(get_base_path(), "mariadb_server", "bin", "mysql.exe")


def revisar(fuente, destino: Destino) -> tuple[list[str], list[str]]:
    """(bloqueos, avisos). Con un bloqueo no se restaura; los avisos se muestran antes de confirmar."""
    bloqueos, avisos = [], []
    como = modo(fuente, destino)
    if fuente.tipo in ("sql", "zip") and destino.motor == "sqlite":
        bloqueos.append("Este respaldo es de MariaDB y esta tienda trabaja con SQLite.")
    if fuente.tipo == "zip" and not destino.es_local:
        bloqueos.append("El respaldo físico (.zip) solo se restaura sentado en la maestra.")
    if fuente.tipo == "sql" and destino.motor == "mariadb" and not os.path.isfile(_mysql_exe()):
        bloqueos.append("Falta mariadb_server\\bin\\mysql.exe en esta PC para aplicar el .sql.")

    if fuente.tipo == "copia":
        if fuente.servidor and destino.servidor and fuente.servidor != destino.servidor:
            avisos.append(f"Esta copia es de otra maestra ({fuente.servidor}). La tienda conectada es {destino.servidor}.")
        elif not fuente.servidor:
            avisos.append("La copia no dice de qué maestra salió (es anterior a esta versión).")
        if not fuente.completa:
            avisos.append(
                f"Copia parcial ({fuente.tablas} tablas): usuarios, configuración y el resto quedan como están en la tienda."
            )
    if fuente.detalle == "solo ventas y caja":
        avisos.append("Este respaldo solo trae ventas, detalles y caja.")
    if fuente.fecha.date() < _dt.date.today():
        avisos.append(f"Los datos son del {fuente.fecha:%d/%m/%Y %H:%M}.")
    if como == "suma":
        avisos.append(
            "Solo se agrega lo que le falta a la tienda: no se borra ni se pisa nada. "
            "Lo que se borró en la tienda después de esta copia vuelve a aparecer."
        )
    else:
        avisos.append(
            "Las tablas del respaldo reemplazan a las de la tienda y después se vuelven a cargar las ventas de hoy."
        )
    avisos.append("Antes se guarda una foto de la tienda como está (pre_restore).")
    return bloqueos, avisos


def _foto_antes(destino: Destino) -> None:
    from src.base_de_datos.autoblindaje_db import AutoBlindajeDB

    AutoBlindajeDB.crear_snapshot_pre_restore(destino.motor, destino.host or "127.0.0.1")


def _respaldo_despues(destino: Destino) -> None:
    from src.base_de_datos.autoblindaje_db import AutoBlindajeDB

    try:
        AutoBlindajeDB.crear_backup_diario_si_corresponde(destino.motor, destino.host or "127.0.0.1", force=True)
    except Exception as e:
        logger.warning(f"Restaurar: no se pudo sellar el respaldo del día ({e})")


def _reemplazar(fuente, destino: Destino) -> dict:
    from src.base_de_datos.autoblindaje_db import AutoBlindajeDB

    ok = AutoBlindajeDB.restaurar_ultimo_backup_valido(
        destino.motor,
        allow_older_than_today=True,
        mariadb_host=destino.host or "127.0.0.1",
        merge_today=True,
        backup_path=fuente.ruta,
    )
    if not ok:
        raise RuntimeError("El respaldo no se pudo aplicar. Revisá el log.")
    return {}


def restaurar(fuente, destino: Destino | None = None, progreso=None) -> dict:
    """Aplica la copia a la tienda. Devuelve el modo y, si sumó, cuánto entró por tabla."""
    destino = destino or destino_actual()
    bloqueos, _ = revisar(fuente, destino)
    if bloqueos:
        raise RuntimeError(bloqueos[0])
    como = modo(fuente, destino)
    logger.info(f"Restaurar: {fuente.ruta} → {destino.motor} {destino.host or destino.archivo} ({como})")
    if progreso:
        progreso(2, "Guardando foto de la tienda…")
    if como == "suma":
        _foto_antes(destino)
        res = sumar(fuente.ruta, destino, progreso)
        _respaldo_despues(destino)
    else:
        if progreso:
            progreso(10, "Aplicando respaldo…")
        res = _reemplazar(fuente, destino)
    if progreso:
        progreso(100, "Listo")
    return {"modo": como, **res}
