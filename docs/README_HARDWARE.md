# Manual de Estabilización de Hardware - PunPro 2026

Este documento detalla la implementación industrial para el control del cajón de dinero y la impresora térmica en el puerto COM3.

## ⚙️ Configuración del Puerto (COM3)
- **Velocidad**: 9600 Baudios (Establecido por compatibilidad de sensor).
- **Control de Flujo**: Ninguno (Software Handshake).
- **Protocolo**: ESC/POS Directo.

## 🚀 Lógica de Apertura (Cajón)
- **Comando**: `ESC p m t1 t2` (`\x1B\x70\x00\xC8\xC8`)
- **Fuerza**: Pulso reforzado de **200ms/400ms** (`0xC8`).
- **Pines**: Soporta Pin 2 (por defecto) y Pin 5 (configurable).

## 🛰️ Monitoreo de Estado (Sensor)
El sistema utiliza una **Ráfaga de Comandos** para obtener el estado real del sensor sin bloqueos:
1. **Comandos**: `DLE EOT 4` + `GS r 2`.
2. **Interpretación**: 
   - `CERRADO`: Recibe `0x12` o `0x10` (Bit 2 = 0).
   - `ABIERTO`: Recibe `0x16`, `0x14` o `0x01` (Bit 0 o 2 = 1).
3. **Filtro Debounce**: Se requiere confirmación doble (100ms) para reportar un cambio de estado, eliminando ruidos eléctricos.

## 🛡️ Watchdog (Vigilante)
- **Hilo**: Corre en segundo plano desde `main.py`.
- **Frecuencia**: Consulta cada 5 segundos.
- **Auto-Recuperación**: Utiliza un `threading.Lock` para evitar colisiones con el proceso de impresión.

## 📂 Archivos Críticos
- `src/hardware/printer.py`: Controlador de bajo nivel y lógica serial.
- `src/hardware/cash_drawer.py`: Lógica de negocio y gestión de intrusiones.
- `main.py`: Punto de entrada y gestión del Watchdog.
