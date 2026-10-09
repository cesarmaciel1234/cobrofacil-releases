# Plano: Cierre de Caja

## 🎯 Objetivo

Sistema centralizado de cierre de caja con arqueo, métricas y consolidación multi-caja.

## 📐 Estructura Modular (Centralizada)

```
cierre/ (admin)
└── cierre_main.py          # Wrapper que hereda de UI global

ui_global/cierre_diario_ui/
├── cierre_main_ui.py       # UI base
├── cierre_premium_ui.py    # UI premium (admin/jefe)
└── componentes/
    ├── metric_card.py      # Tarjetas de métricas
    └── panel_arqueo.py     # Panel de arqueo

cerebro_global/cierre_caja_cerebro/
├── motor_cierre.py         # Orquestador principal
└── procesos/
    ├── cierre.py           # Lógica de cierre
    ├── esperado.py         # Esperado vs físico
    ├── historial_cortes.py # Historial
    ├── modos.py            # Modos (cajero/día)
    ├── multi_caja.py       # Multi-caja
    └── totales.py          # Cálculos
```

## 🔧 Responsabilidades por Módulo

### 1. cierre_main.py (Admin Wrapper)
- **Responsabilidad:** Heredar de UI premium para admin
- **Funciones:**
  - Importar CierreGlobalUI
  - Pasar parent_main
  - Sin lógica adicional

### 2. cierre_premium_ui.py (UI Premium)
- **Responsabilidad:** Interfaz gráfica para admin/jefe
- **Funciones:**
  - Header con controles de fecha y caja
  - Métricas (efectivo, digital, fiado, fondo, movimientos)
  - Panel de arqueo con cálculo de diferencia
  - Tablas de cajas e historial
  - Botón de aprobación de corte
  - Modos: cajero vs día

### 3. cierre_main_ui.py (UI Base)
- **Responsabilidad:** Interfaz gráfica base
- **Funciones:**
  - Similar a premium pero simplificada
  - Usada por cajero
  - Sin features premium

### 4. motor_cierre.py (Orquestador)
- **Responsabilidad:** Coordinar procesos de cierre
- **Funciones:**
  - listar_cajas()
  - obtener_datos_cierre()
  - procesar_corte()
  - validar_arqueo()

### 5. procesos/cierre.py (Lógica)
- **Responsabilidad:** Lógica de cierre
- **Funciones:**
  - Calcular totales del turno
  - Validar diferencias
  - Guardar corte en DB

### 6. procesos/esperado.py (Esperado)
- **Responsabilidad:** Cálculo de esperado
- **Funciones:**
  - Calcular dinero esperado
  - Comparar con físico
  - Detectar sobrantes/faltantes

### 7. procesos/historial_cortes.py (Historial)
- **Responsabilidad:** Historial de cortes
- **Funciones:**
  - Obtener cortes del día
  - Filtrar por cajero/caja
  - Mostrar diferencias

### 8. procesos/modos.py (Modos)
- **Responsabilidad:** Normalizar modos
- **Funciones:**
  - normalizar_modo(modo)
  - etiqueta_modo(modo)
  - Valores: "cajero", "dia"

### 9. procesos/multi_caja.py (Multi-caja)
- **Responsabilidad:** Soporte multi-caja
- **Funciones:**
  - Consolidar datos de múltiples cajas
  - Calcular totales globales
  - Mostrar estado por caja

### 10. procesos/totales.py (Totales)
- **Responsabilidad:** Cálculo de totales
- **Funciones:**
  - Sumar ventas efectivo
  - Sumar ventas digital
  - Sumar movimientos extra
  - Calcular ganancia

## 🔄 Flujo de Datos

```
Usuario (Admin/Jefe/Cajero)
        ↓
CierreGlobalUI (ui_global)
        ↓
MotorCierre (cerebro_global)
        ↓
Procesos específicos
        ↓
Base de datos (punpro.db)
```

## 🎨 Frontend (UI)

### Componentes
- Header con fecha, caja, modo
- 5-6 cards de métricas
- Panel de arqueo (esperado vs físico)
- Tabla de cajas (multi-caja)
- Tabla de historial (cortes del día)
- Botón de aprobación

### Eventos
- dateChanged → _load_data()
- combo_caja → _load_data()
- btn_corte_cajero → _cambiar_modo("cajero")
- btn_corte_admin → _cambiar_modo("dia")
- btn_cierre → _on_click_finalizar()

## 🔙 Backend (Cerebro)

### MotorCierre
```python
class MotorCierre:
    @staticmethod
    def listar_cajas()
    @staticmethod
    def obtener_datos_cierre(caja, fecha, modo)
    @staticmethod
    def procesar_corte(caja, fecha, modo, fisico)
    @staticmethod
    def validar_arqueo(esperado, fisico)
```

### Procesos
```python
# cierre.py
def calcular_totales_ventas()
def procesar_corte_individual()

# esperado.py
def calcular_esperado()
def comparar_fisico()

# historial_cortes.py
def obtener_historial_dia()
def filtrar_por_cajero()

# modos.py
def normalizar_modo(modo)
def etiqueta_modo(modo)

# multi_caja.py
def consolidar_cajas()
def estado_por_caja()

# totales.py
def sumar_efectivo()
def sumar_digital()
def calcular_ganancia()
```

## 📊 Estados del Sistema

### Estados de caja
- **Abierta** - Turno en curso
- **Cerrada** - Turno finalizado
- **En arqueo** - En proceso de arqueo

### Estados de corte
- **Pendiente** - Sin aprobar
- **Aprobado** - Aprobado por admin/jefe
- **Rechazado** - Con discrepancia

### Modos de vista
- **cajero** - Vista individual del cajero
- **dia** - Vista consolidada del día

## 🛡️ Validaciones

### Validaciones de arqueo
- Físico no puede ser negativo
- Diferencia within tolerancia (configurable)
- Fondo de apertura validado

### Validaciones de permisos
- Cajero: Solo modo cajero
- Admin: Modo cajero + día
- Jefe: Modo cajero + día + ganancia

## 🎯 Objetivos de Diseño

1. **Centralización** - Un solo motor para todos los perfiles
2. **Reutilización** - UI compartida entre admin/jefe/cajero
3. **Escalabilidad** - Fácil agregar nuevos modos
4. **Consistencia** - Mismo cálculo en todos los perfiles
5. **Mantenibilidad** - Cambios en un solo lugar

## 📦 Estado Actual

**Estado actual:** Centralizado en ui_global y cerebro_global

**Estado deseado:** Ya está bien diseñado, no requiere cambios

**Prioridad:** Baja - Funciona correctamente
