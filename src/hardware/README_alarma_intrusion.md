# Alarma de Intrusión del Cajón

Módulo separado que muestra una alerta visual cuando el cajón se abre manualmente con la llave (sin autorización).

## Características

- **Independiente**: Corre por encima de todas las ventanas sin interferir con el cajero
- **No invasivo**: Si el motor de alarma no funciona, no inyecta datos y el sistema sigue funcionando
- **Toast flotante**: Ventana sin marco que se superpone a todo mostrando la alerta
- **Auto-ocultación**: Se oculta automáticamente después de 5 segundos

## Funcionamiento

### Detección de intrusión

El módulo `cash_drawer.py` detecta cuando el cajón se abre sin autorización:

```python
# En cash_drawer.py
if not self._apertura_autorizada:
    self.intrusion_detected.emit()
    _mostrar_toast_intrusion()
```

### Toast de alerta

El módulo `alarma_intrusion.py` muestra un toast rojo con el texto:

```
⚠️ CAJÓN ABIERTO SIN AUTORIZACIÓN ⚠️
```

El toast:
- Se centra en la parte superior de la pantalla
- Permanece visible por 5 segundos
- Se superpone a todas las ventanas (WindowStaysOnTopHint)
- No captura el foco (WA_ShowWithoutActivating)

## Integración

### Cómo se activa

1. El cajero abre el cajón con la llave (sin autorización)
2. `drawer_manager` detecta el cambio de estado
3. Como no hay autorización (`_apertura_autorizada = False`), dispara la alarma
4. El toast se muestra por 5 segundos

### Cómo se evita la alarma

Cuando el sistema abre el cajón automáticamente (efectivo, mixto):

```python
# En cobro_controller.py
if debe_abrir:
    drawer_manager.set_authorized(True)  # Marca como autorizada
    # Luego abre el cajón
```

Al estar autorizada, no se dispara la alarma de intrusión.

## API

### `mostrar_alarma_intrusion(duracion_ms=5000)`

Muestra el toast de alarma de intrusión.

```python
from src.hardware.alarma_intrusion import mostrar_alarma_intrusion

mostrar_alarma_intrusion(duracion_ms=5000)  # 5 segundos
```

### `ocultar_alarma_intrusion()`

Oculta el toast de alarma de intrusión si está visible.

```python
from src.hardware.alarma_intrusion import ocultar_alarma_intrusion

ocultar_alarma_intrusion()
```

### `limpiar()`

Limpia la instancia singleton (para testing o reinicio).

```python
from src.hardware.alarma_intrusion import limpiar

limpiar()
```

## Configuración

No requiere configuración. El módulo usa valores por defecto:

- **Duración**: 5000 ms (5 segundos)
- **Texto**: "⚠️ CAJÓN ABIERTO SIN AUTORIZACIÓN ⚠️"
- **Color**: Rojo (#DC2626 con transparencia)
- **Tamaño**: 28px, peso 900

## Seguridad

- No inyecta datos en el cajero
- No afecta el flujo de ventas
- Si falla, el sistema sigue funcionando normalmente
- El cajero puede seguir operando mientras el toast está visible

## Testing

Para probar el módulo:

```python
from src.hardware.alarma_intrusion import mostrar_alarma_intrusion, ocultar_alarma_intrusion

# Simular intrusión
mostrar_alarma_intrusion(duracion_ms=3000)  # 3 segundos

# Ocultar manualmente
ocultar_alarma_intrusion()
```

## Dependencias

- PyQt6 (QWidget, QLabel, QVBoxLayout, Qt, QTimer)
- logging (logger)

## Archivos

- `src/hardware/alarma_intrusion.py` - Módulo principal del toast
- `src/hardware/cash_drawer.py` - Integración con el detector de cajón
- `src/hardware/README_alarma_intrusion.md` - Este archivo
