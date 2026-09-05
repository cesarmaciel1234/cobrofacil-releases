# ESTRUCTURA CARTELERÍA - Documentación Técnica y Arquitectura

Este documento describe la arquitectura, flujo de datos y responsabilidad de cada módulo dentro del sistema de Cartelería Digital. La cartelería está diseñada con una arquitectura limpia, separando la interfaz de usuario (TV), la lógica de negocio y la comunicación con la base de datos.

## 📁 Estructura Principal y Responsabilidades

```text
src/carteleria/
├── __init__.py                          # Inicialización del módulo de cartelería.
├── theme.py                             # Sistema de gestión de temas visuales. Permite alternar entre estilos predefinidos (Apple, Temu, Black Friday) para mantener una interfaz adaptativa.
├── el_cuello.py                         # Punto de entrada moderno y capa de compatibilidad para enlazar componentes sin dependencias circulares.
├── carteleria.py                        # Clase principal (legacy). Contiene la lógica inicial de la cartelería, mantenida por compatibilidad.
├── admin15_carteleria.py                # Panel de administración de la cartelería. Permite a los usuarios configurar qué se muestra, tiempos de rotación y reglas generales.
├── escala_tv.py                         # Utilidad para el escalado dinámico de imágenes y elementos UI para asegurar que se vean correctamente en diferentes resoluciones de TV.
├── utils_condiciones.py                 # Funciones auxiliares para evaluar condiciones (ej. horas felices, días de descuento, etc.).
├── assets_paths.py                      # Gestor centralizado de rutas absolutas para los recursos estáticos (imágenes, fuentes, etc.).
│
├── configuraciones/                      # Widgets y componentes de configuración visual.
│   ├── info_negocio.py                  # Widget que muestra/edita la información del negocio en pantalla.
│   ├── indicador_red_widget.py          # Elemento UI que muestra el estado de conexión de red actual.
│   └── reloj_widget.py                  # Widget de reloj en tiempo real para la pantalla.
│
├── lanzador_tv/                         # Módulo lanzador TV (Cliente / Frontend autónomo).
│   ├── ui_lanzador_tv.py                # Interfaz de usuario simplificada usando PyQt.
│   ├── cerebro_lanzador_tv.py           # Orquestador del lanzador, inicia el navegador en modo kiosk o la vista incrustada.
│   ├── window_manager.py                # Gestión de monitores (manejo de modo pantalla completa F10/F11, selección de pantalla secundaria).
│   ├── _preview_tv.py                   # Herramienta para visualizar cómo quedará la cartelería durante el desarrollo.
│   └── la_cara_web/                     # Frontend web renderizado en la TV.
│       ├── index.html                   # Documento HTML principal que estructura la vista de la TV.
│       ├── app.js                       # Core de lógica empresarial en el lado del cliente (JS). Recibe datos del servidor local.
│       └── css/                         # Hojas de estilo y temas (Apple, Temu, BlackFriday).
│
├── motor_carteleria/                     # Motor principal backend (datos / sync).
│   ├── main_board.py                     # Alias de CarteleriaMainTV.
│   ├── web_server.py                     # Compat: reexporta ServidorCuello de cerebro_lanzador_tv.
│   ├── db_sync_worker.py                 # Hilo de fondo (worker) que sincroniza cambios desde el Inventario (SQLite/MariaDB) hacia la memoria.
│   ├── clima_worker.py                   # Worker encargado de consultar y actualizar el estado del clima.
│   ├── estado_tv.py                      # Gestor del estado actual de lo que debe mostrar la TV.
│   ├── layout_manager.py                 # Gestor de distribución (layouts), decide qué diseño de pantalla usar basado en los productos.
│   └── motor_publicidad.py               # Motor encargado de inyectar anuncios o promociones rotativas.
│
├── el_cerebro/                           # Compat vacío: reexporta estado_tv. No agregar lógica acá.
│
├── assets/                               # Recursos estáticos globales (fondos, iconos como clima y mascotas).
├── creador_png/                          # Creador PNG: panel Qt + UI HTML. Salida en Catalogos/png_productos/.
│   ├── __init__.py                       # Exporta DialogoCreadorPNG, PanelPngProductos, quitar_fondo_negro.
│   ├── panel_png_productos.py            # Lista de productos, asociar PNG, botón Creador PNG Pro.
│   ├── ventana_html.py                   # QDialog con QWebEngineView (o abre el navegador).
│   ├── servidor.py                       # Levanta Flask en 127.0.0.1 (5000 / 5055–5057) en un hilo.
│   ├── app.py                            # Rutas Flask: /, /convert, /api/ping, archivos de salida.
│   ├── convertir_imagen.py               # Recorte de fondo + color + sombra (en el mismo proceso).
│   ├── presets.py                        # Estilos: carteleria, fresco, intenso, cromo, frio_rocio.
│   ├── fondo_transparente.py             # Flood-fill de fondo negro (galería de iconos, no el HTML).
│   ├── rutas.py                          # Helpers de paths (hoy no lo usa app.py).
│   ├── templates/index.html              # UI del creador.
│   ├── static/app.js + estilos.css       # Cliente: subir foto, presets, usar imagen.
│   └── uploads/ / converted/             # Temporales (gitignore). El PNG final va a Catalogos/png_productos/.
│
├── ia_chef_lobo/                         # Integración con Inteligencia Artificial.
│   ├── motor_ia.py                       # Orquestador principal de solicitudes a IA.
│   ├── gemini_worker.py                  # Worker de integración con la API de Google Gemini.
│   └── generar_plantillas_ia.py          # Generador de layouts y textos publicitarios apoyado por IA.
│
├── motor_descuentos_ui/                  # Interfaces y gestores para el sistema de ofertas.
│   ├── ofertas_main.py                   # Módulo principal para aplicar lógica de ofertas a los productos de la cartelería.
│   └── componentes/                      # Diálogos y tablas (Creador de promociones, combos, tabla de ofertas).
│
├── modo_procesos/                        # Gestión de procesos paralelos de red.
│   ├── buscador_red_worker.py            # Busca otras instancias o conexiones en la red.
│   └── espera_conexion.py                # Módulo de espera de respuesta (handshake).
│
├── carteleria_hub/                       # Hub de sincronización de múltiples cartelerías.
│   ├── hub_admin.py                      # Interfaz de administración para conectar múltiples TVs.
│   └── hub_principal.py                  # Lógica del nodo principal del Hub.
│
├── dashboard/                            # Dashboard administrativo o analítico opcional para control de métricas.
└── red_lan/                              # Comunicación por Red Local (LAN) para control remoto o envío de comandos a las pantallas.
```

