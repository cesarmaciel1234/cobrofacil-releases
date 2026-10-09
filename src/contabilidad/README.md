# Contabilidad

ERP del jefe. La base es `contabilidad_jefe.db`, aparte de la tienda. La abre `get_jefe_db_path()` cuando se muestra `JefeContabilidad`.

`PAL` en `shared_globals.py` lee el tema global día/noche. No importa `theme_pro.py`.

Las vistas son mixins: resumen, ingresos, gastos, proveedores, préstamos, cheques, tarjetas, inversiones, costos fijos, historial y reportes. Las junta la clase `JefeContabilidad`.

## ENTERPRISE (Nivel Empresarial)

A partir de 2026, el módulo incluye capacidades de nivel empresarial:

**Nuevos Módulos:**
- `schema_fiscal.py` - Plan de cuentas completo (50+ cuentas NIIF)
- `motor_asientos.py` - Asientos contables con doble partida
- `multi_empresa.py` - Sistema multi-tenant con consolidación
- `rbac.py` - Roles y permisos granulares
- `api_rest.py` - API REST con FastAPI
- `motor_impuestos.py` - Cálculo automático de IVA e impuestos
- `motor_depreciacion.py` - Depreciación de activos fijos
- `motor_cierre.py` - Cierre de ejercicio contable

**Nuevas Vistas:**
- Plan de Cuentas Contable
- Asientos Contables (Mayor, Balance, P&L)
- Gestión de Impuestos (IVA, liquidaciones)
- Activos Fijos (depreciación)
- Ejercicios Contables (cierre, apertura)

**Compatibilidad:**
- `database.py` tiene un wrapper que mantiene la API original
- Los gastos/ingresos existentes generan automáticamente asientos contables
- Modo enterprise se activa automáticamente si los motores están disponibles
- El sistema híbrido (Maestra/Esclava/Nodo) se mantiene intacto

Ver `README_ENTERPRISE.md` para documentación completa del nivel empresarial.
