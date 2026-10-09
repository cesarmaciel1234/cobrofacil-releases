# Cómo vincular un dispositivo Point nuevo automáticamente

## 🎉 FUNCIONALIDAD MÁGICA - Consola Integrada

### ¡Novedad increíble!
Ahora el sistema tiene una **consola de comandos integrada** que:

1. **Detecta automáticamente** cuando seleccionás un dispositivo Point
2. **Ejecuta el comando curl** automáticamente con:
   - El token del cliente
   - El ID del dispositivo seleccionado
3. **Muestra en tiempo real**:
   - El comando curl ejecutándose
   - Barra de progreso animada
   - Salida del comando con colores
   - Confirmación de éxito/error

### ¿Cómo funciona?

#### Escenario 1: Un solo dispositivo vinculado
Cuando presionás **"⚡ Auto-configurar"**:
- El sistema detecta el dispositivo automáticamente
- **MÁGICAMENTE** ejecuta el curl para activarlo en modo PDV
- La consola muestra el comando en tiempo real
- El dispositivo queda listo para usar

#### Escenario 2: Múltiples dispositivos vinculados
Cuando hay 2 o más dispositivos:
- Aparece el diálogo para seleccionar
- Al seleccionar uno:
  - **MÁGICAMENTE** se ejecuta el curl automáticamente
  - La consola muestra todo el proceso
  - El dispositivo seleccionado se activa en modo PDV

#### Escenario 3: Dispositivo nuevo (no vinculado)
1. Presionás **"🔍 Nuevo dispositivo"**
2. Ingresás el serial
3. El sistema lo vincula y activa automáticamente
4. La consola muestra el proceso

### La Consola en Acción

Presioná **"📜 Ver Consola"** para ver:
```
$ curl.exe -X PATCH "https://api.mercadopago.com/terminals/v1/setup" -H "Content-Type: application/json" -H "Authorization: Bearer APP_USR-..." -d "{\"terminals\":[{\"id\":\"NEWLAND_N950__N950NCBA01604854\",\"operating_mode\":\"PDV\"}]}"
⏳ Ejecutando comando...
[████████████░░] 90%
✅ Comando ejecutado con éxito
Salida: {"terminals": [{"id":"NEWLAND_N950__N950NCBA01604854", "operating_mode":"PDV"}]}
🎯 Dispositivo NEWLAND_N950__N950NCBA01604854 activado en modo PDV
```

**Colores:**
- 🔵 Azul: Comando ejecutado
- 🟡 Amarillo: Información
- 🟢 Verde: Éxito
- 🔴 Rojo: Error
- 🟣 Lavanda: Salida del comando

### ✨ ¡NUEVO! Consola Editable + Terminal Manual

Si MercadoPago cambia el API o el comando falla:

1. **Editá el comando directamente** en la consola (es editable)
2. **Presioná "▶ Ejecutar"** para re-ejecutar con tus cambios
3. **Botones adicionales:**
   - **📋 Copiar**: Copia el comando al portapapeles
   - **🗑️ Limpiar**: Limpia la consola

**Ejemplo de uso:**
```
# Si MP cambia el endpoint de /terminals/v1/setup a /terminals/v2/setup:
$ curl.exe -X PATCH "https://api.mercadopago.com/terminals/v2/setup" ...  ← Editá esto
```

### 🖥️ ¡NUEVO! Terminal Manual

Ahora podés ejecutar **cualquier comando** desde la consola, no solo curl de MP:

**Campo de entrada:**
- Escribí comandos directamente en el campo inferior
- Presioná **ENTER** o el botón **▶** para ejecutar

**Ejemplos de comandos útiles:**

```bash
# Verificar conexión a red
ping 192.168.1.1

# Ver configuración de red
ipconfig

# Listar dispositivos Point
curl -X GET https://api.mercadopago.com/point/integration-api/devices -H "Authorization: Bearer TU_TOKEN"

# Verificar si un sitio responde
curl -I https://api.mercadopago.com

# Traceroute para diagnóstico
tracert api.mercadopago.com

# Ver puertos abiertos
netstat -an

# Diagnosticar DNS
nslookup api.mercadopago.com
```

