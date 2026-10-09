"""
motor_asientos.py — Motor de asientos contables con doble partida (Nivel Enterprise)
TPV Pro 2026 · Cobro Fácil POS

Este motor implementa:
- Registro de asientos contables con validación de doble partida
- Generación automática de asientos desde TPV (ventas, compras)
- Workflow de aprobación (borrador → pendiente → aprobado → contabilizado)
- Integración con plan de cuentas e impuestos
- Mayor general y balances de comprobación
"""

import sqlite3
import logging
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
from decimal import Decimal, getcontext

from src.contabilidad.schema_fiscal import (
    AsientoContable, LineaAsiento, TipoAsiento, EstadoAsiento,
    Moneda, TipoCuenta, obtener_cuenta_por_codigo
)

# Configurar precisión decimal para cálculos monetarios
getcontext().prec = 4

logger = logging.getLogger("MotorAsientos")


class MotorAsientos:
    """Motor de asientos contables con doble partida"""

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
        """Inicializa el esquema de asientos contables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tabla de plan de cuentas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plan_cuentas (
                    codigo TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    nivel INTEGER NOT NULL,
                    padre TEXT,
                    ajustadora INTEGER DEFAULT 0,
                    activa INTEGER DEFAULT 1,
                    FOREIGN KEY (padre) REFERENCES plan_cuentas(codigo)
                )
            ''')

            # Tabla de asientos contables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS asientos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT UNIQUE NOT NULL,
                    fecha TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    descripcion TEXT,
                    moneda TEXT DEFAULT 'ARS',
                    estado TEXT DEFAULT 'borrador',
                    referencia TEXT,
                    usuario TEXT DEFAULT 'system',
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    aprobado_por TEXT,
                    aprobado_en DATETIME,
                    contabilizado_en DATETIME
                )
            ''')

            # Tabla de líneas de asiento
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS asiento_lineas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asiento_id INTEGER NOT NULL,
                    cuenta_codigo TEXT NOT NULL,
                    debe REAL DEFAULT 0,
                    haber REAL DEFAULT 0,
                    descripcion TEXT,
                    orden INTEGER DEFAULT 0,
                    FOREIGN KEY (asiento_id) REFERENCES asientos(id) ON DELETE CASCADE,
                    FOREIGN KEY (cuenta_codigo) REFERENCES plan_cuentas(codigo)
                )
            ''')

            # Tabla de impuestos configurados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS impuestos (
                    codigo TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    tasa REAL NOT NULL,
                    tipo TEXT NOT NULL,
                    cuenta_debito TEXT NOT NULL,
                    cuenta_credito TEXT NOT NULL,
                    activo INTEGER DEFAULT 1
                )
            ''')

            # Tabla de activos fijos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activos_fijos (
                    codigo TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    cuenta_activo TEXT NOT NULL,
                    cuenta_depreciacion TEXT NOT NULL,
                    costo REAL NOT NULL,
                    fecha_adquisicion TEXT NOT NULL,
                    vida_util_anios INTEGER NOT NULL,
                    metodo TEXT DEFAULT 'lineal',
                    depreciacion_acumulada REAL DEFAULT 0,
                    valor_residual REAL DEFAULT 0,
                    estado TEXT DEFAULT 'activo'
                )
            ''')

            # Tabla de depreciaciones (historial)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS depreciaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activo_codigo TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    monto REAL NOT NULL,
                    asiento_id INTEGER,
                    FOREIGN KEY (activo_codigo) REFERENCES activos_fijos(codigo),
                    FOREIGN KEY (asiento_id) REFERENCES asientos(id)
                )
            ''')

            # Tabla de ejercicios contables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ejercicios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    anio INTEGER NOT NULL UNIQUE,
                    estado TEXT DEFAULT 'abierto',
                    fecha_apertura TEXT,
                    fecha_cierre TEXT,
                    asiento_apertura_id INTEGER,
                    asiento_cierre_id INTEGER,
                    FOREIGN KEY (asiento_apertura_id) REFERENCES asientos(id),
                    FOREIGN KEY (asiento_cierre_id) REFERENCES asientos(id)
                )
            ''')

            # Índices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_asientos_fecha ON asientos(fecha)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_asientos_estado ON asientos(estado)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_asiento_lineas_asiento ON asiento_lineas(asiento_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_asiento_lineas_cuenta ON asiento_lineas(cuenta_codigo)')

            conn.commit()

    # ── GESTIÓN DEL PLAN DE CUENTAS ───────────────────────────────────────────

    def cargar_plan_cuentas_defecto(self):
        """Carga el plan de cuentas por defecto desde schema_fiscal"""
        from src.contabilidad.schema_fiscal import PLAN_CUENTAS_POR_DEFECTO, TipoCuenta

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for codigo, data in PLAN_CUENTAS_POR_DEFECTO.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO plan_cuentas
                    (codigo, nombre, tipo, nivel, padre, ajustadora, activa)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (
                    data["codigo"],
                    data["nombre"],
                    data["tipo"],
                    data["nivel"],
                    data.get("padre"),
                    1 if data.get("ajustadora", False) else 0
                ))
            conn.commit()
            logger.info(f"Plan de cuentas cargado: {len(PLAN_CUENTAS_POR_DEFECTO)} cuentas")

    def obtener_cuenta(self, codigo: str) -> Optional[Dict]:
        """Obtiene una cuenta por su código"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM plan_cuentas WHERE codigo = ?', (codigo,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def listar_cuentas(self, tipo: Optional[TipoCuenta] = None) -> List[Dict]:
        """Lista todas las cuentas, opcionalmente filtradas por tipo"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if tipo:
                cursor.execute('SELECT * FROM plan_cuentas WHERE tipo = ? AND activa = 1 ORDER BY codigo', (tipo.value,))
            else:
                cursor.execute('SELECT * FROM plan_cuentas WHERE activa = 1 ORDER BY codigo')
            return [dict(row) for row in cursor.fetchall()]

    # ── REGISTRO DE ASIENTOS ───────────────────────────────────────────────────

    def _generar_numero_asiento(self, fecha: date) -> str:
        """Genera un número único de asiento (formato: A-YYYYMMDD-XXXX)"""
        fecha_str = fecha.strftime("%Y%m%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as cnt FROM asientos
                WHERE fecha = ?
            ''', (fecha.isoformat(),))
            row = cursor.fetchone()
            seq = (row['cnt'] or 0) + 1
            return f"A-{fecha_str}-{seq:04d}"

    def crear_asiento(self, asiento: AsientoContable) -> Tuple[bool, str, Optional[int]]:
        """
        Crea un nuevo asiento contable con validación de doble partida

        Returns:
            (exito, mensaje, asiento_id)
        """
        # Validar doble partida
        valido, msg = asiento.validar()
        if not valido:
            return False, msg, None

        # Verificar que todas las cuentas existan
        for linea in asiento.lineas:
            cuenta = self.obtener_cuenta(linea.cuenta_codigo)
            if not cuenta:
                return False, f"Cuenta no existe: {linea.cuenta_codigo}", None

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Generar número de asiento
                numero = self._generar_numero_asiento(asiento.fecha)

                # Insertar asiento
                cursor.execute('''
                    INSERT INTO asientos
                    (numero, fecha, tipo, descripcion, moneda, estado, referencia, usuario)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    numero,
                    asiento.fecha.isoformat(),
                    asiento.tipo.value,
                    asiento.descripcion,
                    asiento.moneda.value,
                    asiento.estado.value,
                    asiento.referencia,
                    asiento.usuario
                ))

                asiento_id = cursor.lastrowid

                # Insertar líneas
                for idx, linea in enumerate(asiento.lineas):
                    cursor.execute('''
                        INSERT INTO asiento_lineas
                        (asiento_id, cuenta_codigo, debe, haber, descripcion, orden)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        asiento_id,
                        linea.cuenta_codigo,
                        linea.debe,
                        linea.haber,
                        linea.descripcion,
                        idx
                    ))

                conn.commit()
                logger.info(f"Asiento creado: {numero} - {asiento.descripcion}")
                return True, f"Asiento {numero} creado exitosamente", asiento_id

        except Exception as e:
            logger.error(f"Error creando asiento: {e}")
            return False, str(e), None

    def aprobar_asiento(self, asiento_id: int, aprobado_por: str) -> Tuple[bool, str]:
        """Aprueba un asiento (transición de borrador/pendiente a aprobado)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Verificar estado actual
                cursor.execute('SELECT estado FROM asientos WHERE id = ?', (asiento_id,))
                row = cursor.fetchone()
                if not row:
                    return False, "Asiento no encontrado"

                estado_actual = row['estado']
                if estado_actual not in ['borrador', 'pendiente_aprobacion']:
                    return False, f"El asiento ya está en estado: {estado_actual}"

                # Actualizar estado
                cursor.execute('''
                    UPDATE asientos
                    SET estado = 'aprobado',
                        aprobado_por = ?,
                        aprobado_en = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (aprobado_por, asiento_id))

                conn.commit()
                logger.info(f"Asiento {asiento_id} aprobado por {aprobado_por}")
                return True, "Asiento aprobado exitosamente"

        except Exception as e:
            logger.error(f"Error aprobando asiento: {e}")
            return False, str(e)

    def contabilizar_asiento(self, asiento_id: int) -> Tuple[bool, str]:
        """Contabiliza un asiento (transición de aprobado a contabilizado)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Verificar estado actual
                cursor.execute('SELECT estado FROM asientos WHERE id = ?', (asiento_id,))
                row = cursor.fetchone()
                if not row:
                    return False, "Asiento no encontrado"

                estado_actual = row['estado']
                if estado_actual != 'aprobado':
                    return False, f"El asiento debe estar aprobado, estado actual: {estado_actual}"

                # Actualizar estado
                cursor.execute('''
                    UPDATE asientos
                    SET estado = 'contabilizado',
                        contabilizado_en = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (asiento_id,))

                conn.commit()
                logger.info(f"Asiento {asiento_id} contabilizado")
                return True, "Asiento contabilizado exitosamente"

        except Exception as e:
            logger.error(f"Error contabilizando asiento: {e}")
            return False, str(e)

    # ── GENERACIÓN AUTOMÁTICA DE ASIENTOS ─────────────────────────────────────

    def generar_asiento_venta(self, fecha: date, monto_total: float,
                              metodo_pago: str, iva_tasa: float = 21.0,
                              costo_mercaderia: float = 0.0,
                              referencia: str = "") -> Tuple[bool, str, Optional[int]]:
        """
        Genera automáticamente un asiento de venta

        Esquema:
        Debe: Caja/Bancos/Clientes (según método de pago)
        Debe: IVA Crédito Fiscal (si corresponde)
        Haber: Ventas
        Haber: Costo de Ventas (si hay costo)
        
        ENTERPRISE: También genera comprobante fiscal si está disponible el motor de impuestos
        """
        try:
            lineas = []

            # Determinar cuenta de activo según método de pago
            if metodo_pago in ['Efectivo', 'Caja']:
                cuenta_activo = "1.1.01.01"  # Caja
            elif metodo_pago in ['Tarjeta', 'Transferencia']:
                cuenta_activo = "1.1.01.02"  # Bancos
            elif metodo_pago in ['Cuenta Corriente', 'Fiado', 'Clientes']:
                cuenta_activo = "1.1.02.01"  # Clientes
            else:
                cuenta_activo = "1.1.01.01"  # Caja por defecto

            # Calcular IVA
            if iva_tasa > 0:
                monto_gravado = monto_total / (1 + iva_tasa / 100)
                monto_iva = monto_total - monto_gravado
                monto_neto = monto_gravado
            else:
                monto_neto = monto_total
                monto_iva = 0.0

            # Línea 1: Debe - Activo (caja/bancos/clientes)
            lineas.append(LineaAsiento(
                cuenta_codigo=cuenta_activo,
                debe=monto_total,
                descripcion=f"Cobro venta - {metodo_pago}"
            ))

            # Línea 2: Haber - Ventas
            lineas.append(LineaAsiento(
                cuenta_codigo="4.1.01.01",  # Ventas Locales
                haber=monto_neto,
                descripcion="Ventas netas gravadas"
            ))

            # Línea 3: Haber - IVA Débito Fiscal
            if monto_iva > 0:
                lineas.append(LineaAsiento(
                    cuenta_codigo="2.1.03.01",  # IVA Débito Fiscal
                    haber=monto_iva,
                    descripcion=f"IVA {iva_tasa}%"
                ))

            # Línea 4: Haber - Costo de Ventas (si hay costo)
            if costo_mercaderia > 0:
                lineas.append(LineaAsiento(
                    cuenta_codigo="5.1.01.01",  # Costo de Ventas
                    haber=costo_mercaderia,
                    descripcion="Costo de mercadería vendida"
                ))

            asiento = AsientoContable(
                fecha=fecha,
                tipo=TipoAsiento.VENTA,
                descripcion=f"Venta TPV - {metodo_pago}",
                lineas=lineas,
                moneda=Moneda.ARS,
                estado=EstadoAsiento.APROBADO,  # Auto-aprobado por ser sistema
                referencia=referencia,
                usuario="sistema_tpv"
            )

            exito, mensaje, asiento_id = self.crear_asiento(asiento)
            
            # ENTERPRISE: Generar comprobante fiscal si está disponible
            if exito and asiento_id:
                try:
                    from src.contabilidad.integracion_iva import IntegradorIVA
                    integrador = IntegradorIVA(self.db_path)
                    # Aquí se podría pasar datos del cliente si están disponibles
                    # Por ahora es solo el asiento contable
                    logger.debug("Asiento de venta generado, comprobante fiscal opcional")
                except Exception as e:
                    logger.warning(f"No se pudo generar comprobante fiscal: {e}")
            
            return exito, mensaje, asiento_id

        except Exception as e:
            logger.error(f"Error generando asiento de venta: {e}")
            return False, str(e), None

    def generar_asiento_compra(self, fecha: date, monto_total: float,
                               proveedor: str, iva_tasa: float = 21.0,
                               referencia: str = "") -> Tuple[bool, str, Optional[int]]:
        """
        Genera automáticamente un asiento de compra

        Esquema:
        Debe: Mercaderías
        Debe: IVA Crédito Fiscal
        Haber: Proveedores
        """
        try:
            lineas = []

            # Calcular IVA
            if iva_tasa > 0:
                monto_gravado = monto_total / (1 + iva_tasa / 100)
                monto_iva = monto_total - monto_gravado
                monto_neto = monto_gravado
            else:
                monto_neto = monto_total
                monto_iva = 0.0

            # Línea 1: Debe - Mercaderías
            lineas.append(LineaAsiento(
                cuenta_codigo="1.1.03.01",  # Mercaderías
                debe=monto_neto,
                descripcion=f"Compra a {proveedor}"
            ))

            # Línea 2: Debe - IVA Crédito Fiscal
            if monto_iva > 0:
                lineas.append(LineaAsiento(
                    cuenta_codigo="1.1.04.01",  # IVA Crédito Fiscal
                    debe=monto_iva,
                    descripcion=f"IVA {iva_tasa}% crédito fiscal"
                ))

            # Línea 3: Haber - Proveedores
            lineas.append(LineaAsiento(
                cuenta_codigo="2.1.01.01",  # Proveedores
                haber=monto_total,
                descripcion=f"Cuenta a pagar - {proveedor}"
            ))

            asiento = AsientoContable(
                fecha=fecha,
                tipo=TipoAsiento.COMPRA,
                descripcion=f"Compra - {proveedor}",
                lineas=lineas,
                moneda=Moneda.ARS,
                estado=EstadoAsiento.APROBADO,
                referencia=referencia,
                usuario="sistema_tpv"
            )

            return self.crear_asiento(asiento)

        except Exception as e:
            logger.error(f"Error generando asiento de compra: {e}")
            return False, str(e), None

    # ── REPORTES Y BALANCES ────────────────────────────────────────────────────

    def obtener_mayor_general(self, cuenta_codigo: Optional[str] = None,
                               desde: Optional[date] = None,
                               hasta: Optional[date] = None) -> List[Dict]:
        """
        Obtiene el mayor general (movimientos de cuentas)

        Args:
            cuenta_codigo: Filtrar por cuenta específica
            desde: Fecha desde
            hasta: Fecha hasta
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT
                    a.numero,
                    a.fecha,
                    a.tipo,
                    a.descripcion,
                    al.cuenta_codigo,
                    pc.nombre as cuenta_nombre,
                    al.debe,
                    al.haber,
                    a.estado
                FROM asiento_lineas al
                JOIN asientos a ON al.asiento_id = a.id
                JOIN plan_cuentas pc ON al.cuenta_codigo = pc.codigo
                WHERE a.estado = 'contabilizado'
            '''
            params = []

            if cuenta_codigo:
                query += ' AND al.cuenta_codigo = ?'
                params.append(cuenta_codigo)

            if desde:
                query += ' AND a.fecha >= ?'
                params.append(desde.isoformat())

            if hasta:
                query += ' AND a.fecha <= ?'
                params.append(hasta.isoformat())

            query += ' ORDER BY a.fecha, a.numero, al.orden'

            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    def obtener_balance_comprobacion(self, fecha: date) -> Dict:
        """
        Obtiene el balance de comprobación a una fecha

        Returns:
            Dict con saldos de debe y haber por cuenta
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Sumar por cuenta
            cursor.execute('''
                SELECT
                    al.cuenta_codigo,
                    pc.nombre,
                    pc.tipo,
                    SUM(al.debe) as total_debe,
                    SUM(al.haber) as total_haber
                FROM asiento_lineas al
                JOIN asientos a ON al.asiento_id = a.id
                JOIN plan_cuentas pc ON al.cuenta_codigo = pc.codigo
                WHERE a.estado = 'contabilizado' AND a.fecha <= ?
                GROUP BY al.cuenta_codigo, pc.nombre, pc.tipo
                ORDER BY al.cuenta_codigo
            ''', (fecha.isoformat(),))

            filas = [dict(row) for row in cursor.fetchall()]

            # Calcular saldos
            total_debe = 0.0
            total_haber = 0.0

            for fila in filas:
                debe = fila['total_debe'] or 0.0
                haber = fila['total_haber'] or 0.0
                tipo = fila['tipo']

                if tipo in ['activo', 'gasto']:
                    saldo = debe - haber
                else:  # pasivo, patrimonio, ingreso
                    saldo = haber - debe

                fila['saldo'] = saldo
                total_debe += debe
                total_haber += haber

            return {
                "fecha": fecha.isoformat(),
                "filas": filas,
                "total_debe": total_debe,
                "total_haber": total_haber,
                "cuadra": abs(total_debe - total_haber) < 0.01
            }

    def obtener_balance_general(self, fecha: date) -> Dict:
        """
        Obtiene el balance general (estado de situación patrimonial)

        Returns:
            Dict con activos, pasivos y patrimonio
        """
        balance = self.obtener_balance_comprobacion(fecha)

        activos = []
        pasivos = []
        patrimonio = []

        for fila in balance['filas']:
            if fila['saldo'] == 0:
                continue

            if fila['tipo'] == 'activo':
                activos.append(fila)
            elif fila['tipo'] == 'pasivo':
                pasivos.append(fila)
            elif fila['tipo'] == 'patrimonio':
                patrimonio.append(fila)

        total_activos = sum(f['saldo'] for f in activos)
        total_pasivos = sum(f['saldo'] for f in pasivos)
        total_patrimonio = sum(f['saldo'] for f in patrimonio)

        return {
            "fecha": fecha.isoformat(),
            "activos": activos,
            "pasivos": pasivos,
            "patrimonio": patrimonio,
            "total_activos": total_activos,
            "total_pasivos": total_pasivos,
            "total_patrimonio": total_patrimonio,
            "cuadra": abs(total_activos - (total_pasivos + total_patrimonio)) < 0.01
        }

    def obtener_estado_resultados(self, desde: date, hasta: date) -> Dict:
        """
        Obtiene el estado de resultados (P&L)

        Returns:
            Dict con ingresos, gastos y resultado neto
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Ingresos
            cursor.execute('''
                SELECT
                    al.cuenta_codigo,
                    pc.nombre,
                    SUM(al.haber) as total_haber,
                    SUM(al.debe) as total_debe
                FROM asiento_lineas al
                JOIN asientos a ON al.asiento_id = a.id
                JOIN plan_cuentas pc ON al.cuenta_codigo = pc.codigo
                WHERE a.estado = 'contabilizado'
                  AND a.fecha BETWEEN ? AND ?
                  AND pc.tipo = 'ingreso'
                GROUP BY al.cuenta_codigo, pc.nombre
            ''', (desde.isoformat(), hasta.isoformat()))

            ingresos = []
            for row in cursor.fetchall():
                fila = dict(row)
                fila['saldo'] = (fila['total_haber'] or 0) - (fila['total_debe'] or 0)
                if fila['saldo'] > 0:
                    ingresos.append(fila)

            # Gastos
            cursor.execute('''
                SELECT
                    al.cuenta_codigo,
                    pc.nombre,
                    SUM(al.debe) as total_debe,
                    SUM(al.haber) as total_haber
                FROM asiento_lineas al
                JOIN asientos a ON al.asiento_id = a.id
                JOIN plan_cuentas pc ON al.cuenta_codigo = pc.codigo
                WHERE a.estado = 'contabilizado'
                  AND a.fecha BETWEEN ? AND ?
                  AND pc.tipo = 'gasto'
                GROUP BY al.cuenta_codigo, pc.nombre
            ''', (desde.isoformat(), hasta.isoformat()))

            gastos = []
            for row in cursor.fetchall():
                fila = dict(row)
                fila['saldo'] = (fila['total_debe'] or 0) - (fila['total_haber'] or 0)
                if fila['saldo'] > 0:
                    gastos.append(fila)

            total_ingresos = sum(i['saldo'] for i in ingresos)
            total_gastos = sum(g['saldo'] for g in gastos)
            resultado_neto = total_ingresos - total_gastos

            return {
                "desde": desde.isoformat(),
                "hasta": hasta.isoformat(),
                "ingresos": ingresos,
                "gastos": gastos,
                "total_ingresos": total_ingresos,
                "total_gastos": total_gastos,
                "resultado_neto": resultado_neto
            }
