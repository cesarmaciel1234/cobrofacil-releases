"""
motor_impuestos.py — Motor de gestión de impuestos (Nivel Enterprise)
TPV Pro 2026 · Cobro Fácil POS

Este módulo implementa:
- Cálculo automático de IVA (débito y crédito fiscal)
- Retenciones y percepciones
- Liquidación de impuestos (IVA, Ingresos Brutos)
- Comprobantes fiscales electrónicos
- Reportes de impuestos
"""

import sqlite3
import logging
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
from decimal import Decimal, getcontext
from enum import Enum

logger = logging.getLogger("MotorImpuestos")

# Configurar precisión decimal
getcontext().prec = 4


class TipoImpuesto(Enum):
    """Tipos de impuestos"""
    IVA = "iva"
    INGRESOS_BRUTOS = "ingresos_brutos"
    RETENCION_GANANCIAS = "retencion_ganancias"
    PERCEPCION_IVA = "percepcion_iva"
    PERCEPCION_IB = "percepcion_ib"


class TipoComprobante(Enum):
    """Tipos de comprobantes fiscales"""
    FACTURA_A = "factura_a"
    FACTURA_B = "factura_b"
    FACTURA_C = "factura_c"
    NOTA_CREDITO_A = "nota_credito_a"
    NOTA_CREDITO_B = "nota_credito_b"
    NOTA_DEBITO_A = "nota_debito_a"
    NOTA_DEBITO_B = "nota_debito_b"


class CondicionFiscal(Enum):
    """Condiciones fiscales del contribuyente"""
    RESPONSABLE_INSCRIPTO = "responsable_inscripto"
    RESPONSABLE_NO_INSCRIPTO = "responsable_no_inscripto"
    EXENTO = "exento"
    MONOTRIBUTO = "monotributo"
    CONSUMIDOR_FINAL = "consumidor_final"


