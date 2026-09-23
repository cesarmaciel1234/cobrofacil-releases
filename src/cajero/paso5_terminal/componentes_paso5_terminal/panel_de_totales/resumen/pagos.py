from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales.resumen.fila import (
    FilaResumen,
)


class ContenedorPagos(FilaResumen):
    def __init__(self, parent=None):
        super().__init__("PAGOS", parent)
