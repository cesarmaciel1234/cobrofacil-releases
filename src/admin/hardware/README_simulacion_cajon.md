# Simulación de Cajón Virtual (Testing)

Feature para simular un cajón virtual desde el panel de hardware del admin, permitiendo testing sin hardware físico con señales REALES.

## Ubicación

**Panel**: Admin → Hardware → PANEL DE SEGURIDAD

**Checkboxes**:
- "CAJÓN VIRTUAL: ABIERTO" (color verde)
- "CAJÓN VIRTUAL: APERTURA CON LLAVE (INTRUSIÓN)" (color rojo)

**Consola**: [TERMINAL ROOT] Consola Interactiva OS (CMD)

## Comandos de Consola

La consola acepta comandos especiales para verificar el estado del cajón virtual:

### `status_cajon` o `drawer_status`
Muestra el estado actual del cajón virtual.

```
C:\TPV_PRO> status_cajon
Estado del Cajón Virtual:
  Estado: ABIERTO
  Apertura: AUTORIZADA
  Método: GENÉRICO
```

### `abrir_cajon` or `open_drawer`
Envía una señal de apertura de cajón (autorizada).

```
C:\TPV_PRO> abrir_cajon
Enviando señal de apertura de cajón...
✅ Señal enviada correctamente
```

### `alarma_test` or `test_alarm`
Activa el toast de alarma de intrusión por 3 segundos para testing.

```
C:\TPV_PRO> alarma_test
Activando toast de alarma de intrusión...
✅ Toast activado por 3 segundos
```

## Funcionamiento

### Checkbox "CAJÓN VIRTUAL: ABIERTO"

Simula que el sistema abrió el cajón (apertura autorizada).

**Marcado**:
- Marca `drawer_manager.set_authorized(True)` (apertura autorizada)
- Fuerza estado `_last_status = True`
- Dispara `_process_status_change(True)`
- El cajero recibe señal de cajón abierto
- **NO** se activa la alarma de intrusión (porque es autorizada)
- Mensaje en cajero: `"✅ COBRO EXITOSO — ticket 12345 · Cajón abierto"`

**Desmarcado**:
- Fuerza estado `_last_status = False`
- Dispara `_process_status_change(False)`
- El cajero deja de recibir la señal
- Mensaje en cajero: `"✅ COBRO EXITOSO — ticket 12345"`

### Checkbox "CAJÓN VIRTUAL: APERTURA CON LLAVE (INTRUSIÓN)"

Simula que el cajero abrió el cajón con la llave física (sin autorización).

**Marcado**:
- Marca `drawer_manager.set_authorized(False)` (NO autorizada)
- Fuerza estado `_last_status = True`
- Dispara `_process_status_change(True)`
- Emite señal `intrusion_detected`
- **SÍ** se activa el toast de alarma de intrusión
- El cajero ve cajón abierto y el toast rojo de alarma

**Desmarcado**:
- Fuerza estado `_last_status = False`
- Dispara `_process_status_change(False)`
- El toast de alarma se oculta
- El cajero deja de ver la señal

## Mensaje de Cobro Exitoso

El mensaje es **REAL** y depende del estado físico del cajón:

```python
# En _comun.py
cajon_realmente_abierto = drawer_manager.is_open

if cajon_realmente_abierto:
    mensaje = f"✅ COBRO EXITOSO — ticket {id_v} · Cajón abierto"
else:
    mensaje = f"✅ COBRO EXITOSO — ticket {id_v}"
```

## Casos de Uso

### Testing 1: Apertura autorizada (efectivo)

1. Marcar "CAJÓN VIRTUAL: ABIERTO"
2. Realizar cobro en el cajero
3. Verificar que el mensaje muestre "Cajón abierto"
4. Verificar que **NO** aparezca el toast de alarma
5. Desmarcar el checkbox
6. Realizar otro cobro
7. Verificar que el mensaje NO muestre "Cajón abierto"

### Testing 2: Intrusión con llave

