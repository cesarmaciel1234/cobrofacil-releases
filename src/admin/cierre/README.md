# Cierre de Caja - Admin y Jefe

## 📋 Estructura del Sistema de Cierre

El sistema de cierre de caja está **centralizado** en módulos compartidos, no hay implementación específica en admin o jefe.

## 🏗️ Arquitectura

```
src/
├── admin/
│   └── cierre/
│       ├── cierre_main.py              # Hereda de CierreGlobalUI
│       └── README.md                   # Esta documentación
├── jefe/
│   └── [sin módulo de cierre específico]
├── ui_global/
│   └── cierre_diario_ui/
│       ├── cierre_main_ui.py          # UI base de cierre
│       ├── cierre_premium_ui.py        # UI premium (usada por admin)
│       └── componentes/
│           ├── metric_card.py
│           └── panel_arqueo.py
└── cerebro_global/
    └── cierre_caja_cerebro/
        ├── motor_cierre.py            # Motor principal de cierre
        └── procesos/
            ├── cierre.py              # Lógica de cierre
            ├── esperado.py            # Manejo de esperado
            ├── historial_cortes.py    # Historial
            ├── modos.py               # Modos de cierre
            ├── multi_caja.py           # Multi-caja
            └── totales.py              # Cálculo de totales
```

## 🎯 Responsabilidades

### 1. Admin (`admin/cierre/cierre_main.py`)
- **Responsabilidad:** Extender la UI premium de cierre
- **Implementación:** Mínima, solo hereda de `CierreGlobalUI`
- **Uso:** Admin accede al cierre con permisos de administrador

### 2. Jefe
- **Responsabilidad:** No tiene módulo de cierre específico
- **Implementación:** Usa la misma `CierreGlobalUI` que admin
- **Uso:** Jefe accede al cierre con permisos de supervisor

### 3. UI Global (`ui_global/cierre_diario_ui/`)
- **Responsabilidad:** Interfaz gráfica compartida
- **Componentes:**
  - `CierreGlobalUI` - Clase base de la UI
  - `cierre_main_ui.py` - Versión base
  - `cierre_premium_ui.py` - Versión premium (usada por admin)
  - `metric_card.py` - Tarjetas de métricas
  - `panel_arqueo.py` - Panel de arqueo

### 4. Cerebro Global (`cerebro_global/cierre_caja_cerebro/`)
- **Responsabilidad:** Lógica de negocio del cierre
- **Componentes:**
  - `motor_cierre.py` - Orquestador principal
  - `cierre.py` - Lógica de cierre
  - `esperado.py` - Manejo de dinero esperado
  - `historial_cortes.py` - Historial de cortes
  - `modos.py` - Modos de cierre (cajero/día)
  - `multi_caja.py` - Soporte multi-caja
  - `totales.py` - Cálculo de totales

## 🔄 Flujo de Cierre

```
Usuario (Admin/Jefe/Cajero)
        ↓
CierreGlobalUI (ui_global)
        ↓
MotorCierre (cerebro_global)
        ↓
Procesos específicos
        ↓
Base de datos
```

## 🎨 Diferencias por Rol

### Cajero
- Solo puede hacer corte cajero
- No ve historial de cortes del día
- No puede seleccionar caja específica
- Botón: "🛡️ APROBAR CORTE Y ARQUEO"

### Admin
- Puede hacer corte cajero o día
- Ve historial de cortes del día
- Puede seleccionar caja específica
- Botón: "🛡️ APROBAR CORTE GLOBAL DEL DÍA"

### Jefe
- Mismo comportamiento que Admin
- Botón: "🛡️ APROBAR CORTE GLOBAL DEL DÍA"
- Puede ver ganancia estimada (card adicional)

## 📊 Métricas Mostradas

- Ventas Efectivo
- Ventas Digital (tarjetas, transferencias, QR, vales, cheques)
- Ventas a Fiado
- Fondo Apertura
- Movimientos Extra (entradas/salidas)
- Ganancia Estimada (solo jefe)

## 🔧 Modos de Cierre

### Corte Cajero
- Arqueo del cajero actual
- Cierre individual por turno
- Sin consolidación

### Corte Día (Admin/Jefe)
- Consolidado de todas las cajas
- Vista global del día
- Historial de cortes por cajero

## 🎛️ Configuración

### Campos guardados
- Fecha del corte
- Tipo de corte (cajero/día)
- Caja seleccionada
- Físico esperado
- Diferencia (sobrante/faltante)

### Permisos
- Cajero: Solo corte cajero
- Admin: Corte cajero + día
- Jefe: Corte cajero + día + ganancia

## 📚 Archivos Relacionados

- `config.json` - Configuración general
- `punpro.db` - Base de datos de ventas
- `MotorCierre` - Motor de cierre central
