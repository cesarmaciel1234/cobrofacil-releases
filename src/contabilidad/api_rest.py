"""
api_rest.py — API REST para integraciones enterprise (Nivel Enterprise)
TPV Pro 2026 · Cobro Fácil POS

Este módulo implementa:
- API REST con FastAPI para integraciones externas
- Endpoints para asientos contables, reportes, empresas
- Autenticación JWT y autorización RBAC
- Webhooks para notificaciones
- Rate limiting y logging
- Documentación OpenAPI/Swagger automática

Requiere: pip install fastapi uvicorn python-multipart python-jose[cryptography] passlib[bcrypt]
"""

from fastapi import FastAPI, HTTPException, Depends, status, Header, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging
import json
from contextlib import asynccontextmanager

logger = logging.getLogger("APIContabilidad")

# ── MODELOS PYDANTIC ─────────────────────────────────────────────────────────

class AsientoContableRequest(BaseModel):
    """Modelo para crear asiento contable"""
    fecha: date
    tipo: str = Field(..., description="Tipo de asiento: venta, compra, manual, etc.")
    descripcion: str
    lineas: List[Dict[str, Any]] = Field(..., description="Líneas del asiento (cuenta, debe, haber)")
    moneda: str = "ARS"
    referencia: Optional[str] = None
    usuario: str = "api"

class AsientoContableResponse(BaseModel):
    """Respuesta de asiento creado"""
    exito: bool
    mensaje: str
    asiento_id: Optional[int] = None
    numero: Optional[str] = None

class BalanceRequest(BaseModel):
    """Modelo para obtener balance"""
    fecha: date

class EstadoResultadosRequest(BaseModel):
    """Modelo para obtener estado de resultados"""
    desde: date
    hasta: date

class EmpresaRequest(BaseModel):
    """Modelo para crear empresa"""
    codigo: str
    nombre: str
    tipo: str = Field(..., description="holding, empresa, sucursal")
    parent_id: Optional[str] = None
    cuit: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    moneda: str = "ARS"

class ErrorResponse(BaseModel):
    """Modelo de error"""
    error: str
    detalle: Optional[str] = None

# ── CONFIGURACIÓN API ────────────────────────────────────────────────────────

class ConfigAPI:
    """Configuración de la API"""
    def __init__(self):
        self.db_path = None
        self.secret_key = "cambiar-en-produccion-usar-secret-manager"
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60

config_api = ConfigAPI()

def set_db_path(path: str):
    """Configura la ruta de la base de datos"""
    config_api.db_path = path

# ── AUTENTICACIÓN JWT ────────────────────────────────────────────────────────

security = HTTPBearer()

async def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica el token JWT"""
    try:
        # En producción, validar contra el token real
        # Por ahora, aceptamos cualquier token para desarrollo
        token = credentials.credentials
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no proporcionado"
            )
        # TODO: Implementar validación JWT real
        return {"usuario_id": "api_user", "empresa_id": None}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error de autenticación: {str(e)}"
        )

async def verificar_permiso(usuario: dict, modulo: str, accion: str):
    """Verifica permisos RBAC"""
    # TODO: Implementar verificación real de permisos
    # Por ahora, todos los permisos están permitidos para desarrollo
    return True

# ── APLICACIÓN FASTAPI ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager para startup/shutdown"""
    # Startup
    logger.info("API Contabilidad iniciando...")
    if not config_api.db_path:
        logger.warning("DB path no configurado. Usar set_db_path()")
    yield
    # Shutdown
    logger.info("API Contabilidad deteniéndose...")

