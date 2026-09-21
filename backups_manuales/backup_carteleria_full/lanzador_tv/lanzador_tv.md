# Componente `lanzador_tv`: Visión General y Estructura de Tematización

Este documento detalla la estructura, funcionalidad y, crucialmente, el sistema de tematización del componente `lanzador_tv`, diseñado para ser una guía exhaustiva para futuras interacciones y modificaciones.

## 1. Propósito y Funcionalidad General

El `lanzador_tv` es el componente frontend encargado de renderizar las pantallas de cartelería digital. Su función principal es mostrar información dinámica (ofertas, rankings, precios, mensajes de zócalo, etc.) en diferentes columnas, utilizando una interfaz visual adaptable y personalizable mediante temas.

## 2. Estructura de Archivos y Carpetas Clave

El componente se encuentra en `src/carteleria/lanzador_tv/la_cara_web/`.

```
src/carteleria/lanzador_tv/la_cara_web/
├── app.js                          # Lógica principal del frontend (manejo de datos, renderizado de módulos)
├── index.html                      # Archivo HTML principal que define la estructura base y carga CSS/JS
├── css/
│   ├── base.css                    # Estilos CSS base (reset, tipografía general, etc.)
│   ├── style.css                   # Estilos generales del layout y componentes que no dependen del tema
│   ├── structural_base.css         # NUEVO: Estilos CSS que definen la ESTRUCTURA y LAYOUT COMÚN a TODOS los temas (el "CEREBRO")
│   ├── columna4_chef.css           # Estilos específicos para la columna 4 (Chef)
│   └── themes/                     # Carpeta contenedora de los temas visuales
│       ├── premium/
│       │   ├── colores.css         # Variables CSS para la paleta de colores del tema Premium
│       │   └── estilos.css         # Estilos visuales del tema Premium, usando las variables de colores (la "MÁSCARA")
│       ├── temu/
│       │   ├── colores.css         # Variables CSS para la paleta de colores del tema Temu
│       │   └── estilos.css         # Estilos visuales del tema Temu, usando las variables de colores
│       └── apple/                  # (Ejemplo de otro tema)
│           ├── colores.css
│           └── estilos.css
└── modules/                        # Módulos JavaScript para cada sección/columna de la TV
    ├── columna1/                   # Lógica y renderizado para la Columna 1 (ej. ranking)
    │   └── tarjetas/
    │       └── tarjeta_ranking.js
    ├── columna2/                   # Lógica y renderizado para la Columna 2 (ej. precios)
    │   └── columna2.js
    ├── columna3/                   # Lógica y renderizado para la Columna 3 (ej. oferta relámpago, venta cruzada)
    │   └── tarjetas/
    │       └── tarjeta_cruzada.js
    ├── columna4/                   # Lógica y renderizado para la Columna 4 (ej. chef)
    │   └── tarjetas/
    │       └── tarjeta_chef.js
    ├── mensaje_zocalo/             # Lógica y renderizado para el mensaje de zócalo inferior
    │   └── mensaje_zocalo.js
    └── shared/                     # Componentes o utilidades JavaScript compartidas
        └── plata_y_texto.js
```

## 3. Proceso de Tematización: "Cerebro" y "Máscara"

La arquitectura de tematización sigue el principio de **separación total entre la estructura/layout y los estilos visuales (colores, fondos, sombras específicas)**.

### a) El "Cerebro Estructural": `structural_base.css`

*   **Ubicación**: `src/carteleria/lanzador_tv/la_cara_web/css/structural_base.css`
*   **Función**: Este archivo contiene todas las reglas CSS que definen la **disposición física** de los elementos en la pantalla. Esto incluye:
    *   `display` (flexbox, grid)
    *   `position`, `top`, `left`, `right`, `bottom`
    *   `width`, `height`, `min-height`, `max-width`, `max-height`
    *   `margin`, `padding`, `gap`
    *   `border-radius` (si es un valor fijo, no temático)
    *   `box-shadow` (si es un valor genérico como `0 4px 16px rgba(0,0,0,0.45)` y no temático)
    *   `font-size`, `font-weight`, `line-height`, `letter-spacing` (si son valores fijos, no temáticos)
    *   `overflow`, `z-index`, `transition`, `animation` (la definición de la animación, no sus colores)
*   **Concepto**: Es el "living" y las "habitaciones" de tu edificio. Define cómo se organizan los espacios, las ventanas, las puertas, pero no el color de las paredes ni el tipo de suelo. Es la **base inmutable** de la experiencia de usuario.
*   **Importancia para la IA**: Cualquier cambio en el layout o la disposición de los elementos debe hacerse aquí.

### b) La "Máscara de Colores": `themes/<nombre_tema>/colores.css`

*   **Ubicación**: `src/carteleria/lanzador_tv/la_cara_web/css/themes/<nombre_tema>/colores.css`
*   **Función**: Define exclusivamente un conjunto de variables CSS (`--bg-primary`, `--accent-primary`, `--text-color`, `--shadow-card`, etc.) que representan la paleta de colores y valores visuales específicos para un tema dado.
*   **Concepto**: Son las latas de pintura y los materiales decorativos disponibles para una "máscara" específica. No contienen ninguna regla CSS directa, solo las definiciones de las variables.
*   **Importancia para la IA**: Si se desea cambiar un color global en un tema, se modifica la variable correspondiente aquí.