class MotorImpuestos:
    """Motor de gestión de impuestos"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_schema()
        self._cargar_alicuotas_defecto()

    def _get_connection(self):
        """Obtiene conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self):
        """Inicializa el esquema de impuestos"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tabla de alicuotas de IVA
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alicuotas_iva (
                    id TEXT PRIMARY KEY,
                    codigo TEXT UNIQUE NOT NULL,
                    porcentaje REAL NOT NULL,
                    descripcion TEXT,
                    activa INTEGER DEFAULT 1
                )
            ''')

            # Tabla de configuración de impuestos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS impuestos_config (
                    id TEXT PRIMARY KEY,
                    tipo TEXT NOT NULL,
                    codigo TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    porcentaje REAL NOT NULL,
                    cuenta_debito TEXT NOT NULL,
                    cuenta_credito TEXT NOT NULL,
                    activo INTEGER DEFAULT 1
                )
            ''')

            # Tabla de comprobantes fiscales
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comprobantes_fiscales (
                    id TEXT PRIMARY KEY,
                    tipo TEXT NOT NULL,
                    numero TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    monto_gravado REAL NOT NULL,
                    monto_no_gravado REAL DEFAULT 0,
                    monto_exento REAL DEFAULT 0,
                    monto_iva REAL DEFAULT 0,
                    monto_total REAL NOT NULL,
                    alicuota_iva_id TEXT,
                    condicion_fiscal TEXT NOT NULL,
                    tipo_persona TEXT,  -- 'juridica' o 'fisica'
                    cuit_cuil TEXT,
                    razon_social TEXT,
                    tipo_operacion TEXT DEFAULT 'venta',  -- 'venta' o 'compra'
                    asiento_id INTEGER,
                    FOREIGN KEY (alicuota_iva_id) REFERENCES alicuotas_iva(id),
                    FOREIGN KEY (asiento_id) REFERENCES asientos(id)
                )
            ''')

            # Tabla de liquidaciones de impuestos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS liquidaciones_impuestos (
                    id TEXT PRIMARY KEY,
                    tipo_impuesto TEXT NOT NULL,
                    periodo_desde TEXT NOT NULL,
                    periodo_hasta TEXT NOT NULL,
                    monto_debito REAL DEFAULT 0,
                    monto_credito REAL DEFAULT 0,
                    saldo REAL DEFAULT 0,
                    estado TEXT DEFAULT 'pendiente',
                    generado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    presentado_en DATETIME,
                    archivo_path TEXT
                )
            ''')

            # Tabla de retenciones/percepciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS retenciones_percepciones (
                    id TEXT PRIMARY KEY,
                    tipo TEXT NOT NULL,
                    comprobante_id TEXT NOT NULL,
                    porcentaje REAL NOT NULL,
                    base_imponible REAL NOT NULL,
                    monto REAL NOT NULL,
                    numero_certificado TEXT,
                    fecha TEXT NOT NULL,
                    FOREIGN KEY (comprobante_id) REFERENCES comprobantes_fiscales(id)
                )
            ''')

            # Índices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comprobantes_fecha ON comprobantes_fiscales(fecha)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comprobantes_tipo ON comprobantes_fiscales(tipo)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_liquidaciones_periodo ON liquidaciones_impuestos(periodo_desde, periodo_hasta)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_retenciones_comprobante ON retenciones_percepciones(comprobante_id)')

            conn.commit()

    def _cargar_alicuotas_defecto(self):
        """Carga las alicuotas de IVA por defecto"""
        import uuid

        with self._get_connection() as conn:
            cursor = conn.cursor()

            alicuotas = [
                ("0", 0.0, "IVA 0% (Exento)"),
                ("10.5", 10.5, "IVA 10.5%"),
                ("21", 21.0, "IVA 21%"),
                ("27", 27.0, "IVA 27%"),
            ]

            for codigo, porcentaje, descripcion in alicuotas:
                cursor.execute('''
                    INSERT OR IGNORE INTO alicuotas_iva
                    (id, codigo, porcentaje, descripcion, activa)
                    VALUES (?, ?, ?, ?, 1)
                ''', (str(uuid.uuid4()), codigo, porcentaje, descripcion))

            conn.commit()
            logger.info("Alicuotas de IVA cargadas")

    # ── CÁLCULO DE IVA ───────────────────────────────────────────────────────

    def calcular_iva(self, monto_total: float, alicuota_codigo: str,
                     invertir: bool = False) -> Tuple[float, float, float]:
        """
        Calcula el IVA de un monto

        Args:
            monto_total: Monto total (con IVA)
            alicuota_codigo: Código de alicuota (0, 10.5, 21, 27)
            invertir: Si True, monto_total es sin IVA y se le suma

        Returns:
            (monto_gravado, monto_iva, monto_total)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT porcentaje FROM alicuotas_iva
                WHERE codigo = ? AND activa = 1
            ''', (alicuota_codigo,))
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"Alicuota {alicuota_codigo} no encontrada")

            porcentaje = row['porcentaje']

            if invertir:
                # Monto total es sin IVA, se le suma
                monto_gravado = monto_total
                monto_iva = monto_total * (porcentaje / 100)
                monto_con_iva = monto_gravado + monto_iva
                return monto_gravado, monto_iva, monto_con_iva
            else:
                # Monto total incluye IVA, se calcula el gravado
                if porcentaje == 0:
                    return monto_total, 0.0, monto_total
                monto_gravado = monto_total / (1 + porcentaje / 100)
                monto_iva = monto_total - monto_gravado
                return monto_gravado, monto_iva, monto_total

    # ── REGISTRO DE COMPROBANTES ─────────────────────────────────────────────

    def registrar_comprobante(self, tipo: TipoComprobante, numero: str,
                              fecha: date, monto_total: float,
                              alicuota_codigo: str,
                              condicion_fiscal: CondicionFiscal,
                              tipo_operacion: str = "venta",
                              tipo_persona: Optional[str] = None,
                              cuit_cuil: Optional[str] = None,
                              razon_social: Optional[str] = None,
                              monto_no_gravado: float = 0.0,
                              monto_exento: float = 0.0,
                              asiento_id: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Registra un comprobante fiscal

        Returns:
            (exito, mensaje, comprobante_id)
        """
        try:
            import uuid

            # Calcular IVA
            monto_gravado, monto_iva, _ = self.calcular_iva(monto_total, alicuota_codigo)

            # Obtener ID de alicuota
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id FROM alicuotas_iva WHERE codigo = ?
                ''', (alicuota_codigo,))
                alicuota_row = cursor.fetchone()
                alicuota_id = alicuota_row['id'] if alicuota_row else None

                # Insertar comprobante
                comprobante_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO comprobantes_fiscales
                    (id, tipo, numero, fecha, monto_gravado, monto_no_gravado,
                     monto_exento, monto_iva, monto_total, alicuota_iva_id,
                     condicion_fiscal, tipo_persona, cuit_cuil, razon_social,
                     tipo_operacion, asiento_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (comprobante_id, tipo.value, numero, fecha.isoformat(),
                      monto_gravado, monto_no_gravado, monto_exento, monto_iva,
                      monto_total, alicuota_id, condicion_fiscal.value,
                      tipo_persona, cuit_cuil, razon_social, tipo_operacion, asiento_id))

                conn.commit()
                logger.info(f"Comprobante registrado: {tipo.value} {numero}")
                return True, "Comprobante registrado exitosamente", comprobante_id

        except Exception as e:
            logger.error(f"Error registrando comprobante: {e}")
            return False, str(e), None

    # ── LIQUIDACIÓN DE IMPUESTOS ─────────────────────────────────────────────

    def liquidar_iva(self, periodo_desde: date, periodo_hasta: date) -> Dict:
        """
        Genera la liquidación de IVA para un período

        Returns:
            Dict con débitos, créditos y saldo
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # IVA Débito Fiscal (ventas)
            cursor.execute('''
                SELECT SUM(monto_iva) as total
                FROM comprobantes_fiscales
                WHERE tipo_operacion = 'venta'
                  AND fecha BETWEEN ? AND ?
                  AND tipo IN ('factura_a', 'factura_b', 'nota_debito_a', 'nota_debito_b')
            ''', (periodo_desde.isoformat(), periodo_hasta.isoformat()))

            row = cursor.fetchone()
            debito_fiscal = row['total'] or 0.0

            # IVA Crédito Fiscal (compras)
            cursor.execute('''
                SELECT SUM(monto_iva) as total
                FROM comprobantes_fiscales
                WHERE tipo_operacion = 'compra'
                  AND fecha BETWEEN ? AND ?
                  AND tipo IN ('factura_a', 'nota_credito_a', 'nota_debito_a')
            ''', (periodo_desde.isoformat(), periodo_hasta.isoformat()))

            row = cursor.fetchone()
            credito_fiscal = row['total'] or 0.0

            # Saldo
            saldo = debito_fiscal - credito_fiscal

            return {
                "periodo_desde": periodo_desde.isoformat(),
                "periodo_hasta": periodo_hasta.isoformat(),
                "debito_fiscal": debito_fiscal,
                "credito_fiscal": credito_fiscal,
                "saldo": saldo,
                "a_pagar": saldo if saldo > 0 else 0,
                "a_creditar": abs(saldo) if saldo < 0 else 0
            }

    def registrar_liquidacion(self, tipo_impuesto: TipoImpuesto,
                              periodo_desde: date, periodo_hasta: date,
                              monto_debito: float, monto_credito: float) -> Tuple[bool, str, Optional[str]]:
        """
        Registra una liquidación de impuestos

        Returns:
            (exito, mensaje, liquidacion_id)
        """
        try:
            import uuid

            saldo = monto_debito - monto_credito

            with self._get_connection() as conn:
                cursor = conn.cursor()

                liquidacion_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO liquidaciones_impuestos
                    (id, tipo_impuesto, periodo_desde, periodo_hasta,
                     monto_debito, monto_credito, saldo, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pendiente')
                ''', (liquidacion_id, tipo_impuesto.value,
                      periodo_desde.isoformat(), periodo_hasta.isoformat(),
                      monto_debito, monto_credito, saldo))

                conn.commit()
                logger.info(f"Liquidación registrada: {tipo_impuesto.value} {periodo_desde} a {periodo_hasta}")
                return True, "Liquidación registrada exitosamente", liquidacion_id

        except Exception as e:
            logger.error(f"Error registrando liquidación: {e}")
            return False, str(e), None

    # ── REPORTES DE IMPUESTOS ────────────────────────────────────────────────

    def obtener_resumen_iva(self, periodo_desde: date, periodo_hasta: date) -> Dict:
        """Obtiene un resumen de operaciones con IVA"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Ventas por alicuota
            cursor.execute('''
                SELECT
                    a.codigo as alicuota,
                    a.porcentaje,
                    SUM(cf.monto_gravado) as total_gravado,
                    SUM(cf.monto_iva) as total_iva,
                    COUNT(*) as cantidad
                FROM comprobantes_fiscales cf
                JOIN alicuotas_iva a ON cf.alicuota_iva_id = a.id
                WHERE cf.tipo_operacion = 'venta'
                  AND cf.fecha BETWEEN ? AND ?
                GROUP BY a.codigo, a.porcentaje
            ''', (periodo_desde.isoformat(), periodo_hasta.isoformat()))

            ventas_por_alicuota = [dict(row) for row in cursor.fetchall()]

            # Compras por alicuota
            cursor.execute('''
                SELECT
                    a.codigo as alicuota,
                    a.porcentaje,
                    SUM(cf.monto_gravado) as total_gravado,
                    SUM(cf.monto_iva) as total_iva,
                    COUNT(*) as cantidad
                FROM comprobantes_fiscales cf
                JOIN alicuotas_iva a ON cf.alicuota_iva_id = a.id
                WHERE cf.tipo_operacion = 'compra'
                  AND cf.fecha BETWEEN ? AND ?
                GROUP BY a.codigo, a.porcentaje
            ''', (periodo_desde.isoformat(), periodo_hasta.isoformat()))

            compras_por_alicuota = [dict(row) for row in cursor.fetchall()]

            return {
                "periodo_desde": periodo_desde.isoformat(),
                "periodo_hasta": periodo_hasta.isoformat(),
                "ventas_por_alicuota": ventas_por_alicuota,
                "compras_por_alicuota": compras_por_alicuota
            }

    def obtener_comprobantes(self, tipo_operacion: str,
                              desde: Optional[date] = None,
                              hasta: Optional[date] = None) -> List[Dict]:
        """Obtiene comprobantes fiscales con filtros"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM comprobantes_fiscales WHERE tipo_operacion = ?'
            params = [tipo_operacion]

            if desde:
                query += ' AND fecha >= ?'
                params.append(desde.isoformat())

            if hasta:
                query += ' AND fecha <= ?'
                params.append(hasta.isoformat())

            query += ' ORDER BY fecha DESC'

            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
