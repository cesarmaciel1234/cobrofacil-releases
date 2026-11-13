# Plano de la Rama: Salida al CRM en la Nube (Espejo Render + Neon DB)

Este módulo es un **satélite desacoplado** del Servidor de Tienda. Su única función es replicar los datos de clientes, ventas y tablas clave hacia el CRM web alojado en Render (`https://crm-frigorifico.onrender.com`), respaldado por Neon DB (PostgreSQL serverless en la nube).

> [!IMPORTANT]
> **Ley de Oro del Espejo Nube:** La nube es un espejo de consulta. La tienda física local es la reina de la verdad. Si la conexión a Render falla, da timeout, devuelve 502/503/504 (cold start de contenedor dormido) o se corta internet, **el Servidor de Tienda, los cajeros y la base local siguen funcionando exactamente igual sin trabarse ni mostrar errores invasivos**.

---

## 1. Frente (Lo que ve el usuario)

1. **Botón en la ventana del Servidor de Tienda:**
   * **Ubicación:** Barra inferior de `src/central_red_global/servidor/ventana/lienzo.py`.
   * **Botón:** `[Empresa del CRM]` (estilo azul oscuro, al lado de `Ocultar en bandeja`).
2. **Diálogo de Configuración (`ventana/crm.py`):**
   * Se abre al presionar el botón `[Empresa del CRM]`.
   * Pide 5 campos:
     * **URL del CRM:** Por defecto `https://crm-frigorifico.onrender.com`.
     * **Contraseña / API Key:** Oculto con puntos (`Password`), no se expone en logs ni en procesos.
     * **Nombre de la Empresa / Usuario:** Con el que la sucursal se identifica en el CRM (ej. `maciel`).
     * **ID de Sucursal:** Número asignado en la nube (por defecto `1`).
     * **Nombre de Sucursal:** Nombre legible (ej. `Casa Central`).
   * Al presionar `[Aceptar]`, guarda en `config.json` e invoca `despertar()` del vigilante para realizar una sincronización inmediata.
   * Al presionar `[Cancelar]`, no toca nada y cierra limpiamente.
3. **Consola y Bandeja:**
   * La consola interna del servidor muestra eventos discretos:
     * `crm_salida  preparando envío a la nube...`
     * `crm_salida  datos sin cambios (huella idéntica, omitido)`
     * `crm_salida  lote enviado con éxito (X tablas, Y filas)`
     * `crm_salida  el envío falló y el servidor sigue (aviso silencioso)`

---

## 2. Fondo (Cómo opera el motor desacoplado)

```
Servidor de Tienda (bandeja.py / headless.py)
   │
   ├──> vigilante.py (prender / turno cada 120s)
   │       │
   │       ├──> proceso.py (ejecuta subproceso `python main.py --crm-cartera`)
   │       │       │
   │       │       └──> motor.py
   │       │               ├──> Lee punpro.db / espejo_tienda.db (modo sqlite ro)
   │       │               ├──> Ofusca passwords y claves secretas
   │       │               ├──> Calcula SHA256 (manifiesto y huella)
   │       │               └──> HTTP POST -> Render (crm-frigorifico.onrender.com)
   │       │                       ├── /api/pos/base/tabla
   │       │                       └── /api/pos/clientes/lote
   │       └──> Si falla: atrapa error y duerme hasta el próximo turno
```

1. **Aislamiento por Subproceso (`proceso.py`):**
   * El Servidor de Tienda **nunca realiza peticiones HTTP a Render en su hilo principal ni en sus hilos de red LAN**.
   * `vigilante.py` lanza un proceso hijo independiente: `[python, main.py, --crm-cartera]`.
   * Las credenciales se inyectan a través de variables de entorno seguras (`CRM_URL`, `CRM_USER`, `CRM_PASSWORD`, `CRM_EMPRESA`, etc.), **nunca por línea de comando**.
2. **Lectura Segura y Aislada (`motor.py`):**
   * Abre SQLite con URI `file:{ruta}?mode=ro` (Read-Only estricto).
   * Nunca bloquea ni bloquea las escrituras de los cajeros ni de MariaDB.
   * Filtra y convierte a `None` cualquier campo cuyo nombre contenga: `password`, `passwd`, `token`, `secret`, `api_key`.
3. **Detección de Cambios por Manifiesto (`huella` y `manifiesto`):**
   * Genera un hash SHA256 del contenido exportable.
   * Si la huella no ha cambiado desde el último ciclo, el proceso termina inmediatamente (`status 0`), ahorrando datos móviles y procesamiento en Render.
4. **Envío por Bloques y Tolerancia a Render (`subir_base` y `_pedir`):**
   * Los registros se dividen en trozos de 150 filas (`_TAMANO_PARTE = 150`).
   * Si Render está durmiendo (HTTP 502/503/504), `_pedir` aplica hasta 4 reintentos con pausa progresiva de 3 a 12 segundos para darle tiempo al contenedor de iniciar.
   * Si la sesión expira a mitad de una subida extensa, `reentrar()` regenera el token automáticamente sin recomenzar desde cero.
5. **Qué no hay que romper:**
   * No importar PyQt6 dentro de `crm_salida/motor.py` ni `proceso.py`.
   * No quitar el flag `mode=ro` al conectar SQLite.
   * No pasar contraseñas por `sys.argv`.
   * Mantener siempre `SOLO_MAESTRA` configurable: por ahora la esclava también puede enviar si tiene configuradas las credenciales de la empresa.
