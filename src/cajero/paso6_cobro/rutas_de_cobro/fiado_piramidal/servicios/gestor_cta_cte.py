# -*- coding: utf-8 -*-
"""
Este gestor actúa como PUENTE.
No hace queries de SQL directamente, sino que llama a las funciones globales de
src.clientes_fiado.cerebro.cerebro para mantener el TPV centralizado.
"""

from src.clientes_fiado.cerebro.cerebro import asentar_fiado, abonar_deuda

def asentar_nueva_deuda(cliente_id, monto, admin_name=""):
    """
    Ruta 1 (Margen OK) usa admin_name=""
    Ruta 2 (Límite Superado) usa admin_name="Nombre Admin"
    """
    return asentar_fiado(cliente_id, monto, admin_name)

def saldar_deuda_f5(cliente_id, monto_abonado):
    """
    Cuando se usa el Puente F5 para bajar la deuda en vivo.
    """
    return abonar_deuda(cliente_id, monto_abonado)
