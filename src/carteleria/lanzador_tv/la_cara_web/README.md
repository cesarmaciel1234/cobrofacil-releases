# Cara web (TV)

Qué hace: HTML/JS/CSS que Chromium muestra en `http://127.0.0.1:8765/`.

Qué función: `app.js` pide `/api/state`, pinta franja, columnas y zócalo.

Cómo funciona: al abrir, `plantilla.js` pinta la última forma guardada en el navegador (el diseño ya armado) y después `/api/state` solo cambia los datos que variaron. Mientras no hay precios, el poll sigue a 600 ms y no se baja a 4 s. Si el módulo no arranca, la página se recarga sola a los 8 s. Si `/api/state` falla 4 veces seguidas, también. Un JSON sin precios no borra lo que ya se ve ni tapa el esqueleto. `/api/state` lee el tema de memoria: no espera a MariaDB. `fetchState` llama `loadTheme` y después compara `lastDataHash` (precio, oferta, foto, publicidad, sello y el texto del ranking). Si solo cambió una venta, la columna 1 se vuelve a pintar igual. El hash **no** incluye el tema: si solo cambió el vestuario, sale sin `innerHTML`. `loadTheme` cambia `css/themes/<tema>/colores.css` y `estilos.css` (`?v=` = `TV_UI` 268). F5 llama `fetchState`; no `location.reload`. `ajustarZoomTv` usa el `zoom` de Chromium para rasterizar la hoja de 1920×1080 al tamaño real del panel.

Qué no debe cambiar: puerto 8765. No meter MariaDB en el JS. El zócalo se desliza; no rediseñar el naranja desde acá. No recargar `precio_tv.css` al cambiar tema.
