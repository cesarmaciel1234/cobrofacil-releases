# 📖 Manual de Supervivencia: Estructura del Proyecto TPV

Este pequeño manual está diseñado para que cualquier persona, sin importar su nivel de programación, pueda entender cómo está organizado el sistema de CobroFacil POS y para qué sirve cada carpeta y archivo.

---

## 🗺️ Mapa Visual del Proyecto

Así se ve tu proyecto desde arriba. Esta es la guía rápida para encontrar lo que buscas:

```text
📁 tpv pro 2026/
│
├── 📁 01_Compiladores_y_Ejecutables/  <-- (Fábrica de .exe e Instalador Web)
├── 📁 02_Soporte_y_Mantenimiento/     <-- (DrHouse, Creador de Licencias)
├── 📁 03_Actualizaciones_y_Red/       <-- (El Actualizador de Firebase)
├── 📁 04_Respaldos_y_Migraciones/     <-- (Importadores de BD Eleventa, Backups)
│
├── 📁 docs/
│   └── 📄 MANUAL_ESTRUCTURA_PROYECTO.md <-- (Este manual de uso)
│
├── 📁 logs/                           <-- (Todos los reportes de error ocultos aquí)
│
├── 📁 src/                            <-- (EL CORAZÓN DEL CÓDIGO)
│   ├── 📁 admin/                      <-- (Pantallas del jefe)
│   ├── 📁 base_de_datos/              <-- (Conexiones SQLite y MariaDB)
│   ├── 📁 cajero/                     <-- (Pantallas de venta y chatbot)
│   ├── 📁 hardware/                   <-- (Impresoras, balanzas)
│   ├── 📁 inicio_y_perfiles/          <-- (Login, Licencia, Selección de Perfil)
│   └── 📁 ui/                         <-- (Diseños visuales)
│
├── 📄 main.py                         <-- (Botón de encendido principal)
├── 📄 punpro.db                       <-- (Tu Base de Datos local SQLite)
├── 📄 config.json                     <-- (Tus configuraciones locales)
├── 📄 version.json                    <-- (Versión actual para el actualizador)
└── 📄 requirements.txt                <-- (Lista de paquetes Python necesarios)
```

---

## 1. 📂 Las 4 Carpetas Maestras (Herramientas Externas)
Estas carpetas contienen programas que NO son el punto de venta en sí, sino herramientas que te ayudan a ti como creador a administrarlo.

*   **`01_Compiladores_y_Ejecutables/`**
    *   **¿Para qué sirve?**: Aquí está la "fábrica" de tu programa. Contiene los scripts que transforman tu código de texto en archivos `.exe` que tus clientes pueden instalar.
    *   **¿Qué tiene adentro?**: `Compilar_Todo.bat` (para crear el programa completo), el creador del Instalador Web, y los scripts que arman los archivos ZIP para subir a Firebase.
*   **`02_Soporte_y_Mantenimiento/`**
    *   **¿Para qué sirve?**: Son tus herramientas de "Mecánico".
    *   **¿Qué tiene adentro?**: El `DrHouse_Diagnostico.py` para arreglar problemas en computadoras de clientes, el `Generador_Licencias.py` para vender claves, y scripts para configurar el Firewall de Windows.
*   **`03_Actualizaciones_y_Red/`**
    *   **¿Para qué sirve?**: Todo lo que conecta a tus clientes con tus nuevos parches.
    *   **¿Qué tiene adentro?**: El `Actualizador.py` (el motor que descarga los ZIPs de Firebase) y herramientas para detectar computadoras en red LAN.
*   **`04_Respaldos_y_Migraciones/`**
    *   **¿Para qué sirve?**: Los salvavidas de la información.
    *   **¿Qué tiene adentro?**: `RespaldoAutomatico.py` (para hacer backups), y scripts para importar bases de datos antiguas de sistemas como Eleventa.

---

## 2. 📂 El Corazón del Sistema (`src/`)
Esta es la carpeta más importante. Contiene TODO el código de las pantallas, botones y funciones que ve el cajero.

*   **`inicio_y_perfiles/`**: Todo lo que pasa ANTES de entrar al sistema. (Pantalla de bienvenida, licencia, selector de cajero/admin, y la ventana de login con contraseña).
*   **`cajero/`**: La pantalla de cobro. Lectura de código de barras, sumar productos, dar vuelto, y el chatbot animado.
*   **`admin/`**: Las pantallas del jefe. Ver estadísticas, agregar inventario, imprimir etiquetas de precios, configurar ofertas.
*   **`base_de_datos/`**: El cerebro de memoria. Aquí están las reglas para leer, guardar o modificar información en las bases de datos SQLite y MariaDB.
*   **`hardware/`**: Controladores de aparatos físicos (impresoras de tickets térmicos, gavetas de dinero, balanzas).
*   **`ui/` y `ui_components/`**: Los diseños visuales, colores, bordes redondeados y botones del programa.
*   **`utils/` y `tools/`**: Herramientas matemáticas y lógicas que el sistema usa por detrás para hacer cálculos.

---

## 3. 📄 ¿Qué son todos esos archivos sueltos que sobraron?

Si miras la carpeta principal, notarás que quedaron algunos archivos sueltos. Esto es normal y necesario, porque son el punto de anclaje de todo el proyecto:

*   **`main.py`**: Es el botón de encendido. Cuando haces doble clic aquí, este archivo llama a todas las carpetas dentro de `src/` y enciende el sistema.
*   **`punpro.db` y `AQVGI.db`**: Son tus bases de datos SQLite actuales. Aquí se guardan los productos, ventas y usuarios en tu propia computadora.
*   **`config.json`**: Un archivo de texto que guarda la configuración local de tu computadora (qué impresora usas, si el tema es oscuro/claro, etc).
*   **`version.json`**: El "DNI" de tu programa. Tiene todos los códigos matemáticos y la versión (`3100.00`) para que el actualizador sepa qué archivos cambiar.
*   **`requirements.txt`**: La lista de ingredientes. Le dice a Python qué herramientas extra necesita descargar de internet para que tu código funcione (como PyQt5 para los gráficos).
*   **Archivos `.log` (`crash.log`, `stderr.log`)**: Son "cajas negras" de aviones. Si el programa se rompe, Python escribe aquí por qué se rompió para que puedas leerlo después.
*   **`CobroFacilPOS_v3.zip`**: Es el bloque empaquetado final que subiste a Firebase.
*   **`.gitignore`**: Un archivo oculto que le dice a GitHub "por favor, ignora los ZIPs pesados y las bases de datos locales, no las subas a internet".

---
*Escrito de forma sencilla y directa, para que nunca te pierdas navegando en tu propio código.*
