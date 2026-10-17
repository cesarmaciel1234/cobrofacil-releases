# Ranking de cartelería

Qué hace: arma «lo más vendido» para la columna 1 de la TV.

Qué función: `ranking_carteleria` (ventas de esta PC), `asegurar_ranking` (la esclava lo baja de la maestra), `completar_ranking_local` (la maestra, si el pulso vino sin ranking).

Cómo funciona: hoy, ayer y semana, en frecuencia y volumen. Un dict vacío no cuenta como ranking: la TV de la maestra vuelve a leer `MotorVentas`.

Qué no debe cambiar: la esclava no pisa el ranking de la maestra con ventas locales sueltas.
