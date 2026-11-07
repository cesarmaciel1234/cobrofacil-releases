# Troubleshooting: Point MP no recibe montos

## Síntoma

El TPV envía la orden pero el terminal Point no muestra el monto. El cajero ve un error o el monto nunca aparece en la pantalla del terminal.

## Causas más comunes

### 1. Cuenta de Mercado Pago desincronizada (80% de los casos)

**Síntoma:** La orden se crea (HTTP 201) pero queda en estado `created` y nunca pasa a `at_terminal`.

**Causa:** La sesión abierta en el terminal físico Point es de una cuenta de Mercado Pago diferente al token configurado en el TPV.

**Cómo verificar:**
```python
# Prueba rápida (desde la raíz del proyecto)
python -c "
import sys
sys.path.insert(0, '.')
from src.config import config
from src.cajero.paso6_cobro.tarjeta_en_cobro.envio import enviar_monto
config._load_config()
token = config.get('mp_access_token', '')
device = config.get('mp_device_id', '')
print(f'Token: {token[:20]}...{token[-10:]}')
print(f'Device: {device}')
resultado = enviar_monto(token, device, 100.0, 'Prueba')
print(f'OK: {resultado.get(\"ok\")}, Motivo: {resultado.get(\"motivo\")}')
"
```

- Si el resultado es `OK: False, Motivo: otra_cuenta` → La sesión del terminal no corresponde al token
- Si el resultado es `OK: False, Motivo: cancelo` → La orden se canceló inmediatamente (misma causa)

**Solución:**
- **Opción A:** Loguear la misma cuenta de Mercado Pago en el terminal físico
  1. Abrir el terminal Point
  2. Cerrar sesión actual
  3. Loguearse con la cuenta que corresponde al token del TPV

- **Opción B:** Actualizar el token en el TPV
  1. Ir a **Admin → Terminales TPV**
  2. Cambiar el token por el de la cuenta abierta en el terminal
  3. Guardar configuración

**Archivo relacionado:** `src/cajero/paso6_cobro/decisiones.md` (líneas 63-80)

---

### 2. Terminal en modo STANDALONE

**Síntoma:** El validador devuelve `standalone` y no envía el monto.

**Causa:** El terminal está configurado en modo STANDALONE, que no recibe montos por API.

**Cómo verificar:**
```python
python -c "
import sys
sys.path.insert(0, '.')
from src.config import config
from src.cajero.paso6_cobro.mercadopago_core.terminal_validator import validar_terminal_point
config._load_config()
token = config.get('mp_access_token', '')
device = config.get('mp_device_id', '')
valido, motivo = validar_terminal_point(token, device)
print(f'Valido: {valido}, Motivo: {motivo}')
"
```

**Solución:**
- Cambiar el terminal a modo PDV desde Mercado Pago (web o API)
- Usar `PATCH /terminals/v1/setup` con `operating_mode: "PDV"`

**Archivo relacionado:** `src/cajero/paso6_cobro/mercadopago_core/terminal_validator.py`

---

### 3. Device ID incorrecto

**Síntoma:** El validador devuelve `sin_terminal`.

**Causa:** El `mp_device_id` configurado no pertenece a la cuenta del token.

**Cómo verificar:**
```python
python -c "
import sys
sys.path.insert(0, '.')
from src.config import config
from src.cajero.paso6_cobro.mercadopago_core.terminal_validator import validar_terminal_point
config._load_config()
token = config.get('mp_access_token', '')
device = config.get('mp_device_id', '')
valido, motivo = validar_terminal_point(token, device)
print(f'Valido: {valido}, Motivo: {motivo}')
"
```

**Solución:**
- Ir a **Admin → Terminales TPV**
- Verificar el Device ID (debe estar en formato `NEWLAND_N950__XXXXXXXXXXXXXX`)
- Usar el botón de escaneo para obtener el ID correcto del terminal

---

### 4. Error de red

**Síntoma:** El validador devuelve `red` o `enviar_monto` devuelve `motivo: red`.

**Causa:** No hay conexión a internet o Mercado Pago no responde.

**Solución:**
- Verificar conexión a internet
- Verificar que el firewall no bloquee peticiones a `api.mercadopago.com`
- Reintentar después de unos segundos

---

## Mensajes de error del TPV

Con los cambios implementados, el TPV muestra mensajes claros:

| Motivo | Mensaje en pantalla | Acción requerida |
|--------|-------------------|------------------|
| `otra_cuenta` | "El Point está abierto con otra cuenta de Mercado Pago que el token de la caja. Logueá la misma cuenta en el terminal o actualizá el token en Admin → Terminales TPV." | Sincronizar cuenta o token |
| `sin_terminal` | "El terminal Point no está vinculado a esta cuenta de Mercado Pago. Verificá el Device ID en Admin → Terminales TPV." | Verificar Device ID |
| `standalone` | "El terminal Point está en modo STANDALONE. Cambialo a modo PDV desde Mercado Pago para que reciba montos." | Cambiar a modo PDV |
| `red` | "No se pudo conectar con Mercado Pago para validar el terminal. Verificá tu conexión a internet." | Verificar red |
| `ocupada` | "La terminal ya tiene un cobro. Cancelalo en el Point y reenviá." | Cancelar cobro anterior |
| `minimo` | "El Point cobra desde $15." | Usar monto mayor a $15 |

---

## Archivos clave del código

### Validación del terminal
- `src/cajero/paso6_cobro/mercadopago_core/terminal_validator.py`
  - `validar_terminal_point(token, device_id)` - Valida antes de enviar