1. Marcar "CAJÓN VIRTUAL: APERTURA CON LLAVE (INTRUSIÓN)"
2. Verificar que aparece el toast rojo: "⚠️ CAJÓN ABIERTO SIN AUTORIZACIÓN ⚠️"
3. Verificar que aparece el punto rojo en el cabezal
4. Desmarcar el checkbox
5. Verificar que desaparece el toast y el punto rojo

### Testing 3: Comportamiento del cajero

1. Con "CAJÓN VIRTUAL: ABIERTO" marcado
2. Realizar cobro en efectivo
3. Verificar que el sistema NO intente abrir el cajón nuevamente (ya está abierto)
4. Verificar que el mensaje muestre "Cajón abierto"

## Implementación

### Código en `hardware_main.py`

```python
# Checkbox de cajón virtual ABIERTO
self.chk_virtual_open = QCheckBox("CAJÓN VIRTUAL: ABIERTO")
self.chk_virtual_open.stateChanged.connect(self.toggle_virtual_open)

def toggle_virtual_open(self, state):
    """Simula cajón virtual ABIERTO (apertura autorizada por sistema)."""
    from src.hardware.cash_drawer import drawer_manager

    if state == 2:  # Qt.Checked
        drawer_manager.set_authorized(True)
        drawer_manager._last_status = True
        drawer_manager._process_status_change(True)
        drawer_manager._is_checking = False
    else:  # Qt.Unchecked
        drawer_manager._last_status = False
        drawer_manager._process_status_change(False)
        drawer_manager._is_checking = False

# Checkbox de apertura con LLAVE (intrusión)
self.chk_virtual_key = QCheckBox("CAJÓN VIRTUAL: APERTURA CON LLAVE (INTRUSIÓN)")
self.chk_virtual_key.stateChanged.connect(self.toggle_virtual_key)

def toggle_virtual_key(self, state):
    """Simula apertura con LLAVE (intrusión sin autorización)."""
    from src.hardware.cash_drawer import drawer_manager

    if state == 2:  # Qt.Checked
        drawer_manager.set_authorized(False)
        drawer_manager._last_status = True
        drawer_manager._process_status_change(True)
        drawer_manager._is_checking = False
    else:  # Qt.Unchecked
        drawer_manager._last_status = False
        drawer_manager._process_status_change(False)
        drawer_manager._is_checking = False
```

### Código en `_comun.py`

```python
# Verificación real del estado del cajón
from src.hardware.cash_drawer import drawer_manager

cajon_realmente_abierto = drawer_manager.is_open

if cajon_realmente_abierto:
    mensaje = f"✅ COBRO EXITOSO — ticket {id_v} · Cajón abierto"
else:
    mensaje = f"✅ COBRO EXITOSO — ticket {id_v}"
```

## Diferencias entre los dos casilleros

| Casillero | Autorización | Alarma | Uso |
|-----------|--------------|--------|-----|
| CAJÓN VIRTUAL: ABIERTO | Sí (autorizada) | No | Simular apertura por sistema (efectivo) |
| CAJÓN VIRTUAL: LLAVE | No (sin autorización) | Sí | Simular intrusión con llave |

## Limitaciones

- La simulación solo afecta el estado en memoria de `drawer_manager`
- No envía señal física al cajón real
- No afecta el sensor físico del cajón
- Al reiniciar la aplicación, la simulación se pierde

## Seguridad

- Los casilleros están disponibles solo en el perfil ADMIN
- No afectan al perfil cajero
- No alteran la lógica de apertura real del cajón
- No afectan las ventas ni el cierre de caja

## Troubleshooting

**Los casilleros no funcionan**:
- Verificar que estás en perfil ADMIN
- Verificar que `drawer_manager` está inicializado
- Revisar logs de errores en consola

**El mensaje no cambia**:
- Verificar que `drawer_manager.is_open` se actualiza correctamente
- Revisar que el casillero realmente cambió el estado
- Probar recargar el panel de hardware

**El toast de alarma no aparece**:
- Marcar "CAJÓN VIRTUAL: APERTURA CON LLAVE (INTRUSIÓN)" (no el de ABIERTO)
- Verificar que el módulo `alarma_intrusion.py` está disponible
- Revisar logs del toast de alarma
