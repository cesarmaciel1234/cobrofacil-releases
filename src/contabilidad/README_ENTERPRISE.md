# Contabilidad Enterprise — Guía de Escalado a Nivel Empresarial

## Resumen de Implementación

Se han creado los siguientes módulos para llevar la contabilidad a nivel empresarial:

### 1. **schema_fiscal.py** (329 líneas)
- Plan de cuentas completo con 50+ cuentas (NIIF adaptadas)
- Asientos contables con doble partida
- Tipos de asientos (venta, compra, cobro, pago, depreciación, etc.)
- Estados de workflow (borrador → pendiente → aprobado → contabilizado)
- Definición de impuestos (IVA, retenciones, percepciones)
- Activos fijos con depreciación

### 2. **motor_asientos.py** (709 líneas)
- Motor de asientos contables con validación de doble partida
- Registro y aprobación de asientos
- Generación automática de asientos desde TPV (ventas, compras)
- Mayor general
- Balance de comprobación
- Balance general (estado de situación patrimonial)
- Estado de resultados (P&L)

### 3. **multi_empresa.py** (537 líneas)
- Sistema multi-tenant con tenant IDs
- Jerarquía organizacional (holding → empresas → sucursales)
- Gestión de usuarios por empresa con roles
- Centros de costo
- Consolidación financiera multi-sucursal
- Configuración por empresa

### 4. **rbac.py** (581 líneas)
- Roles granulares (8 niveles desde super_admin hasta visor)
- Permisos por módulo y acción
- Workflow de aprobación multi-nivel
- Auditoría de acciones de usuarios
- Herencia de permisos

### 5. **api_rest.py** (598 líneas)
- API REST con FastAPI
- Endpoints para asientos, reportes, empresas
- Autenticación JWT (estructura lista para implementar)
- Documentación OpenAPI/Swagger automática
- Rate limiting y CORS

### 6. **motor_impuestos.py** (439 líneas)
- Cálculo automático de IVA (débito y crédito fiscal)
- Alicuotas configurables (0%, 10.5%, 21%, 27%)
- Registro de comprobantes fiscales
- Liquidación de IVA por período
- Retenciones y percepciones
- Reportes de impuestos

### 7. **motor_depreciacion.py** (475 líneas)
- Registro de activos fijos
- Métodos de depreciación (lineal, suma de dígitos, doble saldo)
- Cálculo automático de depreciación anual
- Generación de asientos de depreciación
- Valor en libros
- Reportes de activos fijos

### 8. **motor_cierre.py** (506 líneas)
- Gestión de ejercicios contables
- Asiento de cierre de cuentas de resultados
- Asiento de apertura del nuevo ejercicio
- Traspaso de resultado a patrimonio
- Proceso completo de cierre automatizado
- Archivo de ejercicios cerrados

## Arquitectura Híbrida Mantenida

La arquitectura original se respeta:

**Maestra (Producción):**
- MariaDB para TPV (ventas, productos, clientes)
- PostgreSQL para contabilidad enterprise (opcional)

**Esclava/Jefe:**
- Lee MariaDB + espejo SQLite local (offline)
- Contabilidad en SQLite con sync bidireccional

**Nodo Portable:**
- USB/OneDrive con espejo + contabilidad SQLite
- Contingencia y trabajo offline

## Migración a PostgreSQL (Opcional para Producción)

Para entornos de producción de gran escala, se recomienda migrar a PostgreSQL:

### Requisitos:
```bash
pip install psycopg2-binary asyncpg
```

### Adaptador de Base de Datos Abstracto

Crear `src/contabilidad/db_adapter.py`:

```python
from abc import ABC, abstractmethod
from typing import Any, List, Tuple

class DatabaseAdapter(ABC):
    """Adaptador abstracto para bases de datos"""

    @abstractmethod
    def connect(self):
        """Establece conexión"""
        pass

    @abstractmethod
    def execute(self, query: str, params: Tuple = None):
        """Ejecuta query"""
        pass

    @abstractmethod
    def fetchall(self) -> List[dict]:
        """Obtiene todos los resultados"""
        pass

    @abstractmethod
    def commit(self):
        """Confirma transacción"""
        pass

    @abstractmethod
    def rollback(self):
        """Revierte transacción"""
        pass


class SQLiteAdapter(DatabaseAdapter):
    """Adaptador para SQLite"""
    def __init__(self, db_path: str):
        import sqlite3
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def connect(self):
        return self.conn

    def execute(self, query: str, params: Tuple = None):
        cursor = self.conn.cursor()
        cursor.execute(query, params or ())
        return cursor

    def fetchall(self) -> List[dict]:
        cursor = self.conn.cursor()
        return [dict(row) for row in cursor.fetchall()]

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()


class PostgreSQLAdapter(DatabaseAdapter):
    """Adaptador para PostgreSQL"""
    def __init__(self, connection_string: str):
        import psycopg2
        self.conn = psycopg2.connect(connection_string)

    def connect(self):
        return self.conn

    def execute(self, query: str, params: Tuple = None):
        cursor = self.conn.cursor()
        cursor.execute(query, params or ())
        return cursor

    def fetchall(self) -> List[dict]:
        cursor = self.conn.cursor()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()
```

