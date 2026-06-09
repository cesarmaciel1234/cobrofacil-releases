# 🧪 Pruebas de Integración y Estrés - TPV Pro 2026

Todos los scripts de prueba han sido modularizados y organizados dentro de esta carpeta `tests/` para mantener limpio el directorio raíz.

## 🚀 Cómo Ejecutar las Pruebas

Para ejecutar cualquier script de prueba, hazlo desde la raíz del proyecto usando el entorno virtual `.venv` para que tome correctamente las dependencias y la base de datos local.

### 1. Test de Estrés de Ventas (Consola)
Simula la carga e inserción rápida de 100 ventas, controlando la actualización de stock y activando alarmas de exceso de efectivo.
```bash
.venv\Scripts\python.exe tests/test_estres.py
```

### 2. Test de Inventario y Carga Masiva (Excel)
Valida la importación masiva de productos desde Excel, comprobando la actualización de precios y el control inteligente de duplicados.
```bash
.venv\Scripts\python.exe tests/test_inventario.py
```

### 3. Test de Concurrencia Multicaja LAN
Simula 3 cajas facturando de forma simultánea conectadas al servidor LAN maestro para verificar que no haya bloqueos en la base de datos.
```bash
.venv\Scripts\python.exe tests/test_lan_multicaja.py
```

### 4. Test de Recuperación Offline (Buffer local)
Simula una caída total de red, encolando ventas de forma local en la cola de contingencia y validando su sincronización automática de fondo al retornar la conexión.
```bash
.venv\Scripts\python.exe tests/test_offline_recovery.py
```

### 5. Test de Características del Sistema (Banner de Stock, Cierre Z, Autocierre)
Prueba de forma aislada la lógica del banner de stock bajo, la generación del email HTML de cierre y el cierre de cajas huérfanas de días anteriores.
```bash
.venv\Scripts\python.exe tests/tests_features.py
```

---
*Nota: Todos los archivos temporales generados por las pruebas (como archivos Excel e informes HTML) se guardarán dentro de este mismo directorio `tests/` para no interferir con los datos de producción en la raíz.*