**Casos de uso:**
- 📡 **Diagnosticar red**: Ping a routers, switches, terminales
- 🔍 **Investigar errores**: Verificar API endpoints, respuestas HTTP
- 🛠️ **Depuración**: Ver configuración de red, puertos, DNS
- 🧪 **Testing**: Probar nuevos comandos de MP antes de automatizarlos

**Flujo típico:**
```
1. Presioná "📜 Ver Consola"
2. Escribí: ping 192.168.1.50
3. Presioná ENTER
4. Ves la salida en tiempo real
5. Podés ejecutar más comandos
```

Esto te permite adaptarte rápidamente a cambios de MP sin esperar actualizaciones del software, y también diagnosticar problemas de red en tiempo real.

---

## Funcionalidad Original

### Pasos para vincular una máquina nueva (manual)

### 1. Obtener el serial del dispositivo
**Opción A - Desde la pantalla del dispositivo:**
- Enciende el terminal Point
- Ve a Configuración → Información del dispositivo
- Copia el Serial Number (ej: `N950NCBA01604854`)

**Opción B - Desde la caja:**
- El serial suele estar en una etiqueta debajo del dispositivo
- Formato: `N950NCBA01604854` o `NEWLAND_N950__N950NCBA01604854`

### 2. Ir a Configuración en el TPV
1. Inicia sesión como **ADMIN**
2. Ve a **Configuración** → **Dispositivos** → **Terminales TPV**
3. Asegúrate de tener tu **Access Token** de MercadoPago pegado

### 3. Vincular el dispositivo nuevo
1. Presiona el botón **"🔍 Nuevo dispositivo"** (verde)
2. Ingresá el serial del dispositivo
3. El sistema detecta automáticamente si es formato corto o largo
4. Confirmá la vinculación
5. ✅ El sistema:
   - Vincula el dispositivo a tu cuenta MP
   - Lo activa en modo PDV
   - Llena el campo Device ID automáticamente

### 4. Finalizar configuración
1. Presiona **"⚡ Auto-configurar"** para detectar el POS ID (QR)
2. Presiona **"💾 Guardar Configuración"**
3. Listo ✅

## Para clientes nuevos

Si instalás el TPV en un cliente nuevo:

1. **Opción 1 - Usar su cuenta MP:**
   - El cliente te da su Access Token
   - Seguís los pasos anteriores
   - El dispositivo queda vinculado a SU cuenta

2. **Opción 2 - Usar tu cuenta (demo):**
   - Usá tu token de prueba
   - Vinculás el dispositivo a tu cuenta
   - Cuando el cliente tenga su cuenta, repite el proceso con su token

## Errores comunes

### "Error al vincular - HTTP 400"
- Verificá que el serial sea correcto
- Asegúrate de incluir el prefijo `NEWLAND_N950__` si es necesario

### "Error al vincular - HTTP 401"
- El Access Token no es válido o expiró
- Obtené uno nuevo en mercadopago.com/developers

### "Dispositivo no encontrado"
- El dispositivo debe estar encendido
- Debe tener conexión a internet
- Espera 1-2 minutos después de encenderlo

## Comando curl equivalente (por si falla el botón)

Si por alguna razón el botón no funciona, podés usar curl:

```bash
curl -X PATCH "https://api.mercadopago.com/terminals/v1/setup" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN" \
  -d "{\"terminals\":[{\"id\":\"NEWLAND_N950__N950NCBA01604854\",\"operating_mode\":\"PDV\"}]}"
```

Reemplaza:
- `TU_ACCESS_TOKEN` con tu token real
- `NEWLAND_N950__N950NCBA01604854` con el serial del dispositivo
