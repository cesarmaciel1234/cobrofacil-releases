def generar_texto(subcontexto: str = "", usuario: str = "Cajero", **kwargs) -> str:
    if subcontexto == "ticket_x":
        return f"REPORTE X - CORTE PARCIAL. Generado por: {usuario}. Este documento no es un comprobante fiscal."
    elif subcontexto == "ticket_z":
        return f"REPORTE Z - CORTE DE CAJA FINAL. Generado por: {usuario}. Firma del cajero: __________________ Firma del supervisor: __________________"
    else:
        return "DOCUMENTO INTERNO DE AUDITORIA."
