# Configuración de Terminales TPV (MercadoPago Point)

## 📋 Resumen del Módulo

Este módulo gestiona la configuración de terminales de pago Point de MercadoPago, permitiendo vincular, activar y probar dispositivos TPV.

## 🏗️ Estructura Modular

```
configuracion/
├── configuracion_main.py          # Hub principal de configuración
└── componentes/
    ├── dialogo_terminal_tpv.py  # Diálogo de configuración de terminales TPV
    ├── README_TERMINAL.md         # Esta documentación
    └── [otros diálogos específicos]
```

## 🎯 Objetivo Principal

Gestionar la configuración de terminales Point de MercadoPago para el sistema TPV, incluyendo:
- Vinculación de dispositivos nuevos
- Activación en modo PDV (Punto de Venta)
- Pruebas de cobro
- Alternancia entre múltiples dispositivos

## 🔧 Componentes

### 1. DialogoTerminalTPV (`dialogo_terminal_tpv.py`)

**Responsabilidad:** Interfaz gráfica para configurar terminales Point.

**Funcionalidades principales:**
- Configuración de Access Token de MercadoPago
- Detección automática de dispositivos Point
- Activación de dispositivos en modo PDV
- Pruebas de cobro con consola integrada
- Alternancia automática entre dispositivos

**API pública:**
- `DialogoTerminalTPV(parent)` - Constructor
- `_buscar_devices_mp()` - Auto-configura Device ID y POS ID
- `_vincular_dispositivo_nuevo()` - Vincula dispositivo nuevo
- `_ver_pos_activos()` - Consulta POS stores activos
- `_ver_estado_dispositivo()` - Verifica estado del dispositivo
- `_probar_cobro_point()` - Envía cobro de prueba
- `_auto_completo()` - Flujo automatizado completo
- `_guardar()` - Guarda configuración

## 🔄 Flujo de Trabajo

### Flujo Automático Completo (Recomendado)

```
Usuario presiona "🔄 Auto-Completo"
        ↓
Sistema obtiene dispositivos Point
        ↓
Usuario selecciona dispositivo
        ↓
Sistema desactiva TODOS a STANDALONE
        ↓
Sistema activa el seleccionado en PDV
        ↓
Sistema envía cobro de prueba ($100)
        ↓
Usuario cancela cobro en dispositivo
        ↓
Usuario presiona Enter en TPV
        ↓
Usuario guarda configuración
```

### Flujo Manual Alternativo

```
1. Pegar Access Token
2. Presionar "⚡ Auto-configurar"
3. Sistema detecta dispositivo
4. Sistema activa en modo PDV
5. Presionar "🧪 Prueba cobro"
6. Guardar configuración
```

## 🎨 Interfaz de Usuario

### Secciones del Diálogo

1. **Mercado Pago Point + QR**
   - Campo Access Token
   - Botón Auto-configurar
   - Botón Nuevo dispositivo
   - Botón Ver POS activos
   - Botón Estado dispositivo
   - Botón Prueba cobro
   - Botón Auto-Completo
   - Campos Device ID y POS ID (auto-llenados)

2. **Clover Posnet**
   - Campo IP Address
   - Campo Puerto

3. **Consola de Comandos**
   - Área de texto editable
   - Campo de entrada manual
   - Botones: Ver Consola, Ejecutar, Copiar, Limpiar
   - Barra de progreso animada

## 🔌 Integración con API de MercadoPago

### Endpoints utilizados

1. **GET /point/integration-api/devices**
   - Obtiene dispositivos Point vinculados
   - Retorna lista de dispositivos con ID, modelo, serial

2. **PATCH /terminals/v1/setup**
   - Configura modo de operación de terminales
   - Modos válidos: PDV, STANDALONE, SELF_SERVICE, POS

3. **GET /pos**
   - Consulta POS stores de la cuenta
   - Retorna lista con external_id, name, status

