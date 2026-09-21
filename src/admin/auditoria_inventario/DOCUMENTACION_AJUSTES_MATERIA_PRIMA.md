# Sistema de Ajustes de Materia Prima - Auditoría de Inventario

## 📋 Índice
1. [Visión General](#visión-general)
2. [Arquitectura Piramidal](#arquitectura-piramidal)
3. [Flujo de Trabajo](#flujo-de-trabajo)
4. [Procedimientos Operativos](#procedimientos-operativos)
5. [Guía para Nuevos Empleados](#guía-para-nuevos-empleados)
6. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 Visión General

El sistema de auditoría de inventario permite controlar y ajustar el stock de materia prima y productos terminados de manera modular, rastreable y documentada.

**Objetivos Principales:**
- Mantener precisión del inventario en tiempo real
- Rastrear todos los ajustes de stock
- Detectar pérdidas o ganancias de inventario
- Facilitar auditorías periódicas
- Documentar responsabilidades de cada ajuste

---

## 🏗️ Arquitectura Piramidal

### Nivel 1: Base de Datos (Fundación)
**Ubicación:** `src/base_de_datos/`
**Responsabilidades:**
- Tabla `productos`: Información básica de productos
- Tabla `ajustes_inventario`: Historial de todos los ajustes
- Tabla `escaneos_auditoria`: Registro de escaneos de códigos de barras
- Tabla `materia_prima_log`: Log específico para materia prima

**Estructura de `ajustes_inventario`:**
```sql
CREATE TABLE ajustes_inventario (
    id INT PRIMARY KEY AUTO_INCREMENT,
    producto_id INT,
    codigo VARCHAR(50),
    nombre_producto VARCHAR(200),
    stock_anterior DECIMAL(10,2),
    stock_nuevo DECIMAL(10,2),
    diferencia DECIMAL(10,2),
    unidad_medida VARCHAR(20),
    usuario VARCHAR(100),
    fecha_hora DATETIME,
    motivo VARCHAR(500),
    tipo_ajuste VARCHAR(50), -- 'PERDIDA', 'GANANCIA', 'AJUSTE'
    aprobado_por VARCHAR(100),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);
```

### Nivel 2: Motor de Auditoría (Lógica de Negocio)
**Ubicación:** `src/cerebro_global/auditoria/motor_auditoria.py`
**Responsabilidades:**
- Validar ajustes de stock
- Calcular diferencias
- Registrar historial de cambios
- Aplicar reglas de negocio
- Generar reportes

**Funciones Principales:**
```python
# Obtener inventario actual
MotorAuditoria.obtener_inventario(db_manager)

# Procesar auditoría y aplicar ajustes
MotorAuditoria.procesar_auditoria(ajustes, usuario, db_manager)

# Registrar ajuste individual
MotorAuditoria.registrar_ajuste(producto_id, stock_anterior, stock_nuevo, usuario, motivo, db_manager)

# Obtener historial de ajustes
MotorAuditoria.obtener_historial_ajustes(producto_id, db_manager)
```

### Nivel 3: Interfaz de Usuario (Presentación)
**Ubicación:** `src/admin/auditoria_inventario/auditoria_main.py`
**Responsabilidades:**
- Visualización de inventario
- Edición de conteo real
- Escaneo de códigos de barras
- Aplicación de ajustes
- Visualización de historial

**Características de UI:**
- Auto-focus en buscador
- Detección de escaneo de códigos de barras
- Diálogo para seleccionar unidad (kilos/unidad)
- Edición mediante doble clic
- Historial de ajustes por producto

### Nivel 4: Documentación y Políticas (Cima)
**Ubicación:** Este archivo `.md`
**Responsabilidades:**
- Definir procedimientos estándar
- Establecer políticas de ajustes
- Guía para nuevos empleados
- Solución de problemas comunes
- Mejores prácticas

---

## 🔄 Flujo de Trabajo

### Flujo de Auditoría Estándar

```
1. PREPARACIÓN
   ├── Verificar fecha de última auditoría
   ├── Preparar equipo de escaneo
   └── Imprimir lista de productos a auditar

2. EJECUCIÓN
   ├── Escanear código de barras
   ├── Seleccionar unidad de medida (Kilos/Unidad)
   ├── Ingresar cantidad física
   └── Confirmar entrada

3. REVISIÓN
   ├── Verificar diferencias
   ├── Identificar productos con discrepancias
   └── Documentar motivos de ajustes

4. APROBACIÓN
   ├── Revisar justificaciones
   ├── Aprobar ajustes mayores al 5%
   └── Firmar autorización

5. APLICACIÓN
   ├── Aplicar ajustes en sistema
   ├── Actualizar stock
   └── Generar reporte

6. CIERRE
   ├── Archivar documentación
   ├── Actualizar próxima fecha de auditoría
   └── Notificar equipo
```

### Escenarios de Ajuste

**Ajuste por Pérdida (Merma)**
```
Situación: Producto dañado, vencido o perdido
Procedimiento:
1. Documentar causa (daño, vencimiento, robo)
2. Obtener aprobación del supervisor
3. Registrar en sistema con motivo detallado
4. Ajustar stock al nuevo valor
5. Generar reporte de pérdida
```

**Ajuste por Ganancia (Sobrante)**
```
Situación: Inventario físico mayor al registrado
Procedimiento:
1. Verificar duplicidad de conteo
2. Confirmar no ser error de sistema
3. Investigar origen del sobrante
4. Documentar hallazgo
5. Ajustar stock al valor correcto
```

**Ajuste por Error de Sistema**
```
Situación: Error en registro previo
Procedimiento:
1. Identificar origen del error
2. Corregir registro original si es posible
3. Si no es posible, crear ajuste correctivo
4. Documentar el error y corrección
5. Prevenir recurrencia
```

---

## 📖 Procedimientos Operativos

### Procedimiento: Auditoría Semanal de Materia Prima

**Frecuencia:** Semanal (día lunes)
**Responsable:** Encargado de inventario
**Duración estimada:** 2-3 horas

**Pasos:**

1. **Preparación (15 min)**
   - Imprimir reporte de stock actual
   - Revisar lista de productos de alta rotación
   - Verificar equipo de escaneo

2. **Auditoría (90-120 min)**
   - Escanear cada producto de materia prima
   - Ingresar cantidad física real
   - Notar discrepancias mayores al 5%
   - Tomar fotos de productos dañados

3. **Revisión (30 min)**
   - Comparar stock físico vs sistema
   - Identificar patrones de discrepancias
   - Preparar reporte de diferencias

4. **Aplicación (15 min)**
   - Aplicar ajustes en sistema
   - Generar reporte final
   - Archivar documentación

### Procedimiento: Auditoría Mensual Completa

**Frecuencia:** Mensual (último día del mes)
**Responsable:** Auditor + Supervisor
**Duración estimada:** 1 día completo

**Pasos:**

1. **Preparación (1 hora)**
   - Generar reporte de stock completo
   - Seleccionar muestra aleatoria del 20%
   - Preparar formularios de auditoría

2. **Auditoría física (4-6 horas)**
   - Conteo físico de productos seleccionados
   - Verificación de caducidades
   - Inspección de estado de conservación
   - Documentación de hallazgos

3. **Análisis (2 horas)**
   - Comparación de datos
   - Identificación de tendencias
   - Cálculo de porcentaje de error
   - Preparación de recomendaciones

4. **Informe (1 hora)**
   - Elaborar reporte ejecutivo
   - Presentar hallazgos a gerencia
   - Definir acciones correctivas
   - Establecer métricas de mejora

---

## 👥 Guía para Nuevos Empleados

### Bienvenida al Sistema de Auditoría

**Bienvenido al equipo de inventario.** Esta guía te ayudará a familiarizarte con el sistema de auditoría de materia prima y productos terminados.

### Primeros Pasos

**Día 1: Orientación**
- [ ] Revisar esta documentación completa
- [ ] Conocer la interfaz de auditoría
- [ ] Practicar con datos de prueba
- [ ] Conocer al supervisor de inventario

**Día 2: Práctica Supervisada**
- [ ] Realizar auditoría de muestra con supervisor
- [ ] Aprender a escanear códigos de barras
- [ ] Practicar ingreso de conteos
- [ ] Revisar reportes generados

**Día 3: Auditoría Independente**
- [ ] Realizar auditoría sin supervisión directa
- [ ] Aplicar ajustes básicos
- [ ] Generar reportes
- [ ] Obtener aprobación del supervisor

### Funciones Básicas

**1. Acceder al Módulo de Auditoría**
```
Inicio → Panel Admin → Auditoría de Inventario
```

**2. Buscar Producto**
- Usa el campo de búsqueda
- Ingresa código de barras o nombre
- Presiona Enter para filtrar

**3. Escanear Producto**
- Escanea código de barras con lector
- Se abrirá diálogo automáticamente
- Selecciona unidad (Kilos/Unidad)
- Ingresa cantidad física
- Presiona Aceptar

**4. Editar Conteo Real**
- Haz doble clic en la fila del producto
- Ingresa nuevo conteo real
- Presiona Actualizar
- Sistema calculará diferencia automáticamente

**5. Aplicar Ajustes**
- Revisa todas las diferencias
- Presiona "CONFIRMAR Y APLICAR AJUSTES"
- Confirma en el diálogo
- Sistema actualizará stock

### Reglas de Oro

1. **Siempre documentar el motivo de cada ajuste**
2. **Nunca aplicar ajustes sin aprobación para diferencias > 5%**
3. **Revisar el historial antes de ajustar un producto**
4. **Mantener el equipo de escaneo limpio y calibrado**
5. **Reportar cualquier patrón de discrepancias al supervisor**

### Errores Comunes y Cómo Evitarlos

**Error:** Escanear producto incorrecto
**Solución:** Verificar código y nombre en el diálogo antes de aceptar

**Error:** Seleccionar unidad de medida incorrecta
**Solución:** Revisar etiqueta del producto para confirmar unidad

**Error:** No guardar cambios antes de salir
**Solución:** El sistema te pedirá confirmación antes de aplicar ajustes

**Error:** Ajustar producto sin revisar historial
**Solución:** Siempre usar el botón "VER HISTORIAL" antes de ajustar

---

## 🔧 Solución de Problemas

### Problemas Comunes

**Problema: El código de barras no se reconoce**
```
Causas posibles:
- Código de barras dañado
- Lector de códigos no configurado
- Producto no registrado en sistema

Soluciones:
1. Verificar código de barras manualmente
2. Buscar producto por nombre
3. Registrar producto si no existe
```

**Problema: Diferencia muy grande en un producto**
```
Causas posibles:
- Error de conteo
- Producto no contado anteriormente
- Robo o pérdida no documentada

Soluciones:
1. Recontar producto
2. Verificar historial de ajustes
3. Investigar con supervisor
4. Documentar motivo detallado
```

**Problema: No puedo aplicar ajustes**
```
Causas posibles:
- Perfil de usuario sin permisos
- Diferencias no aprobadas
- Sistema en modo mantenimiento

Soluciones:
1. Verificar perfil de usuario
2. Obtener aprobación del supervisor
3. Contactar soporte técnico
```

**Problema: El sistema no guarda el historial**
```
Causas posibles:
- Error de conexión a base de datos
- Tabla de historial de ajustes corrupta
- Permisos de escritura insuficientes

Soluciones:
1. Verificar conexión a base de datos
2. Revisar logs del sistema
3. Contactar administrador de base de datos
```

### Contacto de Soporte

**Soporte Técnico:** [Email/Extensión]
**Supervisor de Inventario:** [Nombre/Extensión]
**Administrador de Sistema:** [Nombre/Extensión]

---

## 📊 Métricas y KPIs

### Indicadores de Desempeño

- **Precisión de Inventario:** % de coincidencia entre stock físico y sistema
- **Tiempo de Auditoría:** Promedio de tiempo por auditoría
- **Frecuencia de Ajustes:** Número de ajustes por período
- **Porcentaje de Error:** (Diferencia total / Stock total) × 100

### Metas

- Precisión de inventario > 95%
- Tiempo de auditoría < 3 horas (semanal)
- Reducción de ajustes mensuales > 10%
- Porcentaje de error < 2%

---

## 📝 Notas Finales

Este sistema está diseñado para garantizar la precisión del inventario y la trazabilidad de todos los ajustes. La documentación se mantiene actualizada con las mejores prácticas y procedimientos estándar.

**Última actualización:** [Fecha]
**Versión:** 1.0
**Responsable de mantenimiento:** [Nombre]

---

## 🚀 Próximas Mejoras Planificadas

- [ ] Integración con sistema de órdenes de compra
- [ ] Alertas automáticas para stock bajo
- [ ] Reportes de tendencias de inventario
- [ ] Integración con módulo de producción
- [ ] Auditoría con inteligencia artificial
