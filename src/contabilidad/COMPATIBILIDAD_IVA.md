# Compatibilidad IVA - Integración TPV ↔ Contabilidad Enterprise

## Sistema Existente (TPV)

**Ubicación:** `src/admin/configuracion/componentes/dialogo_impuestos.py`

**Función:**
- Configura tasa de IVA general (`config.tax_percentage`, default 21%)
- Configura tasas de IVA por departamento en tabla `departamentos` (MariaDB)
- Cada departamento puede tener su propia tasa de IVA

**Uso en TPV:**
- `src/hardware/printer.py` - `_calcular_iva_desagregado()` usa IVA de departamentos para tickets
- Cálculo de IVA desagregado por tasa en tickets fiscales
- El IVA se calcula por producto según su departamento

## Sistema Enterprise (Contabilidad)

**Ubicación:** `src/contabilidad/motor_impuestos.py`

**Función:**
- Gestión completa de impuestos (IVA, retenciones, percepciones)
- Registro de comprobantes fiscales (Factura A/B/C, notas crédito/débito)
- Liquidación de IVA por período
- Reportes de impuestos

**Alicuotas estándar:**
- 0% (Exento)
- 10.5%
- 21%
- 27%

## Integración Creada

**Archivo:** `src/contabilidad/integracion_iva.py`

**Clase:** `IntegradorIVA`

**Funciones:**

### 1. `sincronizar_alicuotas_desde_departamentos()`
- Lee tasas de IVA de `departamentos` (MariaDB)
- Sincroniza con alicuotas del motor de impuestos (SQLite)
- Detecta tasas no estándar y las mapea a la más cercana
- Se ejecuta automáticamente al guardar en diálogo de impuestos

### 2. `generar_comprobante_fiscal_venta()`
- Genera comprobante fiscal desde venta TPV
- Determina tipo de comprobante según CUIT del cliente:
  - Con CUIT → Factura A
  - Sin CUIT → Factura B
- Calcula IVA desagregado usando departamentos
- Registra en motor de impuestos

### 3. `obtener_resumen_iva_mes()`
- Obtiene resumen de IVA para un mes
- Si motor de impuestos disponible → usa liquidación completa
- Si no disponible → cálculo estimado desde datos TPV

## Flujos de Trabajo

### Configuración de IVA
1. Admin → Configuración → Impuestos
2. Configurar IVA general y por departamento
3. Al guardar → se sincroniza automáticamente con contabilidad enterprise

### Venta TPV
1. Cliente hace compra
2. Sistema calcula IVA usando departamento del producto
3. Ticket muestra IVA desagregado
4. **ENTERPRISE:** Se genera asiento contable automáticamente
5. **ENTERPRISE:** Se genera comprobante fiscal (si motor disponible)

### Liquidación de IVA
1. Jefe → Contabilidad → Impuestos
2. Seleccionar período
3. Sistema muestra:
   - Débito fiscal (ventas)
   - Crédito fiscal (compras)
   - Saldo a pagar/creditar
4. Generar liquidación oficial

## Qué Gestiona Cada Sistema

| Función | TPV (Actual) | Contabilidad Enterprise |
|---------|---------------|------------------------|
| Configurar IVA por departamento | ✅ | ❌ (solo lectura) |
| Calcular IVA en ticket | ✅ | ❌ |
| Imprimir ticket con IVA desagregado | ✅ | ❌ |
| Generar asiento contable con IVA | ❌ | ✅ (automático) |
| Registrar comprobante fiscal | ❌ | ✅ |
| Liquidación de IVA mensual | ❌ | ✅ |
| Reportes de impuestos | ❌ | ✅ |
| Gestión de retenciones/percepciones | ❌ | ✅ |
| Comprobantes electrónicos | ❌ | ✅ (estructura lista) |

## Compatibilidad

**✅ 100% Compatible:**
- TPV sigue funcionando con su sistema IVA actual
- No se modifica el cálculo de IVA en tickets
- Departamentos en MariaDB siguen siendo la fuente de verdad
- Configuración de IVA en admin sigue igual

**✅ Mejoras Enterprise:**
- Asientos contables se generan automáticamente con IVA
- Comprobantes fiscales se registran automáticamente
- Liquidación de IVA mensual unificada
- Reportes de impuestos avanzados

**🔄 Sincronización:**
- Al guardar configuración de IVA → se sincroniza con contabilidad
- Tasas no estándar se mapean automáticamente
- Datos fluyen de TPV → Contabilidad (no al revés)

## Recomendaciones

1. **Mantener configuración en TPV:**
   - IVA por departamento sigue siendo la fuente de verdad
   - Configurar en Admin → Configuración → Impuestos
   - No configurar directamente en contabilidad

2. **Usar contabilidad para:**
   - Liquidación mensual de IVA
   - Reportes fiscales
   - Comprobantes oficiales
   - Asientos contables automáticos

3. **Para futuro:**
   - Si se implementa facturación electrónica AFIP, usar motor de impuestos
   - El sistema está preparado para comprobantes electrónicos
   - API REST expone datos de impuestos para integraciones

## Conclusión

✅ **El sistema es 100% compatible.**
- TPV gestiona IVA de departamentos (cálculo en tickets)
- Contabilidad enterprise gestiona impuestos fiscales (liquidación, reportes)
- Ambos sistemas se sincronizan automáticamente
- No hay conflictos ni duplicación de datos
- Contabilidad puede gestionar TODO lo contable (asientos, IVA, activos, cierres)
