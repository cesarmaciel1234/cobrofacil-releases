def generar_texto(subcontexto: str = "", **kwargs) -> str:
    if subcontexto == "garantia":
        return "Conserve este ticket para cualquier aclaración o garantía. 30 días contra defectos de fábrica."
    elif subcontexto == "devolucion":
        return "Cambios y devoluciones solo dentro de los primeros 7 días presentando este ticket en buen estado."
    else:
        return "¡Gracias por su compra! Vuelva pronto. Todas las ventas son finales."
