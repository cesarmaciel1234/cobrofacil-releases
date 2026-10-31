# Plano: Configuración del Sistema

## 🎯 Objetivo

Hub de configuración para el sistema TPV, permitiendo gestionar todas las opciones de forma modular y organizada.

Ecosistema: cada diálogo lee y escribe su clave en `config.json`. No importa inventario ni ventas. El flag `opt_stock_negativo` lo consume el motor de stock; esta pantalla solo lo guarda. «No vender sin stock» es la UI invertida de ese flag.

## 📐 Estructura del Módulo

```
configuracion/
├── configuracion_main.py          # Hub principal (navegación entre categorías)
├── plano.md                       # Este archivo (plano del módulo)
└── componentes/
    ├── README.md                   # Documentación de componentes
    ├── dialogo_terminal_tpv.py     # Diálogo de terminales TPV
    ├── dialogo_balanza.py          # Diálogo de báscula
    ├── dialogo_cajon.py            # Diálogo de cajón de dinero
    ├── dialogo_facturacion.py      # Diálogo de facturación
    ├── dialogo_impuestos.py         # Diálogo de impuestos
    ├── dialogo_ticket.py           # Diálogo de ticket
    ├── [otros diálogos específicos]
    └── config_button.py             # Botón reutilizable de configuración
```

## 🎨 Categorías de Configuración

### 1. General
- Alertas de efectivo
- Opciones habilitadas
- Cajeros
- Facturación
- Modificar folios
- Administrar cajas

### 2. Personalización
- Logotipo del programa
- Ticket
- Impuestos
- Corte
- Símbolo de moneda
- Unidades de medida

### 3. Dispositivos
- Dos tiketeras 2 cajas
- Lector de códigos
- Cajón de dinero
- Báscula
- Terminal TPV
- Hardware industrial

### 4. Servicios
- App Cobro Fácil
- Integraciones nube
- Notificaciones por correo

### 5. Mantenimiento
- Respaldo
- Licencia
- Actualizaciones

## 🔄 Flujo de Navegación

```
Usuario abre configuración
        ↓
configuracion_main.py muestra hub
        ↓
Usuario selecciona categoría (ej: Dispositivos)
        ↓
configuracion_main muestra sub-hub con tarjetas
        ↓
Usuario selecciona tarjeta (ej: Terminal TPV)
        ↓
configuracion_main abre diálogo específico
        ↓
Usuario modifica configuración
        ↓
Usuario guarda
        ↓
configuración persistida en config.json
```

## 🎨 Diseño UI

### Paleta de colores (Light Theme)
- Fondo: #F8FAFC
- Cards: #FFFFFF
- Bordes: #E2E8F0
- Acentos: #3B82F6 (azul), #10B981 (verde), #F59E0B (naranja)
- Texto: #0F172A (negro), #64748B (gris)

### Tipografía
- Familia: Segoe UI
- Títulos: 22-24px, bold
- Subtítulos: 14-15px, medium
- Cuerpo: 13px, regular

## 🔧 Integración con Config

Todas las configuraciones se guardan en `config.json` usando el módulo `src.config`:

```python
from src.config import config

# Guardar
config.set("mp_access_token", token)

# Leer
token = config.get("mp_access_token", "")
```

## 📊 Componentes Reutilizables

### ConfigButton
Botón reutilizable para todas las opciones de configuración.

**Uso:**
```python
from componentes.config_button import ConfigButton

boton = ConfigButton(
    icon="🖨️",
    title="Ticket",
    description="Configurar ticket de venta",
    callback=self._abrir_ticket
)
```

## 🎯 Objetivos de Diseño

1. **Modularidad** - Cada diálogo es independiente
2. **Consistencia** - Mismo estilo visual en todos los diálogos
3. **Escalabilidad** - Fácil agregar nuevas opciones
4. **Usabilidad** - Navegación intuitiva
5. **Mantenibilidad** - Código organizado por categorías

## 🚀 Extensiones Futuras

- [ ] Configuración por perfil (admin, cajero, jefe)
- [ ] Importar/exportar configuración completa
- [ ] Historial de cambios de configuración
- [ ] Validación de configuración antes de guardar
- [ ] Rollback a configuración anterior
