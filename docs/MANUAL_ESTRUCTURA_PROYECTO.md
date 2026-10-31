# 📖 Manual de Supervivencia: Estructura del Proyecto TPV

Este manual explica cómo está organizado **Cobro Fácil POS** (TPV Pro 2026) y para qué sirve cada carpeta y archivo importante.

---

## 🗺️ Mapa visual del proyecto

```text
📁 tpv pro 2026/
│
├── 📁 01_Compiladores_y_Ejecutables/   ← Empaquetado .exe, instalador web, Firebase
├── 📁 02_Soporte_y_Mantenimiento/      ← DrHouse, licencias, firewall, diagnóstico
├── 📁 03_Actualizaciones_y_Red/        ← Utilidades de red (simulador LAN)
├── 📁 04_Respaldos_y_Migraciones/      ← Backups, init DB, setup MariaDB
│
├── 📁 docs/                            ← Manuales técnicos y de usuario
├── 📁 tests/                           ← Pruebas de integración (consola)
├── 📁 reportes/                        ← CSVs y reportes generados
├── 📁 mariadb_server/                  ← MariaDB portable embebido
│
├── 📁 src/                             ← EL CORAZÓN DEL CÓDIGO
│   ├── 📁 inicio_y_perfiles/           ← Splash, login, licencia, perfiles
│   ├── 📁 cajero/                      ← Terminal de ventas (paso 5–8) + chatbot
│   ├── 📁 admin/                       ← Panel administrativo (inventario, cierre, etc.)
│   ├── 📁 jefe/                        ← Panel gerencial (contabilidad, reportes)
│   ├── 📁 carteleria/                  ← Pantalla para monitor secundario
│   ├── 📁 base_de_datos/               ← Conexión principal + cola offline
│   ├── 📁 db_engines/                  ← Motor MariaDB
│   ├── 📁 services/                    ← LAN, email, caja, facturación, MariaDB
│   ├── 📁 hardware/                    ← Impresora, cajón, drivers
│   ├── 📁 ui_components/               ← Teclados, alertas, componentes visuales
│   ├── 📁 utils/                       ← Temas, paths, códigos de barras
│   ├── 📁 updater/                     ← Actualizador GitHub/Firebase
│   ├── 📁 tools/                       ← Utilidades internas (doctor, respaldos)
│   ├── 📁 navigation/                  ← Índices y registro de pantallas
│   ├── 📁 shared/                      ← UI compartida entre roles
│   ├── 📁 config/                      ← JSONs auxiliares (cartelería, escaneo)
│   ├── 📄 main_window.py               ← Ventana principal y navegación
│   └── 📄 config.py                    ← Clase de configuración (lee config.json)
│
├── 📄 main.py                          ← Punto de entrada de la aplicación
├── 📄 config.json                      ← Configuración local del negocio y hardware
├── 📄 version.json                     ← Versión y checksums para el actualizador
├── 📄 offline_queue.json               ← Ventas en buffer cuando no hay red
├── 📄 requirements.txt                 ← Dependencias Python (PyQt5, etc.)
└── 📄 .gitignore                       ← Archivos que Git debe ignorar
```

---

## 1. 📂 Las 4 carpetas maestras (herramientas externas)

Programas que **no son el TPV en sí**, sino herramientas para compilar, soportar y migrar.

| Carpeta | Para qué sirve | Contenido principal |
|---------|----------------|---------------------|
| **`01_Compiladores_y_Ejecutables/`** | Crear el `.exe` y el instalador | `Compilar_Todo.bat`, PyInstaller, empaquetado Firebase, `generar_version.py` |
| **`02_Soporte_y_Mantenimiento/`** | Soporte en campo | `DrHouse_Diagnostico.py`, `Generador_Licencias.py`, `ConfiguraFirewall.py`, test de estrés MariaDB |
| **`03_Actualizaciones_y_Red/`** | Red y pruebas LAN | `simulador_pc2.py` (el updater principal vive en `src/updater/`) |
| **`04_Respaldos_y_Migraciones/`** | Backups y migraciones | `RespaldoAutomatico.py`, `setup_mariadb.py`, `init_db.py` |

---

## 2. 📂 El corazón del sistema (`src/`)

### Arranque y sesión
*   **`inicio_y_perfiles/`** — Splash, licencia, selector de perfil (cajero / admin / jefe / cartelería) y login.

### Roles de usuario
*   **`cajero/`** — Terminal de ventas: escaneo, cobro (`paso5`–`paso8`), chatbot (`chat_bot.py`).
*   **`admin/`** — Backoffice: inventario, ofertas, reportes, cierre Z, Mercado Pago, Nexus, hardware, etc.
    *   **`admin/nexus/`** — Paneles del centro de control Nexus.
    *   **`admin/etiquetas/`** — Impresión de etiquetas de góndola.
    *   **`admin6_red_lan.py`** — Panel dedicado de red LAN / multicaja.
    *   **`admin15_carteleria.py`** — Configuración de mensajes en pantalla secundaria.
*   **`jefe/`** — Gerencia: dashboard, contabilidad (`jefe/contabilidad/`), reportes financieros.
*   **`carteleria/`** — Pantalla fullscreen para monitor secundario (`main_board.py`).

### Datos y servicios
*   **`base_de_datos/`** — `database.py` (manager principal) y `offline_sync.py` (cola offline).
*   **`db_engines/`** — Adaptador MariaDB.
*   **`services/`** — Servidor LAN (`lan_server.py`), control MariaDB, email, caja, facturación.
*   **`mariadb_server/`** (en raíz) — Binarios y datos del servidor MariaDB embebido.

