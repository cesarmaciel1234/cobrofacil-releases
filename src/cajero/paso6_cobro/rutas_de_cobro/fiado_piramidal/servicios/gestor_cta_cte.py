# -*- coding: utf-8 -*-
"""
Este gestor actúa como PUENTE.
No hace queries de SQL directamente, sino que llama a las funciones globales de
src.clientes_fiado.cerebro.cerebro para mantener el TPV centralizado.
"""

from src.clientes_fiado.cerebro.cerebro import asentar_fiado


def asentar_nueva_deuda(cliente_id, monto, admin_name=""):
    """
    Ruta 1 (Margen OK) usa admin_name=""
    Ruta 2 (Límite Superado) usa admin_name="Nombre Admin"
    """
    return asentar_fiado(cliente_id, monto, admin_name)
