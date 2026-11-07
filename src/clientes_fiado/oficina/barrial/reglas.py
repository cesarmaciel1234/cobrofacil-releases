"""Constantes del modo barrial. Sin cuotas ni mora automática diaria."""

ESTADO_ACTIVO = "activo"
ESTADO_SUSPENDIDO = "suspendido"

# Días desde el último pago (con deuda) → bucket de aging / Estado
AGING_30 = 30
AGING_60 = 60
AGING_90 = 90

BUCKET_OK = "ok"
BUCKET_30 = "d30"
BUCKET_60 = "d60"
BUCKET_90 = "d90"

# Mantenimiento de cuenta (% sobre deuda). Default 3%.
# Solo si hay deuda (ticket/cargos). Cuenta en 0 → no aplica.
# Se cobra al haber deuda y luego una vez por mes (ventana).
# Apalancamiento: días desde el último ABONO; pago parcial sigue contando;
# si deja la cuenta en 0 antes del mes, no se aplica.
# Config: fiado_mantenimiento_pct / fiado_apalancamiento_pct
MANTENIMIENTO_PCT_DEFAULT = 3.0
APALANCAMIENTO_PCT_DEFAULT = 5.0
MANTENIMIENTO_PCT_MIN = 0.0
MANTENIMIENTO_PCT_MAX = 15.0
MARCA_MANTENIMIENTO = "MANTENIMIENTO ·"
# No volver a cobrar mantenimiento si ya hubo uno en esta ventana (días)
MANTENIMIENTO_VENTANA_DIAS = 30
