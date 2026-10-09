"""
schema_fiscal.py — Plan de cuentas y asientos contables (Nivel Enterprise)
TPV Pro 2026 · Cobro Fácil POS

Este módulo define el esquema contable fiscal para nivel empresarial:
- Plan de cuentas (catálogo contable)
- Asientos contables con doble partida
- Gestión de IVA, retenciones, percepciones
- Depreciación de activos fijos
- Cierre de ejercicio contable
"""

from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum


class TipoCuenta(Enum):
    """Tipos de cuentas según el plan contable"""
    ACTIVO = "activo"
    PASIVO = "pasivo"
    PATRIMONIO = "patrimonio"
    INGRESO = "ingreso"
    GASTO = "gasto"


class TipoAsiento(Enum):
    """Tipos de asientos contables"""
    MANUAL = "manual"
    VENTA = "venta"
    COMPRA = "compra"
    COBRO = "cobro"
    PAGO = "pago"
    DEPRECIACION = "depreciacion"
    AJUSTE = "ajuste"
    CIERRE = "cierre"
    APERTURA = "apertura"


class Moneda(Enum):
    """Monedas soportadas"""
    ARS = "ARS"
    USD = "USD"
    EUR = "EUR"


class EstadoAsiento(Enum):
    """Estados de workflow de asientos"""
    BORRADOR = "borrador"
    PENDIENTE_APROBACION = "pendiente_aprobacion"
    APROBADO = "aprobado"
    CONTABILIZADO = "contabilizado"
    ANULADO = "anulado"


# ── PLAN DE CUENTAS (Catálogo Contable) ──────────────────────────────────────
# Basado en normas contables locales (NIIF adaptadas)