## Creador PNG — flujo

1. Cartelería o dashboard abre `PanelPngProductos`.
2. **Creador PNG Pro** abre `DialogoCreadorPNG` → `servidor.asegurar_servidor()` → Flask (`app.py`).
3. El HTML llama `POST /convert`. Flask ejecuta `crear_efecto_3d_realista` en el mismo proceso.
4. El PNG queda en `Catalogos/png_productos/`. El diálogo lee el título `CREADOR_PNG_DONE:` y asocia el archivo al producto.

No hay carpeta `creator png` (nombre viejo). `version.json` todavía lista rutas de esa carpeta.

## 🎯 Flujo de Datos y Arquitectura

El sistema funciona con un esquema de **Servidor Local (Motor Backend)** + **Cliente Web (Lanzador TV)**. Esto permite separar de forma robusta la carga de procesamiento de base de datos de la interfaz visual de la TV.

1. **Sincronización de Base de Datos**: `db_sync_worker.py` lee constantemente (o mediante eventos) la base de datos principal del sistema (MariaDB/SQLite) y extrae los productos actualizados.
2. **Tablero y Estado**: `main_board.py` y `estado_tv.py` procesan y estructuran los datos extraídos en un formato JSON listo para consumo del frontend.
3. **API Local**: `cerebro_lanzador_tv.py` (`ServidorCuello`) sirve la cara TV desde `tv_cara.bin` (o `la_cara_web` en dev) y expone `/api/state`. `web_server.py` solo reexporta esas clases.
4. **Cliente Web (Navegador)**: el mismo cerebro abre Chrome/Edge en kiosk. `app.js` hace polling a `/api/state`.
5. **Renderizado**: `app.js` recibe el JSON con el estado de la TV e inyecta la información dinámicamente en el DOM de `index.html`.

## 🧠 Lógica Empresarial en el Cliente (`app.js`)

Para liberar carga del servidor Python local y aprovechar el rendimiento en navegador para animaciones, gran parte de la lógica de negocio visual está implementada directamente en el frontend:

1. **Scoring de Productos (Estilo Amazon)**: Califica productos basado en niveles de stock o banderas de ventas para decidir cuáles destacar en pantalla grande.
2. **Personalización Temporal (Estilo Netflix)**: Cambia automáticamente la paleta de colores o el enfoque del contenido dependiendo de la hora del día (mañana, tarde o noche).
3. **Precios Dinámicos (Estilo Uber)**: Aplica efectos visuales llamativos para resaltar precios reducidos, combos u ofertas de tiempo limitado.
4. **Categorización Fluida (Estilo Airbnb)**: Organización automática de productos agrupados por categorías o departamentos (ej. Carnes, Bebidas, Lácteos) facilitando la lectura a distancia.
5. **Discovery (Estilo Spotify)**: Animaciones suaves para mostrar productos en tendencia o nuevos ingresos en un bloque rotativo.
6. **Combos Inteligentes (Estilo Shopify)**: Agrupa visualmente productos que se compran juntos con frecuencia para incentivar la venta cruzada.
7. **Organización Limpia (Estilo Notion)**: Uso de estructuras de listas y tarjetas minimalistas, sin saturar la pantalla.
8. **UX Premium (Estilo Stripe)**: Foco en la fluidez de animaciones a 60 fps, transiciones sin saltos bruscos y tipografías legibles.

## 📊 Integraciones Avanzadas

- **IA Chef Lobo**: Módulo impulsado por la API de Google Gemini para redactar eslóganes automáticamente, mejorar los textos publicitarios y sugerir paletas de colores basadas en eventos o temporadas.
- **Multitalla y Resoluciones**: Mediante `escala_tv.py` y `window_manager.py`, el sistema se adapta inteligentemente a monitores extra (por HDMI o red), escalando a proporciones Full HD (1920x1080) o 4K dependiendo de la pantalla secundaria elegida.
- **Hub y Red LAN**: Permite tener un nodo principal (Servidor/Caja) que transmite los productos y su estado hacia múltiples pantallas satélites conectadas a la misma red local.