### UI, hardware y utilidades
*   **`ui_components/`** — Teclados virtuales, alertas, toasts, cobro industrial.
*   **`hardware/`** — Impresora térmica, cajón de dinero, instalador de drivers.
*   **`utils/`** — Temas, rutas de archivos, parser de balanza/códigos de barras.
*   **`tools/`** — TPV Doctor, simulador de caja, respaldos, firewall.
*   **`updater/`** — Cliente/servidor de actualizaciones (GitHub / Firebase).
*   **`navigation/`** — Índices y registro central de pantallas (`screen_indices.py`, `screen_registry.py`).
*   **`shared/`** — Componentes reutilizados entre roles (p. ej. proveedores unificado).
*   **`_deprecated/`** — Módulos archivados; no usar en código nuevo.
*   **`vistas/`** — Shims de compatibilidad (redirigen a `shared/`).

### Navegación interna (`src/navigation/`)

Los índices del **QStackedWidget** están definidos en `src/navigation/screen_indices.py` como la clase `Screen`. Las fábricas lazy-load viven en `screen_registry.py`. `main_window.py` solo orquesta la navegación.

| Constante `Screen` | Pantalla |
|--------------------|----------|
| `ADMIN_DASHBOARD` (0) | Dashboard Admin |
| `CAJERO` (1) | Terminal Cajero |
| `INVENTARIO`–`CONFIGURACION` (2–5) | Inventario, Ofertas, Reportes, Configuración |
| `RED_LAN` (6) | Servidor LAN |
| `CIERRE`, `ETIQUETAS` (7–8) | Cierre Z, Etiquetas |
| `CONTABILIDAD` (9) | Contabilidad Jefe |
| `MERCADO_PAGO`, `PROVEEDORES` (10–11) | Mercado Pago, Proveedores |
| `HARDWARE`, `VENTAS_DIGITALES` (13–14) | Hardware, Ventas digitales |
| `CARTELERIA_CONFIG` (15) | Config TV (no es slot libre) |
| `CLIENTES` (17) | Fiado / Clientes |
| `NEXUS` (18) | Nexus Pro |
| `JEFE_DASHBOARD`, `JEFE_REPORTES` (19–20) | Dashboard y reportes Jefe |
| `CARTELERIA`, `CARTELERIA_DASHBOARD` (21–22) | TV y hub de cartelería |
| `IA_BOSS` (23) | IA proactiva del jefe |
| `PROMEDIOS` (24) | Promedios jefe |
| `AUDITORIA` (25) | Auditoría de inventario (admin) |
| `PROVEEDORES_JEFE`, `PROVEEDORES_CARTELERIA` (26–27) | Proveedores por perfil |
| `FREE` (12, 16) | Slots reservados — no navegar |

---

## 3. 📂 Pruebas (`tests/`)

Scripts de integración que se ejecutan desde consola (no son pytest automático):

```bash
.venv\Scripts\python.exe tests/test_estres.py
.venv\Scripts\python.exe tests/test_inventario.py
.venv\Scripts\python.exe tests/test_lan_multicaja.py
.venv\Scripts\python.exe tests/test_offline_recovery.py
.venv\Scripts\python.exe tests/tests_features.py
.venv\Scripts\python.exe tests/test_nexus.py
```

Ver `tests/README.md` para detalle de cada prueba.

---

## 4. 📄 Archivos importantes en la raíz

| Archivo | Función |
|---------|---------|
| **`main.py`** | Enciende la app: splash, DB, servidor LAN, login, ventana principal |
| **`config.json`** | Nombre del negocio, impresoras, tema, motor de BD (`mariadb` o `sqlite`), caja ID |
| **`version.json`** | Versión y checksums de archivos para el actualizador remoto |
| **`offline_queue.json`** | Ventas guardadas localmente cuando falla la red |
| **`requirements.txt`** | Paquetes Python necesarios |
| **`*.log`** (`crash.log`, etc.) | Registro de errores si la app falla |
| **`.gitignore`** | Excluye `.venv/`, bases de datos, logs, ZIPs y binarios pesados de Git |

### Base de datos

El motor por defecto es **MariaDB** (`config.json` → `"db_engine": "mariadb"`), servido desde `mariadb_server/`.

También se soporta **SQLite** (`*.db` en la raíz, p. ej. `AQVGI.db`) para instalaciones simples o legacy.

La contabilidad del módulo Jefe usa además un SQLite auxiliar en `src/jefe/contabilidad/database.py`.

---

## 5. 📂 Documentación (`docs/`)

| Archivo | Contenido |
|---------|-----------|
| `MANUAL_ESTRUCTURA_PROYECTO.md` | Este manual |
| `manual_cajero.md` / `manual_admin.md` | Guías de usuario |
| `checklist_testing.md` | Checklist manual de hardware y flujos |
| `servidor_local.md` | Configuración del servidor LAN |
| `README_HARDWARE.md` | Impresoras, cajón, balanza |

---

## 6. 🧹 Qué NO debería estar en el repo

Estos elementos fueron eliminados o ignorados por `.gitignore` porque no forman parte del TPV en producción:

*   `chatbot/` duplicado (el chatbot vive en `src/cajero/chat_bot.py`)
*   `IPython/` (extensiones ajenas al proyecto)
*   `scripts_historicos/` (parches one-shot ya aplicados)
*   `reportes/backups_actualizacion/` (snapshots viejos de código)
*   `src/_deprecated/` (módulos legacy archivados)
*   Carpetas `.venv/`, `__pycache__/`, bases de datos locales y logs

> **Nota:** Tras cambios grandes de estructura, regenerar `version.json` con `01_Compiladores_y_Ejecutables/generar_version.py` antes de publicar una actualización.

---
*Actualizado para reflejar la estructura real del proyecto — TPV Pro 2026.*
