# Columna 3 en la cara

Qué hace: pinta la pregunta «¿Llevás…?» y rota con la oferta relámpago.

Qué función: `iniciarRotacionColumna3` en `columna3.js`. La tarjeta es `htmlTarjetaCruzada` en `tarjetas/tarjeta_cruzada.js`.

Cómo funciona: si `/api/state` trae `columna3`, usa esos slides. No rearma la pregunta con el rubro del catálogo cuando el motor ya mandó pares. Rota cada 7 s. Si no hay slides, muestra el texto vacío.

Qué no debe cambiar: no inventar acompañantes en el navegador si el JSON ya trae `tipo: cruzada`.
