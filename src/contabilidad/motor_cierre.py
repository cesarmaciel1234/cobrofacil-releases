"""
motor_cierre.py — Motor de cierre de ejercicio contable (Nivel Enterprise)
TPV Pro 2026 · Cobro Fácil POS

Este módulo implementa:
- Gestión de ejercicios contables
- Asiento de cierre de cuentas de resultados
- Asiento de apertura del nuevo ejercicio
- Traspaso de resultado a patrimonio
- Generación de balances de cierre
- Archivo y bloqueo de ejercicios cerrados
"""

import sqlite3
import logging
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum
import uuid

logger = logging.getLogger("MotorCierre")


class EstadoEjercicio(Enum):
    """Estados de un ejercicio contable"""
    ABIERTO = "abierto"
    EN_PROCESO_CIERRE = "en_proceso_cierre"
    CERRADO = "cerrado"
    ARCHIVADO = "archivado"


class MotorCierre:
    """Motor de cierre de ejercicio contable"""

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
        """Inicializa el esquema de ejercicios"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tabla de ejercicios contables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ejercicios (
                    id TEXT PRIMARY KEY,
                    anio INTEGER NOT NULL UNIQUE,
                    estado TEXT DEFAULT 'abierto',
                    fecha_apertura TEXT,
                    fecha_cierre TEXT,
                    asiento_apertura_id INTEGER,
                    asiento_cierre_id INTEGER,
                    asiento_resultado_id INTEGER,
                    resultado_ejercicio REAL DEFAULT 0,
                    cerrado_por TEXT,
                    archivado_por TEXT,
                    notas TEXT,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asiento_apertura_id) REFERENCES asientos(id),
                    FOREIGN KEY (asiento_cierre_id) REFERENCES asientos(id),
                    FOREIGN KEY (asiento_resultado_id) REFERENCES asientos(id)
                )
            ''')

            # Tabla de asientos de cierre
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS asientos_cierre_detalle (
                    id TEXT PRIMARY KEY,
                    ejercicio_id TEXT NOT NULL,
                    cuenta_codigo TEXT NOT NULL,
                    tipo_cuenta TEXT NOT NULL,
                    saldo_cierre REAL NOT NULL,
                    debe REAL DEFAULT 0,
                    haber REAL DEFAULT 0,
                    cuenta_destino TEXT,
                    FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id)
                )
            ''')

            # Tabla de archivos de ejercicios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS archivos_ejercicios (
                    id TEXT PRIMARY KEY,
                    ejercicio_id TEXT NOT NULL,
                    tipo_archivo TEXT NOT NULL,
                    ruta_archivo TEXT NOT NULL,
                    tamaño_bytes INTEGER,
                    hash_md5 TEXT,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id)
                )
            ''')

            # Índices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ejercicios_anio ON ejercicios(anio)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ejercicios_estado ON ejercicios(estado)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cierre_detalle_ejercicio ON asientos_cierre_detalle(ejercicio_id)')

            conn.commit()

    # ── GESTIÓN DE EJERCICIOS ─────────────────────────────────────────────────

    def crear_ejercicio(self, anio: int, fecha_apertura: Optional[date] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Crea un nuevo ejercicio contable

        Returns:
            (exito, mensaje, ejercicio_id)
        """
        try:
            ejercicio_id = str(uuid.uuid4())
            fecha_apertura_str = (fecha_apertura or date(anio, 1, 1)).isoformat()

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Verificar que no exista
                cursor.execute('SELECT id FROM ejercicios WHERE anio = ?', (anio,))
                if cursor.fetchone():
                    return False, f"El ejercicio {anio} ya existe", None

                # Insertar ejercicio
                cursor.execute('''
                    INSERT INTO ejercicios
                    (id, anio, estado, fecha_apertura)
                    VALUES (?, ?, 'abierto', ?)
                ''', (ejercicio_id, anio, fecha_apertura_str))

                conn.commit()
                logger.info(f"Ejercicio creado: {anio}")
                return True, f"Ejercicio {anio} creado exitosamente", ejercicio_id

        except Exception as e:
            logger.error(f"Error creando ejercicio: {e}")
            return False, str(e), None

    def obtener_ejercicio(self, anio: int) -> Optional[Dict]:
        """Obtiene un ejercicio por año"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM ejercicios WHERE anio = ?', (anio,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def obtener_ejercicio_actual(self) -> Optional[Dict]:
        """Obtiene el ejercicio actual (el más reciente abierto)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM ejercicios
                WHERE estado = 'abierto'
                ORDER BY anio DESC
                LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None

    def listar_ejercicios(self) -> List[Dict]:
        """Lista todos los ejercicios"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM ejercicios ORDER BY anio DESC')
            return [dict(row) for row in cursor.fetchall()]

    # ── CIERRE DE EJERCICIO ───────────────────────────────────────────────────

    def iniciar_cierre(self, anio: int, usuario: str) -> Tuple[bool, str]:
        """Inicia el proceso de cierre de un ejercicio"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Verificar estado
                cursor.execute('SELECT estado FROM ejercicios WHERE anio = ?', (anio,))
                row = cursor.fetchone()
                if not row:
                    return False, f"El ejercicio {anio} no existe"

                estado = row['estado']
                if estado != 'abierto':
                    return False, f"El ejercicio no está abierto, estado actual: {estado}"

                # Cambiar estado
                cursor.execute('''
                    UPDATE ejercicios
                    SET estado = 'en_proceso_cierre'
                    WHERE anio = ?
                ''', (anio,))

                conn.commit()
                logger.info(f"Cierre iniciado para ejercicio {anio}")
                return True, "Cierre iniciado exitosamente"

        except Exception as e:
            logger.error(f"Error iniciando cierre: {e}")
            return False, str(e)

    def generar_asiento_cierre(self, anio: int, usuario: str) -> Tuple[bool, str, Optional[int]]:
        """
        Genera el asiento de cierre de cuentas de resultados

        Cierra todas las cuentas de ingresos y gastos, traspasando el resultado
        a la cuenta de Resultado del Ejercicio en patrimonio
        """
        try:
            from src.contabilidad.motor_asientos import MotorAsientos
            from src.contabilidad.schema_fiscal import AsientoContable, LineaAsiento, TipoAsiento, Moneda, EstadoAsiento

            motor = MotorAsientos(self.db_path)

            # Obtener saldos de cuentas de resultados al 31/12 del año
            fecha_cierre = date(anio, 12, 31)
            balance = motor.obtener_balance_comprobacion(fecha_cierre)

            lineas = []
            total_ingresos = 0.0
            total_gastos = 0.0

            # Cerrar cuentas de ingresos (haber → debe)
            for fila in balance['filas']:
                if fila['tipo'] == 'ingreso' and fila['saldo'] > 0:
                    lineas.append(LineaAsiento(
                        cuenta_codigo=fila['cuenta_codigo'],
                        debe=fila['saldo'],
                        descripcion=f"Cierre cuenta {fila['nombre']}"
                    ))
                    total_ingresos += fila['saldo']

            # Cerrar cuentas de gastos (debe → haber)
            for fila in balance['filas']:
                if fila['tipo'] == 'gasto' and fila['saldo'] > 0:
                    lineas.append(LineaAsiento(
                        cuenta_codigo=fila['cuenta_codigo'],
                        haber=fila['saldo'],
                        descripcion=f"Cierre cuenta {fila['nombre']}"
                    ))
                    total_gastos += fila['saldo']

            # Calcular resultado
            resultado = total_ingresos - total_gastos

            # Traspasar resultado a Resultado del Ejercicio
            if resultado > 0:
                # Ganancia: Resultado del Ejercicio (haber)
                lineas.append(LineaAsiento(
                    cuenta_codigo="3.1.04.01",  # Resultado del Ejercicio
                    haber=resultado,
                    descripcion="Resultado del ejercicio (ganancia)"
                ))
            elif resultado < 0:
                # Pérdida: Resultado del Ejercicio (debe)
                lineas.append(LineaAsiento(
                    cuenta_codigo="3.1.04.01",  # Resultado del Ejercicio
                    debe=abs(resultado),
                    descripcion="Resultado del ejercicio (pérdida)"
                ))

            # Crear asiento de cierre
            asiento = AsientoContable(
                fecha=fecha_cierre,
                tipo=TipoAsiento.CIERRE,
                descripcion=f"Cierre de ejercicio {anio}",
                lineas=lineas,
                moneda=Moneda.ARS,
                estado=EstadoAsiento.APROBADO,
                referencia=f"CIERRE-{anio}",
                usuario=usuario
            )

            exito, mensaje, asiento_id = motor.crear_asiento(asiento)

            if exito and asiento_id:
                # Actualizar ejercicio
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE ejercicios
                        SET asiento_cierre_id = ?, resultado_ejercicio = ?
                        WHERE anio = ?
                    ''', (asiento_id, resultado, anio))
                    conn.commit()

                logger.info(f"Asiento de cierre generado para ejercicio {anio}, resultado: {resultado}")
                return True, f"Asiento de cierre generado, resultado: {resultado}", asiento_id
            else:
                return False, mensaje, None

        except Exception as e:
            logger.error(f"Error generando asiento de cierre: {e}")
            return False, str(e), None

    def generar_asiento_apertura(self, anio_nuevo: int, usuario: str) -> Tuple[bool, str, Optional[int]]:
        """
        Genera el asiento de apertura del nuevo ejercicio

        Copia los saldos de las cuentas de balance (activo, pasivo, patrimonio)
        del ejercicio anterior al nuevo
        """
        try:
            from src.contabilidad.motor_asientos import MotorAsientos
            from src.contabilidad.schema_fiscal import AsientoContable, LineaAsiento, TipoAsiento, Moneda, EstadoAsiento

            motor = MotorAsientos(self.db_path)

            # Obtener balances al 31/12 del año anterior
            anio_anterior = anio_nuevo - 1
            fecha_cierre_anterior = date(anio_anterior, 12, 31)
            balance = motor.obtener_balance_comprobacion(fecha_cierre_anterior)

            lineas = []

            # Solo cuentas de balance (activo, pasivo, patrimonio)
            for fila in balance['filas']:
                if fila['tipo'] in ['activo', 'pasivo', 'patrimonio'] and fila['saldo'] != 0:
                    if fila['tipo'] in ['activo']:
                        # Activos: mantienen saldo al debe
                        lineas.append(LineaAsiento(
                            cuenta_codigo=fila['cuenta_codigo'],
                            debe=fila['saldo'],
                            descripcion=f"Apertura saldo {fila['nombre']}"
                        ))
                    else:
                        # Pasivos y patrimonio: mantienen saldo al haber
                        lineas.append(LineaAsiento(
                            cuenta_codigo=fila['cuenta_codigo'],
                            haber=fila['saldo'],
                            descripcion=f"Apertura saldo {fila['nombre']}"
                        ))

            # Crear asiento de apertura
            fecha_apertura = date(anio_nuevo, 1, 1)
            asiento = AsientoContable(
                fecha=fecha_apertura,
                tipo=TipoAsiento.APERTURA,
                descripcion=f"Apertura de ejercicio {anio_nuevo}",
                lineas=lineas,
                moneda=Moneda.ARS,
                estado=EstadoAsiento.APROBADO,
                referencia=f"APERTURA-{anio_nuevo}",
                usuario=usuario
            )

            exito, mensaje, asiento_id = motor.crear_asiento(asiento)

            if exito and asiento_id:
                # Actualizar ejercicio nuevo
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE ejercicios
                        SET asiento_apertura_id = ?
                        WHERE anio = ?
                    ''', (asiento_id, anio_nuevo))
                    conn.commit()

                logger.info(f"Asiento de apertura generado para ejercicio {anio_nuevo}")
                return True, f"Asiento de apertura generado para ejercicio {anio_nuevo}", asiento_id
            else:
                return False, mensaje, None

        except Exception as e:
            logger.error(f"Error generando asiento de apertura: {e}")
            return False, str(e), None

    def finalizar_cierre(self, anio: int, usuario: str) -> Tuple[bool, str]:
        """Finaliza el cierre de un ejercicio"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Verificar estado
                cursor.execute('''
                    SELECT asiento_cierre_id FROM ejercicios WHERE anio = ?
                ''', (anio,))
                row = cursor.fetchone()
                if not row:
                    return False, f"El ejercicio {anio} no existe"

                if not row['asiento_cierre_id']:
                    return False, "Debe generar el asiento de cierre antes de finalizar"

                # Cambiar estado a cerrado
                cursor.execute('''
                    UPDATE ejercicios
                    SET estado = 'cerrado',
                        fecha_cierre = CURRENT_TIMESTAMP,
                        cerrado_por = ?
                    WHERE anio = ?
                ''', (usuario, anio))

                conn.commit()
                logger.info(f"Ejercicio {anio} cerrado por {usuario}")
                return True, f"Ejercicio {anio} cerrado exitosamente"

        except Exception as e:
            logger.error(f"Error finalizando cierre: {e}")
            return False, str(e)

    def proceso_completo_cierre(self, anio: int, usuario: str) -> Tuple[bool, str]:
        """
        Ejecuta el proceso completo de cierre:
        1. Iniciar cierre
        2. Generar asiento de cierre
        3. Generar asiento de apertura del siguiente año
        4. Finalizar cierre
        """
        try:
            # 1. Iniciar cierre
            exito, msg = self.iniciar_cierre(anio, usuario)
            if not exito:
                return False, f"Error iniciando cierre: {msg}"

            # 2. Generar asiento de cierre
            exito, msg, asiento_cierre_id = self.generar_asiento_cierre(anio, usuario)
            if not exito:
                return False, f"Error generando asiento de cierre: {msg}"

            # 3. Generar asiento de apertura del siguiente año
            anio_siguiente = anio + 1
            exito, msg, asiento_apertura_id = self.generar_asiento_apertura(anio_siguiente, usuario)
            if not exito:
                return False, f"Error generando asiento de apertura: {msg}"

            # 4. Finalizar cierre
            exito, msg = self.finalizar_cierre(anio, usuario)
            if not exito:
                return False, f"Error finalizando cierre: {msg}"

            return True, f"Cierre completo del ejercicio {anio} finalizado exitosamente"

        except Exception as e:
            logger.error(f"Error en proceso completo de cierre: {e}")
            return False, str(e)

    # ── REPORTES DE CIERRE ────────────────────────────────────────────────────

    def obtener_balance_cierre(self, anio: int) -> Dict:
        """Obtiene el balance de cierre de un ejercicio"""
        ejercicio = self.obtener_ejercicio(anio)
        if not ejercicio:
            return {"error": "Ejercicio no encontrado"}

        from src.contabilidad.motor_asientos import MotorAsientos

        motor = MotorAsientos(self.db_path)
        fecha_cierre = date(anio, 12, 31)

        balance_general = motor.obtener_balance_general(fecha_cierre)
        estado_resultados = motor.obtener_estado_resultados(date(anio, 1, 1), fecha_cierre)

        return {
            "ejercicio": ejercicio,
            "balance_general": balance_general,
            "estado_resultados": estado_resultados
        }

    def archivar_ejercicio(self, anio: int, usuario: str, ruta_archivo: str) -> Tuple[bool, str]:
        """Archiva un ejercicio cerrado"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Verificar estado
                cursor.execute('SELECT estado FROM ejercicios WHERE anio = ?', (anio,))
                row = cursor.fetchone()
                if not row:
                    return False, f"El ejercicio {anio} no existe"

                estado = row['estado']
                if estado != 'cerrado':
                    return False, f"Solo se pueden archivar ejercicios cerrados, estado actual: {estado}"

                # Cambiar estado
                cursor.execute('''
                    UPDATE ejercicios
                    SET estado = 'archivado',
                        archivado_por = ?
                    WHERE anio = ?
                ''', (usuario, anio))

                # Registrar archivo
                import os
                archivo_id = str(uuid.uuid4())
                tamaño = os.path.getsize(ruta_archivo) if os.path.exists(ruta_archivo) else 0

                cursor.execute('''
                    INSERT INTO archivos_ejercicios
                    (id, ejercicio_id, tipo_archivo, ruta_archivo, tamaño_bytes)
                    VALUES (?, (SELECT id FROM ejercicios WHERE anio = ?), 'backup_completo', ?, ?)
                ''', (archivo_id, anio, ruta_archivo, tamaño))

                conn.commit()
                logger.info(f"Ejercicio {anio} archivado en {ruta_archivo}")
                return True, f"Ejercicio {anio} archivado exitosamente"

        except Exception as e:
            logger.error(f"Error archivando ejercicio: {e}")
            return False, str(e)
