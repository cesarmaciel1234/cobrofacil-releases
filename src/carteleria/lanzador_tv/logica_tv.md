# 📺 Lógica y Funcionamiento de la Cartelería TV

Este documento explica de forma sencilla cómo funciona el módulo de la TV. Está pensado para que cualquiera pueda entender la arquitectura y saber exactamente dónde buscar cuando quiera cambiar algo, sin necesidad de saber programar.

---

## 1. El Concepto Principal: El "Cerebro" y la "Pantalla Tonta"

El sistema funciona con dos partes separadas que hablan entre sí:

*   **El Cerebro (CobroFacil POS - Python):** Es tu computadora de ventas. Acá es donde el sistema sabe qué productos hay, los precios, el stock y cuántas ventas tuvo cada cosa.
*   **La Pantalla Tonta (La Cara Web - HTML/JS):** Es lo que se ve en la TV. No calcula nada por su cuenta. Simplemente le pregunta al Cerebro todo el tiempo: *"¿Qué muestro ahora?"* y lo dibuja en pantalla.

---

## 2. El Blindaje Total (La Separación en 3 Capas)

Para que el sistema sea seguro, no se rompa por accidente y sea fácil de editar, lo dividimos en tres capas estrictamente aisladas. Si querés cambiar algo, tenés que ir al archivo correcto de la capa correcta:

### Capa 1: Lógica de Negocio (El Director)
*   **Archivos clave:** pp.js (dentro de la_cara_web) y el código Python.
*   **¿Qué hace?:** Define **qué** se muestra y **cuándo**. Por ejemplo:
    *   Decide que los productos con más ventas van primero (como en Amazon).
    *   Cambia automáticamente el tema según la hora (claro a la mañana, oscuro a la noche).
    *   Pregunta al servidor cada 2 o 3 segundos si cambiaron los precios.
*   **Regla:** Acá **no hay nada de diseño ni de colores**.

### Capa 2: Estructura Visual (El Esqueleto)
*   **Archivos clave:** index.html, style.css (importa base.css y cards.css), columna4_chef.css. Cada tema importa structural_base.css.
*   **¿Qué hace?:** Define los tamaños de las cajas, en qué parte de la pantalla va cada cosa, cómo se hacen más grandes o más chicas según el tamaño del televisor (zoom automático).
*   **Regla:** Acá **no hay nada de colores ni diseño visual puro**. El esqueleto es "daltónico". Solo usa variables vacías esperando que un tema las llene.

### Capa 3: La Piel y los Colores (Los Temas)
*   **Archivos clave:** Carpeta 	hemes/ (ej: 	emu/colores.css, premium/colores.css).
*   **¿Qué hace?:** Define los fondos, los degradados, si los bordes son rojos, amarillos, si las letras tienen sombras brillantes, etc.
*   **Regla:** Acá **solo hay colores y maquillaje**. Cada tema es una "burbuja" super privada. Si elijes el tema Temu, la TV borra de su memoria los colores de Premium. Por lo tanto, si tocás algo en Temu, es imposible que rompas Premium.

---

## 3. ¿Cómo funciona el Empaquetado? (El archivo 	v_cara.bin)

Cuando ves el ejecutable final (CobroFacil_POS.exe), no vas a ver las carpetas de imágenes y colores de la TV sueltas. 

Por seguridad y prolijidad, todo lo que está en la carpeta la_cara_web se comprime, se encripta y se mete en una "caja fuerte" llamada **	v_cara.bin**.

**¿Cómo es el viaje?**
1. Vos hacés un cambio en 	emu/colores.css.
2. Al compilarse el programa, un script agarra todos esos archivos y los tritura dentro del 	v_cara.bin.
3. Cuando abrís el sistema en el local, el ejecutable lee ese .bin en su memoria interna (sin descargar basura en el disco duro del cliente) y "levanta" la página web para la TV de forma invisible.

---

## 4. Guía Rápida: "¿Dónde toco si quiero cambiar...?"

*   **¿... el color del sombreado de la tarjeta de la TV?**
    Vas a la_cara_web/css/themes/[tu_tema]/colores.css.
*   **¿... el grosor o la ubicación de la barra lateral?**
    Vas a la_cara_web/css/columna4_chef.css o ase.css (Capa Estructura).
*   **¿... cómo calcula quién es el Top 1 en ventas?**
    Vas a la_cara_web/app.js (Capa Lógica).
*   **¿... el diseño de la ventanita desde donde lanzo la TV en el sistema de ventas?**
    Vas a src/ui_components/carteleria_tv/ (ahí están los .qss de esa pantalla específica del sistema).

> **Resumen del blindaje:** Podés jugar tranquilo con los .css de los temas. Si te equivocás escribiendo un color, a lo sumo ese botón quedará invisible o gris en ese tema, pero la estructura de la TV no va a explotar y el sistema de ventas seguirá cobrando sin enterarse.
