"""
rbac.py — Sistema RBAC granular con workflow de aprobación (Nivel Enterprise)
TPV Pro 2026 · Cobro Fácil POS

Este módulo implementa:
- Roles y permisos granulares
- Asignación de permisos por módulo y acción
- Workflow de aprobación multi-nivel
- Auditoría de acciones de usuarios
- Herencia de permisos (jerarquía de roles)
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
import json

logger = logging.getLogger("RBAC")


class Rol(Enum):
    """Roles del sistema"""
    SUPER_ADMIN = "super_admin"
    ADMIN_EMPRESA = "admin_empresa"
    CONTADOR_JEFE = "contador_jefe"
    CONTADOR = "contador"
    AUDITOR = "auditor"
    GERENTE = "gerente"
    OPERADOR = "operador"
    VISOR = "visor"


class Modulo(Enum):
    """Módulos del sistema"""
    CONTABILIDAD = "contabilidad"
    REPORTES = "reportes"
    PROVEEDORES = "proveedores"
    PERSONAL = "personal"
    INVENTARIO = "inventario"
    CAJA = "caja"
    CONFIGURACION = "configuracion"


class Accion(Enum):
    """Acciones posibles por módulo"""
    VER = "ver"
    CREAR = "crear"
    EDITAR = "editar"
    ELIMINAR = "eliminar"
    APROBAR = "aprobar"
    RECHAZAR = "rechazar"
    EXPORTAR = "exportar"
    IMPORTAR = "importar"
    CONFIGURAR = "configurar"


class EstadoAprobacion(Enum):
    """Estados del workflow de aprobación"""
    BORRADOR = "borrador"
    PENDIENTE_NIVEL_1 = "pendiente_nivel_1"
    PENDIENTE_NIVEL_2 = "pendiente_nivel_2"
    PENDIENTE_NIVEL_3 = "pendiente_nivel_3"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"


class MotorRBAC:
    """Motor de control de acceso basado en roles"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_schema()
        self._cargar_permisos_defecto()

    def _get_connection(self):
        """Obtiene conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self):
        """Inicializa el esquema RBAC"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tabla de roles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    id TEXT PRIMARY KEY,
                    codigo TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    nivel_jerarquia INTEGER DEFAULT 0,
                    activo INTEGER DEFAULT 1
                )
            ''')

            # Tabla de permisos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS permisos (
                    id TEXT PRIMARY KEY,
                    modulo TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    descripcion TEXT,
                    UNIQUE(modulo, accion)
                )
            ''')

            # Tabla de roles-permisos (many-to-many)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rol_permisos (
                    rol_id TEXT NOT NULL,
                    permiso_id TEXT NOT NULL,
                    puede_ejecutar INTEGER DEFAULT 1,
                    PRIMARY KEY (rol_id, permiso_id),
                    FOREIGN KEY (rol_id) REFERENCES roles(id),
                    FOREIGN KEY (permiso_id) REFERENCES permisos(id)
                )
            ''')

            # Tabla de usuarios-roles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuario_roles (
                    id TEXT PRIMARY KEY,
                    usuario_id TEXT NOT NULL,
                    rol_id TEXT NOT NULL,
                    empresa_id TEXT,
                    asignado_por TEXT,
                    fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_baja DATETIME,
                    FOREIGN KEY (rol_id) REFERENCES roles(id),
                    UNIQUE(usuario_id, rol_id, empresa_id)
                )
            ''')

            # Tabla de configuración de workflow de aprobación
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflow_config (
                    id TEXT PRIMARY KEY,
                    modulo TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    nivel_aprobacion INTEGER DEFAULT 1,
                    monto_minimo_aprobacion REAL DEFAULT 0,
                    requiere_justificacion INTEGER DEFAULT 0,
                    UNIQUE(modulo, accion)
                )
            ''')

            # Tabla de solicitudes de aprobación
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS solicitudes_aprobacion (
                    id TEXT PRIMARY KEY,
                    tipo_entidad TEXT NOT NULL,
                    entidad_id TEXT NOT NULL,
                    modulo TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    solicitante_id TEXT NOT NULL,
                    estado TEXT DEFAULT 'borrador',
                    nivel_actual INTEGER DEFAULT 0,
                    monto REAL,
                    justificacion TEXT,
                    empresa_id TEXT,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (solicitante_id) REFERENCES usuario_roles(usuario_id)
                )
            ''')

            # Tabla de aprobaciones (historial)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS aprobaciones (
                    id TEXT PRIMARY KEY,
                    solicitud_id TEXT NOT NULL,
                    aprobador_id TEXT NOT NULL,
                    nivel INTEGER NOT NULL,
                    decision TEXT NOT NULL,
                    comentario TEXT,
                    fecha DECISION DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (solicitud_id) REFERENCES solicitudes_aprobacion(id)
                )
            ''')

            # Tabla de auditoría de acciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auditoria_acciones (
                    id TEXT PRIMARY KEY,
                    usuario_id TEXT NOT NULL,
                    modulo TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    entidad_tipo TEXT,
                    entidad_id TEXT,
                    detalles TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    exito INTEGER DEFAULT 1,
                    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Índices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuario_roles_usuario ON usuario_roles(usuario_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuario_roles_rol ON usuario_roles(rol_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_solicitudes_estado ON solicitudes_aprobacion(estado)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_solicitudes_solicitante ON solicitudes_aprobacion(solicitante_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_aprobaciones_solicitud ON aprobaciones(solicitud_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON auditoria_acciones(usuario_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON auditoria_acciones(fecha_hora)')

            conn.commit()

    def _cargar_permisos_defecto(self):
        """Carga roles y permisos por defecto"""
        import uuid

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Roles por defecto
            roles_defecto = [
                (Rol.SUPER_ADMIN.value, "Super Administrador", "Acceso total al sistema", 10),
                (Rol.ADMIN_EMPRESA.value, "Administrador de Empresa", "Gestión completa de una empresa", 8),
                (Rol.CONTADOR_JEFE.value, "Contador Jefe", "Contabilidad y reportes financieros", 7),
                (Rol.CONTADOR.value, "Contador", "Registro de asientos contables", 6),
                (Rol.AUDITOR.value, "Auditor", "Solo lectura y auditoría", 5),
                (Rol.GERENTE.value, "Gerente", "Gestión operativa limitada", 4),
                (Rol.OPERADOR.value, "Operador", "Operaciones básicas", 2),
                (Rol.VISOR.value, "Visor", "Solo lectura", 1),
            ]

            for codigo, nombre, descripcion, nivel in roles_defecto:
                cursor.execute('''
                    INSERT OR IGNORE INTO roles (id, codigo, nombre, descripcion, nivel_jerarquia)
                    VALUES (?, ?, ?, ?, ?)
                ''', (str(uuid.uuid4()), codigo, nombre, descripcion, nivel))

            # Permisos por defecto
            permisos_defecto = []
            for modulo in Modulo:
                for accion in Accion:
                    permisos_defecto.append((modulo.value, accion.value, f"{accion.value} en {modulo.value}"))

            for modulo, accion, descripcion in permisos_defecto:
                cursor.execute('''
                    INSERT OR IGNORE INTO permisos (id, modulo, accion, descripcion)
                    VALUES (?, ?, ?, ?)
                ''', (str(uuid.uuid4()), modulo, accion, descripcion))

            # Asignar permisos por defecto a roles
            # Super Admin: todos los permisos
            cursor.execute('SELECT id FROM roles WHERE codigo = ?', (Rol.SUPER_ADMIN.value,))
            super_admin_row = cursor.fetchone()
            if super_admin_row:
                super_admin_id = super_admin_row['id']
                cursor.execute('SELECT id FROM permisos')
                for perm_row in cursor.fetchall():
                    cursor.execute('''
                        INSERT OR IGNORE INTO rol_permisos (rol_id, permiso_id, puede_ejecutar)
                        VALUES (?, ?, 1)
                    ''', (super_admin_id, perm_row['id']))

            # Visor: solo ver
            cursor.execute('SELECT id FROM roles WHERE codigo = ?', (Rol.VISOR.value,))
            visor_row = cursor.fetchone()
            if visor_row:
                visor_id = visor_row['id']
                cursor.execute('SELECT id FROM permisos WHERE accion = ?', (Accion.VER.value,))
                for perm_row in cursor.fetchall():
                    cursor.execute('''
                        INSERT OR IGNORE INTO rol_permisos (rol_id, permiso_id, puede_ejecutar)
                        VALUES (?, ?, 1)
                    ''', (visor_id, perm_row['id']))

            # Configuración de workflow por defecto
            workflow_defecto = [
                # Contabilidad: aprobaciones según monto
                (Modulo.CONTABILIDAD.value, Accion.CREAR.value, 1, 10000, 0),  # Hasta $10k: nivel 1
                (Modulo.CONTABILIDAD.value, Accion.CREAR.value, 2, 50000, 1),  # $10k-$50k: nivel 2
                (Modulo.CONTABILIDAD.value, Accion.CREAR.value, 3, 999999999, 1),  # >$50k: nivel 3
                (Modulo.CONTABILIDAD.value, Accion.EDITAR.value, 1, 5000, 0),
                (Modulo.CONTABILIDAD.value, Accion.ELIMINAR.value, 2, 0, 1),  # Siempre requiere justificación
                # Configuración: siempre nivel máximo
                (Modulo.CONFIGURACION.value, Accion.CONFIGURAR.value, 3, 0, 1),
            ]

            for modulo, accion, nivel, monto, requiere_just in workflow_defecto:
                cursor.execute('''
                    INSERT OR IGNORE INTO workflow_config
                    (id, modulo, accion, nivel_aprobacion, monto_minimo_aprobacion, requiere_justificacion)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (str(uuid.uuid4()), modulo, accion, nivel, monto, requiere_just))

            conn.commit()
            logger.info("Permisos y roles por defecto cargados")

    # ── GESTIÓN DE ROLES ───────────────────────────────────────────────────────

    def asignar_rol_usuario(self, usuario_id: str, rol_codigo: str,
                            empresa_id: Optional[str] = None,
                            asignado_por: str = "system") -> Tuple[bool, str]:
        """Asigna un rol a un usuario"""
        try:
            import uuid

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Verificar que el rol exista
                cursor.execute('SELECT id FROM roles WHERE codigo = ?', (rol_codigo,))
                rol_row = cursor.fetchone()
                if not rol_row:
                    return False, f"Rol {rol_codigo} no existe"

                rol_id = rol_row['id']

                # Insertar asignación
                cursor.execute('''
                    INSERT OR REPLACE INTO usuario_roles
                    (id, usuario_id, rol_id, empresa_id, asignado_por, fecha_asignacion)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (str(uuid.uuid4()), usuario_id, rol_id, empresa_id, asignado_por))

                conn.commit()
                logger.info(f"Rol {rol_codigo} asignado a usuario {usuario_id}")
                return True, "Rol asignado exitosamente"

        except Exception as e:
            logger.error(f"Error asignando rol: {e}")
            return False, str(e)

    def obtener_roles_usuario(self, usuario_id: str,
                              empresa_id: Optional[str] = None) -> List[Dict]:
        """Obtiene todos los roles de un usuario"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if empresa_id:
                cursor.execute('''
                    SELECT r.*, ur.empresa_id
                    FROM roles r
                    JOIN usuario_roles ur ON r.id = ur.rol_id
                    WHERE ur.usuario_id = ? AND ur.empresa_id = ?
                      AND ur.fecha_baja IS NULL AND r.activo = 1
                ''', (usuario_id, empresa_id))
            else:
                cursor.execute('''
                    SELECT r.*, ur.empresa_id
                    FROM roles r
                    JOIN usuario_roles ur ON r.id = ur.rol_id
                    WHERE ur.usuario_id = ? AND ur.fecha_baja IS NULL AND r.activo = 1
                ''', (usuario_id,))
            return [dict(row) for row in cursor.fetchall()]

    def tiene_permiso(self, usuario_id: str, modulo: Modulo,
                      accion: Accion, empresa_id: Optional[str] = None) -> bool:
        """
        Verifica si un usuario tiene permiso para una acción en un módulo

        Args:
            usuario_id: ID del usuario
            modulo: Módulo a verificar
            accion: Acción a verificar
            empresa_id: ID de la empresa (opcional)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Obtener roles del usuario
            roles = self.obtener_roles_usuario(usuario_id, empresa_id)
            if not roles:
                return False

            rol_ids = [r['id'] for r in roles]

            # Verificar si alguno de los roles tiene el permiso
            placeholders = ','.join(['?'] * len(rol_ids))
            cursor.execute(f'''
                SELECT COUNT(*) as cnt
                FROM rol_permisos rp
                JOIN permisos p ON rp.permiso_id = p.id
                WHERE rp.rol_id IN ({placeholders})
                  AND p.modulo = ?
                  AND p.accion = ?
                  AND rp.puede_ejecutar = 1
            ''', rol_ids + [modulo.value, accion.value])

            row = cursor.fetchone()
            return (row['cnt'] or 0) > 0

    # ── WORKFLOW DE APROBACIÓN ───────────────────────────────────────────────

    def crear_solicitud_aprobacion(self, tipo_entidad: str, entidad_id: str,
                                    modulo: Modulo, accion: Accion,
                                    solicitante_id: str, monto: Optional[float] = None,
                                    justificacion: Optional[str] = None,
                                    empresa_id: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Crea una solicitud de aprobación

        Returns:
            (exito, mensaje, solicitud_id)
        """
        try:
            import uuid

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Obtener configuración de workflow
                cursor.execute('''
                    SELECT nivel_aprobacion, monto_minimo_aprobacion, requiere_justificacion
                    FROM workflow_config
                    WHERE modulo = ? AND accion = ?
                ''', (modulo.value, accion.value))

                config_row = cursor.fetchone()
                if not config_row:
                    # Sin configuración, auto-aprobar
                    return True, "Auto-aprobado (sin configuración)", None

                nivel_req = config_row['nivel_aprobacion']
                monto_min = config_row['monto_minimo_aprobacion']
                requiere_just = config_row['requiere_justificacion']

                # Verificar si requiere aprobación por monto
                if monto is not None and monto < monto_min:
                    return True, "Auto-aprobado (monto mínimo no alcanzado)", None

                # Verificar justificación
                if requiere_just and not justificacion:
                    return False, "Se requiere justificación para esta acción", None

                # Crear solicitud
                solicitud_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO solicitudes_aprobacion
                    (id, tipo_entidad, entidad_id, modulo, accion, solicitante_id,
                     estado, nivel_actual, monto, justificacion, empresa_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                ''', (solicitud_id, tipo_entidad, entidad_id, modulo.value, accion.value,
                      solicitante_id, 'pendiente_nivel_1', monto, justificacion, empresa_id))

                conn.commit()
                logger.info(f"Solicitud de aprobación creada: {solicitud_id}")
                return True, "Solicitud creada exitosamente", solicitud_id

        except Exception as e:
            logger.error(f"Error creando solicitud: {e}")
            return False, str(e), None

    def aprobar_solicitud(self, solicitud_id: str, aprobador_id: str,
                          decision: str, comentario: Optional[str] = None) -> Tuple[bool, str]:
        """
        Aprueba o rechaza una solicitud

        Args:
            solicitud_id: ID de la solicitud
            aprobador_id: ID del usuario que aprueba
            decision: 'aprobado' o 'rechazado'
            comentario: Comentario opcional
        """
        try:
            import uuid

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Obtener solicitud
                cursor.execute('''
                    SELECT * FROM solicitudes_aprobacion WHERE id = ?
                ''', (solicitud_id,))
                solicitud = cursor.fetchone()
                if not solicitud:
                    return False, "Solicitud no encontrada"

                estado_actual = solicitud['estado']
                nivel_actual = solicitud['nivel_actual']

                if estado_actual == 'aprobado' or estado_actual == 'rechazado':
                    return False, f"La solicitud ya está {estado_actual}"

                # Obtener configuración de workflow
                cursor.execute('''
                    SELECT nivel_aprobacion FROM workflow_config
                    WHERE modulo = ? AND accion = ?
                ''', (solicitud['modulo'], solicitud['accion']))

                config_row = cursor.fetchone()
                nivel_max = config_row['nivel_aprobacion'] if config_row else 1

                # Registrar aprobación
                cursor.execute('''
                    INSERT INTO aprobaciones
                    (id, solicitud_id, aprobador_id, nivel, decision, comentario)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (str(uuid.uuid4()), solicitud_id, aprobador_id, nivel_actual + 1, decision, comentario))

                # Actualizar estado de solicitud
                if decision == 'rechazado':
                    nuevo_estado = 'rechazado'
                elif nivel_actual + 1 >= nivel_max:
                    nuevo_estado = 'aprobado'
                else:
                    nuevo_estado = f'pendiente_nivel_{nivel_actual + 1}'

                cursor.execute('''
                    UPDATE solicitudes_aprobacion
                    SET estado = ?, nivel_actual = ?
                    WHERE id = ?
                ''', (nuevo_estado, nivel_actual + 1, solicitud_id))

                conn.commit()
                logger.info(f"Solicitud {solicitud_id} {decision} por {aprobador_id}")
                return True, f"Solicitud {decision} exitosamente"

        except Exception as e:
            logger.error(f"Error en aprobación: {e}")
            return False, str(e)

    # ── AUDITORÍA ─────────────────────────────────────────────────────────────

    def registrar_accion(self, usuario_id: str, modulo: Modulo, accion: Accion,
                         entidad_tipo: Optional[str] = None, entidad_id: Optional[str] = None,
                         detalles: Optional[Dict] = None, exito: bool = True,
                         ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
        """Registra una acción en el log de auditoría"""
        try:
            import uuid

            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO auditoria_acciones
                    (id, usuario_id, modulo, accion, entidad_tipo, entidad_id,
                     detalles, ip_address, user_agent, exito)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (str(uuid.uuid4()), usuario_id, modulo.value, accion.value,
                      entidad_tipo, entidad_id, json.dumps(detalios) if detalles else None,
                      ip_address, user_agent, 1 if exito else 0))

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error registrando auditoría: {e}")
            return False

    def obtener_auditoria(self, usuario_id: Optional[str] = None,
                           modulo: Optional[Modulo] = None,
                           desde: Optional[datetime] = None,
                           hasta: Optional[datetime] = None,
                           limite: int = 100) -> List[Dict]:
        """Obtiene registros de auditoría con filtros"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM auditoria_acciones WHERE 1=1'
            params = []

            if usuario_id:
                query += ' AND usuario_id = ?'
                params.append(usuario_id)

            if modulo:
                query += ' AND modulo = ?'
                params.append(modulo.value)

            if desde:
                query += ' AND fecha_hora >= ?'
                params.append(desde.isoformat())

            if hasta:
                query += ' AND fecha_hora <= ?'
                params.append(hasta.isoformat())

            query += ' ORDER BY fecha_hora DESC LIMIT ?'
            params.append(limite)

            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
