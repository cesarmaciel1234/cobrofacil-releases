"""
multi_empresa.py — Sistema multi-empresa con tenant IDs (Nivel Enterprise)
TPV Pro 2026 · Cobro Fácil POS

Este módulo implementa:
- Multi-tenant con separación por empresa_id
- Gestión de empresas/sucursales
- Consolidación financiera multi-sucursal
- Jerarquía organizacional (holding → empresas → sucursales)
- Mapeo de usuarios a empresas
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum
import uuid

logger = logging.getLogger("MultiEmpresa")


class TipoEmpresa(Enum):
    """Tipos de entidades en la jerarquía"""
    HOLDING = "holding"
    EMPRESA = "empresa"
    SUCURSAL = "sucursal"


class EstadoEmpresa(Enum):
    """Estados de una empresa"""
    ACTIVA = "activa"
    SUSPENDIDA = "suspendida"
    CERRADA = "cerrada"


class MotorMultiEmpresa:
    """Motor de gestión multi-empresa"""

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
        """Inicializa el esquema multi-empresa"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tabla de empresas (tenants)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS empresas (
                    id TEXT PRIMARY KEY,
                    codigo TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    parent_id TEXT,
                    cuit TEXT UNIQUE,
                    direccion TEXT,
                    telefono TEXT,
                    email TEXT,
                    moneda_principal TEXT DEFAULT 'ARS',
                    estado TEXT DEFAULT 'activa',
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_baja DATETIME,
                    configuracion_json TEXT,
                    FOREIGN KEY (parent_id) REFERENCES empresas(id)
                )
            ''')

            # Tabla de relación usuario-empresa
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuario_empresas (
                    id TEXT PRIMARY KEY,
                    usuario_id TEXT NOT NULL,
                    empresa_id TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    es_principal INTEGER DEFAULT 0,
                    fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_baja DATETIME,
                    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
                    UNIQUE(usuario_id, empresa_id)
                )
            ''')

            # Tabla de centros de costo
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS centros_costo (
                    id TEXT PRIMARY KEY,
                    empresa_id TEXT NOT NULL,
                    codigo TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    parent_id TEXT,
                    activo INTEGER DEFAULT 1,
                    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
                    FOREIGN KEY (parent_id) REFERENCES centros_costo(id),
                    UNIQUE(empresa_id, codigo)
                )
            ''')

            # Tabla de configuración por empresa
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS empresa_config (
                    empresa_id TEXT PRIMARY KEY,
                    plan_cuentas_id TEXT,
                    ejercicio_corriente INTEGER,
                    moneda_base TEXT DEFAULT 'ARS',
                    requiere_aprobacion INTEGER DEFAULT 0,
                    nivel_aprobacion INTEGER DEFAULT 1,
                    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
                )
            ''')

            # Tabla de consolidaciones (histórico)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consolidaciones (
                    id TEXT PRIMARY KEY,
                    empresa_id TEXT NOT NULL,
                    periodo_desde TEXT NOT NULL,
                    periodo_hasta TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    archivo_path TEXT,
                    generado_por TEXT,
                    generado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
                )
            ''')

            # Índices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_empresas_tipo ON empresas(tipo)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_empresas_parent ON empresas(parent_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuario_empresas_usuario ON usuario_empresas(usuario_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuario_empresas_empresa ON usuario_empresas(empresa_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_centros_costo_empresa ON centros_costo(empresa_id)')

            conn.commit()

    # ── GESTIÓN DE EMPRESAS ───────────────────────────────────────────────────

    def crear_empresa(self, codigo: str, nombre: str, tipo: TipoEmpresa,
                       parent_id: Optional[str] = None, cuit: Optional[str] = None,
                       direccion: Optional[str] = None, telefono: Optional[str] = None,
                       email: Optional[str] = None, moneda: str = "ARS") -> Tuple[bool, str, Optional[str]]:
        """
        Crea una nueva empresa/sucursal

        Returns:
            (exito, mensaje, empresa_id)
        """
        try:
            empresa_id = str(uuid.uuid4())

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Verificar que el código no exista
                cursor.execute('SELECT id FROM empresas WHERE codigo = ?', (codigo,))
                if cursor.fetchone():
                    return False, f"El código {codigo} ya existe", None

                # Verificar parent si existe
                if parent_id:
                    cursor.execute('SELECT id FROM empresas WHERE id = ?', (parent_id,))
                    if not cursor.fetchone():
                        return False, "La empresa padre no existe", None

                # Insertar empresa
                cursor.execute('''
                    INSERT INTO empresas
                    (id, codigo, nombre, tipo, parent_id, cuit, direccion, telefono, email, moneda_principal, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'activa')
                ''', (empresa_id, codigo, nombre, tipo.value, parent_id, cuit,
                      direccion, telefono, email, moneda))

                # Crear configuración por defecto
                cursor.execute('''
                    INSERT INTO empresa_config
                    (empresa_id, plan_cuentas_id, ejercicio_corriente, moneda_base)
                    VALUES (?, 'DEFAULT', ?, ?)
                ''', (empresa_id, datetime.now().year, moneda))

                conn.commit()
                logger.info(f"Empresa creada: {codigo} - {nombre} ({empresa_id})")
                return True, "Empresa creada exitosamente", empresa_id

        except Exception as e:
            logger.error(f"Error creando empresa: {e}")
            return False, str(e), None

    def obtener_empresa(self, empresa_id: str) -> Optional[Dict]:
        """Obtiene una empresa por ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM empresas WHERE id = ?', (empresa_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def obtener_empresa_por_codigo(self, codigo: str) -> Optional[Dict]:
        """Obtiene una empresa por código"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM empresas WHERE codigo = ?', (codigo,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def listar_empresas(self, tipo: Optional[TipoEmpresa] = None,
                        estado: Optional[EstadoEmpresa] = None,
                        parent_id: Optional[str] = None) -> List[Dict]:
        """Lista empresas con filtros opcionales"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM empresas WHERE 1=1'
            params = []

            if tipo:
                query += ' AND tipo = ?'
                params.append(tipo.value)

            if estado:
                query += ' AND estado = ?'
                params.append(estado.value)

            if parent_id:
                query += ' AND parent_id = ?'
                params.append(parent_id)

            query += ' ORDER BY codigo'

            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    def obtener_arbol_empresas(self, parent_id: Optional[str] = None) -> List[Dict]:
        """
        Obtiene el árbol jerárquico de empresas

        Args:
            parent_id: Si es None, devuelve la raíz (holdings)
        """
        empresas = self.listar_empresas(parent_id=parent_id)

        for emp in empresas:
            emp['hijos'] = self.obtener_arbol_empresas(emp['id'])

        return empresas

    def actualizar_empresa(self, empresa_id: str, **kwargs) -> Tuple[bool, str]:
        """Actualiza datos de una empresa"""
        try:
            campos_permitidos = ['nombre', 'cuit', 'direccion', 'telefono', 'email',
                                 'moneda_principal', 'estado']

            actualizaciones = []
            params = []

            for campo, valor in kwargs.items():
                if campo in campos_permitidos:
                    actualizaciones.append(f"{campo} = ?")
                    params.append(valor)

            if not actualizaciones:
                return False, "No hay campos para actualizar"

            params.append(empresa_id)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE empresas
                    SET {', '.join(actualizaciones)}
                    WHERE id = ?
                ''', tuple(params))
                conn.commit()

            return True, "Empresa actualizada exitosamente"

        except Exception as e:
            logger.error(f"Error actualizando empresa: {e}")
            return False, str(e)

    # ── GESTIÓN DE USUARIOS POR EMPRESA ───────────────────────────────────────

    def asignar_usuario_empresa(self, usuario_id: str, empresa_id: str,
                                  rol: str, es_principal: bool = False) -> Tuple[bool, str]:
        """
        Asigna un usuario a una empresa con un rol

        Roles posibles: 'admin', 'contador', 'auditor', 'operador', 'visor'
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Verificar que existan ambos
                cursor.execute('SELECT id FROM empresas WHERE id = ?', (empresa_id,))
                if not cursor.fetchone():
                    return False, "La empresa no existe"

                # Si es principal, quitar principalidad de otros
                if es_principal:
                    cursor.execute('''
                        UPDATE usuario_empresas
                        SET es_principal = 0
                        WHERE usuario_id = ? AND empresa_id = ?
                    ''', (usuario_id, empresa_id))

                # Insertar o actualizar
                asignacion_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT OR REPLACE INTO usuario_empresas
                    (id, usuario_id, empresa_id, rol, es_principal, fecha_asignacion)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (asignacion_id, usuario_id, empresa_id, rol, 1 if es_principal else 0))

                conn.commit()
                logger.info(f"Usuario {usuario_id} asignado a empresa {empresa_id} como {rol}")
                return True, "Usuario asignado exitosamente"

        except Exception as e:
            logger.error(f"Error asignando usuario a empresa: {e}")
            return False, str(e)

    def obtener_empresas_usuario(self, usuario_id: str) -> List[Dict]:
        """Obtiene todas las empresas a las que tiene acceso un usuario"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.*, ue.rol, ue.es_principal
                FROM empresas e
                JOIN usuario_empresas ue ON e.id = ue.empresa_id
                WHERE ue.usuario_id = ? AND ue.fecha_baja IS NULL
                  AND e.estado = 'activa'
                ORDER BY ue.es_principal DESC, e.codigo
            ''', (usuario_id,))
            return [dict(row) for row in cursor.fetchall()]

    def obtener_usuario_empresa_principal(self, usuario_id: str) -> Optional[Dict]:
        """Obtiene la empresa principal de un usuario"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.*, ue.rol
                FROM empresas e
                JOIN usuario_empresas ue ON e.id = ue.empresa_id
                WHERE ue.usuario_id = ? AND ue.es_principal = 1
                  AND ue.fecha_baja IS NULL AND e.estado = 'activa'
                LIMIT 1
            ''', (usuario_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ── CENTROS DE COSTO ───────────────────────────────────────────────────────

    def crear_centro_costo(self, empresa_id: str, codigo: str, nombre: str,
                            parent_id: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Crea un centro de costo para una empresa"""
        try:
            centro_id = str(uuid.uuid4())

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Verificar unicidad
                cursor.execute('''
                    SELECT id FROM centros_costo
                    WHERE empresa_id = ? AND codigo = ?
                ''', (empresa_id, codigo))
                if cursor.fetchone():
                    return False, f"El código {codigo} ya existe en esta empresa", None

                cursor.execute('''
                    INSERT INTO centros_costo
                    (id, empresa_id, codigo, nombre, parent_id, activo)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (centro_id, empresa_id, codigo, nombre, parent_id))

                conn.commit()
                logger.info(f"Centro de costo creado: {codigo} para empresa {empresa_id}")
                return True, "Centro de costo creado exitosamente", centro_id

        except Exception as e:
            logger.error(f"Error creando centro de costo: {e}")
            return False, str(e), None

    def listar_centros_costo(self, empresa_id: str) -> List[Dict]:
        """Lista centros de costo de una empresa"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM centros_costo
                WHERE empresa_id = ? AND activo = 1
                ORDER BY codigo
            ''', (empresa_id,))
            return [dict(row) for row in cursor.fetchall()]

    # ── CONSOLIDACIÓN FINANCIERA ───────────────────────────────────────────────

    def consolidar_empresas(self, empresa_ids: List[str], desde: str, hasta: str,
                            tipo: str = "balance_general") -> Tuple[bool, str, Optional[Dict]]:
        """
        Genera una consolidación financiera de múltiples empresas

        Args:
            empresa_ids: Lista de IDs de empresas a consolidar
            desde: Fecha desde (YYYY-MM-DD)
            hasta: Fecha hasta (YYYY-MM-DD)
            tipo: Tipo de consolidación ('balance_general', 'estado_resultados', 'flujo_efectivo')

        Returns:
            (exito, mensaje, datos_consolidacion)
        """
        try:
            from src.contabilidad.motor_asientos import MotorAsientos

            consolidacion = {
                "empresa_ids": empresa_ids,
                "desde": desde,
                "hasta": hasta,
                "tipo": tipo,
                "empresas": [],
                "totales": {}
            }

            total_activos = 0.0
            total_pasivos = 0.0
            total_patrimonio = 0.0
            total_ingresos = 0.0
            total_gastos = 0.0

            for emp_id in empresa_ids:
                empresa = self.obtener_empresa(emp_id)
                if not empresa:
                    continue

                # Obtener configuración de la empresa
                config = self._obtener_config_empresa(emp_id)
                db_path = config.get('db_path') if config else None

                if not db_path:
                    logger.warning(f"No hay DB path para empresa {emp_id}")
                    continue

                # Obtener datos de cada empresa
                motor = MotorAsientos(db_path)

                if tipo == "balance_general":
                    balance = motor.obtener_balance_general(
                        datetime.strptime(hasta, "%Y-%m-%d").date()
                    )
                    empresa_data = {
                        "empresa": empresa,
                        "balance": balance
                    }
                    total_activos += balance.get('total_activos', 0)
                    total_pasivos += balance.get('total_pasivos', 0)
                    total_patrimonio += balance.get('total_patrimonio', 0)

                elif tipo == "estado_resultados":
                    desde_date = datetime.strptime(desde, "%Y-%m-%d").date()
                    hasta_date = datetime.strptime(hasta, "%Y-%m-%d").date()
                    er = motor.obtener_estado_resultados(desde_date, hasta_date)
                    empresa_data = {
                        "empresa": empresa,
                        "estado_resultados": er
                    }
                    total_ingresos += er.get('total_ingresos', 0)
                    total_gastos += er.get('total_gastos', 0)

                consolidacion['empresas'].append(empresa_data)

            # Calcular totales consolidados
            if tipo == "balance_general":
                consolidacion['totales'] = {
                    "total_activos": total_activos,
                    "total_pasivos": total_pasivos,
                    "total_patrimonio": total_patrimonio,
                    "total_pasivo_patrimonio": total_pasivos + total_patrimonio,
                    "cuadra": abs(total_activos - (total_pasivos + total_patrimonio)) < 0.01
                }
            elif tipo == "estado_resultados":
                consolidacion['totales'] = {
                    "total_ingresos": total_ingresos,
                    "total_gastos": total_gastos,
                    "resultado_neto_consolidado": total_ingresos - total_gastos
                }

            # Guardar registro de consolidación
            with self._get_connection() as conn:
                cursor = conn.cursor()
                consolidacion_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO consolidaciones
                    (id, empresa_id, periodo_desde, periodo_hasta, tipo, generado_por)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (consolidacion_id, empresa_ids[0] if empresa_ids else None,
                      desde, hasta, tipo, "sistema"))
                conn.commit()

            return True, "Consolidación generada exitosamente", consolidacion

        except Exception as e:
            logger.error(f"Error en consolidación: {e}")
            return False, str(e), None

    def _obtener_config_empresa(self, empresa_id: str) -> Optional[Dict]:
        """Obtiene configuración de una empresa"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM empresa_config WHERE empresa_id = ?', (empresa_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def configurar_db_empresa(self, empresa_id: str, db_path: str) -> Tuple[bool, str]:
        """Configura la ruta de DB para una empresa"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Actualizar o insertar configuración
                cursor.execute('''
                    INSERT OR REPLACE INTO empresa_config
                    (empresa_id, db_path)
                    VALUES (?, ?)
                ''', (empresa_id, db_path))

                conn.commit()
                return True, "DB configurada exitosamente"

        except Exception as e:
            logger.error(f"Error configurando DB: {e}")
            return False, str(e)