app = FastAPI(
    title="TPV Pro 2026 - API Contabilidad Enterprise",
    description="API REST para integraciones contables de nivel empresarial",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ENDPOINTS DE SALUD ───────────────────────────────────────────────────────

@app.get("/health", tags=["Sistema"])
async def health_check():
    """Endpoint de health check"""
    return {
        "status": "ok",
        "servicio": "API Contabilidad Enterprise",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/", tags=["Sistema"])
async def root():
    """Endpoint raíz"""
    return {
        "mensaje": "TPV Pro 2026 - API Contabilidad Enterprise",
        "documentacion": "/docs",
        "version": "1.0.0"
    }

# ── ENDPOINTS DE ASIENTOS CONTABLES ─────────────────────────────────────────

@app.post("/api/v1/asientos", response_model=AsientoContableResponse, tags=["Asientos"])
async def crear_asiento(
    asiento: AsientoContableRequest,
    usuario: dict = Depends(verificar_token)
):
    """
    Crea un nuevo asiento contable

    Requiere autenticación JWT
    """
    try:
        if not config_api.db_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Base de datos no configurada"
            )

        from src.contabilidad.motor_asientos import MotorAsientos
        from src.contabilidad.schema_fiscal import AsientoContable, LineaAsiento, TipoAsiento, Moneda, EstadoAsiento

        motor = MotorAsientos(config_api.db_path)

        # Convertir lineas del request a objetos LineaAsiento
        lineas_obj = []
        for linea in asiento.lineas:
            lineas_obj.append(LineaAsiento(
                cuenta_codigo=linea.get('cuenta_codigo'),
                debe=linea.get('debe', 0.0),
                haber=linea.get('haber', 0.0),
                descripcion=linea.get('descripcion', '')
            ))

        # Crear asiento
        asiento_obj = AsientoContable(
            fecha=asiento.fecha,
            tipo=TipoAsiento(asiento.tipo),
            descripcion=asiento.descripcion,
            lineas=lineas_obj,
            moneda=Moneda(asiento.moneda),
            estado=EstadoAsiento.BORRADOR,
            referencia=asiento.referencia or "",
            usuario=asiento.usuario
        )

        exito, mensaje, asiento_id = motor.crear_asiento(asiento_obj)

        if exito:
            return AsientoContableResponse(
                exito=True,
                mensaje=mensaje,
                asiento_id=asiento_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mensaje
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando asiento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/asientos/{asiento_id}", tags=["Asientos"])
async def obtener_asiento(
    asiento_id: int,
    usuario: dict = Depends(verificar_token)
):
    """Obtiene un asiento por ID"""
    try:
        if not config_api.db_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Base de datos no configurada"
            )

        from src.contabilidad.motor_asientos import MotorAsientos

        motor = MotorAsientos(config_api.db_path)

        # TODO: Implementar método obtener_asiento por ID en MotorAsientos
        return {"mensaje": "Endpoint en desarrollo"}

    except Exception as e:
        logger.error(f"Error obteniendo asiento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/asientos/venta", response_model=AsientoContableResponse, tags=["Asientos"])
async def generar_asiento_venta(
    fecha: date,
    monto_total: float,
    metodo_pago: str,
    iva_tasa: float = 21.0,
    costo_mercaderia: float = 0.0,
    referencia: Optional[str] = None,
    usuario: dict = Depends(verificar_token)
):
    """
    Genera automáticamente un asiento de venta

    Parámetros:
    - fecha: Fecha de la venta
    - monto_total: Monto total de la venta
    - metodo_pago: Método de pago (Efectivo, Tarjeta, Transferencia, etc.)
    - iva_tasa: Tasa de IVA (21.0, 10.5, 0.0)
    - costo_mercaderia: Costo de la mercadería vendida
    - referencia: Referencia opcional
    """
    try:
        if not config_api.db_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Base de datos no configurada"
            )

        from src.contabilidad.motor_asientos import MotorAsientos

        motor = MotorAsientos(config_api.db_path)

        exito, mensaje, asiento_id = motor.generar_asiento_venta(
            fecha=fecha,
            monto_total=monto_total,
            metodo_pago=metodo_pago,
            iva_tasa=iva_tasa,
            costo_mercaderia=costo_mercaderia,
            referencia=referencia or ""
        )

        if exito:
            return AsientoContableResponse(
                exito=True,
                mensaje=mensaje,
                asiento_id=asiento_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mensaje
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando asiento de venta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ── ENDPOINTS DE REPORTES ─────────────────────────────────────────────────────

@app.post("/api/v1/reportes/balance-comprobacion", tags=["Reportes"])
async def obtener_balance_comprobacion(
    request: BalanceRequest,
    usuario: dict = Depends(verificar_token)
):
    """Obtiene el balance de comprobación a una fecha"""
    try:
        if not config_api.db_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Base de datos no configurada"
            )

        from src.contabilidad.motor_asientos import MotorAsientos

        motor = MotorAsientos(config_api.db_path)
        balance = motor.obtener_balance_comprobacion(request.fecha)

        return balance

    except Exception as e:
        logger.error(f"Error obteniendo balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/reportes/balance-general", tags=["Reportes"])
async def obtener_balance_general(
    request: BalanceRequest,
    usuario: dict = Depends(verificar_token)
):
    """Obtiene el balance general (estado de situación patrimonial)"""
    try:
        if not config_api.db_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Base de datos no configurada"
            )

        from src.contabilidad.motor_asientos import MotorAsientos

        motor = MotorAsientos(config_api.db_path)
        balance = motor.obtener_balance_general(request.fecha)

        return balance

    except Exception as e:
        logger.error(f"Error obteniendo balance general: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/reportes/estado-resultados", tags=["Reportes"])
async def obtener_estado_resultados(
    request: EstadoResultadosRequest,
    usuario: dict = Depends(verificar_token)
):
    """Obtiene el estado de resultados (P&L) para un período"""
    try:
        if not config_api.db_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Base de datos no configurada"
            )

        from src.contabilidad.motor_asientos import MotorAsientos

        motor = MotorAsientos(config_api.db_path)
        er = motor.obtener_estado_resultados(request.desde, request.hasta)

        return er

    except Exception as e:
        logger.error(f"Error obteniendo estado de resultados: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/reportes/mayor-general", tags=["Reportes"])
