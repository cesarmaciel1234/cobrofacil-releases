"""Creador PNG — módulo independiente de cartelería."""

__all__ = ["DialogoCreadorPNG", "PanelPngProductos", "quitar_fondo_negro"]


def __getattr__(name):
    if name == "DialogoCreadorPNG":
        from .ventana_html import DialogoCreadorPNG
        return DialogoCreadorPNG
    if name == "PanelPngProductos":
        from .panel_png_productos import PanelPngProductos
        return PanelPngProductos
    if name == "quitar_fondo_negro":
        from .fondo_transparente import quitar_fondo_negro
        return quitar_fondo_negro
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
