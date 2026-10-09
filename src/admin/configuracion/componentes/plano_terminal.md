# Plano: Configuración de Terminales TPV

## 🎯 Objetivo

Gestionar la configuración de terminales Point de MercadoPago con interfaz gráfica, consola integrada y automatización completa.

## 📐 Estructura Modular (Encartetada)

```
componentes/
├── dialogo_terminal_tpv.py          # Diálogo principal (coordina todo)
├── mp_api_client.py                  # Cliente API MercadoPago (encapsula curl)
├── console_manager.py                # Gestor de consola de comandos
├── terminal_config.py                # Lógica de configuración de terminales
├── payment_tester.py                 # Lógica de pruebas de cobro
└── README_TERMINAL.md                # Documentación del módulo
```

## 🔧 Responsabilidades por Módulo

### 1. dialogo_terminal_tpv.py (Orquestador)
- **Responsabilidad:** Coordinar UI y orquestar flujos
- **Funciones:**
  - Construir interfaz gráfica
  - Manejar eventos de botones
  - Orquestar llamadas a otros módulos
  - Mostrar diálogos y mensajes

### 2. mp_api_client.py (Cliente API)
- **Responsabilidad:** Encapsular llamadas a API de MercadoPago
- **Funciones:**
  - Obtener dispositivos Point
  - Configurar modo de terminal (PDV/STANDALONE)
  - Consultar POS stores
  - Crear órdenes de cobro
  - Manejar códigos HTTP y errores

### 3. console_manager.py (Consola)
- **Responsabilidad:** Gestionar consola de comandos
- **Funciones:**
  - Mostrar comandos con colores
  - Ejecutar comandos curl
  - Barra de progreso animada
  - Terminal manual
  - Copiar/limpiar consola

### 4. terminal_config.py (Configuración)
- **Responsabilidad:** Lógica de configuración de terminales
- **Funciones:**
  - Desactivar dispositivos a STANDALONE
  - Activar dispositivo en PDV
  - Alternar entre dispositivos
  - Validar estados

### 5. payment_tester.py (Pruebas)
- **Responsabilidad:** Lógica de pruebas de cobro
- **Funciones:**
  - Crear payload de cobro
  - Enviar orden de prueba
  - Validar respuesta
  - Generar archivos temporales JSON

## 🔄 Flujo de Datos

```
Usuario → dialogo_terminal_tpv
         ↓
   [Orquesta acciones]
         ↓
mp_api_client ← → MercadoPago API
         ↓
   [Respuesta]
         ↓
console_manager ← [Mostrar en consola]
         ↓
   [Usuario ve resultado]
```

## 🎨 Frontend (dialogo_terminal_tpv.py)

### Componentes UI
- Campo Access Token
- Botones de acción (6 botones)
- Campos auto-llenados (Device ID, POS ID)
- Consola de comandos
- Botones de consola

### Eventos
- `clicked.connect()` - Conecta botones a funciones
- `returnPressed.connect()` - Enter en consola manual

## 🔙 Backend (Otros módulos)

### mp_api_client.py
```python
class MPApiClient:
    def get_devices(token)
    def set_terminal_mode(token, device_id, mode)
    def get_pos_stores(token)
    def create_payment_order(token, device_id, amount)
```

### console_manager.py
```python
class ConsoleManager:
    def log(message, type)
    def execute_command(command)
    def animate_progress()
    def show_console()
```

### terminal_config.py
```python
class TerminalConfig:
    def deactivate_all(token)
    def activate_terminal(token, device_id)
    def switch_terminals(token, old_device, new_device)
```

### payment_tester.py
```python
class PaymentTester:
    def create_test_order(device_id, amount)
    def send_order(token, payload)
    def validate_response(response)
```

## 📊 Estados del Sistema

### Estados de dispositivo
- **PDV** - Modo Punto de Venta (escucha montos del POS)
- **STANDALONE** - Modo independiente
- **SELF_SERVICE** - Modo autoservicio
- **POS** - Modo POS

### Estados de flujo
- **idle** - Esperando acción del usuario
- **detecting** - Detectando dispositivos
- **configuring** - Configurando terminal
- **testing** - Enviando cobro de prueba
- **complete** - Flujo completado

## 🛡️ Validaciones

### Validaciones de entrada
- Token no vacío
- Token debe ser APP_USR- (no TEST-)
- Device ID no vacío
- Monto mínimo $15

### Validaciones de API
- HTTP 200/201/204 - Éxito
- HTTP 401 - Token inválido
- HTTP 409 - Terminal ocupada
- HTTP 412 - Límite POS PDV
- HTTP 400 - Error en payload

## 🎯 Objetivos de Modularización

1. **Separación de responsabilidades** - Cada módulo hace una cosa bien
2. **Reutilización** - Cliente API puede usarse en otros módulos
3. **Testabilidad** - Cada módulo puede testearse independently
4. **Mantenibilidad** - Cambios en API solo afectan mp_api_client.py
5. **Legibilidad** - Código más fácil de entender

## 📦 Implementación Actual

**Estado actual:** Todo en `dialogo_terminal_tpv.py` (monolítico)

**Estado deseado:** Modularizado en 5 archivos como se describe arriba

**Prioridad:** Media - Funciona, pero sería más mantenible modularizado
