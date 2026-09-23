# Vista de Nexus

`NexusMainView` arma los tres paneles y no consulta la base.

`_setup_ui` coloca izquierdo, centro y derecho. `_aplicar_estilos` recibe `light` u `oscuro` y repinta. El controlador le avisa cuando cambia el tema, así no hace falta reiniciar.

`_play_sound` dispara el sonido de alerta cuando el controlador manda un cierre. No decide si el cierre es válido.