4. **POST /v1/orders**
   - Crea orden de cobro para dispositivo Point
   - Payload incluye amount (string), terminal_id, expiration_time

## 🐛 Manejo de Errores

### Errores comunes

1. **HTTP 412 - Only one pos-store with pdv.mode=ON or SUSPENDED is allowed**
   - Causa: MercadoPago solo permite un POS PDV activo
   - Solución: Desactivar todos los dispositivos a STANDALONE antes de activar uno nuevo

2. **HTTP 400 - Incorrect type for property (amount)**
   - Causa: amount enviado como número en lugar de string
   - Solución: Usar `f"{monto:.2f}"` para enviar como string

3. **HTTP 401 - Token inválido**
   - Causa: Token expirado o incorrecto
   - Solución: Obtener nuevo token en mercadopago.com/developers

4. **HTTP 409 - Terminal ocupada**
   - Causa: Ya hay un cobro pendiente en el dispositivo
   - Solución: Cancelar cobro en el dispositivo y reintentar

## 📝 Configuración

### Campos guardados en config.json

```json
{
  "mp_access_token": "APP_USR-...",
  "mp_device_id": "NEWLAND_N950__...",
  "mp_qr_pos_external_id": "macielcaja",
  "mp_user_id": "140284216",
  "clover_ip": "",
  "clover_port": "1234"
}
```

## 🧪 Pruebas

### Prueba de cobro automática

```python
payload = {
    "type": "point",
    "external_reference": uuid.uuid4().hex[:20],
    "description": "Prueba de cobro",
    "expiration_time": "PT15M",
    "transactions": {"payments": [{"amount": "100.00"}]},  # IMPORTANTE: string
    "config": {
        "point": {
            "terminal_id": "DEVICE_ID",
            "print_on_terminal": "seller_ticket"
        },
        "payment_method": {"default_type": "credit_card"}
    }
}
```

## 🔐 Seguridad

- Access Token nunca se muestra en texto plano (modo password)
- Tokens TEST- son rechazados con advertencia
- Solo se usan tokens de producción (APP_USR-...)

## 📊 Consola Integrada

### Funcionalidades

1. **Visualización de comandos curl** - Muestra comando ejecutándose
2. **Barra de progreso animada** - Indica progreso de ejecución
3. **Colores de output:**
   - 🔵 Azul: Comando ejecutado
   - 🟡 Amarillo: Información
   - 🟢 Verde: Éxito
   - 🔴 Rojo: Error
   - 🟣 Lavanda: Salida del comando

4. **Terminal manual** - Ejecutar cualquier comando (ping, ipconfig, etc.)
5. **Editable** - Modificar comandos antes de ejecutar
6. **Botones útiles:** Copiar, Limpiar, Ejecutar

## 🎛️ Dependencias

### Librerías Python
- `PyQt6` - Interfaz gráfica
- `requests` - Cliente HTTP (para fallback)
- `json` - Parsing de JSON
- `uuid` - Generación de IDs únicos
- `subprocess` - Ejecución de curl

### Módulos internos
- `src.config` - Gestión de configuración
- `src.utils.qt_compat` - Compatibilidad Qt
- `src.utils.theme_manager` - Gestión de temas

## 🚀 Extensiones Futuras

Posibles mejoras:
- [ ] Agregar soporte para múltiples cuentas MP
- [ ] Historial de dispositivos utilizados
- [ ] Notificaciones de cambios de configuración
- [ ] Exportar/importar configuración de terminales
- [ ] Integración con otros POS (Clover, etc.)

## 📚 Referencias

- [Documentación MercadoPago Point](https://www.mercadopago.com.ar/developers/es/point/integration-api)
- [API de Orders](https://www.mercadopago.com.ar/developers/es/reference/point/_point_integration_api/integration-api)
- [API de Devices](https://www.mercadopago.com.ar/developers/es/reference/point/_point_integration_api/devices)