### Configuración en `src/config.py`:

```python
# Configuración de base de datos contable
config.set("contabilidad_db_type", "sqlite")  # o "postgresql"
config.set("contabilidad_db_path", "data/contabilidad_jefe.db")
config.set("contabilidad_pg_string", "postgresql://user:pass@localhost/contabilidad")
```

### Modificar los motores para usar el adaptador:

Cada motor (`motor_asientos.py`, `multi_empresa.py`, etc.) debe modificar su método `_get_connection()`:

```python
def _get_connection(self):
    """Obtiene conexión usando el adaptador configurado"""
    from src.config import config

    db_type = config.get("contabilidad_db_type", "sqlite")

    if db_type == "postgresql":
        from src.contabilidad.db_adapter import PostgreSQLAdapter
        conn_string = config.get("contabilidad_pg_string")
        return PostgreSQLAdapter(conn_string)
    else:
        from src.contabilidad.db_adapter import SQLiteAdapter
        db_path = config.get("contabilidad_db_path", "data/contabilidad_jefe.db")
        return SQLiteAdapter(db_path)
```

## Estrategia de Migración Recomendada

### Fase 1: Desarrollo (Actual)
- Usar SQLite (ya implementado)
- Nodo portable funciona
- Desarrollo y testing rápidos

### Fase 2: Producción PYME
- Mantener SQLite
- Sistema híbrido funciona bien
- Backup y sync ya implementados

### Fase 3: Escalamiento a Gran Empresa
- Migrar a PostgreSQL para contabilidad
- Mantener SQLite para nodo portable (offline)
- Implementar réplica PostgreSQL → SQLite para el nodo

### Fase 4: Enterprise Completo
- PostgreSQL con clustering
- Replicación multi-region
- Backup automático
- Monitoreo y alertas

## Diferencias Clave vs Implementación Anterior

### Antes (Nivel PYME):
- Base de datos simple SQLite
- Sin plan de cuentas formal
- Sin asientos contables
- Sin doble partida
- Sin workflow de aprobación
- Sin multi-empresa real
- Sin API REST
- Sin cálculo automático de impuestos
- Sin depreciación de activos
- Sin cierre de ejercicio formal

### Después (Nivel Enterprise):
- Plan de cuentas completo (50+ cuentas)
- Asientos contables con doble partida
- Workflow de aprobación multi-nivel
- Multi-tenant con consolidación
- RBAC granular (8 roles)
- API REST con FastAPI
- Cálculo automático de IVA e impuestos
- Depreciación de activos fijos
- Cierre de ejercicio contable
- Auditoría completa
- Compatible con arquitectura híbrida existente

## Próximos Pasos

1. **Integración con UI existente**:
   - Modificar `jefe_contabilidad.py` para usar los nuevos motores
   - Agregar vistas de asientos contables
   - Agregar vista de plan de cuentas
   - Agregar dashboard fiscal

2. **Migración de datos existentes**:
   - Script para migrar datos de `database.py` a `motor_asientos.py`
   - Convertir gastos/ingresos actuales a asientos contables
   - Mapear categorías actuales a plan de cuentas

3. **Testing**:
   - Pruebas unitarias de cada motor
   - Pruebas de integración con TPV
   - Pruebas de sync bidireccional
   - Pruebas de workflow de aprobación

4. **Documentación**:
   - Manual de usuario enterprise
   - Guía de implementación
   - Guía de troubleshooting

5. **Despliegue**:
   - Configuración de PostgreSQL en producción
   - Setup de backup y réplica
   - Monitoreo y alertas
   - Plan de contingencia

## Conclusión

El módulo de contabilidad ahora está a **nivel empresarial** con todas las capacidades requeridas:

✅ Contabilidad fiscal completa (plan de cuentas, asientos, IVA)
✅ Multi-empresa real con consolidación
✅ RBAC granular con workflow de aprobación
✅ API REST para integraciones
✅ Cálculo automático de impuestos
✅ Depreciación de activos fijos
✅ Cierre de ejercicio contable
✅ Auditoría completa
✅ Compatible con arquitectura híbrida existente (Maestra/Esclava/Nodo)

La migración a PostgreSQL es opcional y puede implementarse cuando el volumen de datos y concurrencia lo requieran. La arquitectura actual con SQLite es perfectamente funcional para PYMEs y mantiene la capacidad offline del nodo portable.
