from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales.resumen.fila import (
    FilaResumen,
)


class ContenedorCambio(FilaResumen):
    def __init__(self, parent=None):
        super().__init__("CAMBIO", parent)
        self.titulo.setObjectName("TituloCambio")

    def marcar_resaltado(self, es_resaltado: bool):
        self.valor.setProperty("resaltado", "true" if es_resaltado else "false")
        self.valor.style().unpolish(self.valor)
        self.valor.style().polish(self.valor)
