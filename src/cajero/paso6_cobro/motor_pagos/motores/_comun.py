from src.cajero.paso6_cobro.motor_pagos.comandos.persistir_cobro import persistir_cobro
from src.cajero.paso6_cobro.motor_pagos.comandos.post_cobro import post_cobro
from src.cajero.paso6_cobro.motor_pagos.consultas.venta import carrito_valido


def ejecutar_comun(datos, extra_validar=None):
    if not carrito_valido(datos.get("items_carrito")):
        return False, "El carrito esta vacio."
    if extra_validar:
        err = extra_validar(datos)
        if err:
            return False, err
    id_v, resultado = persistir_cobro(datos)
    if not id_v:
        return False, (resultado or {}).get("error") or "Error al guardar la venta en la base de datos."
    if resultado.get("cliente_nombre"):
        datos["cliente_nombre"] = resultado["cliente_nombre"]
    post_cobro(datos, id_v, resultado)
    return True, None
