# Motor Conector Auditoría - Arquitectura Modular

## 📋 Visión General

El **Motor Conector Auditoría** es un componente intermedio que permite que el sistema de auditoría se comunique con el motor de inventario de forma segura y modular, sin romper ninguna funcionalidad existente.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│  CAPA DE PRESENTACIÓN (UI)                                      │
│  AuditoriaMain (auditoria_main.py)                              │
│  - Interfaz de usuario                                          │
│  - Visualización de datos                                       │
│  - Interacción con operador                                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAPA DE CONEXIÓN (MOTOR CONECTOR)                              │
│  MotorConectorAuditoria (motor_conector_auditoria.py)           │
│  - Intermediario único                                          │
│  - Validación de solicitudes                                   │
│  - Transformación de datos                                     │
│  - Caché de productos                                          │
│  - NO accede a BD directamente                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAPA DE NEGOCIO (MOTOR INVENTARIO)                            │
│  MotorCatalogo (motor_catalogo.py)                              │
│  - Gestión de productos                                        │
│  - CRUD de inventario                                          │
│  - Lógica de negocio                                           │
│  - Acceso a base de datos                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Principios de Diseño

### 1. Separación de Responsabilidades
- **UI**: Solo presenta datos y recibe input del usuario
- **Conector**: Solo valida y transforma datos
- **Motor Inventario**: Solo gestiona lógica de negocio de inventario

### 2. No Modificación de Código Existente
- El conector NO modifica el motor de inventario
- El conector NO accede directamente a la base de datos
- El conector usa solo la API pública del motor de inventario

### 3. Lazy Loading
- El motor de inventario se carga solo cuando se necesita
- El db_manager se carga solo cuando se necesita
- Reduce el tiempo de inicio y memoria

### 4. Caché Inteligente
- Cachea productos por 5 minutos
- Actualiza solo cuando es necesario
- Reduce consultas a la base de datos

### 5. Transformación de Datos
- Convierte formatos entre sistemas
- Estandariza datos para auditoría
- Mantiene compatibilidad con inventario

## 🔌 API del Motor Conector

### Métodos Públicos

#### `obtener_inventario_para_auditoria(forzar_actualizacion=False)`
Obtiene el inventario actual para auditoría.

**Args:**
- `forzar_actualizacion`: Si True, ignora el caché y actualiza desde BD

**Returns:**
- Lista de diccionarios con datos de productos

**Uso:**
```python
conector = obtener_conector_auditoria()
productos = conector.obtener_inventario_para_auditoria()
```

#### `buscar_producto_por_codigo(codigo)`
Busca un producto por código de barras.

**Args:**
- `codigo`: Código de barras del producto

**Returns:**
- Diccionario con datos del producto o None

**Uso:**
```python
producto = conector.buscar_producto_por_codigo("123456789")
if producto:
    print(producto['nombre'])
```

#### `buscar_producto_por_id(producto_id)`
Busca un producto por ID.

**Args:**
- `producto_id`: ID del producto

**Returns:**
- Diccionario con datos del producto o None

**Uso:**
```python
producto = conector.buscar_producto_por_id(42)
if producto:
    print(producto['nombre'])
```

#### `solicitar_ajuste_stock(producto_id, stock_nuevo, usuario, motivo)`
Solicita un ajuste de stock al motor de inventario.

**Args:**
- `producto_id`: ID del producto a ajustar
- `stock_nuevo`: Nuevo valor de stock
- `usuario`: Usuario que solicita el ajuste
- `motivo`: Motivo del ajuste

**Returns:**
- Tuple (exito, mensaje)

**Uso:**
```python
exito, mensaje = conector.solicitar_ajuste_stock(
    42, 150.0, "Admin", "Ajuste de auditoría"
)
if exito:
    print("Ajuste aplicado")
```

#### `obtener_historial_ajustes(producto_id=None)`
Obtiene el historial de ajustes de auditoría.

**Args:**
- `producto_id`: ID del producto (opcional)

**Returns:**
- Lista de diccionarios con historial

**Uso:**
```python
historial = conector.obtener_historial_ajustes(42)
for ajuste in historial:
    print(f"{ajuste['fecha']}: {ajuste['diferencia']}")
```

#### `verificar_integridad()`
Verifica la integridad de la conexión con el motor de inventario.

**Returns:**
- Diccionario con estado de la conexión