### Envío del monto
- `src/cajero/paso6_cobro/tarjeta_en_cobro/envio/mandar.py`
  - `enviar_monto(token, device_id, monto)` - Crea la orden y espera `at_terminal`
- `src/cajero/paso6_cobro/tarjeta_en_cobro/envio/estado.py`
  - `clasificar_estado(estado)` - Traduce status de MP
  - `detalle_orden(token, intent_id)` - Consulta estado de la orden

### Servicio Point
- `src/cajero/paso6_cobro/mercadopago_core/point_service.py`
  - `procesar_pago_mercadopago_point()` - Orquesta el cobro con validación

### UI
- `src/cajero/paso6_cobro/tarjeta_en_cobro/panel.py`
  - `PanelTarjetaCobro` - Muestra el panel de tarjeta con mensajes de error

### Documentación
- `src/cajero/paso6_cobro/decisiones.md` - Reglas y decisiones de diseño
- `src/cajero/paso6_cobro/mercadopago_core/README.md` - Arquitectura del módulo

---

## API de Mercado Pago (Orders API)

### Crear orden
```
POST https://api.mercadopago.com/v1/orders
Headers:
  - Authorization: Bearer {token}
  - X-Idempotency-Key: {uuid}
Body:
  {
    "type": "point",
    "external_reference": "{uuid}",
    "description": "Venta TPV",
    "expiration_time": "PT15M",
    "transactions": {
      "payments": [{"amount": "100.00"}]
    },
    "config": {
      "point": {
        "terminal_id": "NEWLAND_N950__XXXXXXXXXXXXXX",
        "print_on_terminal": "seller_ticket"
      },
      "payment_method": {"default_type": "credit_card"}
    }
  }
```

### Estados de orden
- `created` - Orden creada, no capturada por el terminal
- `at_terminal` - Orden capturada por el terminal, lista para procesar
- `processed` - Pago aprobado
- `failed` - Pago rechazado
- `canceled` - Orden cancelada
- `expired` - Orden expiró

### Listar terminales
```
GET https://api.mercadopago.com/terminals/v1/list
Headers:
  - Authorization: Bearer {token}

Response:
{
  "data": {
    "terminals": [
      {
        "id": "NEWLAND_N950__XXXXXXXXXXXXXX",
        "pos_id": "12345678",
        "store_id": "12345678",
        "operating_mode": "PDV"
      }
    ]
  }
}
```

### Cambiar modo de terminal
```
PATCH https://api.mercadopago.com/terminals/v1/setup
Headers:
  - Authorization: Bearer {token}
Body:
  {
    "terminals": [
      {
        "id": "NEWLAND_N950__XXXXXXXXXXXXXX",
        "operating_mode": "PDV"
      }
    ]
  }
```

---

## Historial de cambios

### 2026-11-07
- Implementado `terminal_validator.py` para validar antes de enviar
- Mejorados mensajes de error para `otra_cuenta`, `sin_terminal`, `standalone`
- Actualizada documentación en `decisiones.md` y `README.md`

### Referencia histórica
- 2026-10-26: El Point `NEWLAND_N950__N950NCBA01604854` no mostraba montos porque el token de la caja (usuario 680256868) no correspondía a la sesión abierta en el terminal (usuario 140284216). Documentado en `decisiones.md`.

---

## Pruebas de diagnóstico

### Prueba 1: Validar terminal
```bash
cd "C:\Users\cesar\OneDrive\Desktop\tpv pro 2026"
python -c "
import sys
sys.path.insert(0, '.')
from src.config import config
from src.cajero.paso6_cobro.mercadopago_core.terminal_validator import validar_terminal_point
config._load_config()
token = config.get('mp_access_token', '')
device = config.get('mp_device_id', ')
print(f'Token: {token[:20]}...{token[-10:]}')
print(f'Device: {device}')
valido, motivo = validar_terminal_point(token, device)
print(f'VALIDO: {valido}, MOTIVO: {motivo}')
"
```

### Prueba 2: Enviar monto de prueba
```bash
cd "C:\Users\cesar\OneDrive\Desktop\tpv pro 2026"
python -c "
import sys
sys.path.insert(0, '.')
from src.config import config
from src.cajero.paso6_cobro.tarjeta_en_cobro.envio import enviar_monto
config._load_config()
token = config.get('mp_access_token', '')
device = config.get('mp_device_id', ')
resultado = enviar_monto(token, device, 100.0, 'Prueba')
print(f'OK: {resultado.get(\"ok\")}, MOTIVO: {resultado.get(\"motivo\")}, INTENT: {resultado.get(\"intent\")}')
"
```

### Prueba 3: Ver detalle de orden
```bash
# Reemplazar ORDER_ID con el ID de la prueba anterior
curl -X GET "https://api.mercadopago.com/v1/orders/{ORDER_ID}" \
  -H "Authorization: Bearer {TOKEN}"
```

---

## Checklist de resolución

Cuando el Point no recibe montos:

- [ ] Verificar conexión a internet
- [ ] Correr prueba de validación de terminal
- [ ] Si `motivo == otra_cuenta`: Sincronizar cuenta de MP en terminal o token en TPV
- [ ] Si `motivo == standalone`: Cambiar terminal a modo PDV
- [ ] Si `motivo == sin_terminal`: Verificar Device ID en Admin
- [ ] Si `motivo == red`: Verificar firewall y proxy
- [ ] Correr prueba de envío de monto
- [ ] Verificar que el monto aparezca en el terminal físico
- [ ] Probar un cobro real desde el TPV
