from datetime import datetime

_DIAS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
_MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def fecha_cabecera(momento=None) -> str:
    ahora = momento or datetime.now()
    return f"{_DIAS[ahora.weekday()]} {ahora.day} {_MESES[ahora.month - 1]}   ·   {ahora:%H:%M}"
