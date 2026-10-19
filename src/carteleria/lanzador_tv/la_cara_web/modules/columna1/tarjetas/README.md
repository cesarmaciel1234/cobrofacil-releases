# Tarjetas ranking

Qué hace: HTML de una tarjeta #1–#4 (nombre, etiqueta, recuadro PNG). Sin precio.

Qué función: `htmlTarjetaRanking` en `tarjeta_ranking.js`.

Cómo funciona: llama `htmlDealStage` de `foto_tarjeta`. La letra tapa hasta que el PNG está listo. PNG chico (`is-chica`) se agranda; sombra 3D en `claridad_50.css`. Si el motor ya mandó `detalle`, se muestra ese texto. Si no, el mismo camuflaje: kilos como `4,5 %`, plata como `56.00%` (÷ 1000), tickets como `3+ familias lo eligieron`.

Qué no debe cambiar: no agregar precio acá. No destapar pesos, kg ni la palabra tickets.