PLAN_CUENTAS_POR_DEFECTO = {
    # ACTIVO CORRIENTE
    "1.1.01.01": {"codigo": "1.1.01.01", "nombre": "Caja", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.1.01"},
    "1.1.01.02": {"codigo": "1.1.01.02", "nombre": "Bancos", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.1.01"},
    "1.1.01.03": {"codigo": "1.1.01.03", "nombre": "Valores a Cobrar", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.1.01"},
    "1.1.02.01": {"codigo": "1.1.02.01", "nombre": "Clientes", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.1.02"},
    "1.1.02.02": {"codigo": "1.1.02.02", "nombre": "Documentos a Cobrar", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.1.02"},
    "1.1.03.01": {"codigo": "1.1.03.01", "nombre": "Mercaderías", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.1.03"},
    "1.1.03.02": {"codigo": "1.1.03.02", "nombre": "Materias Primas", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.1.03"},
    "1.1.04.01": {"codigo": "1.1.04.01", "nombre": "IVA Crédito Fiscal", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.1.04"},
    "1.1.04.02": {"codigo": "1.1.04.02", "nombre": "Impuestos a Recuperar", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.1.04"},

    # ACTIVO NO CORRIENTE
    "1.2.01.01": {"codigo": "1.2.01.01", "nombre": "Terrenos", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.2.01"},
    "1.2.01.02": {"codigo": "1.2.01.02", "nombre": "Edificios", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.2.01"},
    "1.2.01.03": {"codigo": "1.2.01.03", "nombre": "Maquinaria y Equipo", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.2.01"},
    "1.2.01.04": {"codigo": "1.2.01.04", "nombre": "Equipos de Cómputo", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.2.01"},
    "1.2.01.05": {"codigo": "1.2.01.05", "nombre": "Mobiliario", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.2.01"},
    "1.2.01.06": {"codigo": "1.2.01.06", "nombre": "Vehículos", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.2.01"},
    "1.2.02.01": {"codigo": "1.2.02.01", "nombre": "Depreciación Acumulada", "tipo": TipoCuenta.ACTIVO, "nivel": 4, "padre": "1.2.02", "ajustadora": True},

    # PASIVO CORRIENTE
    "2.1.01.01": {"codigo": "2.1.01.01", "nombre": "Proveedores", "tipo": TipoCuenta.PASIVO, "nivel": 4, "padre": "2.1.01"},
    "2.1.01.02": {"codigo": "2.1.01.02", "nombre": "Documentos a Pagar", "tipo": TipoCuenta.PASIVO, "nivel": 4, "padre": "2.1.01"},
    "2.1.02.01": {"codigo": "2.1.02.01", "nombre": "Sueldos por Pagar", "tipo": TipoCuenta.PASIVO, "nivel": 4, "padre": "2.1.02"},
    "2.1.02.02": {"codigo": "2.1.02.02", "nombre": "Cargas Sociales por Pagar", "tipo": TipoCuenta.PASIVO, "nivel": 4, "padre": "2.1.02"},
    "2.1.03.01": {"codigo": "2.1.03.01", "nombre": "IVA Débito Fiscal", "tipo": TipoCuenta.PASIVO, "nivel": 4, "padre": "2.1.03"},
    "2.1.03.02": {"codigo": "2.1.03.02", "nombre": "Impuestos por Pagar", "tipo": TipoCuenta.PASIVO, "nivel": 4, "padre": "2.1.03"},
    "2.1.04.01": {"codigo": "2.1.04.01", "nombre": "Préstamos Bancarios CP", "tipo": TipoCuenta.PASIVO, "nivel": 4, "padre": "2.1.04"},

    # PASIVO NO CORRIENTE
    "2.2.01.01": {"codigo": "2.2.01.01", "nombre": "Préstamos Bancarios LP", "tipo": TipoCuenta.PASIVO, "nivel": 4, "padre": "2.2.01"},
    "2.2.02.01": {"codigo": "2.2.02.01", "nombre": "Hipotecas por Pagar", "tipo": TipoCuenta.PASIVO, "nivel": 4, "padre": "2.2.02"},

    # PATRIMONIO
    "3.1.01.01": {"codigo": "3.1.01.01", "nombre": "Capital Social", "tipo": TipoCuenta.PATRIMONIO, "nivel": 4, "padre": "3.1.01"},
    "3.1.02.01": {"codigo": "3.1.02.01", "nombre": "Reserva Legal", "tipo": TipoCuenta.PATRIMONIO, "nivel": 4, "padre": "3.1.02"},
    "3.1.03.01": {"codigo": "3.1.03.01", "nombre": "Resultados Acumulados", "tipo": TipoCuenta.PATRIMONIO, "nivel": 4, "padre": "3.1.03"},
    "3.1.04.01": {"codigo": "3.1.04.01", "nombre": "Resultado del Ejercicio", "tipo": TipoCuenta.PATRIMONIO, "nivel": 4, "padre": "3.1.04"},

    # INGRESOS
    "4.1.01.01": {"codigo": "4.1.01.01", "nombre": "Ventas Locales", "tipo": TipoCuenta.INGRESO, "nivel": 4, "padre": "4.1.01"},
    "4.1.01.02": {"codigo": "4.1.01.02", "nombre": "Ventas Exportación", "tipo": TipoCuenta.INGRESO, "nivel": 4, "padre": "4.1.01"},
    "4.1.02.01": {"codigo": "4.1.02.01", "nombre": "Ingresos por Servicios", "tipo": TipoCuenta.INGRESO, "nivel": 4, "padre": "4.1.02"},
    "4.1.03.01": {"codigo": "4.1.03.01", "nombre": "Intereses Ganados", "tipo": TipoCuenta.INGRESO, "nivel": 4, "padre": "4.1.03"},
    "4.1.04.01": {"codigo": "4.1.04.01", "nombre": "Otros Ingresos", "tipo": TipoCuenta.INGRESO, "nivel": 4, "padre": "4.1.04"},

    # GASTOS
    "5.1.01.01": {"codigo": "5.1.01.01", "nombre": "Costo de Ventas", "tipo": TipoCuenta.GASTO, "nivel": 4, "padre": "5.1.01"},
    "5.1.02.01": {"codigo": "5.1.02.01", "nombre": "Gastos de Personal", "tipo": TipoCuenta.GASTO, "nivel": 4, "padre": "5.1.02"},
    "5.1.02.02": {"codigo": "5.1.02.02", "nombre": "Cargas Sociales", "tipo": TipoCuenta.GASTO, "nivel": 4, "padre": "5.1.02"},
    "5.1.03.01": {"codigo": "5.1.03.01", "nombre": "Alquileres", "tipo": TipoCuenta.GASTO, "nivel": 4, "padre": "5.1.03"},
    "5.1.03.02": {"codigo": "5.1.03.02", "nombre": "Servicios", "tipo": TipoCuenta.GASTO, "nivel": 4, "padre": "5.1.03"},
    "5.1.03.03": {"codigo": "5.1.03.03", "nombre": "Mantenimiento", "tipo": TipoCuenta.GASTO, "nivel": 4, "padre": "5.1.03"},
    "5.1.04.01": {"codigo": "5.1.04.01", "nombre": "Intereses Pagados", "tipo": TipoCuenta.GASTO, "nivel": 4, "padre": "5.1.04"},
    "5.1.05.01": {"codigo": "5.1.05.01", "nombre": "Depreciación", "tipo": TipoCuenta.GASTO, "nivel": 4, "padre": "5.1.05"},
    "5.1.06.01": {"codigo": "5.1.06.01", "nombre": "Impuestos", "tipo": TipoCuenta.GASTO, "nivel": 4, "padre": "5.1.06"},
    "5.1.07.01": {"codigo": "5.1.07.01", "nombre": "Otros Gastos", "tipo": TipoCuenta.GASTO, "nivel": 4, "padre": "5.1.07"},
}


# ── CLASES DEL MODELO ───────────────────────────────────────────────────────────

class CuentaContable:
    """Representa una cuenta del plan contable"""
    def __init__(self, codigo: str, nombre: str, tipo: TipoCuenta,
                 nivel: int, padre: Optional[str] = None, ajustadora: bool = False):
        self.codigo = codigo
        self.nombre = nombre
        self.tipo = tipo
        self.nivel = nivel
        self.padre = padre
        self.ajustadora = ajustadora

    def to_dict(self) -> dict:
        return {
            "codigo": self.codigo,
            "nombre": self.nombre,
            "tipo": self.tipo.value,
            "nivel": self.nivel,
            "padre": self.padre,
            "ajustadora": self.ajustadora
        }


class LineaAsiento:
    """Línea de un asiento contable (una cuenta con debe/haber)"""
    def __init__(self, cuenta_codigo: str, debe: float = 0.0,
                 haber: float = 0.0, descripcion: str = ""):
        self.cuenta_codigo = cuenta_codigo
        self.debe = debe
        self.haber = haber
        self.descripcion = descripcion

    def to_dict(self) -> dict:
        return {
            "cuenta_codigo": self.cuenta_codigo,
            "debe": self.debe,
            "haber": self.haber,
            "descripcion": self.descripcion
        }


class AsientoContable:
    """Asiento contable con doble partida"""
    def __init__(self, fecha: date, tipo: TipoAsiento,
                 descripcion: str, lineas: List[LineaAsiento],
                 moneda: Moneda = Moneda.ARS,
                 estado: EstadoAsiento = EstadoAsiento.BORRADOR,
                 referencia: str = "",
                 usuario: str = "system"):
        self.fecha = fecha
        self.tipo = tipo
        self.descripcion = descripcion
        self.lineas = lineas
        self.moneda = moneda
        self.estado = estado
        self.referencia = referencia
        self.usuario = usuario
        self.creado_en = datetime.now()

    def validar(self) -> Tuple[bool, str]:
        """Valida que el asiento cumpla la doble partida"""
        total_debe = sum(l.debe for l in self.lineas)
        total_haber = sum(l.haber for l in self.lineas)

        if abs(total_debe - total_haber) > 0.01:
            return False, f"El asiento no cuadra: Debe={total_debe}, Haber={total_haber}"

        if not self.lineas:
            return False, "El asiento no tiene líneas"

        for linea in self.lineas:
            if linea.debe < 0 or linea.haber < 0:
                return False, f"Línea con valores negativos: {linea.cuenta_codigo}"
            if linea.debe > 0 and linea.haber > 0:
                return False, f"Línea con debe y haber simultáneos: {linea.cuenta_codigo}"

        return True, ""

    def to_dict(self) -> dict:
        return {
            "fecha": self.fecha.isoformat(),
            "tipo": self.tipo.value,
            "descripcion": self.descripcion,
            "lineas": [l.to_dict() for l in self.lineas],
            "moneda": self.moneda.value,
            "estado": self.estado.value,
            "referencia": self.referencia,
            "usuario": self.usuario,
            "creado_en": self.creado_en.isoformat()
        }


class Impuesto:
    """Configuración de impuestos (IVA, retenciones, etc.)"""
    def __init__(self, codigo: str, nombre: str, tasa: float,
                 tipo: str, cuenta_debito: str, cuenta_credito: str):
        self.codigo = codigo
        self.nombre = nombre
        self.tasa = tasa  # Porcentaje (ej: 21.0 para 21%)
        self.tipo = tipo  # "iva", "retencion", "percepcion", "ingreso_bruto"
        self.cuenta_debito = cuenta_debito  # Cuenta donde se debita
        self.cuenta_credito = cuenta_credito  # Cuenta donde se acredita

    def to_dict(self) -> dict:
        return {
            "codigo": self.codigo,
            "nombre": self.nombre,
            "tasa": self.tasa,
            "tipo": self.tipo,
            "cuenta_debito": self.cuenta_debito,
            "cuenta_credito": self.cuenta_credito
        }


# ── IMPUESTOS POR DEFECTO ─────────────────────────────────────────────────────

IMPUESTOS_POR_DEFECTO = [
    Impuesto("IVA_21", "IVA 21%", 21.0, "iva", "2.1.03.01", "1.1.04.01"),
    Impuesto("IVA_10.5", "IVA 10.5%", 10.5, "iva", "2.1.03.01", "1.1.04.01"),
    Impuesto("IVA_27", "IVA 27%", 27.0, "iva", "2.1.03.01", "1.1.04.01"),
    Impuesto("IVA_0", "IVA 0% (Exento)", 0.0, "iva", "2.1.03.01", "1.1.04.01"),
    Impuesto("IIBG_CABA", "Ingresos Brutos CABA", 3.0, "percepcion", "5.1.06.01", "2.1.03.02"),
    Impuesto("IIBG_PBA", "Ingresos Brutos PBA", 3.5, "percepcion", "5.1.06.01", "2.1.03.02"),
]


class ActivoFijo:
    """Activo fijo con depreciación"""
    def __init__(self, codigo: str, nombre: str, cuenta_activo: str,
                 cuenta_depreciacion: str, costo: float,
                 fecha_adquisicion: date, vida_util_anios: int,
                 metodo: str = "lineal"):
        self.codigo = codigo
        self.nombre = nombre
        self.cuenta_activo = cuenta_activo
        self.cuenta_depreciacion = cuenta_depreciacion
        self.costo = costo
        self.fecha_adquisicion = fecha_adquisicion
        self.vida_util_anios = vida_util_anios
        self.metodo = metodo  # "lineal", "acelerado"
        self.depreciacion_acumulada = 0.0
        self.valor_residual = 0.0  # Valor al final de vida útil (usualmente 0 o 10%)

    def calcular_depreciacion_anual(self) -> float:
        """Calcula la depreciación anual según el método"""
        if self.metodo == "lineal":
            return (self.costo - self.valor_residual) / self.vida_util_anios
        elif self.metodo == "acelerado":
            # Método de suma de dígitos
            suma_digitos = sum(range(1, self.vida_util_anios + 1))
            return (self.costo - self.valor_residual) * self.vida_util_anios / suma_digitos
        return 0.0

    def valor_en_libros(self) -> float:
        """Valor neto en libros (costo - depreciación acumulada)"""
        return self.costo - self.depreciacion_acumulada

    def to_dict(self) -> dict:
        return {
            "codigo": self.codigo,
            "nombre": self.nombre,
            "cuenta_activo": self.cuenta_activo,
            "cuenta_depreciacion": self.cuenta_depreciacion,
            "costo": self.costo,
            "fecha_adquisicion": self.fecha_adquisicion.isoformat(),
            "vida_util_anios": self.vida_util_anios,
            "metodo": self.metodo,
            "depreciacion_acumulada": self.depreciacion_acumulada,
            "valor_residual": self.valor_residual,
            "valor_en_libros": self.valor_en_libros()
        }


# ── FUNCIÓN DE UTILIDAD ─────────────────────────────────────────────────────

def obtener_cuenta_por_codigo(codigo: str) -> Optional[CuentaContable]:
    """Obtiene una cuenta del plan por su código"""
    data = PLAN_CUENTAS_POR_DEFECTO.get(codigo)
    if data:
        return CuentaContable(
            codigo=data["codigo"],
            nombre=data["nombre"],
            tipo=TipoCuenta(data["tipo"]),
            nivel=data["nivel"],
            padre=data.get("padre"),
            ajustadora=data.get("ajustadora", False)
        )
    return None


def obtener_cuentas_por_tipo(tipo: TipoCuenta) -> List[CuentaContable]:
    """Obtiene todas las cuentas de un tipo"""
    return [
        CuentaContable(
            codigo=data["codigo"],
            nombre=data["nombre"],
            tipo=TipoCuenta(data["tipo"]),
            nivel=data["nivel"],
            padre=data.get("padre"),
            ajustadora=data.get("ajustadora", False)
        )
        for data in PLAN_CUENTAS_POR_DEFECTO.values()
        if data["tipo"] == tipo.value
    ]


def inicializar_plan_cuentas():
    """Devuelve el plan completo como lista de diccionarios"""
    return [data for data in PLAN_CUENTAS_POR_DEFECTO.values()]
