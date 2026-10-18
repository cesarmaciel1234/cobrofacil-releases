# CSS cara TV

Qué hace: hojas de la cara. `claridad_50.css` va al final. Temas en `themes/` (README ahí).

`claridad_50.css`: en 50" se veía ahumado (`mix-blend: screen` + sombras grandes). PNG en recorte sólido, letras con trazo de 1 px. Ranking #1–#4: foto nítida y sombra 3D (sin blend). En el zócalo solo se saca el glow de las letras. La foto no tapa la letra hasta `.is-ready`. Las fotos piden `image-rendering: high-quality` (el escalador de Chromium). No volver a `optimize-contrast`. No prender `backdrop-filter`.

Qué no debe cambiar: columnas, cajero, ni recargar `precio_tv.css` cuando cambia el tema.
