"""
motor_depreciacion.py — Motor de depreciación de activos fijos (Nivel Enterprise)
TPV Pro 2026 · Cobro Fácil POS

Este módulo implementa:
- Registro de activos fijos
- Cálculo de depreciación (método lineal y acelerado)
- Generación automática de asientos de depreciación
- Reportes de activos fijos
- Valor en libros
"""

import sqlite3
import logging
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
from decimal import Decimal, getcontext
from enum import Enum
import calendar

logger = logging.getLogger("MotorDepreciacion")

# Configurar precisión decimal
getcontext().prec = 4


class MetodoDepreciacion(Enum):
    """Métodos de depreciación"""
    LINEAL = "lineal"
    ACELERADO_SUMA_DIGITOS = "acelerado_suma_digitos"
    ACELERADO_DOBLE_SALDO = "acelerado_doble_saldo"


class EstadoActivo(Enum):
    """Estados de un activo fijo"""
    ACTIVO = "activo"
    EN_DEPRECIACION = "en_depreciacion"
    TOTALMENTE_DEPRECIADO = "totalmente_depreciado"
    DADO_DE_BAJA = "dado_de_baja"
    VENDIDO = "vendido"


class MotorDepreciacion:
    """Motor de depreciación de activos fijos"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_schema()

    def _get_connection(self):
        """Obtiene conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self):
        """Inicializa el esquema de activos fijos"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tabla de activos fijos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activos_fijos (
                    id TEXT PRIMARY KEY,
                    codigo TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    cuenta_activo TEXT NOT NULL,
                    cuenta_depreciacion TEXT NOT NULL,
                    cuenta_gasto_depreciacion TEXT NOT NULL,
                    costo REAL NOT NULL,
                    valor_residual REAL DEFAULT 0,
                    fecha_adquisicion TEXT NOT NULL,
                    fecha_puesta_en_marcha TEXT,
                    vida_util_anios INTEGER NOT NULL,
                    metodo TEXT DEFAULT 'lineal',
                    estado TEXT DEFAULT 'activo',
                    fecha_baja TEXT,
                    motivo_baja TEXT,
                    valor_venta REAL,
                    ubicacion TEXT,
                    responsable TEXT,
                    numero_serie TEXT,
                    proveedor TEXT,
                    factura TEXT,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabla de depreciaciones (histórico)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS depreciaciones (
                    id TEXT PRIMARY KEY,
                    activo_id TEXT NOT NULL,
                    periodo TEXT NOT NULL,  # Formato: YYYY-MM
                    monto_depreciacion REAL NOT NULL,
                    depreciacion_acumulada_anterior REAL,
                    depreciacion_acumulada_actual REAL,
                    valor_en_libros_anterior REAL,
                    valor_en_libros_actual REAL,
                    asiento_id INTEGER,
                    generado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (activo_id) REFERENCES activos_fijos(id),
                    FOREIGN KEY (asiento_id) REFERENCES asientos(id),
                    UNIQUE(activo_id, periodo)
                )
            ''')

            # Tabla de mejoras capitalizables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mejoras_activos (
                    id TEXT PRIMARY KEY,
                    activo_id TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    monto REAL NOT NULL,
                    fecha TEXT NOT NULL,
                    asiento_id INTEGER,
                    FOREIGN KEY (activo_id) REFERENCES activos_fijos(id),
                    FOREIGN KEY (asiento_id) REFERENCES asientos(id)
                )
            ''')

            # Índices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activos_estado ON activos_fijos(estado)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_depreciaciones_activo ON depreciaciones(activo_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_depreciaciones_periodo ON depreciaciones(periodo)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mejoras_activo ON mejoras_activos(activo_id)')

            conn.commit()

    # ── GESTIÓN DE ACTIVOS FIJOS ───────────────────────────────────────────────

    def registrar_activo_fijo(self, codigo: str, nombre: str,
                               cuenta_activo: str, cuenta_depreciacion: str,
                               cuenta_gasto: str, costo: float,
                               fecha_adquisicion: date,
                               vida_util_anios: int,
                               metodo: MetodoDepreciacion = MetodoDepreciacion.LINEAL,
                               valor_residual: float = 0.0,
                               descripcion: Optional[str] = None,
                               ubicacion: Optional[str] = None,
                               responsable: Optional[str] = None,
                               numero_serie: Optional[str] = None,
                               proveedor: Optional[str] = None,
                               factura: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Registra un nuevo activo fijo

        Returns:
            (exito, mensaje, activo_id)
        """
        try:
            import uuid

            activo_id = str(uuid.uuid4())

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Verificar unicidad de código
                cursor.execute('SELECT id FROM activos_fijos WHERE codigo = ?', (codigo,))
                if cursor.fetchone():
                    return False, f"El código {codigo} ya existe", None

                # Insertar activo
                cursor.execute('''
                    INSERT INTO activos_fijos
                    (id, codigo, nombre, descripcion, cuenta_activo, cuenta_depreciacion,
                     cuenta_gasto_depreciacion, costo, valor_residual, fecha_adquisicion,
                     vida_util_anios, metodo, estado, ubicacion, responsable,
                     numero_serie, proveedor, factura)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'activo', ?, ?, ?, ?, ?)
                ''', (activo_id, codigo, nombre, descripcion, cuenta_activo,
                      cuenta_depreciacion, cuenta_gasto, costo, valor_residual,
                      fecha_adquisicion.isoformat(), vida_util_anios, metodo.value,
                      ubicacion, responsable, numero_serie, proveedor, factura))

                conn.commit()
                logger.info(f"Activo fijo registrado: {codigo} - {nombre}")
                return True, "Activo fijo registrado exitosamente", activo_id

        except Exception as e:
            logger.error(f"Error registrando activo fijo: {e}")
            return False, str(e), None

    def obtener_activo(self, activo_id: str) -> Optional[Dict]:
        """Obtiene un activo fijo por ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM activos_fijos WHERE id = ?', (activo_id,))
            row = cursor.fetchone()
            if row:
                activo = dict(row)
                # Calcular valor en libros actual
                activo['valor_en_libros'] = self._calcular_valor_en_libros(activo)
                return activo
            return None

    def listar_activos(self, estado: Optional[EstadoActivo] = None) -> List[Dict]:
        """Lista activos fijos con filtro opcional de estado"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if estado:
                cursor.execute('''
                    SELECT * FROM activos_fijos WHERE estado = ? ORDER BY codigo
                ''', (estado.value,))
            else:
                cursor.execute('SELECT * FROM activos_fijos ORDER BY codigo')

            activos = []
            for row in cursor.fetchall():
                activo = dict(row)
                activo['valor_en_libros'] = self._calcular_valor_en_libros(activo)
                activos.append(activo)

            return activos

    # ── CÁLCULO DE DEPRECIACIÓN ───────────────────────────────────────────────

    def _calcular_valor_en_libros(self, activo: Dict) -> float:
        """Calcula el valor en libros de un activo"""
        costo = activo['costo']
        valor_residual = activo.get('valor_residual', 0)

        # Obtener depreciación acumulada
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MAX(depreciacion_acumulada_actual) as acum
                FROM depreciaciones
                WHERE activo_id = ?
            ''', (activo['id'],))
            row = cursor.fetchone()
            depreciacion_acumulada = row['acum'] or 0.0

        return max(0, costo - valor_residual - depreciacion_acumulada)

    def calcular_depreciacion_anual(self, activo_id: str, anio: int) -> float:
        """
        Calcula la depreciación anual para un activo en un año específico

        Args:
            activo_id: ID del activo
            anio: Año fiscal

        Returns:
            Monto de depreciación para el año
        """
        activo = self.obtener_activo(activo_id)
        if not activo:
            return 0.0

        costo = activo['costo']
        valor_residual = activo.get('valor_residual', 0)
        vida_util = activo['vida_util_anios']
        metodo = MetodoDepreciacion(activo['metodo'])
        fecha_adquisicion = datetime.strptime(activo['fecha_adquisicion'], "%Y-%m-%d").date()

        # Verificar si el activo está dado de baja
        if activo['estado'] in ['dado_de_baja', 'vendido']:
            return 0.0

        # Verificar si ya está totalmente depreciado
        valor_en_libros = self._calcular_valor_en_libros(activo)
        if valor_en_libros <= 0.01:
            return 0.0

        # Calcular año de vida del activo
        anio_adquisicion = fecha_adquisicion.year
        anio_vida = anio - anio_adquisicion + 1

        if anio_vida < 1 or anio_vida > vida_util:
            return 0.0

        base_depreciable = costo - valor_residual

        if metodo == MetodoDepreciacion.LINEAL:
            # Método lineal: misma cantidad cada año
            return base_depreciable / vida_util

        elif metodo == MetodoDepreciacion.ACELERADO_SUMA_DIGITOS:
            # Método de suma de dígitos
            suma_digitos = sum(range(1, vida_util + 1))
            anios_restantes = vida_util - anio_vida + 1
            return base_depreciable * anios_restantes / suma_digitos

        elif metodo == MetodoDepreciacion.ACELERADO_DOBLE_SALDO:
            # Método de doble saldo decreciente
            tasa = 2.0 / vida_util
            valor_en_libros_inicio_anio = self._calcular_valor_en_libros(activo)
            depreciacion = valor_en_libros_inicio_anio * tasa

            # No depreciar por debajo del valor residual
            if valor_en_libros_inicio_anio - depreciacion < valor_residual:
                depreciacion = valor_en_libros_inicio_anio - valor_residual

            return max(0, depreciacion)

        return 0.0

    def generar_depreciacion_periodo(self, periodo: str) -> Tuple[bool, str, List[str]]:
        """
        Genera las depreciaciones para todos los activos en un período

        Args:
            periodo: Período en formato YYYY-MM

        Returns:
            (exito, mensaje, lista_depreciaciones_generadas)
        """
        try:
            anio, mes = map(int, periodo.split('-'))
            fecha_periodo = date(anio, mes, 1)

            activos = self.listar_activos(estado=EstadoActivo.ACTIVO)
            depreciaciones_generadas = []

            from src.contabilidad.motor_asientos import MotorAsientos
            from src.contabilidad.schema_fiscal import AsientoContable, LineaAsiento, TipoAsiento, Moneda, EstadoAsiento

            motor_asientos = MotorAsientos(self.db_path)

            for activo in activos:
                # Calcular depreciación para el período
                monto_depreciacion = self.calcular_depreciacion_anual(activo['id'], anio)

                if monto_depreciacion <= 0.01:
                    continue

                # Verificar si ya existe depreciación para este período
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT id FROM depreciaciones
                        WHERE activo_id = ? AND periodo = ?
                    ''', (activo['id'], periodo))
                    if cursor.fetchone():
                        continue  # Ya existe, saltar

                # Crear asiento de depreciación
                lineas = [
                    LineaAsiento(
                        cuenta_codigo=activo['cuenta_gasto_depreciacion'],
                        debe=monto_depreciacion,
                        descripcion=f"Depreciación {activo['nombre']} - {periodo}"
                    ),
                    LineaAsiento(
                        cuenta_codigo=activo['cuenta_depreciacion'],
                        haber=monto_depreciacion,
                        descripcion=f"Depreciación acumulada {activo['nombre']}"
                    )
                ]

                asiento = AsientoContable(
                    fecha=fecha_periodo,
                    tipo=TipoAsiento.DEPRECIACION,
                    descripcion=f"Depreciación {activo['nombre']} - {periodo}",
                    lineas=lineas,
                    moneda=Moneda.ARS,
                    estado=EstadoAsiento.APROBADO,
                    referencia=f"DEP-{activo['codigo']}-{periodo}",
                    usuario="sistema_depreciacion"
                )

                exito, mensaje, asiento_id = motor_asientos.crear_asiento(asiento)

                if exito and asiento_id:
                    # Registrar depreciación
                    import uuid
                    with self._get_connection() as conn:
                        cursor = conn.cursor()

                        depreciacion_anterior = self._obtener_depreciacion_acumulada_anterior(activo['id'], periodo)
                        valor_libros_anterior = activo['costo'] - depreciacion_anterior

                        depreciacion_acumulada_actual = depreciacion_anterior + monto_depreciacion
                        valor_libros_actual = activo['costo'] - depreciacion_acumulada_actual

                        cursor.execute('''
                            INSERT INTO depreciaciones
                            (id, activo_id, periodo, monto_depreciacion,
                             depreciacion_acumulada_anterior, depreciacion_acumulada_actual,
                             valor_en_libros_anterior, valor_en_libros_actual, asiento_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (str(uuid.uuid4()), activo['id'], periodo,
                              monto_depreciacion, depreciacion_anterior,
                              depreciacion_acumulada_actual, valor_libros_anterior,
                              valor_libros_actual, asiento_id))

                        conn.commit()

                    depreciaciones_generadas.append(activo['codigo'])

            logger.info(f"Depreciaciones generadas para período {periodo}: {len(depreciaciones_generadas)} activos")
            return True, f"Depreciaciones generadas: {len(depreciaciones_generadas)} activos", depreciaciones_generadas

        except Exception as e:
            logger.error(f"Error generando depreciaciones: {e}")
            return False, str(e), []

    def _obtener_depreciacion_acumulada_anterior(self, activo_id: str, periodo_actual: str) -> float:
        """Obtiene la depreciación acumulada antes del período actual"""
        anio_actual, mes_actual = map(int, periodo_actual.split('-'))

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MAX(depreciacion_acumulada_actual) as acum
                FROM depreciaciones
                WHERE activo_id = ? AND periodo < ?
            ''', (activo_id, periodo_actual))
            row = cursor.fetchone()
            return row['acum'] or 0.0

    # ── REPORTES ─────────────────────────────────────────────────────────────

    def obtener_reporte_activos(self) -> Dict:
        """Obtiene un reporte completo de activos fijos"""
        activos = self.listar_activos()

        total_costo = sum(a['costo'] for a in activos)
        total_depreciacion_acumulada = 0.0
        total_valor_en_libros = 0.0

        for activo in activos:
            total_depreciacion_acumulada += (activo['costo'] - activo['valor_en_libros'])
            total_valor_en_libros += activo['valor_en_libros']

        return {
            "cantidad_activos": len(activos),
            "total_costo": total_costo,
            "total_depreciacion_acumulada": total_depreciacion_acumulada,
            "total_valor_en_libros": total_valor_en_libros,
            "activos": activos
        }

    def obtener_historial_depreciacion(self, activo_id: str) -> List[Dict]:
        """Obtiene el historial de depreciaciones de un activo"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM depreciaciones
                WHERE activo_id = ?
                ORDER BY periodo
            ''', (activo_id,))
            return [dict(row) for row in cursor.fetchall()]

    def dar_de_baja_activo(self, activo_id: str, motivo: str,
                           valor_venta: Optional[float] = None,
                           fecha_baja: Optional[date] = None) -> Tuple[bool, str]:
        """Da de baja un activo fijo"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                fecha_baja_str = (fecha_baja or date.today()).isoformat()

                cursor.execute('''
                    UPDATE activos_fijos
                    SET estado = 'dado_de_baja',
                        motivo_baja = ?,
                        valor_venta = ?,
                        fecha_baja = ?
                    WHERE id = ?
                ''', (motivo, valor_venta, fecha_baja_str, activo_id))

                conn.commit()
                logger.info(f"Activo {activo_id} dado de baja: {motivo}")
                return True, "Activo dado de baja exitosamente"

        except Exception as e:
            logger.error(f"Error dando de baja activo: {e}")
            return False, str(e)
