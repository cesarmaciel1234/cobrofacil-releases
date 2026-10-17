# Módulos de la cara

Qué hace: un módulo por franja de la TV (hero, ranking, precios, cruzada, chef, zócalo).

Qué función: cada carpeta exporta su `render*` o `iniciarRotacion*`. `app.js` las llama en orden.

Cómo funciona: reciben el JSON de `/api/state`. Las tarjetas con PNG importan `foto_tarjeta`. Las filas de precio no.

Qué no debe cambiar: no cruzar estado con el cajero. No pintar foto en `fila_precio.js`.
