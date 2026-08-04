"""Fachada pública del cerebro de cierre (compat con imports existentes)."""

from __future__ import annotations

from src.cerebro_global.cierre_caja_cerebro.procesos.cierre import cerrar_caja as _cerrar_caja
from src.cerebro_global.cierre_caja_cerebro.procesos.modos import normalizar_modo
from src.cerebro_global.cierre_caja_cerebro.procesos.historial_cortes import (
    listar_cortes_del_dia as _listar_cortes_del_dia,
    resumen_cortes_por_cajero as _resumen_cortes_por_cajero,
)
from src.cerebro_global.cierre_caja_cerebro.procesos.multi_caja import (
    listar_caja_ids,
    resumen_multi_caja,
)
from src.cerebro_global.cierre_caja_cerebro.procesos.totales import obtener_datos_cierre


class MotorCierre:
    """
    Cerebro Global para el Cierre de Caja.
    Delega en procesos/ (totales, esperado, cierre, modos, multi_caja).
    """

    @staticmethod
    def obtener_datos_cierre_diario(fecha_str=None, cajero=None, caja_id=None):
        # Sin caja_id en modo supervisión → consolidado multi-caja (no arqueable)
        if caja_id is None and cajero is None:
            return resumen_multi_caja(fecha_str=fecha_str)
        return obtener_datos_cierre(
            fecha_str=fecha_str,
            cajero=cajero,
            caja_id=caja_id,
        )

    @staticmethod
    def resumen_tienda(fecha_str=None):
        return resumen_multi_caja(fecha_str=fecha_str)

    @staticmethod
    def listar_cajas():
        return listar_caja_ids()

    @staticmethod
    def listar_cortes_del_dia(fecha_str=None, caja_id=None, cajero=None):
        return _listar_cortes_del_dia(fecha_str=fecha_str, caja_id=caja_id, cajero=cajero)

    @staticmethod
    def resumen_cortes_por_cajero(fecha_str=None, caja_id=None):
        return _resumen_cortes_por_cajero(fecha_str=fecha_str, caja_id=caja_id)

    @staticmethod
    def cerrar_caja(username, caja_id, fisico, dif, esperado, t_total, modo):
        if caja_id is None:
            raise ValueError(
                "Debés elegir una caja concreta. En cadenas el arqueo es por terminal, no global."
            )
        return _cerrar_caja(
            username=username,
            caja_id=caja_id,
            fisico=fisico,
            dif=dif,
            esperado=esperado,
            t_total=t_total,
            modo=normalizar_modo(modo),
        )