### c) El "Vestuario del Tema": `themes/<nombre_tema>/estilos.css`

*   **Ubicación**: `src/carteleria/lanzador_tv/la_cara_web/css/themes/<nombre_tema>/estilos.css`
*   **Función**: Este archivo aplica los estilos visuales específicos de un tema, **utilizando las variables definidas en `colores.css`**. Contiene reglas CSS que establecen `background`, `color`, `border-color`, `text-shadow`, `box-shadow`, `linear-gradient`, `radial-gradient`, etc., para los selectores de CSS.
*   **Concepto**: Es el "decorador" que usa las pinturas y materiales de `colores.css` para darle una apariencia única a la estructura definida en `structural_base.css`. Nunca debe contener reglas estructurales (`display`, `position`, `width`, `height`, `margin`, `padding`, `border-radius` fijos, etc.).
*   **Importancia para la IA**: Si se desea cambiar la apariencia específica de un elemento (ej. el color de un botón) *dentro de un tema particular*, se modifica la regla aquí, asegurándose de usar las variables de `colores.css` para mantener la coherencia. Si un elemento tiene un estilo *único* que no se puede expresar con variables (ej. un gradiente muy específico), también se define aquí.

### d) Carga en `index.html`

El `index.html` carga los archivos CSS en un orden específico para garantizar la correcta aplicación:

1.  `base.css` (estilos globales básicos)
2.  `style.css` (estilos generales del layout)
3.  `structural_base.css` (la estructura común)
4.  `themes/<tema_actual>/colores.css` (las variables de color del tema activo)
5.  `themes/<tema_actual>/estilos.css` (los estilos visuales del tema activo, aplicando las variables)

Este orden asegura que la estructura se define primero, y luego los colores y estilos visuales del tema sobrescriben los valores por defecto o aplican los suyos propios.

## 4. Componentes Principales (Módulos JavaScript)

Los archivos en la carpeta `modules/` gestionan la lógica y el renderizado de contenido para las diferentes secciones de la TV:

*   **`columna1`**: Generalmente muestra rankings o listas destacadas.
*   **`columna2`**: Dedicada a la visualización de precios y ofertas.
*   **`columna3`**: Implementa las "ofertas relámpago" y secciones de venta cruzada.
*   **`columna4`**: Utilizada para contenido "Chef" o presentaciones especiales.
*   **`mensaje_zocalo`**: Gestiona la barra de mensajes deslizante en la parte inferior de la pantalla.

Cada módulo es responsable de buscar sus propios datos (a través de `app.js` o directamente) y renderizarlos en el HTML correspondiente dentro de `index.html`.

## 5. Flujo de Datos y Renderizado (Simplificado)

1.  El navegador carga `index.html`.
2.  Se cargan todos los archivos CSS en el orden especificado, estableciendo la estructura y los estilos del tema activo.
3.  Se carga `app.js`.
4.  `app.js` inicializa los diferentes módulos (`columna1`, `columna2`, etc.).
5.  Estos módulos, a su vez, obtienen los datos necesarios y actualizan el DOM en las secciones correspondientes (`#content1`, `#content2`, etc.).
6.  La lógica de cambio de tema (si la hay) se maneja en `app.js` modificando los atributos `href` de los `<link>` con `id="theme-colors"` y `id="theme-styles"` y el atributo `data-theme` del `body`.

## 6. Consideraciones Clave para la IA (Instrucciones para Trabajar con este Componente)

Para trabajar de manera eficiente con el `lanzador_tv`, ten en cuenta lo siguiente:

*   **Prioridad de `structural_base.css`**: Este archivo es el "cerebro". Si necesitas ajustar el layout, el tamaño, el espaciado o la posición de un elemento de forma global para todos los temas, **siempre** modifica `structural_base.css`.
*   **Modificaciones de Estilo Visual**:
    *   Si un color, fondo o sombra es global y se usa en varios temas, considera definirlo como una variable en `colores.css` (o un archivo global de variables si se crea).
    *   Si un color, fondo o sombra es **específico de un tema**, asegúrate de que esté definido en `themes/<nombre_tema>/colores.css` (como variable) y aplicado en `themes/<nombre_tema>/estilos.css`.
*   **Añadir un Nuevo Tema**:
    1.  Crea una nueva carpeta en `themes/` (ej. `themes/blackfriday/`).
    2.  Dentro, crea `colores.css` con las variables de color del nuevo tema.
    3.  Crea `estilos.css` para aplicar los estilos visuales del nuevo tema, **utilizando las variables definidas en su `colores.css`** y apoyándose en `structural_base.css` para la disposición.
    4.  Actualiza `index.html` (o la lógica de cambio de tema en `app.js`) para cargar el nuevo tema.
*   **Evitar Duplicidad Estructural**: No añadas reglas de layout, posicionamiento o tamaño a los archivos `estilos.css` de los temas individuales si ya están o deberían estar en `structural_base.css`. Esto mantendría la coherencia y facilitaría el mantenimiento.
*   **Uso de Variables**: Siempre que sea posible, utiliza las variables CSS (`var(--nombre-variable)`) para los colores y otros valores temáticos en `estilos.css` para asegurar la consistencia.

Al seguir estas directrices, podemos mantener la codebase del `lanzador_tv` organizada, modular y fácil de extender con nuevos temas sin afectar la estructura fundamental.
