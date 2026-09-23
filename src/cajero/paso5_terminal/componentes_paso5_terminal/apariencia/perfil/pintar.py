"""Marca azul Francia o rosa en la pantalla del cajero."""


def pintar(terminal):
    from src.cajero.cajero_activo import CajeroActivo

    auxiliar = CajeroActivo.numero == 2
    terminal.setProperty("cajero_perfil", "auxiliar" if auxiliar else "principal")
    color = "rosa" if auxiliar else "francia"
    for marco in (
        getattr(terminal, "cabecera", None),
        getattr(terminal, "componente_tabla", None),
    ):
        if marco is None:
            continue
        marco.setProperty("perfil_color", color)
    terminal.apply_theme()
    for marco in (
        getattr(terminal, "cabecera", None),
        getattr(terminal, "componente_tabla", None),
    ):
        if marco is None:
            continue
        marco.style().unpolish(marco)
        marco.style().polish(marco)
