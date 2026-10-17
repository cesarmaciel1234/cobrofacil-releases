# Cara web (TV)

Qué hace: HTML/JS/CSS que Chromium muestra en `http://127.0.0.1:8765/`.

Qué función: `app.js` pide `/api/state`, pinta franja, columnas y zócalo.

Cómo funciona: poll 600 ms hasta tener precios+rotación, después 4 s. `precargarFotosEstado` corre antes de pintar. Un JSON sin precios no borra lo que ya se ve. `fetchState` llama `loadTheme` y después compara `lastDataHash` (precios, rotación, sello). El hash **no** incluye el tema: si solo cambió el vestuario, sale sin `innerHTML`. `loadTheme` cambia `css/themes/<tema>/colores.css` y `estilos.css` (`?v=` = `TV_UI` 268). F5 llama `fetchState`; no `location.reload`.

Qué no debe cambiar: puerto 8765. No meter MariaDB en el JS. El zócalo se desliza; no rediseñar el naranja desde acá. No recargar `precio_tv.css` al cambiar tema.
