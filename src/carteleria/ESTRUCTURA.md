# ESTRUCTURA CARTELERÍA - Limpia y Moderna

## 📁 Estructura Final Organizada

```
src/carteleria/
├── __init__.py                          # Inicialización del módulo
├── theme.py                             # Sistema de temas (Apple, Temu, Black Friday)
├── el_cuello.py                         # Punto de entrada (compatibilidad)
├── carteleria.py                        # Clase principal (legacy)
├── admin15_carteleria.py                # Admin de cartelería
├── escala_tv.py                         # Escalado de imágenes para TV
├── utils_condiciones.py                 # Utilidades
│
├── configuraciones/                      # Widgets de configuración
│   ├── __init__.py
│   ├── info_negocio.py                  # Información del negocio
│   ├── indicador_red_widget.py          # Widget de estado de red
│   └── reloj_widget.py                  # Widget de reloj
│
├── lanzador_tv/                         # Módulo lanzador TV (autónomo)
│   ├── __init__.py
│   ├── ui_lanzador_tv.py                # UI Qt simplificada
│   ├── cerebro_lanzador_tv.py           # Servidor HTTP + navegador kiosk
│   ├── window_manager.py                # Gestión de monitores F10/F11
│   ├── _preview_tv.py                  # Vista previa para desarrollo
│   └── la_cara_web/                     # Interfaz web específica del lanzador
│       ├── index.html                    # HTML principal
│       ├── app.js                        # JavaScript con lógica empresarial
│       ├── css/                          # Estilos
│       │   ├── style.css                # CSS base premium
│       │   └── themes/                  # Temas
│       │       ├── apple/
│       │       │   ├── colores.css
│       │       │   └── estilos.css
│       │       ├── temu/
│       │       │   ├── colores.css
│       │       │   └── estilos.css
│       │       └── blackfriday/
│       │           ├── colores.css
│       │           └── estilos.css
│
├── motor_carteleria/                     # Motor principal (motores globales)
│   ├── __init__.py
│   ├── main_board.py                     # Tablero principal (web-only)
│   ├── web_server.py                     # Servidor HTTP local compartido
│   ├── db_sync_worker.py                # Worker de sincronización DB
│   ├── clima_worker.py                  # Worker de clima
│   ├── estado_tv.py                     # Motor de estado de TV (compartido)
│   ├── layout_manager.py                # Layout manager (simplificado)
│   └── motor_publicidad.py              # Motor de publicidad
│
├── assets/                              # Recursos estáticos
│   ├── macos_bg.png
│   ├── chef_lobo.png
│   ├── lluvia.png
│   ├── nube.png
│   └── sol.png
│
├── dashboard/                           # Dashboard (opcional)
│   ├── __init__.py
│   └── dashboard_main.py
│
├── ia_chef_lobo/                        # IA Chef (opcional)
│   ├── __init__.py
│   ├── motor_ia.py
│   ├── gemini_worker.py
│   └── generar_plantillas_ia.py
│
├── modo_procesos/                        # Procesos de red (opcional)
│   ├── __init__.py
│   ├── buscador_red_worker.py
│   └── espera_conexion.py
│
├── motor_descuentos_ui/                 # UI de descuentos (opcional)
│   ├── __init__.py
│   ├── ofertas_main.py
│   └── componentes/
│       ├── __init__.py
│       ├── creador_promociones.py
│       ├── dialogo_combos.py
│       └── tabla_ofertas.py
│
├── carteleria_hub/                       # Hub de cartelería (opcional)
│   ├── __init__.py
│   ├── hub_admin.py
│   └── hub_principal.py
│
└── red_lan/                             # Red LAN (opcional)
    ├── __init__.py
    └── red_lan_main.py
```

## 🎯 Flujo de Datos Actual

```
Inventario (SQLite/MariaDB)
    ↓
db_sync_worker.py
    ↓
main_board.py (carga productos)
    ↓
web_server.py (API /api/state)
    ↓
app.js (lógica empresarial)
    ↓
index.html (renderizado)
```

## 🧠 Lógica Empresarial en app.js

1. **Amazon ML** - Scoring de productos
2. **Netflix** - Personalización por hora
3. **Uber** - Precios dinámicos (surge pricing)
4. **Airbnb** - Categorización por departamento
5. **Spotify** - Discovery y trending
6. **Shopify** - Combos inteligentes
7. **Notion** - Organización de precios
8. **Stripe** - UX premium

## 📊 Estado Final

- ✅ Estructura limpia y organizada
- ✅ Sin archivos duplicados
- ✅ Código obsoleto eliminado
- ✅ Lógica empresarial implementada
- ✅ Interfaz web premium funcional
- ✅ Temas dinámicos activos
- ✅ Conexión con inventario real
