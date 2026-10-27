"""Textos del reporte. Van en escapes para que un guardado mal no los vuelva a romper."""

DIAS = ("Lun", "Mar", "Mi\u00e9", "Jue", "Vie", "S\u00e1b", "Dom")
ENCABEZADO_DIA = ("D\u00eda", "Actual", "Anterior", "Rendimiento")

TITULO_HORA = "Ventas por hora"
TITULO_DIA = "Ventas por d\u00eda"
TITULO_MES = "Ventas por mes"
TITULO_SEMANA = "Ventas por semana"
TITULO_PERIODO = "Ventas en el periodo"
TITULO_RECAUDACION = "Mayor recaudaci\u00f3n ($)"
AVISO_SIN_COSTO = "Carg\u00e1 inventario y precio de costo"
AVISO_SIN_IMPUESTOS = "- No se registr\u00f3 ninguna venta con impuestos -"
AVISO_ERROR = "Ocurri\u00f3 un error al cargar los datos"
TITULO_ARTICULOS = "Art\u00edculos (unidades)"
TITULO_KILOS = "Volumen f\u00edsico (peso)"
TITULO_EXPORTAR = "Exportar auditor\u00eda a Excel"
HOJA_AUDITORIA = "Auditor\u00eda de ventas"
AVISO_EXPORTADO = "Exportaci\u00f3n completada"
EXPORTANDO = "Exportando..."
EXPORTAR = "Exportar"


def es_anio(periodo: str) -> bool:
    return "A\u00f1o" in (periodo or "")


def titulo_serie(periodo: str) -> str:
    texto = periodo or ""
    if "Hoy" in texto:
        return TITULO_HORA
    if es_anio(texto):
        return TITULO_MES
    if "Semana" in texto:
        return TITULO_SEMANA
    if "Mes" in texto:
        return TITULO_DIA
    return TITULO_PERIODO


def nombre_dia(fecha) -> str:
    return DIAS[fecha.weekday()]


def nombres_comparacion(periodo: str) -> tuple[str, str]:
    texto = periodo or ""
    if texto in ("Semana p.", "Semana Pasada"):
        return "Semana pasada", "Semana previa"
    if "Semana" in texto:
        return "Semana en curso", "Semana pasada"
    if texto == "Mes Anterior":
        return "Mes anterior", "Mes previo"
    if "Mes" in texto:
        return "Mes en curso", "Mes pasado"
    if es_anio(texto):
        return "A\u00f1o en curso", "A\u00f1o pasado"
    if texto == "Hoy":
        return "Hoy", "Ayer"
    return "Periodo", "Periodo anterior"
