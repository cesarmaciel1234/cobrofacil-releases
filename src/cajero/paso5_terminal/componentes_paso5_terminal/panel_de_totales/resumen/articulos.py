from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales.resumen.fila import (
    FilaResumen,
)


class ContenedorArticulos(FilaResumen):
    def __init__(self, parent=None):
        super().__init__("ARTÍCULOS", parent)