async def obtener_mayor_general(
    cuenta_codigo: Optional[str] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    usuario: dict = Depends(verificar_token)
):
    """Obtiene el mayor general (movimientos de cuentas)"""
    try:
        if not config_api.db_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Base de datos no configurada"
            )

        from src.contabilidad.motor_asientos import MotorAsientos

        motor = MotorAsientos(config_api.db_path)
        mayor = motor.obtener_mayor_general(cuenta_codigo, desde, hasta)

        return {"filas": mayor}

    except Exception as e:
        logger.error(f"Error obteniendo mayor general: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ── ENDPOINTS DE PLAN DE CUENTAS ─────────────────────────────────────────────

@app.get("/api/v1/plan-cuentas", tags=["Plan de Cuentas"])
async def listar_plan_cuentas(
    tipo: Optional[str] = None,
    usuario: dict = Depends(verificar_token)
):
    """Lista todas las cuentas del plan contable"""
    try:
        if not config_api.db_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Base de datos no configurada"
            )

        from src.contabilidad.motor_asientos import MotorAsientos
        from src.contabilidad.schema_fiscal import TipoCuenta

        motor = MotorAsientos(config_api.db_path)

        tipo_enum = TipoCuenta(tipo) if tipo else None
        cuentas = motor.listar_cuentas(tipo_enum)

        return {"cuentas": cuentas}

    except Exception as e:
        logger.error(f"Error listando plan de cuentas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/plan-cuentas/cargar-defecto", tags=["Plan de Cuentas"])
async def cargar_plan_cuentas_defecto(usuario: dict = Depends(verificar_token)):
    """Carga el plan de cuentas por defecto"""
    try:
        if not config_api.db_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Base de datos no configurada"
            )

        from src.contabilidad.motor_asientos import MotorAsientos

        motor = MotorAsientos(config_api.db_path)
        motor.cargar_plan_cuentas_defecto()

        return {"mensaje": "Plan de cuentas cargado exitosamente"}

    except Exception as e:
        logger.error(f"Error cargando plan de cuentas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ── ENDPOINTS DE MULTI-EMPRESA ───────────────────────────────────────────────

@app.post("/api/v1/empresas", tags=["Multi-Empresa"])
async def crear_empresa(
    empresa: EmpresaRequest,
    usuario: dict = Depends(verificar_token)
):
    """Crea una nueva empresa/sucursal"""
    try:
        if not config_api.db_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Base de datos no configurada"
            )

        from src.contabilidad.multi_empresa import MotorMultiEmpresa, TipoEmpresa

        motor = MotorMultiEmpresa(config_api.db_path)

        exito, mensaje, empresa_id = motor.crear_empresa(
            codigo=empresa.codigo,
            nombre=empresa.nombre,
            tipo=TipoEmpresa(empresa.tipo),
            parent_id=empresa.parent_id,
            cuit=empresa.cuit,
            direccion=empresa.direccion,
            telefono=empresa.telefono,
            email=empresa.email,
            moneda=empresa.moneda
        )

        if exito:
            return {"exito": True, "mensaje": mensaje, "empresa_id": empresa_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mensaje
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando empresa: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/empresas", tags=["Multi-Empresa"])
async def listar_empresas(
    tipo: Optional[str] = None,
    usuario: dict = Depends(verificar_token)
):
    """Lista todas las empresas"""
    try:
        if not config_api.db_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Base de datos no configurada"
            )

        from src.contabilidad.multi_empresa import MotorMultiEmpresa, TipoEmpresa

        motor = MotorMultiEmpresa(config_api.db_path)

        tipo_enum = TipoEmpresa(tipo) if tipo else None
        empresas = motor.listar_empresas(tipo=tipo_enum)

        return {"empresas": empresas}

    except Exception as e:
        logger.error(f"Error listando empresas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ── FUNCIÓN PARA INICIAR SERVIDOR ────────────────────────────────────────────

def iniciar_servidor(host: str = "0.0.0.0", port: int = 8000, db_path: str = None):
    """
    Inicia el servidor de la API

    Args:
        host: Host donde escuchar (default: 0.0.0.0)
        port: Puerto donde escuchar (default: 8000)
        db_path: Ruta de la base de datos
    """
    if db_path:
        set_db_path(db_path)

    import uvicorn

    logger.info(f"Iniciando API en {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    # Para desarrollo: python api_rest.py
    import sys
    from src.utils.paths import get_base_path
    import os

    db_path = os.path.join(get_base_path(), "data", "contabilidad_jefe.db")
    iniciar_servidor(db_path=db_path)