**Uso:**
```python
estado = conector.verificar_integridad()
print(f"Motor disponible: {estado['motor_inventario_disponible']}")
print(f"Productos en caché: {estado['productos_en_cache']}")
```

## 🔄 Flujo de Datos

### Obtener Inventario
```
UI Auditoría
    ↓
MotorConectorAuditoria.obtener_inventario_para_auditoria()
    ↓
¿Caché válido?
    ↓ Sí → Devolver caché
    ↓ No
    ↓
MotorCatalogo.obtener_productos()
    ↓
Transformar datos
    ↓
Actualizar caché
    ↓
Devolver a UI
```

### Aplicar Ajuste
```
UI Auditoría
    ↓
MotorConectorAuditoria.solicitar_ajuste_stock()
    ↓
Validar solicitud
    ↓
MotorCatalogo.guardar_producto()
    ↓
MotorAuditoria.procesar_auditoria()
    ↓
Confirmar a UI
```

## 🛡️ Seguridad y Validación

### Validaciones del Conector

1. **Validación de Stock**
   - No permite stock negativo
   - Valida tipos de datos
   - Verifica existencia del producto

2. **Validación de Permisos**
   - Verifica rol del usuario (en UI)
   - Valida autorización para ajustes

3. **Validación de Datos**
   - Transforma tipos de datos
   - Estandariza formatos
   - Maneja excepciones

## 📊 Caché de Productos

### Configuración
- **Duración**: 5 minutos (300 segundos)
- **Capacidad**: Todos los productos (límite 10,000)
- **Actualización**: Automática o forzada

### Beneficios
- Reduce consultas a base de datos
- Mejora rendimiento de UI
- Disminuye carga en motor de inventario

### Gestión
```python
# Forzar actualización
productos = conector.obtener_inventario_para_auditoria(forzar_actualizacion=True)

# Verificar estado de caché
estado = conector.verificar_integridad()
print(f"Caché válido: {estado['cache_valido']}")
```

## 🔧 Solución de Problemas

### Problema: Motor de inventario no disponible
**Causa:** MotorCatalogo no se puede cargar
**Solución:** Verificar que el módulo de inventario está instalado correctamente

### Problema: Caché desactualizado
**Causa:** Productos modificados fuera de auditoría
**Solución:** Usar `forzar_actualizacion=True` al obtener inventario

### Problema: Ajuste no se aplica
**Causa:** Error en validación o en motor de inventario
**Solución:** Revisar mensaje de error y verificar integridad

## 📝 Integración con Código Existente

### Uso en AuditoriaMain
```python
from src.cerebro_global.auditoria.motor_conector_auditoria import obtener_conector_auditoria

class AuditoriaMain(QWidget):
    def __init__(self):
        super().__init__()
        self.conector_auditoria = obtener_conector_auditoria()
        
    def cargar_datos(self):
        productos = self.conector_auditoria.obtener_inventario_para_auditoria()
        # Procesar productos...
        
    def aplicar_ajustes(self):
        exito, mensaje = self.conector_auditoria.solicitar_ajuste_stock(
            producto_id, stock_nuevo, usuario, motivo
        )
```

## 🎓 Mejores Prácticas

1. **Siempre usar el conector**
   - Nunca acceder directamente a MotorCatalogo desde auditoría
   - Nunca acceder directamente a db_manager desde auditoría

2. **Validar resultados**
   - Siempre verificar el valor de retorno de los métodos
   - Manejar errores apropiadamente

3. **Usar caché cuando sea posible**
   - Reducir actualizaciones forzadas
   - Aprovechar el caché de 5 minutos

4. **Registrar errores**
   - Los errores se registran automáticamente en el logger
   - Revisar logs para diagnóstico

## 🚀 Futuras Mejoras

- [ ] Implementar historial completo en MotorAuditoria
- [ ] Agregar notificaciones de cambios de stock
- [ ] Integrar con sistema de alertas
- [ ] Optimizar caché con expiración por producto
- [ ] Agregar modo offline con sincronización

## 📞 Soporte

Para problemas con el motor conector:
1. Revisar logs de aplicación
2. Verificar integridad con `verificar_integridad()`
3. Consultar documentación de MotorCatalogo
4. Contactar equipo de desarrollo

---

**Última actualización:** [Fecha]
**Versión:** 1.0
**Autor:** Sistema de Auditoría
