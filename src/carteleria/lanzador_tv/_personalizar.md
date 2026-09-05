# 🎨 Guía Definitiva: Cómo Personalizar la Interfaz sin Romper el Blindaje

Si querés mejorar el diseño de la TV, mover cajas, hacer textos más grandes o agregar funcionalidades visuales, este es el flujo de trabajo exacto que tenés que usar. 

Siguiendo esta guía te asegurás de que **tu mejora aplique automáticamente a todos los temas (Temu, Premium, Apple, etc.)**, sin que los colores se mezclen.

---

## 1. Cambios de "Esqueleto" (Estructura, Tamaños y Posiciones)

Si estás mirando el tema Premium y querés que el precio sea más grande o que las esquinas de una tarjeta sean más redondas:

*   **¿Dónde lo hacés?:** En los archivos globales (ej: ase.css, cards.css, columna4_chef.css).
*   **¿Qué lográs con esto?:** Como estos archivos son compartidos, **cualquier cambio impacta en todos los temas al instante**. No tenés que repetir el trabajo 4 veces.
*   **🚨 REGLA DE ORO 🚨:** Mientras edites estos archivos globales, **tenés PROHIBIDO escribir un color fijo** (ejemplo: ackground: red; o color: #FFFFFF;). Aquí solo modificás estructura: width, ont-size, margin, padding, order-radius, display: flex, etc.

---

## 2. Cómo agregar Cajas Nuevas y darles Color

Supongamos que agregás un cartelito nuevo en el HTML que dice *"¡Última Unidad!"* y querés que tenga fondo y color de letra, adaptándose al estilo de cada tema.

### Paso 1: Crear la estructura (Archivo Global)
Vas a cards.css (o el CSS estructural que corresponda) y armás la caja. Para el color, vas a inventar una **variable** usando un color "de rescate" (fallback) por si algún tema se olvida de configurarlo. Se escribe así:

`css
/* Dentro de cards.css o columna4_chef.css */
.cartel-ultima-unidad {
    font-size: 14px;
    padding: 5px;
    border-radius: 8px;
    
    /* ACÁ ESTÁ EL TRUCO MÁGICO: var(--nombre-variable, color-de-rescate) */
    background: var(--bg-ultima-unidad, #000000); 
    color: var(--texto-ultima-unidad, #FFFFFF);
}
`
*Si parás acá, todos los temas de la TV van a mostrar este cartel con fondo negro y letra blanca (el rescate).*

### Paso 2: Darle la "Piel" en cada Tema
Ahora, querés que el cartel combine con el estilo de cada tienda. Vas a ir a las carpetas de los temas y le vas a dar valor a esa variable que inventaste.

**A) Para el tema Premium:**
Abrís css/themes/premium/colores.css y agregás:
`css
:root {
    --bg-ultima-unidad: #FFD700; /* Fondo Dorado */
    --texto-ultima-unidad: #000000; /* Letra Negra */
}
`

**B) Para el tema Temu:**
Abrís css/themes/temu/colores.css y agregás:
`css
:root {
    --bg-ultima-unidad: #FF0000; /* Fondo Rojo Chillón */
    --texto-ultima-unidad: #FFFFFF; /* Letra Blanca */
}
`

---

## 3. Resumen del Flujo de Trabajo Ideal

1. **Iniciá el sistema** con el Tema Premium (o tu favorito) activo en pantalla.
2. **Jugá con la estructura:** Abrí index.html y los archivos como columna4_chef.css para mover cosas de lugar, cambiar formas y tamaños. **(Acordate: 0 colores fijos acá).** Al guardar, todos los temas ya heredaron esa nueva estructura automáticamente.
3. **Usá Variables:** Si necesitás que tu nueva estructura tenga color de fondo o borde, ponelo como ar(--tu-nombre-inventado).
4. **Coloreá:** Pasá por los archivos colores.css de cada tema (	emu, pple, premium) y asignale a esa variable inventada el código de color exacto que requiera ese estilo.

¡Con este método tu diseño puede evolucionar infinitamente, manteniéndose profesional, ordenado y 100% blindado!
